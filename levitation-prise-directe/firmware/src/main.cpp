// Bloc treuil « lévitation » — firmware v0.1
//
// Version prise directe : le tambour est monté sur l'arbre du servo, sans courroie.
// Un bloc = un servo intégré (pas/direction) qui entraîne le tambour, un petit
// moteur pas-à-pas qui déplace le guide-fil (trancannage), un frein à manque de
// courant, et une liaison Ethernet qui reçoit de l'OSC (Chataigne, Orchestr…).
//
// Position = longueur de fil déroulée en mm ; 0 = origine haute, positif = descente.
// Le protocole OSC est décrit dans ../README.md.

#include <Arduino.h>
#include <ETH.h>
#include <WiFiUdp.h>
#include <Preferences.h>
#include <FastAccelStepper.h>
#include "config.h"
#include "osc.h"

enum State : uint8_t {
  ST_DISARMED = 0,  // frein serré, servo coupé
  ST_ARMING   = 1,  // servo sous tension, frein en cours de desserrage
  ST_HOLD     = 2,  // armé, immobile
  ST_GOTO     = 3,  // déplacement temporisé (courbe douce)
  ST_STREAM   = 4,  // suivi d'une consigne envoyée en continu
  ST_JOG      = 5,  // déplacement manuel en vitesse
  ST_HOMING   = 6,  // recherche de l'origine haute
  ST_STOPPING = 7,  // décélération jusqu'à l'arrêt
  ST_FAULT    = 8,  // défaut : frein serré, il faut /reset
};
enum Fault : uint8_t { F_NONE = 0, F_ESTOP = 1, F_SERVO_ALARM = 2, F_SLACK = 3 };

static FastAccelStepperEngine engine;
static FastAccelStepper* servo = nullptr;
static FastAccelStepper* lw = nullptr;
static WiFiUDP udp;
static Preferences prefs;

static State state = ST_DISARMED;
static Fault fault = F_NONE;
static bool homed = false;
static bool ethUp = false;

static float pRef = 0, vRef = 0;          // consigne interne (mm, mm/s)
static float posMin = 0, posMax = TRAVEL_DEFAULT_MM;

static float gotoP0, gotoP1, gotoT;       // déplacement temporisé
static uint32_t gotoStartMs;
static float streamTarget, streamVel;   // dernière consigne reçue et sa vitesse estimée
static uint32_t streamLastUs;
static float streamDt;
static float jogVel;
static uint32_t jogLastMs;
static uint32_t armAtMs;
static uint32_t idleSinceMs;
static float savedPos = NAN;

static IPAddress peer(255, 255, 255, 255);
static bool hasPeer = false;

// ---------------------------------------------------------------- entrées/sorties

static inline bool inActive(uint8_t pin, bool activeHigh) { return digitalRead(pin) == (activeHigh ? HIGH : LOW); }
static inline void servoEnable(bool on) { digitalWrite(PIN_SERVO_EN, on == (bool)SERVO_EN_ACTIVE ? HIGH : LOW); }
static inline void brakeRelease(bool on) { digitalWrite(PIN_BRAKE, on ? HIGH : LOW); }
static inline float actualPos() { return servo->getCurrentPosition() / STEPS_PER_MM; }

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
//         4 = consigne hors course (écrêtée), 5 = commande refusée en mouvement

static void savePosition() {
  float p = actualPos();
  if (homed && !isnan(savedPos) && fabsf(p - savedPos) < 0.02f) return;
  prefs.putFloat("pos", p);
  prefs.putBool("homed", homed);
  savedPos = p;
}

// ---------------------------------------------------------------- sécurité

static void enterFault(Fault f) {
  if (state == ST_FAULT) return;
  brakeRelease(false);                      // frein serré tout de suite
  servo->forceStopAndNewPosition(servo->getCurrentPosition());
  servoEnable(false);
  // Après un arrêt brutal ou une alarme servo, la position n'est plus garantie.
  if (f == F_SERVO_ALARM || fabsf(vRef) > 1.0f) homed = false;
  vRef = 0;
  pRef = actualPos();
  fault = f;
  state = ST_FAULT;
  prefs.putBool("homed", homed);
  prefs.putFloat("pos", pRef);
  savedPos = pRef;
  Serial.printf("DEFAUT %d\n", (int)f);
}

