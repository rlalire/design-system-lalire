// Faux SimpleFOC pour la simulation : même interface, avec un modèle physique derrière
// (moteur, bobine, objet suspendu, butée haute, fil attaché qui peut casser).
#pragma once
#include "Arduino.h"

struct SimPlant {
  // Partie tournante et moteur
  double J = 8.0e-5, Kt = 0.0827, R = 10.0, KV = 100.0, V = 12.0, r = 0.040025;
  double theta = 0, omega = 0, iq = 0, iReal = 0;
  bool enabled = false;
  // Monde
  double mass = 0.005;          // objet suspendu, kg
  double pOffset = 500;         // position physique (mm sous la butée) quand theta = 0
  double stopP = 0;             // butée haute : l'objet ne monte pas plus haut
  bool anchored = false;        // fil attaché à un point fixe (test de rupture)
  double breakG = 120;          // charge de rupture du fil attaché
  double peakWindG = 0;         // plus forte traction exercée par le moteur
  double phys() const { return theta * r * 1000.0 + pOffset; }
  void step(double dt) {
    const double g = 9.81;
    double bemf = omega * 60.0 / (2 * M_PI) / KV;                 // le moteur plafonne en vitesse
    double v = iq * R + bemf;
    v = v > V ? V : (v < -V ? -V : v);
    iReal = enabled ? (v - bemf) / R : 0;
    double windG = -Kt * iReal / r / g * 1000.0;
    if (windG > peakWindG) peakWindG = windG;
    if (anchored) {
      if (windG > breakG) { anchored = false; mass = 0; }          // le fil casse
      else { omega = 0; return; }
    }
    double tq = Kt * iReal + mass * g * r;                        // positif = sens du déroulement
    double fr = 3.0e-4;
    if (fabs(omega) < 0.05 && fabs(tq) <= fr) { omega = 0; return; }
    tq -= (omega > 0 ? fr : (omega < 0 ? -fr : (tq > 0 ? fr : -fr))) + 2.0e-6 * omega;
    omega += tq / (J + mass * r * r) * dt;
    theta += omega * dt;
    if (phys() < stopP) { theta = (stopP - pOffset) / 1000.0 / r; if (omega < 0) omega = 0; }
  }
};
extern SimPlant plant;

enum class TorqueControlType { voltage };
enum class MotionControlType { torque };
struct LowPass { float Tf = 0.005f; };
struct MagneticSensorSPIConfig_s {};
static const MagneticSensorSPIConfig_s AS5048_SPI;
struct MagneticSensorSPI { MagneticSensorSPI(MagneticSensorSPIConfig_s, int) {} void init() {} };
struct BLDCDriver3PWM { float voltage_power_supply = 12; BLDCDriver3PWM(int, int, int, int) {} int init() { return 1; } };

struct BLDCMotor {
  float shaft_angle = 0, shaft_velocity = 0, voltage_limit = 12, current_limit = 1;
  TorqueControlType torque_controller; MotionControlType controller; LowPass LPF_velocity;
  double lastTheta = 0; uint64_t lastUs = 0;
  BLDCMotor(int, float, float) {}
  void linkSensor(MagneticSensorSPI*) {}
  void linkDriver(BLDCDriver3PWM*) {}
  void init() {}
  int initFOC() { sample(); return 1; }
  void enable() { plant.enabled = true; }
  void disable() { plant.enabled = false; plant.iq = 0; }
  void loopFOC() {}
  void sample() {
    const double q = 2 * M_PI / 16384.0;                           // encodeur 14 bits
    double th = floor(plant.theta / q) * q;
    double dt = (simUs - lastUs) * 1e-6;
    if (lastUs && dt > 0) {
      double raw = (th - lastTheta) / dt, a = dt / (LPF_velocity.Tf + dt);
      shaft_velocity += (float)(a * (raw - shaft_velocity));
    }
    lastTheta = th; lastUs = simUs; shaft_angle = (float)th;
  }
  void move(float target) {
    sample();
    float lim = current_limit;
    plant.iq = plant.enabled ? (target > lim ? lim : (target < -lim ? -lim : target)) : 0;
  }
};
