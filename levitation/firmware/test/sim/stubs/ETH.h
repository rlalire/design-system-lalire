#pragma once
#include "Arduino.h"
struct IPAddress { uint8_t b[4]; IPAddress(uint8_t a = 0, uint8_t c = 0, uint8_t d = 0, uint8_t e = 0) : b{a, c, d, e} {} };
enum WiFiEvent_t { ARDUINO_EVENT_ETH_GOT_IP, ARDUINO_EVENT_ETH_DISCONNECTED, ARDUINO_EVENT_ETH_STOP };
struct WiFiStub { void onEvent(void (*f)(WiFiEvent_t)) { f(ARDUINO_EVENT_ETH_GOT_IP); } };
struct EthStub { void begin() {} void config(IPAddress, IPAddress, IPAddress) {} };
extern WiFiStub WiFi; extern EthStub ETH;
