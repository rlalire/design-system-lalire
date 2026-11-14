// Bloc treuil micro — firmware v0.2
//
// Un moteur de gimbal avec encodeur entraîne directement une bobine étroite. Le moteur est
// piloté en couple : le courant qu'on lui donne fixe la force sur le fil. Cela permet de
// plafonner la tension du fil, de sentir un fil accroché et de mesurer sa charge de rupture.
//
// Position = longueur de fil déroulée en mm ; 0 = origine haute, positif = descente.
// Le protocole OSC est décrit dans ../README.md.

#include <Arduino.h>
#include <ETH.h>
#include <WiFiUdp.h>
#include <SPI.h>
#include <Preferences.h>
#include <SimpleFOC.h>
#include "config.h"
#include "osc.h"

enum State : uint8_t {
  ST_DISARMED  = 0,  // moteur coupé : l'objet n'est plus retenu
  ST_HOLD      = 2,  // armé, immobile
  ST_GOTO      = 3,  // déplacement temporisé (courbe douce)
  ST_STREAM    = 4,  // suivi d'une consigne envoyée en continu
  ST_JOG       = 5,  // déplacement manuel en vitesse
  ST_HOMING    = 6,  // remontée douce jusqu'à la butée haute
  ST_STOPPING  = 7,  // décélération jusqu'à l'arrêt
  ST_FAULT     = 8,  // défaut : il faut /reset
  ST_BREAKTEST = 9,  // mesure de la charge de rupture du fil
  ST_MEASURE   = 10, // mesure d'une longueur : remontée douce jusqu'à ce que le fil se tende
};
enum Fault : uint8_t { F_NONE = 0, F_ESTOP = 1, F_SNAG = 3 };

static BLDCMotor motor(MOTOR_POLE_PAIRS, MOTOR_PHASE_R, MOTOR_KV);
static BLDCDriver3PWM driver(PIN_PWM_A, PIN_PWM_B, PIN_PWM_C, PIN_DRV_EN);
static MagneticSensorSPI encoder(AS5048_SPI, PIN_ENC_CS);
static WiFiUDP udp;
static Preferences prefs;

static State state = ST_DISARMED;
static Fault fault = F_NONE;
static bool homed = false;
static bool ethUp = false;

static float pos = 0, vel = 0;            // mesurés par l'encodeur (mm, mm/s)
static float angle0 = 0;                  // angle moteur qui correspond à la position 0
static float pRef = 0, vRef = 0;          // consigne interne
static float vRefPrev = 0;
static float iCmd = 0;                    // courant demandé ; positif = sens du déroulement
static float iInt = 0;                    // terme intégral : il porte le poids de l'objet
static float tensionEstG = 0;             // tension du fil estimée, en grammes
static float posMin = 0, posMax = TRAVEL_DEFAULT_MM;
static float tensionMaxG = TENSION_MAX_DEFAULT_G;
static float homeTensionG = HOME_TENSION_DEFAULT_G;

static float gotoP0, gotoP1, gotoT;
static uint32_t gotoStartMs;
static float streamTarget, streamVel, streamDt;
static uint32_t streamLastUs;
static float jogVel;
static uint32_t jogLastMs;
static uint32_t idleSinceMs;
static uint32_t snagSinceMs, stallSinceMs;
static float breakG;                      // tension en cours pendant le test de rupture
static float seekStartPos;                // position au départ d'une prise d'origine ou d'une mesure
static float measureTensionG;             // tension plafond pendant une mesure de longueur

static IPAddress peer(255, 255, 255, 255);
static bool hasPeer = false;

// Arrêt de groupe : un bloc en défaut prévient les autres, qui s'arrêtent et refusent tout
// nouveau mouvement jusqu'à un /reset. Aucun bloc ne commande les autres pour autant.
static uint8_t groupHoldFrom = 0;         // numéro du bloc qui a déclenché l'arrêt, 0 = aucun
static uint32_t lastGroupStopMs = 0;
static bool msgFromBlock = false;         // le dernier message venait d'un bloc, pas du logiciel

// ---------------------------------------------------------------- utilitaires

static inline bool inActive(uint8_t pin, bool activeHigh) { return digitalRead(pin) == (activeHigh ? HIGH : LOW); }

static void readPosition() {
  pos = DIR_SIGN * (motor.shaft_angle - angle0) * R_EFF_MM;
  vel = DIR_SIGN * motor.shaft_velocity * R_EFF_MM;
}

