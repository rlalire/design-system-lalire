// Réglages du bloc treuil, version MICRO : objets de quelques grammes sur fil très fin.
// Moteur pas-à-pas en prise directe (driver silencieux TMC2209), bobine étroite de 80 mm,
// sortie du fil par un œillet fixe. Ni frein, ni réducteur, ni guide-fil mobile.
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
#define DRUM_DIAMETER_MM   80.0f      // diamètre du tambour, fond de fil
#define LINE_DIAMETER_MM    0.05f     // diamètre du fil (un cheveu : 0,05 à 0,1 mm)
#define BELT_RATIO          1.0f      // prise directe
#define SERVO_PULSES_PER_REV 3200     // moteur 200 pas/tour, 16 micro-pas
// Longueur de fil par tour de tambour (une seule couche). A étalonner sur le
// prototype : mesurer la course réelle sur 50 tours et corriger ici.
#define LINE_PER_TURN_MM   (PI * (DRUM_DIAMETER_MM + LINE_DIAMETER_MM))
#define STEPS_PER_MM       ((SERVO_PULSES_PER_REV * BELT_RATIO) / LINE_PER_TURN_MM)

// ---------- Limites de mouvement ----------
// Position = longueur de fil déroulée, en mm. 0 = origine haute, positif = descente.
#define VMAX_MM_S          3000.0f
// Un objet très léger ne tombe pas plus vite que l'air ne le laisse descendre : au-delà,
// le fil se détend. A régler pour chaque objet (une feuille de papier : bien moins).
#define VMAX_DOWN_MM_S     1500.0f
#define AMAX_MM_S2         4000.0f    // doit rester nettement sous la pesanteur (9800)
#define TRAVEL_DEFAULT_MM  10000.0f   // butée logicielle basse par défaut
#define KP_POS             20.0f      // rattrapage d'écart consigne/pas émis (1/s)
#define STREAM_OMEGA       25.0f      // gain de rattrapage en mode flux (1/s)
#define JOG_DEADMAN_MS     300
#define HOME_SPEED_MM_S    50.0f
#define HOME_BACKOFF_MM    20.0f
#define AUTO_DISARM_S      0          // le moteur reste alimenté : c'est lui qui tient l'objet

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
#define SERVO_EN_ACTIVE     0         // l'entrée EN du TMC2209 est active à l'état bas
#define SERVO_ALARM_ACTIVE  0
#define LW_EN_ACTIVE        0
#define LW_HOME_ACTIVE      0
#define HOME_ACTIVE         0
#define SLACK_ACTIVE        0
#define ESTOP_ACTIVE        0         // boucle d'arrêt d'urgence ouverte = niveau bas
#define SLACK_ENABLED       0         // un objet de quelques grammes ne peut pas actionner un capteur
#define DIR_INVERT          0         // inverser si « positif » fait monter
