#pragma once
#include <map>
#include <string>
struct Preferences {
  std::map<std::string, float> m;
  void begin(const char*, bool) {}
  float getFloat(const char* k, float d) { return m.count(k) ? m[k] : d; }
  bool getBool(const char* k, bool d) { return m.count(k) ? m[k] != 0 : d; }
  void putFloat(const char* k, float v) { m[k] = v; }
  void putBool(const char* k, bool v) { m[k] = v; }
};
