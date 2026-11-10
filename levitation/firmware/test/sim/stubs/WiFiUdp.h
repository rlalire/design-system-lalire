#pragma once
#include "ETH.h"
#include <vector>
#include <deque>
extern std::deque<std::vector<uint8_t>> simRx;   // paquets à livrer au firmware
extern std::vector<std::vector<uint8_t>> simTx;  // paquets émis par le firmware
struct WiFiUDP {
  std::vector<uint8_t> cur, out;
  void begin(int) {}
  int parsePacket() { if (simRx.empty()) return 0; cur = simRx.front(); simRx.pop_front(); return (int)cur.size(); }
  IPAddress remoteIP() { return IPAddress(192, 168, 10, 2); }
  int read(uint8_t* b, size_t n) { size_t c = min(n, cur.size()); memcpy(b, cur.data(), c); return (int)c; }
  void beginPacket(IPAddress, int) { out.clear(); }
  void write(const uint8_t* b, size_t n) { out.assign(b, b + n); }
  void endPacket() { simTx.push_back(out); }
};
