// Simulation sur PC du firmware complet : on lui envoie de vrais paquets OSC et on
// vérifie les mouvements obtenus. Lancer avec ./run.sh
#include "Arduino.h"
#include "WiFiUdp.h"
#include "FastAccelStepper.h"
uint64_t simUs = 0; int simPins[64]; SerialStub Serial; WiFiStub WiFi; EthStub ETH;
std::deque<std::vector<uint8_t>> simRx; std::vector<std::vector<uint8_t>> simTx;
std::vector<FastAccelStepper*> simSteppers;
void simAdvance(uint32_t us) { simUs += us; for (auto* s : simSteppers) s->advance(us * 1e-6); }

#include "../../src/main.cpp"

static bool estopOk = true; static double homeAtSteps = -1e12;
int simRead(uint8_t pin) {
  if (pin == PIN_ESTOP) return estopOk ? HIGH : LOW;
  if (pin == PIN_LW_HOME) return (simSteppers.size() > 1 && simSteppers[1]->pos < -400) ? LOW : HIGH;
  if (pin == PIN_HOME) return simSteppers[0]->pos <= homeAtSteps ? LOW : HIGH;
  return HIGH;                                  // alarme servo, fil détendu : inactifs
}

static int fails = 0;
#define CHECK(cond, ...) do { bool ok_ = (cond); printf("%s  ", ok_ ? "OK   " : "ECHEC"); printf(__VA_ARGS__); printf("\n"); if (!ok_) fails++; } while (0)

static void send(const char* addr, std::initializer_list<float> a = {}) {
  std::string tags(a.size(), 'f'); std::vector<float> v(a);
  uint8_t b[128]; size_t n = oscBuild(b, sizeof(b), addr, tags.c_str(), v.data());
  simRx.emplace_back(b, b + n);
}
static double maxErr, maxV;
static void run(double seconds, void (*each)(double) = nullptr) {
  maxErr = maxV = 0; uint64_t t0 = simUs;
  for (int i = 0; i < seconds * 2000; i++) {
    if (each) each((simUs - t0) * 1e-6);
    float before = pRef;
    simAdvance(500); loop();
    // L'écart se lit au moment où la consigne vient d'être recalculée
    if (pRef != before) maxErr = max(maxErr, (double)fabsf(pRef - actualPos()));
    maxV = max(maxV, fabs(simSteppers[0]->vel) / STEPS_PER_MM);
  }
}
#if LW_ENABLED
static float lwMm() { return simSteppers[1]->pos / LW_STEPS_PER_MM; }
#endif

