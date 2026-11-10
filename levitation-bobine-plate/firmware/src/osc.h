// Lecture/écriture OSC minimale (messages et bundles, arguments f i d T F).
#pragma once
#include <Arduino.h>

struct OscMsg {
  char addr[64];
  float arg[8];
  uint8_t n;
};

static inline uint32_t oscBE32(const uint8_t* p) {
  return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3];
}

// Renvoie la longueur (padding compris) de la chaîne commençant en b, ou 0 si invalide.
static inline size_t oscStrLen(const uint8_t* b, size_t len) {
  size_t i = 0;
  while (i < len && b[i]) i++;
  if (i >= len) return 0;
  size_t padded = (i + 4) & ~(size_t)3;
  return padded <= len ? padded : 0;
}

static inline bool oscParseMessage(const uint8_t* b, size_t len, OscMsg& m) {
  size_t a = oscStrLen(b, len);
  if (!a || b[0] != '/') return false;
  strlcpy(m.addr, (const char*)b, sizeof(m.addr));
  m.n = 0;
  if (a >= len) return true;                       // message sans argument
  size_t t = oscStrLen(b + a, len - a);
  if (!t || b[a] != ',') return false;
  const char* tags = (const char*)b + a + 1;
  size_t p = a + t;
  for (; *tags && m.n < 8; tags++) {
    switch (*tags) {
      case 'f': {
        if (p + 4 > len) return false;
        uint32_t u = oscBE32(b + p); float f; memcpy(&f, &u, 4);
        m.arg[m.n++] = f; p += 4; break;
      }
      case 'i':
        if (p + 4 > len) return false;
        m.arg[m.n++] = (float)(int32_t)oscBE32(b + p); p += 4; break;
      case 'd': {
        if (p + 8 > len) return false;
        uint64_t u = ((uint64_t)oscBE32(b + p) << 32) | oscBE32(b + p + 4);
        double d; memcpy(&d, &u, 8);
        m.arg[m.n++] = (float)d; p += 8; break;
      }
      case 'T': m.arg[m.n++] = 1; break;
      case 'F': m.arg[m.n++] = 0; break;
      default: return false;                       // type non géré
    }
  }
  return true;
}

// Appelle fn(msg) pour chaque message du paquet (bundles imbriqués compris).
template <typename F>
static void oscDispatch(const uint8_t* b, size_t len, F fn, uint8_t depth = 0) {
  if (len >= 16 && memcmp(b, "#bundle", 8) == 0) {
    if (depth > 3) return;
    size_t p = 16;
    while (p + 4 <= len) {
      uint32_t sz = oscBE32(b + p); p += 4;
      if (sz > len - p) return;
      oscDispatch(b + p, sz, fn, depth + 1);
      p += sz;
    }
    return;
  }
  OscMsg m;
  if (oscParseMessage(b, len, m)) fn(m);
}

// Construit un message ; tags ne contient que 'f' ou 'i'. Renvoie la taille, 0 si trop grand.
static inline size_t oscBuild(uint8_t* out, size_t cap, const char* addr,
                              const char* tags, const float* vals) {
  size_t al = (strlen(addr) + 4) & ~(size_t)3;
  size_t nt = strlen(tags);
  size_t tl = (nt + 1 + 4) & ~(size_t)3;
  if (al + tl + 4 * nt > cap) return 0;
  memset(out, 0, al + tl);
  memcpy(out, addr, strlen(addr));
  out[al] = ',';
  memcpy(out + al + 1, tags, nt);
  size_t p = al + tl;
  for (size_t i = 0; i < nt; i++) {
    uint32_t u;
    if (tags[i] == 'i') u = (uint32_t)(int32_t)lroundf(vals[i]);
    else memcpy(&u, &vals[i], 4);
    out[p++] = u >> 24; out[p++] = u >> 16; out[p++] = u >> 8; out[p++] = u;
  }
  return p;
}