static void setPosition(float p) {
  angle0 = motor.shaft_angle - DIR_SIGN * p / R_EFF_MM;
  pos = p;
}

static void sendOsc(const char* leaf, const char* tags, const float* vals) {
  if (!ethUp) return;
  char addr[48];
  snprintf(addr, sizeof(addr), "/levi/%d/%s", WINCH_ID, leaf);
  uint8_t buf[96];
  size_t n = oscBuild(buf, sizeof(buf), addr, tags, vals);
  if (!n) return;
  udp.beginPacket(hasPeer ? peer : IPAddress(255, 255, 255, 255), OSC_OUT_PORT);
  udp.write(buf, n);
  udp.endPacket();
}

static void warn(int code) {
  float v = code;
  sendOsc("warn", "i", &v);
  Serial.printf("avertissement %d\n", code);
}
// Codes : 1 = pas armé, 2 = origine non faite, 3 = durée allongée (limites),
//         4 = consigne hors course (écrêtée), 5 = commande refusée en mouvement,
//         6 = arrêt de groupe en cours (un autre bloc est en défaut)

// Prévient les autres blocs, en diffusion sur le réseau, que celui-ci est en défaut.
static void sendGroupStop() {
  lastGroupStopMs = millis();
  if (!ethUp) return;
  float v[2] = { (float)WINCH_ID, (float)fault };
  uint8_t buf[64];
  size_t n = oscBuild(buf, sizeof(buf), "/levi/all/groupstop", "ii", v);
  if (!n) return;
  udp.beginPacket(IPAddress(NET_IP_BASE, 255), OSC_IN_PORT);
  udp.write(buf, n);
  udp.endPacket();
}

static void holdHere() {
  pRef = pos; vRef = 0; vRefPrev = 0;
  idleSinceMs = millis();
}

// ---------------------------------------------------------------- sécurité

static void enterFault(Fault f) {
  if (state == ST_FAULT) return;
  if (f == F_ESTOP) {
    motor.disable();                        // arrêt d'urgence : plus aucune force sur le fil
    iCmd = 0; iInt = 0;
    homed = false;                          // moteur coupé, l'objet redescend : position perdue
  }
  holdHere();                               // fil accroché : on tient en place, sans forcer
  fault = f;
  state = ST_FAULT;
  sendGroupStop();                          // les autres blocs s'arrêtent sans attendre le logiciel
  Serial.printf("DEFAUT %d\n", (int)f);
}

static void arm() {
  if (state != ST_DISARMED) return;
  iInt = 0;
  motor.enable();
  holdHere();
  state = ST_HOLD;
}

static void disarm() {
  motor.disable();
  iCmd = 0; iInt = 0;
  homed = false;
  state = ST_DISARMED;
}

static bool readyToMove() {
  if (state == ST_FAULT || state == ST_DISARMED) { warn(1); return false; }
  if (state == ST_HOMING || state == ST_BREAKTEST || state == ST_MEASURE) { warn(5); return false; }
  return true;
}

static float clampTarget(float p) {
  if (p < posMin) { warn(4); return posMin; }
  if (p > posMax) { warn(4); return posMax; }
  return p;
}

// ---------------------------------------------------------------- commandes

static void cmdGoto(float target, float dur) {
  if (!readyToMove()) return;
  if (groupHoldFrom) { warn(6); return; }
  if (!homed) { warn(2); return; }
  target = clampTarget(target);
  if (fabsf(vRef) > 1.0f) {                 // déjà en mouvement : on raccorde en suivi
    streamTarget = target; streamVel = 0; streamLastUs = micros();
    state = ST_STREAM;
    return;
  }
  float d = fabsf(target - pRef);
  float vLim = target > pRef ? VMAX_DOWN_MM_S : VMAX_MM_S;   // la descente est plus lente que la montée
  // Courbe en S (polynôme de degré 5) : v max = 1,875·d/T ; a max = 5,774·d/T²
  float tMin = max(1.875f * d / vLim, sqrtf(5.774f * d / AMAX_MM_S2));
  if (dur < tMin) { if (dur > 0) warn(3); dur = tMin; }
  if (d < 0.01f || dur <= 0) return;
  gotoP0 = pRef; gotoP1 = target; gotoT = dur; gotoStartMs = millis();
  state = ST_GOTO;
}

