// Simulation sur PC du firmware micro : on lui envoie de vrais paquets OSC et un modèle
// physique (moteur, bobine, objet de 5 g, butée, fil qui casse) répond. Lancer avec ./run.sh
#include "Arduino.h"
#include "WiFiUdp.h"
#include "SPI.h"
#include "SimpleFOC.h"
uint64_t simUs = 0; int simPins[64]; SerialStub Serial; WiFiStub WiFi; EthStub ETH; SpiStub SPI;
std::deque<std::vector<uint8_t>> simRx; std::vector<std::vector<uint8_t>> simTx;
SimPlant plant;
void simAdvance(uint32_t us) { for (uint32_t t = 0; t < us; t += 50) plant.step(50e-6); simUs += us; }

#include "../../src/main.cpp"

static bool estopOk = true;
int simRead(uint8_t pin) { return pin == PIN_ESTOP ? (estopOk ? HIGH : LOW) : HIGH; }

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
  for (int i = 0; i < seconds * 4000; i++) {
    if (each) each((simUs - t0) * 1e-6);
    simAdvance(250); loop();
    if (state == ST_GOTO || state == ST_STREAM) maxErr = max(maxErr, fabs(pRef - plant.phys()));
    maxV = max(maxV, fabs(plant.omega * plant.r * 1000.0));
  }
}