static void disarm() {
  brakeRelease(false);
  servo->forceStopAndNewPosition(servo->getCurrentPosition());
  delay(150);                               // temps de serrage du frein
  servoEnable(false);
  vRef = 0;
  pRef = actualPos();
  state = ST_DISARMED;
  savePosition();
}

static void arm() {
  if (state != ST_DISARMED) return;
  pRef = actualPos();
  vRef = 0;
  servoEnable(true);                        // le servo tient avant d'ouvrir le frein
  armAtMs = millis();
  state = ST_ARMING;
}

static bool readyToMove() {
  if (state == ST_FAULT || state == ST_DISARMED || state == ST_ARMING) { warn(1); return false; }
  if (state == ST_HOMING) { warn(5); return false; }
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
  if (!homed) { warn(2); return; }
  target = clampTarget(target);
  if (fabsf(vRef) > 1.0f) {                 // déjà en mouvement : on raccorde en suivi
    streamTarget = target; streamVel = 0; streamLastUs = micros();
    state = ST_STREAM;
    return;
  }
  float d = fabsf(target - pRef);
  // Courbe en S (polynôme de degré 5) : v max = 1,875·d/T ; a max = 5,774·d/T²
  float tMin = max(1.875f * d / VMAX_MM_S, sqrtf(5.774f * d / AMAX_MM_S2));
  if (dur < tMin) { if (dur > 0) warn(3); dur = tMin; }
  if (d < 0.01f || dur <= 0) return;
  gotoP0 = pRef; gotoP1 = target; gotoT = dur; gotoStartMs = millis();
  state = ST_GOTO;
}