static void cmdStream(float target) {
  if (!readyToMove()) return;
  if (groupHoldFrom) { warn(6); return; }
  if (!homed) { warn(2); return; }
  target = clampTarget(target);
  uint32_t nowUs = micros();
  float dt = (nowUs - streamLastUs) * 1e-6f;
  if (state == ST_STREAM && dt > 0.002f && dt < 0.2f) {
    streamVel = 0.5f * streamVel + 0.5f * (target - streamTarget) / dt;
    streamDt = dt;
  } else {
    streamVel = 0; streamDt = 0;
  }
  streamTarget = target;
  streamLastUs = nowUs;
  state = ST_STREAM;
}

static void cmdJog(float v) {
  if (!readyToMove()) return;
  if (state == ST_GOTO || state == ST_STREAM) { warn(5); return; }
  jogVel = constrain(v, -VMAX_MM_S, VMAX_DOWN_MM_S);
  if (!homed) jogVel = constrain(jogVel, -200.0f, 200.0f);
  jogLastMs = millis();
  state = ST_JOG;
}

static void cmdStop() {
  if (state == ST_GOTO || state == ST_STREAM || state == ST_JOG) state = ST_STOPPING;
  else if (state == ST_HOMING || state == ST_BREAKTEST || state == ST_MEASURE) { holdHere(); state = ST_HOLD; }
}

static void cmdHome() {
  if (state != ST_HOLD) { warn(state == ST_DISARMED || state == ST_FAULT ? 1 : 5); return; }
  homed = false;
  stallSinceMs = 0;
  seekStartPos = pos;
  state = ST_HOMING;
}

// Mesure d'une longueur sans toucher à l'origine : le bloc remonte doucement, avec une
// force plafonnée, jusqu'à ce que le fil se tende (bout attaché à un point fixe, par exemple
// la bague d'un autre bloc). Il renvoie la position atteinte, puis rend un peu de mou.
static void cmdMeasure(float tensionG) {
  if (state != ST_HOLD) { warn(state == ST_DISARMED || state == ST_FAULT ? 1 : 5); return; }
  measureTensionG = tensionG > 0 ? min(tensionG, tensionMaxG) : min(homeTensionG, tensionMaxG);
  stallSinceMs = 0;
  seekStartPos = pos;
  state = ST_MEASURE;
}

static void cmdZero() {                     // la position actuelle devient l'origine
  if (state != ST_HOLD) { warn(state == ST_DISARMED || state == ST_FAULT ? 1 : 5); return; }
  setPosition(0);
  holdHere();
  homed = true;
}

static void cmdBreakTest() {
  // Le fil doit être attaché à un point fixe, légèrement tendu.
  if (state != ST_HOLD) { warn(state == ST_DISARMED || state == ST_FAULT ? 1 : 5); return; }
  breakG = 0;
  state = ST_BREAKTEST;
}

static void cmdReset() {
  groupHoldFrom = 0;                        // lève aussi l'arrêt de groupe
  if (state != ST_FAULT) return;
  if (inActive(PIN_ESTOP, ESTOP_ACTIVE)) return;
  bool wasEstop = fault == F_ESTOP;
  fault = F_NONE;
  if (wasEstop) { state = ST_DISARMED; }
  else { holdHere(); state = ST_HOLD; }
}

