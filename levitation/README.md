# Lévitation — bloc treuil synchronisé

Un bloc autonome qui enroule et déroule un fil avec précision, en silence, et qui se
synchronise avec d'autres blocs pour faire voler un objet sur 2, 3 ou 4 fils. Pilotage en OSC
(Chataigne, Orchestr…) par Ethernet.

![Maquette du bloc](cad/export/treuil.svg)

**État du projet : conception v0.1, rien n'est encore construit.**

| Élément | Où | Ce qui a été vérifié |
|---|---|---|
| Dimensionnement, composants, câblage | ce document | calculs ci-dessous ; références et prix à confirmer sur les fiches techniques avant achat |
| Firmware | `firmware/` | 25 vérifications passent en simulation sur PC ; **pas encore compilé pour la carte ni essayé sur un moteur** |
| Maquette 3D paramétrique | `cad/` | volumes et entraxes sans interférence ; les perçages et tolérances restent à dessiner |

## 1. Ce que fait un bloc

| | Valeur visée |
|---|---|
| Charge par fil | 10 kg en continu (objets de 8–9 kg), pointes à 30 kg |
| Vitesse | 3 m/s |
| Accélération | 6 m/s² (0 à 3 m/s en une demi-seconde) |
| Course | 10 m de fil sur une seule couche (paramétrable) |
| Résolution | 0,03 mm par pas |
| Encombrement | environ 290 × 205 × 140 mm, hors alimentation |
| Liaison | Ethernet, OSC, jusqu'à 100 m de câble par bloc |

## 2. Principe

```
 Chataigne / Orchestr ──OSC──> switch Ethernet ──> bloc 1, bloc 2, bloc 3, bloc 4

 Dans chaque bloc :
   carte ESP32 ──pas/direction──> servo 400 W ──courroie 2:1──> tambour Ø 40 ──> fil
        │                                                          │
        ├──> petit moteur + vis ──> chariot guide-fil (trancannage)┘
        ├──> frein à manque de courant sur l'axe du tambour
        └──< capteurs : origine haute, fil détendu, arrêt d'urgence, alarme servo
```

**Tambour à une seule couche.** C'est le choix qui donne la précision : le fil s'enroule en
spires jointives, toujours au même diamètre, donc un tour vaut toujours la même longueur
(128,8 mm). Avec plusieurs couches, le diamètre change et la précision au millimètre est perdue.

**Trancannage.** Un chariot porte un œillet céramique et avance de 1,2 mm par tour de tambour,
poussé par une vis et un petit moteur pas-à-pas piloté par un driver silencieux. J'ai préféré
cela à un servo de modélisme : la course fait 105 mm, il faut un mouvement linéaire propre et
inaudible, et à 3 m/s le chariot ne se déplace qu'à 28 mm/s, ce qui est très facile à suivre.

**Moteur.** Un servo intégré (moteur brushless, codeur et variateur dans le même boîtier) avec
une courroie crantée de rapport 2. La courroie est le réducteur le plus silencieux, et le servo
ne perd pas de pas : il signale une alarme s'il n'arrive plus à suivre.

**Frein.** Un frein électromagnétique serre l'axe dès que le courant est coupé. Sans lui, la
charge redescend toute seule à la moindre coupure.

## 3. Dimensionnement

- Fil par tour : π × (40 + 1) = **128,8 mm**. Pour 10 m : 78 tours + 5 tours morts, soit un
  tambour de **105 mm** de large au pas de 1,2 mm.
- Vitesse : le servo tourne à 3000 tr/min, le tambour à 1500 tr/min, soit 25 tours/s × 128,8 mm
  = **3,2 m/s**.
- Force : couple nominal 1,27 N·m × 2 (courroie) = 2,54 N·m au tambour, sur un rayon de
  20,5 mm : **124 N, soit 12,6 kg en continu**. En pointe (×3) : environ 37 kg.
- Puissance : 124 N × 3,2 m/s ≈ **400 W**, ce qui correspond exactement au moteur.
- Rayon de courbure du fil : tambour Ø 40 pour un fil de 1 mm, rapport 40, confortable pour
  une tresse Dyneema.

Deux points que le calcul fait apparaître :

1. **En vol à plusieurs fils, un fil peut porter plus que le poids de l'objet.** Deux fils qui
   forment un V très ouvert tirent chacun bien plus que la moitié de la charge : à 15° sous
   l'horizontale, chaque fil porte près de deux fois le poids. C'est pour cela que chaque bloc
   est prévu pour 10 kg et non 2 ou 3.
