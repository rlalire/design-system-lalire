// Réglages du bloc treuil, version BOBINE PLATE (Ø 250 mm, réducteur planétaire 10:1,
// sortie du fil par une poulie fixe, pas de guide-fil mobile).
// Réglages du bloc treuil. Tout ce qui dépend de la mécanique est ici.
#pragma once
#include <Arduino.h>

#ifndef WINCH_ID
#define WINCH_ID 1
#endif
#define WINCH_COUNT 4                 // nombre de blocs adressés par /levi/all/...

// ---------- Réseau ----------
// IP fixe : 192.168.10.(10 + WINCH_ID)
#define NET_IP_BASE   192, 168, 10
#define NET_IP_OFFSET 10
#define OSC_IN_PORT   9000            // le bloc écoute ici (unicast et broadcast)
#define OSC_OUT_PORT  9001            // retour d'état vers le dernier émetteur
#define FEEDBACK_PERIOD_MS 50

// ---------- Mécanique ----------
#define DRUM_DIAMETER_MM  250.0f      // diamètre du tambour, fond de fil
#define LINE_DIAMETER_MM    1.0f      // diamètre du fil
#define BELT_RATIO         10.0f      // rapport du réducteur planétaire
#define SERVO_PULSES_PER_REV 2000     // réglage « pulses/tour » du servo intégré
// Longueur de fil par tour de tambour (une seule couche). A étalonner sur le
// prototype : mesurer la course réelle sur 50 tours et corriger ici.
#define LINE_PER_TURN_MM   (PI * (DRUM_DIAMETER_MM + LINE_DIAMETER_MM))
#define STEPS_PER_MM       ((SERVO_PULSES_PER_REV * BELT_RATIO) / LINE_PER_TURN_MM)

// ---------- Limites de mouvement ----------
// Position = longueur de fil déroulée, en mm. 0 = origine haute, positif = descente.
#define VMAX_MM_S          3000.0f
#define AMAX_MM_S2         6000.0f
#define TRAVEL_DEFAULT_MM  10000.0f   // butée logicielle basse par défaut
#define KP_POS             20.0f      // rattrapage d'écart consigne/pas émis (1/s)
#define STREAM_OMEGA       25.0f      // gain de rattrapage en mode flux (1/s)
#define JOG_DEADMAN_MS     300
#define HOME_SPEED_MM_S    50.0f
#define HOME_BACKOFF_MM    20.0f
#define AUTO_DISARM_S      30         // frein serré après N s d'immobilité (0 = jamais)

// ---------- Trancannage (guide-fil) ----------
#define LW_ENABLED         0          // pas de guide-fil mobile sur cette version
#define LW_PITCH_MM        1.2f       // avance du guide par tour de tambour
#define LW_STEPS_PER_MM    800.0f     // NEMA 11, vis au pas de 2 mm, 1/8 de pas
#define LW_TRAVEL_MM       110.0f
#define LW_X_AT_ZERO_MM    105.0f     // position du guide quand le fil est tout enroulé
#define LW_SIGN            (-1.0f)    // sens du guide quand le fil se déroule
#define LW_HOME_SPEED_MM_S 10.0f

// ---------- Broches (Olimex ESP32-POE) — à valider sur le prototype ----------
#define PIN_SERVO_STEP   4
#define PIN_SERVO_DIR    5
#define PIN_SERVO_EN    13
#define PIN_SERVO_ALARM 34            // entrée seule, tirage externe requis
#define PIN_BRAKE       14            // HIGH = frein alimenté = desserré
#define PIN_LW_STEP     15
#define PIN_LW_DIR      16
#define PIN_LW_EN       32
#define PIN_LW_HOME     36            // entrée seule, tirage externe requis
#define PIN_HOME        35            // entrée seule, tirage externe requis
#define PIN_SLACK       39            // entrée seule, tirage externe requis
#define PIN_ESTOP       33

// Polarités (1 = actif à l'état haut)
#define SERVO_EN_ACTIVE     1
#define SERVO_ALARM_ACTIVE  0
#define LW_EN_ACTIVE        0
#define LW_HOME_ACTIVE      0
#define HOME_ACTIVE         0
#define SLACK_ACTIVE        0
#define ESTOP_ACTIVE        0         // boucle d'arrêt d'urgence ouverte = niveau bas
#define SLACK_ENABLED       1
#define DIR_INVERT          0         // inverser si « positif » fait monter