static void handleOsc(const OscMsg& m) {
  // Adresses : /levi/<id>/<cmd> ou /levi/all/<cmd>
  if (strncmp(m.addr, "/levi/", 6) != 0) return;
  const char* p = m.addr + 6;
  const char* slash = strchr(p, '/');
  if (!slash) return;
  bool all = (slash - p == 3 && strncmp(p, "all", 3) == 0);
  if (!all && atoi(p) != WINCH_ID) return;
  const char* cmd = slash + 1;
  // En adressage « all », les arguments sont rangés par numéro de bloc.
  const uint8_t i = all ? WINCH_ID - 1 : 0;

  if (!strcmp(cmd, "goto")) {
    if (all) { if (m.n >= WINCH_COUNT + 1) cmdGoto(m.arg[i], m.arg[WINCH_COUNT]); }
    else if (m.n >= 1) cmdGoto(m.arg[0], m.n >= 2 ? m.arg[1] : 0);
  } else if (!strcmp(cmd, "pos")) {
    if (m.n > i) cmdStream(m.arg[i]);
  } else if (!strcmp(cmd, "jog")) {
    if (m.n > i) cmdJog(m.arg[i]);
  } else if (!strcmp(cmd, "stop")) cmdStop();
  else if (!strcmp(cmd, "arm")) arm();
  else if (!strcmp(cmd, "disarm")) { if (state == ST_HOLD) disarm(); else if (state != ST_DISARMED) warn(5); }
  else if (!strcmp(cmd, "home")) cmdHome();
  else if (!strcmp(cmd, "zero")) cmdZero();
  else if (!strcmp(cmd, "reset")) cmdReset();
  else if (!strcmp(cmd, "groupstop")) {
    // Envoyé par un bloc en défaut. On s'arrête en douceur et on attend un /reset.
    msgFromBlock = true;
    if (m.n >= 1 && (int)m.arg[0] != WINCH_ID) {
      groupHoldFrom = (uint8_t)m.arg[0];
      cmdStop();
    }
  }
  else if (!strcmp(cmd, "breaktest") && !all) cmdBreakTest();
  else if (!strcmp(cmd, "measure") && !all) cmdMeasure(m.n >= 1 ? m.arg[0] : 0);
  else if (!strcmp(cmd, "tension") && !all && m.n >= 1 && m.arg[0] > 0 && m.arg[0] <= BREAKTEST_MAX_G) {
    tensionMaxG = m.arg[0]; prefs.putFloat("tmax", tensionMaxG);
  } else if (!strcmp(cmd, "hometension") && !all && m.n >= 1 && m.arg[0] > 0 && m.arg[0] <= BREAKTEST_MAX_G) {
    homeTensionG = m.arg[0]; prefs.putFloat("thome", homeTensionG);
  } else if (!strcmp(cmd, "limits") && !all && m.n >= 2 && m.arg[1] > m.arg[0]) {
    posMin = m.arg[0]; posMax = m.arg[1];
    prefs.putFloat("pmin", posMin); prefs.putFloat("pmax", posMax);
  }
}

// ---------------------------------------------------------------- boucle de mouvement

static void approach(float& v, float target, float maxStep) {
  if (v < target) v = min(v + maxStep, target);
  else v = max(v - maxStep, target);
}