int main() {
  setup();
  CHECK(state == ST_DISARMED && simPins[PIN_BRAKE] == LOW, "demarrage : frein serre, non arme");
#if LW_ENABLED
  CHECK(fabsf(lwMm() - LW_X_AT_ZERO_MM) < 200, "guide-fil : origine trouvee");
#endif

  send("/levi/1/goto", {500, 1}); run(0.2);
  CHECK(state == ST_DISARMED && fabsf(actualPos()) < 0.01f, "goto refuse tant que le bloc n'est pas arme");

  send("/levi/all/arm"); run(0.5);
  CHECK(state == ST_HOLD && simPins[PIN_BRAKE] == HIGH, "armement : frein desserre, etat HOLD");
  send("/levi/1/goto", {500, 1}); run(0.2);
  CHECK(fabsf(actualPos()) < 0.01f, "goto refuse tant que l'origine n'est pas faite");
  send("/levi/2/zero"); run(0.1);
  CHECK(!homed, "commande adressee au bloc 2 ignoree");
  send("/levi/1/zero"); run(0.1);
  CHECK(homed, "zero : origine fixee");

  send("/levi/all/goto", {1000, 2000, 3000, 4000, 2.0f}); run(2.3);
  CHECK(fabsf(actualPos() - 1000) < 0.1f, "goto groupe : arrivee a %.3f mm (vise 1000)", actualPos());
  CHECK(maxErr < 1.0 && maxV < 960, "  ecart de suivi max %.3f mm, vitesse max %.0f mm/s (theorie 937)", maxErr, maxV);
#if LW_ENABLED
  CHECK(fabsf(lwMm() - (LW_X_AT_ZERO_MM - 1000 / LINE_PER_TURN_MM * LW_PITCH_MM)) < 0.05f, "  guide-fil a %.2f mm (suit le tambour)", lwMm());
#endif

  send("/levi/1/goto", {9000, 0.5f}); run(5.3);
  CHECK(fabsf(actualPos() - 9000) < 0.1f && maxV <= VMAX_MM_S * 1.05, "goto trop rapide : duree allongee, v max %.0f mm/s, arrivee %.3f", maxV, actualPos());
  CHECK(maxErr < 1.0, "  ecart de suivi max a 3 m/s : %.3f mm", maxErr);

  send("/levi/1/goto", {20000, 8}); run(8.5);
  CHECK(fabsf(actualPos() - posMax) < 0.1f, "consigne hors course ecretee a %.0f mm", actualPos());

  send("/levi/1/goto", {5000, 4}); run(4.5);
  static double lagMax; lagMax = 0;
  run(6, [](double t) {
    static int k = 0;
    float tgt = 5000 + 500 * (1 - cosf(2 * PI * 0.5f * (float)t));
    if (k++ % 40 == 0) send("/levi/all/pos", {tgt, 0, 0, 0});
    if (t > 0.5) lagMax = max(lagMax, (double)fabsf(tgt - actualPos()));
  });
  CHECK(state == ST_STREAM && maxErr < 3.0 && maxV < 1650, "flux 50 Hz (sinus 0,5 Hz, 1 m de course) : v max %.0f mm/s (theorie 1571), ecart interne %.3f mm", maxV, maxErr);
  CHECK(lagMax < 20, "  retard sur la consigne envoyee : %.1f mm max, soit environ %.0f ms (identique sur tous les blocs)", lagMax, lagMax / 1.571);
  send("/levi/all/stop"); run(1.5);
  CHECK(state == ST_HOLD && fabs(simSteppers[0]->vel) < 1, "stop : arret en douceur");

  send("/levi/1/jog", {300}); run(0.2); CHECK(maxV > 100, "jog : le fil descend");
  run(1.0); CHECK(state == ST_HOLD && fabs(simSteppers[0]->vel) < 1, "jog : arret tout seul sans renvoi de la commande");

  send("/levi/1/goto", {1000, 3}); run(1.5);
  estopOk = false; run(0.05);
  CHECK(state == ST_FAULT && simPins[PIN_BRAKE] == LOW && !homed, "arret d'urgence en mouvement : defaut, frein serre, origine invalidee");
  send("/levi/1/arm"); send("/levi/1/reset"); run(0.2);
  CHECK(state == ST_FAULT, "reset refuse tant que l'arret d'urgence est enfonce");
  estopOk = true; send("/levi/1/reset"); run(0.1); send("/levi/1/arm"); run(0.5);
  CHECK(state == ST_HOLD, "reset puis armement apres liberation");

  homeAtSteps = simSteppers[0]->pos - 100 * STEPS_PER_MM;
  send("/levi/1/home"); run(4);
  homeAtSteps = -1e12;
  CHECK(homed && fabsf(actualPos() - HOME_BACKOFF_MM) < 0.1f, "prise d'origine : capteur trouve, degagement a %.2f mm", actualPos());

  run(AUTO_DISARM_S + 1);
  CHECK(state == ST_DISARMED && simPins[PIN_BRAKE] == LOW, "frein automatique apres %d s d'immobilite", AUTO_DISARM_S);

  // Retour d'état et bundle OSC
  OscMsg m{}; bool got = false;
  for (auto& p : simTx) { OscMsg t; if (oscParseMessage(p.data(), p.size(), t) && !strcmp(t.addr, "/levi/1/state")) { m = t; got = true; } }
  CHECK(got && m.n == 5 && fabsf(m.arg[0] - actualPos()) < 0.1f && m.arg[2] == ST_DISARMED, "retour d'etat OSC lisible (%zu paquets emis)", simTx.size());
  uint8_t bundle[128] = "#bundle"; uint8_t msg[64];
  float one = 1; size_t n = oscBuild(msg, sizeof(msg), "/levi/1/arm", "", &one);
  bundle[16 + 3] = (uint8_t)n; memcpy(bundle + 20, msg, n);
  simRx.emplace_back(bundle, bundle + 20 + n); run(0.5);
  CHECK(state == ST_HOLD, "message recu dans un bundle OSC");
  uint8_t junk[7] = {'/', 'l', 'e', 'v', 'i', '/', '1'};
  simRx.emplace_back(junk, junk + 7); run(0.05);
  CHECK(state == ST_HOLD, "paquet malforme ignore");

  printf("\n%s (%d echec%s)\n", fails ? "ECHECS" : "TOUT EST BON", fails, fails > 1 ? "s" : "");
  return fails ? 1 : 0;
}
