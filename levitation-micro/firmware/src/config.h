// Réglages du bloc treuil, version MICRO : objets de quelques grammes sur fil très fin.
// Moteur de gimbal CubeMars GL35 KV100 avec encodeur AS5048A, en prise directe, piloté en couple
// (bibliothèque SimpleFOC). Bobine étroite de 80 mm, sortie du fil par un œillet fixe.
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
#define OSC_IN_PORT   9000
#define OSC_OUT_PORT  9001
#define FEEDBACK_PERIOD_MS 50

// ---------- Mécanique ----------
#define DRUM_DIAMETER_MM   80.0f      // diamètre de la bobine, fond de gorge
#define LINE_DIAMETER_MM    0.05f     // diamètre du fil (un cheveu : 0,05 à 0,1 mm)
// Rayon utile. A étalonner : dérouler un mètre mesuré et corriger DRUM_DIAMETER_MM.
#define R_EFF_MM           ((DRUM_DIAMETER_MM + LINE_DIAMETER_MM) / 2.0f)
#define DIR_SIGN           1.0f       // mettre -1 si « positif » fait monter l'objet

// ---------- Moteur : CubeMars GL35 KV100, valeurs confirmées par CubeMars ----------
#define MOTOR_POLE_PAIRS   7
#define MOTOR_PHASE_R      1.8f       // une phase = la moitié des 3,6 ohms annoncés entre phases
#define MOTOR_KV           82.5f      // tr/min par volt : 990 tr/min à vide sous 12 V (nom commercial : KV100)
#define SUPPLY_VOLTAGE     12.0f
#define MOTOR_KT           0.115f                             // N·m par ampère, annoncé
// Inertie de la partie tournante (rotor + bobine), kg·m². Sert à calculer les gains.
#define INERTIA_KGM2       8.0e-5f
#define ACC_PER_AMP        (MOTOR_KT * R_EFF_MM / INERTIA_KGM2)   // mm/s² de fil par ampère
// Courant nécessaire pour un gramme de tension dans le fil
#define AMP_PER_GRAM       (9.81e-6f * R_EFF_MM / MOTOR_KT)

// ---------- Asservissement de position ----------
#define CTRL_OMEGA         60.0f      // raideur (rad/s) : plus haut = plus ferme, plus bruyant
#define KP_A_PER_MM        (CTRL_OMEGA * CTRL_OMEGA / ACC_PER_AMP)
#define KD_A_PER_MM_S      (2.0f * CTRL_OMEGA / ACC_PER_AMP)
#define KI_A_PER_MM_S      (KP_A_PER_MM * 8.0f)               // rattrape le poids de l'objet
#define VELOCITY_FILTER_S  0.004f
#define PUSH_CURRENT_A     0.15f      // on ne pousse pas un fil : juste de quoi lancer la bobine

// ---------- Limites de mouvement ----------
// Position = longueur de fil déroulée, en mm. 0 = origine haute, positif = descente.
#define VMAX_MM_S          3000.0f
// Un objet très léger ne tombe pas plus vite que l'air ne le laisse descendre : au-delà,
// le fil se détend. A régler pour chaque objet (une feuille de papier : bien moins).
#define VMAX_DOWN_MM_S     1500.0f
#define AMAX_MM_S2         4000.0f    // doit rester nettement sous la pesanteur (9800)
#define TRAVEL_DEFAULT_MM  10000.0f
#define STREAM_OMEGA       25.0f
#define JOG_DEADMAN_MS     300

// ---------- Fil ----------
#define TENSION_MAX_DEFAULT_G   30.0f // tension maximale du fil, réglable par /levi/N/tension
#define HOME_TENSION_DEFAULT_G  15.0f // tension pendant la prise d'origine (> poids de l'objet)
#define HOME_SPEED_MM_S         60.0f
#define HOME_BACKOFF_MM         20.0f
#define MEASURE_SLACK_MM        20.0f // mou rendu après une mesure de longueur
#define SNAG_ERROR_MM           30.0f // écart au-delà duquel on considère le fil accroché
#define SNAG_TIME_MS            150
#define BREAKTEST_RATE_G_S      10.0f // montée en tension pendant le test de rupture
#define BREAKTEST_MAX_G         300.0f
#define BREAKTEST_SPEED_MM_S    300.0f // la bobine qui s'emballe = le fil a cassé

// ---------- Broches (Olimex ESP32-POE) — à valider sur le prototype ----------
#define PIN_PWM_A        4
#define PIN_PWM_B        5
#define PIN_PWM_C       13
#define PIN_DRV_EN      14
#define PIN_ENC_CS      16            // encodeur AS5048A en SPI, 14 bits : SCK 15, MISO 36, MOSI 2
#define PIN_ENC_SCK     15
#define PIN_ENC_MISO    36            // entrée libre ; 34, 35 et 39 servent déjà sur la carte Olimex
#define PIN_ENC_MOSI     2
#define PIN_HOME        35            // capteur d'origine facultatif, désactivé par défaut
#define PIN_ESTOP       33

#define HOME_SENSOR_ENABLED 0
#define HOME_ACTIVE         0
#define ESTOP_ACTIVE        0         // boucle d'arrêt d'urgence ouverte = niveau bas