// Calcule la consigne de position selon l'état, puis le courant à donner au moteur.
static void controlTick(float dt) {
  const uint32_t now = millis();
  readPosition();

  if (state != ST_FAULT && inActive(PIN_ESTOP, ESTOP_ACTIVE)) enterFault(F_ESTOP);
  if (state == ST_DISARMED || (state == ST_FAULT && fault == F_ESTOP)) { iCmd = 0; return; }

  switch (state) {
    case ST_HOLD:
    case ST_FAULT:
      vRef = 0;
      break;

    case ST_GOTO: {
      float tau = (now - gotoStartMs) / 1000.0f / gotoT;
      if (tau >= 1.0f) { pRef = gotoP1; vRef = 0; state = ST_HOLD; idleSinceMs = now; break; }
      float s = tau * tau * tau * (10.0f - 15.0f * tau + 6.0f * tau * tau);
      float ds = 30.0f * tau * tau * (1.0f - tau) * (1.0f - tau) / gotoT;
      pRef = gotoP0 + (gotoP1 - gotoP0) * s;
      vRef = (gotoP1 - gotoP0) * ds;
      break;
    }

    case ST_STREAM: {
      float age = (micros() - streamLastUs) * 1e-6f;
      if (age > 2.0f * streamDt + 0.01f) streamVel = 0;   // plus de paquets : on vise la dernière consigne
      float tgt = constrain(streamTarget + streamVel * age, posMin, posMax);
      // Vitesse visée = vitesse de la consigne + rattrapage de l'écart. Le rattrapage est
      // proportionnel près du but, puis en racine carrée pour pouvoir toujours freiner à temps.
      float e = tgt - pRef;
      float catchUp = min(STREAM_OMEGA * fabsf(e), sqrtf(2.0f * 0.8f * AMAX_MM_S2 * fabsf(e)));
      float vDes = constrain(streamVel + (e > 0 ? catchUp : -catchUp), -VMAX_MM_S, VMAX_DOWN_MM_S);
      approach(vRef, vDes, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (streamVel != 0 || fabsf(vRef) > 0.5f || fabsf(streamTarget - pRef) > 0.05f) idleSinceMs = now;
      else if (now - idleSinceMs > 1000) { pRef = streamTarget; vRef = 0; state = ST_HOLD; idleSinceMs = now; }
      break;
    }

    case ST_JOG: {
      if (now - jogLastMs > JOG_DEADMAN_MS) jogVel = 0;   // « homme mort » : il faut renvoyer la commande
      float target = jogVel;
      if (homed) {
        float stopDist = vRef * vRef / (2.0f * AMAX_MM_S2) + 1.0f;
        if (target > 0 && pRef + stopDist >= posMax) target = 0;
        if (target < 0 && pRef - stopDist <= posMin) target = 0;
      }
      approach(vRef, target, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (vRef == 0 && jogVel == 0) { state = ST_HOLD; idleSinceMs = now; }
      break;
    }

    case ST_HOMING:
    case ST_MEASURE: {
      // On remonte doucement, avec une force plafonnée, jusqu'à ce que l'objet (ou une perle
      // sur le fil) bute contre l'œillet : le moteur n'avance plus, c'est l'origine.
      approach(vRef, -HOME_SPEED_MM_S, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (pRef < pos - 8.0f) pRef = pos - 8.0f;           // la consigne n'a pas à s'éloigner de l'objet
      bool atSensor = state == ST_HOMING && HOME_SENSOR_ENABLED && inActive(PIN_HOME, HOME_ACTIVE);
      bool blocked = (pRef < pos - 5.0f) && fabsf(vel) < 5.0f;
      if (!blocked) stallSinceMs = now;
      if (state == ST_MEASURE && now - stallSinceMs > 300) {
        // Fil tendu : on renvoie la position, la distance parcourue et la tension appliquée,
        // puis on rend du mou. L'origine n'est pas modifiée.
        float r[3] = { pos, seekStartPos - pos, measureTensionG };
        sendOsc("measured", "fff", r);
        pRef = pos; vRef = 0;
        gotoP0 = pos; gotoP1 = pos + MEASURE_SLACK_MM; gotoT = 1.0f; gotoStartMs = now;
        state = ST_GOTO;
      } else if (atSensor || now - stallSinceMs > 300) {
        // Distance remontée depuis le départ : objet posé au sol au départ, c'est la hauteur.
        float travel = seekStartPos - pos;
        sendOsc("homed", "f", &travel);
        setPosition(0);
        homed = true;
        iInt = 0;
        pRef = 0; vRef = 0;
        gotoP0 = 0; gotoP1 = HOME_BACKOFF_MM; gotoT = 1.0f; gotoStartMs = now;
        state = ST_GOTO;
      }
      break;
    }

    case ST_STOPPING:
      approach(vRef, 0, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (vRef == 0) { state = ST_HOLD; idleSinceMs = now; }
      break;

    case ST_BREAKTEST: {
      // Le fil est attaché à un point fixe. On tire de plus en plus fort ; quand la bobine
      // s'emballe, le fil vient de casser et la dernière tension appliquée est sa rupture.
      bool broke = vel < -BREAKTEST_SPEED_MM_S;
      if (broke || breakG >= BREAKTEST_MAX_G) {
        float r[2] = { breakG, broke ? 1.0f : 0.0f };
        sendOsc("break", "fi", r);
        Serial.printf("rupture : %.1f g (%s)\n", breakG, broke ? "fil casse" : "maximum atteint sans casser");
        iInt = 0;
        holdHere();
        state = ST_HOLD;
        break;
      }
      breakG += BREAKTEST_RATE_G_S * dt;
      iCmd = -breakG * AMP_PER_GRAM;
      tensionEstG = breakG;
      return;
    }

    default:
      break;
  }

  // Asservissement : proportionnel sur l'écart, amortissement sur la vitesse, intégral pour
  // porter le poids, plus l'anticipation de l'accélération demandée.
  float capG = state == ST_HOMING ? min(homeTensionG, tensionMaxG) : (state == ST_MEASURE ? measureTensionG : tensionMaxG);
  float windMax = capG * AMP_PER_GRAM;
  float aRef = (vRef - vRefPrev) / dt;
  vRefPrev = vRef;
  float err = pRef - pos;
  float raw = KP_A_PER_MM * err + KD_A_PER_MM_S * (vRef - vel) + iInt + aRef / ACC_PER_AMP;
  iCmd = constrain(raw, -windMax, PUSH_CURRENT_A);
  if (raw == iCmd) iInt = constrain(iInt + KI_A_PER_MM_S * err * dt, -windMax, PUSH_CURRENT_A);   // pas d'emballement en butée
  tensionEstG += 0.02f * (-iCmd / AMP_PER_GRAM - tensionEstG);

  // Fil accroché, ou objet trop lourd pour la tension autorisée : l'écart ne se résorbe pas.
  if (state != ST_HOMING && state != ST_MEASURE && state != ST_FAULT) {
    if (fabsf(err) < SNAG_ERROR_MM) snagSinceMs = now;
    else if (now - snagSinceMs > SNAG_TIME_MS) enterFault(F_SNAG);
  }
}

static void sendFeedback() {
  float v[7] = { pos, vel, (float)state, homed ? 1.0f : 0.0f, (float)fault, tensionEstG, (float)groupHoldFrom };
  sendOsc("state", "ffiiifi", v);
}

// ---------------------------------------------------------------- démarrage

static void onEthEvent(WiFiEvent_t event) {
  if (event == ARDUINO_EVENT_ETH_GOT_IP) ethUp = true;
  else if (event == ARDUINO_EVENT_ETH_DISCONNECTED || event == ARDUINO_EVENT_ETH_STOP) ethUp = false;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_HOME, INPUT);
  pinMode(PIN_ESTOP, INPUT_PULLDOWN);       // fil coupé = arrêt d'urgence

  prefs.begin("treuil", false);
  posMin = prefs.getFloat("pmin", 0);
  posMax = prefs.getFloat("pmax", TRAVEL_DEFAULT_MM);
  tensionMaxG = prefs.getFloat("tmax", TENSION_MAX_DEFAULT_G);
  homeTensionG = prefs.getFloat("thome", HOME_TENSION_DEFAULT_G);

  SPI.begin(PIN_ENC_SCK, PIN_ENC_MISO, PIN_ENC_MOSI, PIN_ENC_CS);
  encoder.init();
  motor.linkSensor(&encoder);
  driver.voltage_power_supply = SUPPLY_VOLTAGE;
  driver.init();
  motor.linkDriver(&driver);
  motor.torque_controller = TorqueControlType::voltage;   // courant estimé à partir de R et du KV
  motor.controller = MotionControlType::torque;
  // Modulation vectorielle : c'est elle qui tire le plus de tension de l'alimentation sans
  // déformer le courant. La tension utile par phase est alors l'alimentation divisée par 1,73.
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;
  motor.voltage_limit = SUPPLY_VOLTAGE / _SQRT3;
  motor.current_limit = BREAKTEST_MAX_G * AMP_PER_GRAM * 1.2f;
  motor.LPF_velocity.Tf = VELOCITY_FILTER_S;
  motor.init();
  motor.initFOC();                          // aligne l'encodeur : la bobine bouge un peu
  motor.disable();                          // on démarre désarmé
  motor.move(0);
  readPosition();

  WiFi.onEvent(onEthEvent);
  ETH.begin();
  ETH.config(IPAddress(NET_IP_BASE, NET_IP_OFFSET + WINCH_ID), IPAddress(NET_IP_BASE, 1),
             IPAddress(255, 255, 255, 0));
  udp.begin(OSC_IN_PORT);

  Serial.printf("Treuil micro %d pret - %.1f mA par gramme - tension max %.0f g\n",
                WINCH_ID, AMP_PER_GRAM * 1000.0f, tensionMaxG);
}

void loop() {
  motor.loopFOC();                          // commutation du moteur, aussi souvent que possible

  static uint32_t lastTickUs = micros();
  uint32_t nowUs = micros();
  if (nowUs - lastTickUs >= 1000) {          // asservissement de position à 1 kHz
    float dt = min((nowUs - lastTickUs) * 1e-6f, 0.01f);
    lastTickUs = nowUs;

    static uint8_t buf[512];
    int len;
    while ((len = udp.parsePacket()) > 0) {
      IPAddress from = udp.remoteIP();
      int n = udp.read(buf, sizeof(buf));
      if (n > 0) {
        msgFromBlock = false;
        oscDispatch(buf, (size_t)n, handleOsc);
        if (!msgFromBlock) { peer = from; hasPeer = true; }   // l'état repart vers le logiciel, pas vers un bloc
      }
    }

    controlTick(dt);
    motor.move(DIR_SIGN * iCmd);            // en mode couple, la consigne est un courant (A)
  }

  // Tant que ce bloc est en défaut, il le répète : un bloc qui aurait manqué le message,
  // ou qu'on aurait acquitté trop tôt, reste à l'arrêt.
  if (state == ST_FAULT && millis() - lastGroupStopMs >= 200) sendGroupStop();

  static uint32_t lastFbMs = 0;
  if (millis() - lastFbMs >= FEEDBACK_PERIOD_MS) {
    lastFbMs = millis();
    sendFeedback();
  }
}
