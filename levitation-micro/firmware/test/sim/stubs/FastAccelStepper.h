// Moteur simulé : même interface que FastAccelStepper, rampe limitée en accélération.
#pragma once
#include "Arduino.h"
#include <vector>
struct FastAccelStepper {
  double pos = 0, vel = 0, speed = 1000, accel = 1000; int32_t target = 0;
  enum { IDLE, FWD, BWD, TO, STOP } mode = IDLE;
  double peak = 0;
  void setDirectionPin(uint8_t, bool = true) {}
  int8_t setSpeedInHz(uint32_t h) { speed = h; return 0; }
  int8_t setSpeedInMilliHz(uint32_t h) { speed = h / 1000.0; return 0; }
  int8_t setAcceleration(int32_t a) { accel = a; return 0; }
  int8_t runForward() { mode = FWD; return 0; }
  int8_t runBackward() { mode = BWD; return 0; }
  int8_t moveTo(int32_t t) { target = t; mode = TO; return 0; }
  void stopMove() { if (mode != IDLE) mode = STOP; }
  void forceStopAndNewPosition(int32_t p) { pos = p; vel = 0; mode = IDLE; }
  int32_t getCurrentPosition() { return (int32_t)lround(pos); }
  void setCurrentPosition(int32_t p) { pos = p; }
  void advance(double dt) {
    double want = 0;
    if (mode == FWD) want = speed; else if (mode == BWD) want = -speed;
    else if (mode == TO) { double d = target - pos; want = (d > 0 ? 1 : -1) * min(speed, sqrt(2 * accel * fabs(d))); if (fabs(d) < 0.5) want = 0; }
    double dv = accel * dt;
    vel = vel < want ? min(vel + dv, want) : max(vel - dv, want);
    pos += vel * dt;
    peak = max(peak, fabs(vel));
    if (mode == STOP && vel == 0) mode = IDLE;
  }
};
extern std::vector<FastAccelStepper*> simSteppers;
struct FastAccelStepperEngine {
  void init() {}
  FastAccelStepper* stepperConnectToPin(uint8_t) { auto* s = new FastAccelStepper(); simSteppers.push_back(s); return s; }
};