static void cmdStream(float target) {
  if (!readyToMove()) return;
  if (!homed) { warn(2); return; }
  target = clampTarget(target);
  // La vitesse de la consigne est estimée d'un paquet au suivant : le bloc peut ainsi
  // prolonger le mouvement entre deux paquets au lieu d'avancer par à-coups.
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

static void cmdJog(float vel) {
  if (!readyToMove()) return;
  if (state == ST_GOTO || state == ST_STREAM) { warn(5); return; }
  jogVel = constrain(vel, -VMAX_MM_S, VMAX_MM_S);
  if (!homed) jogVel = constrain(jogVel, -200.0f, 200.0f);  // lent tant que l'origine est inconnue
  jogLastMs = millis();
  state = ST_JOG;
}

static void cmdStop() {
  if (state == ST_GOTO || state == ST_STREAM || state == ST_JOG || state == ST_HOMING) state = ST_STOPPING;
}

static void cmdHome() {
  if (state != ST_HOLD) { warn(state == ST_DISARMED || state == ST_FAULT ? 1 : 5); return; }
  homed = false;
  state = ST_HOMING;
}

static void cmdZero() {                     // la position actuelle devient l'origine
  if (state != ST_HOLD && state != ST_DISARMED) { warn(5); return; }
  servo->forceStopAndNewPosition(0);
  pRef = 0; vRef = 0;
  homed = true;
  savedPos = NAN;
  savePosition();
}

static void cmdReset() {
  if (state != ST_FAULT) return;
  if (inActive(PIN_ESTOP, ESTOP_ACTIVE) || inActive(PIN_SERVO_ALARM, SERVO_ALARM_ACTIVE)) return;
  fault = F_NONE;
  state = ST_DISARMED;
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
  else if (!strcmp(cmd, "limits") && !all && m.n >= 2 && m.arg[1] > m.arg[0]) {
    posMin = m.arg[0]; posMax = m.arg[1];
    prefs.putFloat("pmin", posMin); prefs.putFloat("pmax", posMax);
  }
}

// ---------------------------------------------------------------- boucle de mouvement

static void approach(float& v, float target, float maxStep) {
  if (v < target) v = min(v + maxStep, target);
  else v = max(v - maxStep, target);
}

static void controlTick(float dt) {
  const uint32_t now = millis();

  // Sécurités, vérifiées à chaque cycle
  if (state != ST_FAULT) {
    if (inActive(PIN_ESTOP, ESTOP_ACTIVE)) enterFault(F_ESTOP);
    else if (state != ST_DISARMED && inActive(PIN_SERVO_ALARM, SERVO_ALARM_ACTIVE)) enterFault(F_SERVO_ALARM);
    else if (SLACK_ENABLED && vRef > 5.0f && inActive(PIN_SLACK, SLACK_ACTIVE)) enterFault(F_SLACK);
  }

  switch (state) {
    case ST_ARMING:
      if (now - armAtMs > 150) brakeRelease(true);
      if (now - armAtMs > 350) { state = ST_HOLD; idleSinceMs = now; }
      break;

    case ST_HOLD:
      vRef = 0;
      if (AUTO_DISARM_S > 0 && now - idleSinceMs > AUTO_DISARM_S * 1000UL) disarm();
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
      float vDes = constrain(streamVel + (e > 0 ? catchUp : -catchUp), -VMAX_MM_S, VMAX_MM_S);
      approach(vRef, vDes, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (streamVel != 0 || fabsf(vRef) > 0.5f || fabsf(streamTarget - pRef) > 0.05f) idleSinceMs = now;
      else if (now - idleSinceMs > 1000) { pRef = streamTarget; vRef = 0; state = ST_HOLD; idleSinceMs = now; }
      break;
    }

    case ST_JOG: {
      if (now - jogLastMs > JOG_DEADMAN_MS) jogVel = 0;   // « homme mort » : il faut renvoyer la commande
      float target = jogVel;
      if (homed) {                                        // freinage à l'approche des butées logicielles
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
      if (inActive(PIN_HOME, HOME_ACTIVE)) {
        servo->forceStopAndNewPosition(0);
        pRef = 0; vRef = 0;
        homed = true;
        savedPos = NAN;
        savePosition();
        gotoP0 = 0; gotoP1 = HOME_BACKOFF_MM; gotoT = 1.0f; gotoStartMs = now;
        state = ST_GOTO;
        break;
      }
      approach(vRef, -HOME_SPEED_MM_S, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      break;

    case ST_STOPPING:
      approach(vRef, 0, AMAX_MM_S2 * dt);
      pRef += vRef * dt;
      if (vRef == 0) { state = ST_HOLD; idleSinceMs = now; }
      break;

    default:
      break;
  }

  // Génération des pas : vitesse de consigne + rattrapage de l'écart de position
  if (state == ST_HOLD) {
    // A l'arrêt : positionnement exact sur le pas visé, sans oscillation autour
    servo->setSpeedInHz((uint32_t)(100.0f * STEPS_PER_MM));
    servo->moveTo((int32_t)lroundf(pRef * STEPS_PER_MM));
  } else if (state > ST_HOLD && state <= ST_STOPPING) {
    float vCmd = vRef + KP_POS * (pRef - actualPos());
    vCmd = constrain(vCmd, -VMAX_MM_S * 1.05f, VMAX_MM_S * 1.05f);
    uint32_t mHz = (uint32_t)(fabsf(vCmd) * STEPS_PER_MM * 1000.0f);
    if (mHz < 1000) {
      servo->stopMove();
    } else {
      servo->setSpeedInMilliHz(mHz);
      if (vCmd > 0) servo->runForward(); else servo->runBackward();
    }
  }

#if LW_ENABLED
  // Le guide-fil suit le tambour : une avance de LW_PITCH_MM par tour
  float x = LW_X_AT_ZERO_MM + LW_SIGN * (actualPos() / LINE_PER_TURN_MM) * LW_PITCH_MM;
  x = constrain(x, 0.0f, LW_TRAVEL_MM);
  lw->moveTo((int32_t)lroundf(x * LW_STEPS_PER_MM));
#endif
}

static void sendFeedback() {
  float v[5] = { actualPos(), vRef, (float)state, homed ? 1.0f : 0.0f, (float)fault };
  sendOsc("state", "ffiii", v);
}

// ---------------------------------------------------------------- démarrage

static void onEthEvent(WiFiEvent_t event) {
  if (event == ARDUINO_EVENT_ETH_GOT_IP) ethUp = true;
  else if (event == ARDUINO_EVENT_ETH_DISCONNECTED || event == ARDUINO_EVENT_ETH_STOP) ethUp = false;
}

#if LW_ENABLED
static void homeLevelWind() {
  lw->setSpeedInHz((uint32_t)(LW_HOME_SPEED_MM_S * LW_STEPS_PER_MM));
  lw->setAcceleration((uint32_t)(200.0f * LW_STEPS_PER_MM));
  lw->runBackward();
  uint32_t t0 = millis();
  uint32_t timeout = (uint32_t)(LW_TRAVEL_MM / LW_HOME_SPEED_MM_S * 1500.0f);
  while (!inActive(PIN_LW_HOME, LW_HOME_ACTIVE) && millis() - t0 < timeout) delay(1);
  lw->forceStopAndNewPosition(0);
  // En marche normale le guide doit pouvoir suivre le tambour à pleine vitesse
  lw->setSpeedInHz((uint32_t)(60.0f * LW_STEPS_PER_MM));
  lw->setAcceleration((uint32_t)(2000.0f * LW_STEPS_PER_MM));
}
#endif

void setup() {
  Serial.begin(115200);

  // Etat sûr avant tout : frein serré, servo coupé
  pinMode(PIN_BRAKE, OUTPUT);     brakeRelease(false);
  pinMode(PIN_SERVO_EN, OUTPUT);  servoEnable(false);
  pinMode(PIN_SERVO_ALARM, INPUT);
  pinMode(PIN_HOME, INPUT);
  pinMode(PIN_SLACK, INPUT);
  pinMode(PIN_LW_HOME, INPUT);
  pinMode(PIN_ESTOP, INPUT_PULLDOWN);       // fil coupé = arrêt d'urgence

  prefs.begin("treuil", false);
  posMin = prefs.getFloat("pmin", 0);
  posMax = prefs.getFloat("pmax", TRAVEL_DEFAULT_MM);
  homed = prefs.getBool("homed", false);
  savedPos = prefs.getFloat("pos", 0);

  engine.init();
  servo = engine.stepperConnectToPin(PIN_SERVO_STEP);
  servo->setDirectionPin(PIN_SERVO_DIR, !DIR_INVERT);
  // Marge de 50 % : c'est la trajectoire qui fixe l'accélération, pas le générateur de pas
  servo->setAcceleration((uint32_t)(AMAX_MM_S2 * 1.5f * STEPS_PER_MM));
  servo->setSpeedInHz(1000);
  // Le frein a tenu le tambour pendant la coupure : on reprend la position mémorisée
  servo->setCurrentPosition((int32_t)lroundf(savedPos * STEPS_PER_MM));
  pRef = actualPos();

#if LW_ENABLED
  lw = engine.stepperConnectToPin(PIN_LW_STEP);
  lw->setDirectionPin(PIN_LW_DIR);
  pinMode(PIN_LW_EN, OUTPUT);
  digitalWrite(PIN_LW_EN, LW_EN_ACTIVE ? HIGH : LOW);
  homeLevelWind();
#endif

  WiFi.onEvent(onEthEvent);
  ETH.begin();
  ETH.config(IPAddress(NET_IP_BASE, NET_IP_OFFSET + WINCH_ID), IPAddress(NET_IP_BASE, 1),
             IPAddress(255, 255, 255, 0));
  udp.begin(OSC_IN_PORT);

  Serial.printf("Treuil %d pret - %.3f pas/mm - position %.1f mm - origine %s\n",
                WINCH_ID, STEPS_PER_MM, pRef, homed ? "connue" : "A FAIRE");
}

void loop() {
  static uint8_t buf[512];
  int len;
  while ((len = udp.parsePacket()) > 0) {
    IPAddress from = udp.remoteIP();
    int n = udp.read(buf, sizeof(buf));
    if (n > 0) {
      peer = from; hasPeer = true;
      oscDispatch(buf, (size_t)n, handleOsc);
    }
  }

  static uint32_t lastTickUs = micros();
  uint32_t nowUs = micros();
  if (nowUs - lastTickUs >= 5000) {          // boucle de mouvement à 200 Hz
    float dt = (nowUs - lastTickUs) * 1e-6f;
    lastTickUs = nowUs;
    controlTick(min(dt, 0.02f));
  }

  static uint32_t lastFbMs = 0;
  if (millis() - lastFbMs >= FEEDBACK_PERIOD_MS) {
    lastFbMs = millis();
    sendFeedback();
  }
}
