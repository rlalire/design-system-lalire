// Faux environnement Arduino pour faire tourner le firmware sur un PC (simulation).
#pragma once
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <algorithm>
using std::min; using std::max; using std::isnan;
#define PI 3.14159265358979f
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLDOWN 2
#define constrain(x, lo, hi) ((x) < (lo) ? (lo) : ((x) > (hi) ? (hi) : (x)))
extern uint64_t simUs;
extern int simPins[64];
void simAdvance(uint32_t us);
int simRead(uint8_t pin);
inline uint32_t micros() { return (uint32_t)simUs; }
inline uint32_t millis() { return (uint32_t)(simUs / 1000); }
inline void delay(uint32_t ms) { simAdvance(ms * 1000); }
inline void pinMode(uint8_t, uint8_t) {}
inline void digitalWrite(uint8_t p, int v) { simPins[p] = v; }
inline int digitalRead(uint8_t p) { return simRead(p); }
struct SerialStub { void begin(int) {} void printf(const char*, ...) {} };
extern SerialStub Serial;