2. **« Au millimètre » veut dire répétable au millimètre.** Le treuil place le fil à 0,03 mm
   près, mais un fil s'allonge sous la charge : une tresse Dyneema fine peut prendre plusieurs
   millimètres par mètre selon le poids. Un même objet reviendra toujours au même endroit ; en
   revanche changer d'objet demande de refaire le calage. Plus le fil est gros par rapport à
   la charge, moins il s'allonge.

## 4. Composants (par bloc)

Références données comme candidates, prix en ordre de grandeur. À vérifier sur les fiches
techniques avant de commander.

| Fonction | Composant | Prix indicatif |
|---|---|---|
| Moteur | Servo intégré JMC iHSV60-30-40-48-SC, version avec frein 24 V intégré (400 W, 48 V, 3000 tr/min, 1,27 N·m, longueur 180 mm, 2 kg) | 180 € |
| Transmission | Poulies HTD 3M 20 et 40 dents, courroie largeur 15 mm, entraxe 90 mm | 25 € |
| Frein sur l'axe du tambour | Frein à manque de courant 24 V, 4 N·m minimum, alésage 12 mm. Facultatif hors public : le frein du servo suffit, mais il ne retient rien si la courroie casse | 45 € |
| Trancannage | Moteur pas-à-pas NEMA 11 à vis intégrée (pas 2 mm), 2 colonnes Ø 6, douilles | 45 € |
| Driver du trancannage | TMC2209 (mode silencieux) | 8 € |
| Carte | Olimex ESP32-POE (Ethernet, alimentée par le câble réseau) | 25 € |
| Interface | Driver de ligne 5 V (74HCT245 ou AM26LS31) vers le servo, MOSFET + diode pour le frein, optocoupleurs pour les capteurs | 15 € |
| Alimentation | Mean Well HLG-480H-48 (48 V, sans ventilateur, donc silencieuse) | 120 € |
| Freinage électrique | Module de dissipation (résistance de freinage 48 V) : en descente d'une charge lourde, le moteur renvoie du courant | 30 € |
| Convertisseur | 48 V vers 24 V, 2 A (frein, trancannage) | 12 € |
| Capteurs | Origine haute (inductif ou fourche optique), fil détendu (bras à ressort + fourche), fin de course du chariot | 20 € |
| Mécanique | 2 flasques alu 8 mm, tambour alu, chariot, axe Ø 12, 2 roulements 6001, 4 entretoises (usinage en Chine) | 100–150 € |
| Guide-fil | Œillet céramique, poulie de sortie sur roulement | 15 € |
| Divers | Connecteurs, câbles, visserie, capot | 40 € |
| | **Total par bloc** | **environ 650–750 €** |

Pour les objets de moins d'un kilo seulement, le servo 180 W (iHSV57-30-18-36) suffirait et
économiserait une centaine d'euros avec son alimentation. Je conseille de construire
directement la version 400 W : la mécanique est la même et il n'y aura rien à refaire pour les
objets lourds.

## 5. Câblage

- **Servo** : la carte sort du 3,3 V, les entrées du servo attendent du 5 V et jusqu'à 100 000
  impulsions par seconde. Il faut un driver de ligne entre les deux, et un câble blindé.
- **Frein** : alimenté en 24 V à travers un MOSFET commandé par la carte, avec une diode de
  roue libre. La carte doit alimenter le frein pour le desserrer : carte éteinte ou plantée,
  le frein serre.
- **Arrêt d'urgence** : une boucle câblée qui passe par tous les blocs et **coupe directement
  le 24 V des freins**, sans passer par le logiciel. La carte lit aussi cette boucle pour
  s'arrêter proprement, mais la sécurité ne dépend pas d'elle.
- **Capteurs** : sur optocoupleurs. Quatre entrées de la carte (34, 35, 36, 39) n'ont pas de
  résistance de tirage interne, il faut en mettre sur la carte d'interface.
- **Réseau** : un switch, un câble par bloc. Un switch PoE alimente les cartes par le même
  câble, ce qui permet de garder la main sur un bloc même si son 48 V est coupé.

L'affectation des broches est dans `firmware/src/config.h`.

## 6. Protocole OSC

Chaque bloc écoute sur le port **9000**, à l'adresse `192.168.10.11` (bloc 1) à `.14` (bloc 4),
et aussi en diffusion (`192.168.10.255`). Il renvoie son état sur le port **9001**, 20 fois par
seconde.

Les positions sont en **millimètres de fil déroulé** : 0 = origine haute, positif = descente.
`N` est le numéro du bloc, ou `all` pour tous.