int main() {
  setup();
  CHECK(state == ST_DISARMED && !plant.enabled, "demarrage : moteur coupe, non arme");
  send("/levi/1/goto", {500, 1}); run(0.1);
  CHECK(state == ST_DISARMED, "goto refuse tant que le bloc n'est pas arme");

  plant.theta = 0; plant.omega = 0;                      // l'objet de 5 g pend 50 cm sous la butee
  run(0.002);
  double p0 = plant.phys();
  send("/levi/all/arm"); run(1.5);
  CHECK(state == ST_HOLD && fabs(plant.phys() - p0) < 1.0, "armement : objet de 5 g rattrape et tenu en place (ecart %.2f mm)", plant.phys() - p0);
  CHECK(fabsf(tensionEstG - 5) < 1.5, "tension du fil estimee : %.1f g (objet de 5 g)", tensionEstG);
  send("/levi/1/goto", {500, 1}); run(0.2);
  CHECK(state == ST_HOLD, "goto refuse tant que l'origine n'est pas faite");
  send("/levi/2/home"); run(0.2);
  CHECK(state == ST_HOLD, "commande adressee au bloc 2 ignoree");

  plant.peakWindG = 0;
  send("/levi/1/home"); run(12);
  CHECK(homed && state == ST_HOLD && fabs(plant.phys() - HOME_BACKOFF_MM) < 0.5, "prise d'origine en butee douce : objet a %.2f mm sous la butee (vise %.0f)", plant.phys(), HOME_BACKOFF_MM);
  CHECK(plant.peakWindG < HOME_TENSION_DEFAULT_G * 1.1, "  traction maximale pendant la prise d'origine : %.1f g (plafond %.0f g)", plant.peakWindG, HOME_TENSION_DEFAULT_G);

  send("/levi/all/goto", {1000, 2000, 3000, 4000, 2.0f}); run(2.6);
  CHECK(fabs(plant.phys() - 1000) < 0.3, "goto groupe : objet a %.3f mm (vise 1000)", plant.phys());
  CHECK(maxErr < 3.0 && maxV < 970, "  ecart de suivi max %.2f mm, vitesse max %.0f mm/s (theorie 937)", maxErr, maxV);

  send("/levi/1/goto", {9000, 0.5f}); run(1.875 * 8000 / VMAX_DOWN_MM_S + 0.6);
  CHECK(fabs(plant.phys() - 9000) < 0.3 && maxV <= VMAX_DOWN_MM_S * 1.03, "descente trop rapide : duree allongee, v max %.0f mm/s (limite %.0f), arrivee %.3f", maxV, VMAX_DOWN_MM_S, plant.phys());
  send("/levi/1/goto", {20000, 8}); run(8.5);
  CHECK(fabs(plant.phys() - posMax) < 0.3, "consigne hors course ecretee a %.0f mm", plant.phys());
  send("/levi/1/goto", {1000, 0.5f}); run(1.875 * 9000 / VMAX_MM_S + 0.6);
  CHECK(fabs(plant.phys() - 1000) < 0.3 && maxV > 2800 && maxV <= VMAX_MM_S * 1.03, "montee a pleine vitesse : v max %.0f mm/s, arrivee %.3f, ecart max %.2f mm", maxV, plant.phys(), maxErr);

  send("/levi/1/goto", {5000, 6}); run(6.5);
  static double lagMax; lagMax = 0;
  run(6, [](double t) {
    static int k = 0;
    float tgt = 5000 + 300 * (1 - cosf(2 * PI * 0.5f * (float)t));
    if (k++ % 80 == 0) send("/levi/all/pos", {tgt, 0, 0, 0});
    if (t > 0.5) lagMax = max(lagMax, fabs(tgt - plant.phys()));
  });
  CHECK(state == ST_STREAM && maxV < 1000, "flux 50 Hz (sinus 0,5 Hz, 0,6 m de course) : v max %.0f mm/s (theorie 942)", maxV);
  CHECK(lagMax < 20, "  retard sur la consigne envoyee : %.1f mm max, soit environ %.0f ms", lagMax, lagMax / 0.942);
  send("/levi/all/stop"); run(1.5);
  CHECK(state == ST_HOLD && fabs(plant.omega) < 0.05, "stop : arret en douceur");

  send("/levi/1/jog", {300}); run(0.2); CHECK(maxV > 100, "jog : le fil descend");
  run(1.0); CHECK(state == ST_HOLD && fabs(plant.omega) < 0.05, "jog : arret tout seul sans renvoi de la commande");

  // Le fil s'accroche pendant une remontee : l'objet ne peut plus monter
  send("/levi/1/goto", {1000, 4}); run(1.5);
  plant.stopP = plant.phys() - 60; plant.peakWindG = 0; run(2.0);
  CHECK(state == ST_FAULT && fault == F_SNAG, "fil accroche en montee : defaut, le moteur tient sans forcer");
  CHECK(plant.peakWindG < TENSION_MAX_DEFAULT_G * 1.1, "  traction maximale sur le fil : %.1f g (plafond %.0f g)", plant.peakWindG, TENSION_MAX_DEFAULT_G);
  plant.stopP = 0; send("/levi/1/reset"); run(0.5);
  CHECK(state == ST_HOLD && homed, "reset : reprise sans perdre l'origine");

  send("/levi/1/tension", {12}); run(0.1); plant.peakWindG = 0;
  send("/levi/1/goto", {plant.phys() > 1500 ? 1000.0f : 400.0f, 3}); run(1.2);
  plant.stopP = plant.phys() - 60; run(2.0);
  CHECK(fault == F_SNAG && plant.peakWindG < 12 * 1.1, "tension reglee a 12 g par OSC : traction maximale %.1f g", plant.peakWindG);
  plant.stopP = 0; send("/levi/1/reset"); send("/levi/1/tension", {30}); run(0.5);

  // Arret de groupe : un autre bloc (le 2) se met en defaut pendant un vol
  send("/levi/1/goto", {plant.phys() > 1500 ? 800.0f : 2200.0f, 4}); run(1.5);
  double vBefore = fabs(plant.omega * plant.r * 1000.0);
  send("/levi/all/groupstop", {2, 3}); run(1.0);
  CHECK(vBefore > 100 && state == ST_HOLD && fabs(plant.omega) < 0.05 && groupHoldFrom == 2, "arret de groupe recu du bloc 2 : arret en douceur (vitesse avant %.0f mm/s)", vBefore);
  double pHeld = plant.phys();
  send("/levi/1/goto", {pHeld + 300, 1}); send("/levi/all/pos", {(float)pHeld + 300, 0, 0, 0}); run(0.6);
  CHECK(fabs(plant.phys() - pHeld) < 0.5, "  mouvements refuses tant que l'arret de groupe n'est pas acquitte");
  send("/levi/all/groupstop", {1, 3}); run(0.1);
  CHECK(groupHoldFrom == 2, "  message portant son propre numero ignore");
  send("/levi/all/reset"); run(0.1);
  send("/levi/1/goto", {pHeld + 300, 1.5f}); run(2.0);
  CHECK(groupHoldFrom == 0 && fabs(plant.phys() - pHeld - 300) < 0.5, "  reset : les mouvements reprennent");
  int nGs = 0; for (auto& p : simTx) { OscMsg t; if (oscParseMessage(p.data(), p.size(), t) && !strcmp(t.addr, "/levi/all/groupstop") && t.arg[0] == WINCH_ID) nGs++; }
  CHECK(nGs >= 4, "ce bloc a prevenu les autres pendant ses propres defauts (%d messages emis)", nGs);

  // Arret d'urgence : moteur coupe, l'objet n'est plus retenu
  estopOk = false; run(0.05);
  CHECK(state == ST_FAULT && !plant.enabled && !homed, "arret d'urgence : moteur coupe, origine invalidee");
  send("/levi/1/reset"); run(0.2);
  CHECK(state == ST_FAULT, "reset refuse tant que l'arret d'urgence est enfonce");
  estopOk = true; send("/levi/1/reset"); run(0.1);
  CHECK(state == ST_DISARMED, "reset apres liberation : bloc desarme");

  // Test de rupture : fil attache a un point fixe, il casse a 120 g
  plant.omega = 0; plant.anchored = true; plant.breakG = 120;
  send("/levi/1/arm"); run(0.3); send("/levi/1/breaktest"); run(16);
  OscMsg br{}; bool gotBr = false;
  for (auto& p : simTx) { OscMsg t; if (oscParseMessage(p.data(), p.size(), t) && !strcmp(t.addr, "/levi/1/break")) { br = t; gotBr = true; } }
  CHECK(gotBr && br.arg[1] == 1 && fabsf(br.arg[0] - 120) < 6, "test de rupture : %.1f g mesures (le fil simule casse a 120 g)", br.arg[0]);
  CHECK(state == ST_HOLD && fabs(plant.omega) < 0.5, "  bobine arretee apres la rupture");
  plant.anchored = true; plant.breakG = 1000; plant.omega = 0;
  send("/levi/1/breaktest"); run(BREAKTEST_MAX_G / BREAKTEST_RATE_G_S + 1.5);
  gotBr = false;
  for (auto& p : simTx) { OscMsg t; if (oscParseMessage(p.data(), p.size(), t) && !strcmp(t.addr, "/levi/1/break")) { br = t; gotBr = true; } }
  CHECK(gotBr && br.arg[1] == 0 && plant.peakWindG < BREAKTEST_MAX_G * 1.05, "fil trop solide : test arrete a %.0f g sans casser", br.arg[0]);
  plant.anchored = false; plant.mass = 0.005;

  // Retour d'état et bundle OSC
  send("/levi/1/disarm"); run(0.3);
  OscMsg m{}; bool got = false;
  for (auto& p : simTx) { OscMsg t; if (oscParseMessage(p.data(), p.size(), t) && !strcmp(t.addr, "/levi/1/state")) { m = t; got = true; } }
  CHECK(got && m.n == 7 && m.arg[2] == ST_DISARMED, "retour d'etat OSC lisible, avec la tension du fil (%zu paquets emis)", simTx.size());
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