| Message | Arguments | Effet |
|---|---|---|
| `/levi/N/arm` | — | Met le servo sous tension puis desserre le frein. Obligatoire avant tout mouvement. |
| `/levi/N/disarm` | — | Serre le frein et coupe le servo. |
| `/levi/N/goto` | position, durée (s) | Va à la position en courbe douce, dans la durée donnée. |
| `/levi/all/goto` | p1, p2, p3, p4, durée | Le même paquet pour tous : chaque bloc prend sa position et tous partent ensemble. |
| `/levi/N/pos` | position | Consigne envoyée en continu (50 à 100 fois par seconde), pour piloter depuis une courbe ou un capteur. |
| `/levi/all/pos` | p1, p2, p3, p4 | Idem pour tous les blocs en un seul paquet. |
| `/levi/N/jog` | vitesse (mm/s) | Déplacement manuel. S'arrête seul si le message n'est pas renvoyé toutes les 300 ms. |
| `/levi/N/stop` | — | Arrêt en douceur. |
| `/levi/N/home` | — | Remonte lentement jusqu'au capteur d'origine. |
| `/levi/N/zero` | — | La position actuelle devient l'origine. |
| `/levi/N/limits` | min, max | Butées logicielles, mémorisées. |
| `/levi/N/reset` | — | Acquitte un défaut, une fois sa cause disparue. |

Retour : `/levi/N/state` position (mm), vitesse (mm/s), état, origine connue (0/1), défaut.
États : 0 désarmé, 1 armement, 2 immobile, 3 goto, 4 flux, 5 jog, 6 prise d'origine, 7 arrêt en
cours, 8 défaut. Défauts : 1 arrêt d'urgence, 2 alarme servo, 3 fil détendu en descente.
`/levi/N/warn` signale une commande refusée ou modifiée (1 pas armé, 2 origine non faite,
3 durée allongée, 4 consigne écrêtée, 5 refusé en mouvement).

**Synchronisation.** Les blocs ne se parlent pas entre eux : ils reçoivent le même paquet au
même instant (moins d'une milliseconde d'écart sur un réseau câblé) et chacun exécute sa part
avec la même courbe. La position de chaque bloc est mémorisée quand le frein serre, donc
l'origine n'est pas à refaire à chaque mise sous tension.

À savoir : si une durée demandée est trop courte pour un bloc, il l'allonge pour respecter ses
limites et prévient par `/levi/N/warn 3`. Les autres ne s'alignent pas d'eux-mêmes ; il faut
donc que les durées demandées restent réalistes.

## 7. Firmware

```
cd firmware
pio run -t upload        # changer WINCH_ID dans platformio.ini pour chaque bloc
./test/sim/run.sh        # simulation sur PC, sans matériel
```

La simulation fait tourner le firmware complet avec un moteur simulé et de vrais paquets OSC.
Elle vérifie les refus de sécurité, un déplacement groupé (arrivée à 0,02 mm de la cible), un
déplacement à 3 m/s, le suivi d'une consigne continue (environ 9 ms de retard, identique sur
tous les blocs), le suivi du guide-fil, l'arrêt d'urgence, la prise d'origine et le frein
automatique.

Ce que la simulation ne dit pas : le comportement de la vraie bibliothèque de génération de
pas, le réglage du servo, le bruit, la tenue thermique. Tout cela se joue sur le prototype.

## 8. Silence : à quoi s'attendre

- À l'arrêt et à faible vitesse (jusqu'à environ 0,5 m/s) : quasiment inaudible dans une salle.
- À 3 m/s : la courroie et le fil dans l'œillet s'entendent. C'est un souffle, pas un
  grincement, et une musique le couvre, mais ce ne sera pas silencieux.
- L'alimentation choisie n'a pas de ventilateur. Un capot avec mousse et des plots en
  caoutchouc sous le bloc font le reste : le bruit vient surtout de la structure qui résonne.

## 9. Sécurité

Je peux concevoir le treuil, pas le certifier.

- **Au-dessus du public**, même avec un objet léger, le montage doit être validé par un
  rigger ou un bureau de contrôle. La pratique du spectacle demande un coefficient de sécurité
  de 10 sur le fil et les accroches, et une sécurité secondaire indépendante qui retient
  l'objet si le fil ou le treuil lâche.
- **Hors public**, viser un coefficient de 5 au minimum sur le fil.
- Tant que le prototype n'a pas été éprouvé (charge d'essai, coupure de courant en mouvement,
  arrêt d'urgence à pleine vitesse), personne ne passe dessous.

## 10. Suite

1. Confirmer le fil (diamètre et charge de rupture) et la course nécessaire : ces deux valeurs
   fixent la largeur du tambour.
2. Commander les composants d'**un** bloc et monter un prototype sur flasques imprimés en 3D.
3. Compiler le firmware, régler le servo, étalonner la longueur par tour.
4. Dessiner les pièces définitives sur les composants réels, puis lancer l'usinage des 4 blocs.
5. Écrire le module Chataigne qui convertit une position X, Y, Z de l'objet en longueurs de
   fil pour 2, 3 ou 4 blocs.
