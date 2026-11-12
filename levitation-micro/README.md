# Lévitation — bloc treuil micro

Un boîtier fermé de **112 × 135 × 60 mm** pour faire voler des objets de quelques grammes
(bague, pliage de papier, carton) au bout d'un fil très fin. Le fil sort par un seul œillet.

**État : conception v0.3, rien n'est encore construit.** Le firmware passe 31 vérifications
dans une simulation sur PC qui reproduit le moteur, la bobine et un objet suspendu. Il n'a pas
été compilé pour la carte ni essayé sur un moteur.

- `simulation.html` : vue 3D animée (boîtier, objet, salle).
- `cad/` : maquette paramétrique, boîtier, couvercles et bobine.
- `firmware/` : le firmware, avec sa simulation dans `firmware/test/sim/`.

## Le moteur

Un moteur de gimbal **CubeMars G35 KV100**, en prise directe. C'est le GL35 dans un carter
fermé, avec l'encodeur à l'intérieur (159 g, 49,8 mm de diamètre, 31,6 mm de long).

- **Il est silencieux** : il tourne en continu, sans pas.
- **Son carter est fixe et fermé** : il se visse sur la cloison, et seul un petit moyeu
  tourne. La bobine est une cloche vissée sur ce moyeu, qui revient entourer le carter. Il
  n'y a ni arbre, ni roulement à ajouter, et le fil ne peut pas entrer dans le moteur.
- **Il se pilote en force** : le courant qu'on lui donne fixe la tension du fil. Tout ce qui
  suit en découle.

## Ce que le pilotage en force apporte

| Fonction | Commande OSC | Ce qu'elle fait |
|---|---|---|
| Tension plafonnée | `/levi/N/tension 30` | Le moteur ne tire jamais plus fort que la valeur donnée, en grammes |
| Fil accroché | automatique | Si l'objet ne suit plus, le moteur s'arrête et tient en place sans forcer (défaut 3) |
| Test de rupture | `/levi/N/breaktest` | Fil attaché à un point fixe : le moteur tire de plus en plus fort et renvoie la tension à laquelle le fil a cassé (`/levi/N/break grammes cassé`) |
| Prise d'origine douce | `/levi/N/home` | L'objet remonte lentement jusqu'à buter sous l'œillet, avec une force plafonnée (`/levi/N/hometension`, 15 g par défaut) |
| Tension lue | dans `/levi/N/state` | La tension estimée du fil est renvoyée 20 fois par seconde |

**Régler un fil inconnu.** Faire le test de rupture sur un bout de fil, puis régler la
tension maximale au tiers de la valeur obtenue. Le test coûte quelques centimètres de fil.

**Précision des grammes.** Le courant est estimé, pas mesuré : sans capteur de courant, les
valeurs en grammes sont justes à quelques grammes près, et les frottements du moteur
s'ajoutent. C'est suffisant pour protéger le fil avec une marge de trois ; une carte de
commande avec mesure de courant ferait mieux.

Les autres commandes (`arm`, `goto`, `pos`, `jog`, `stop`, `zero`, `limits`, `reset`) sont
celles des autres versions : voir [`../levitation/README.md`](../levitation/README.md),
section 6. Le retour d'état a une valeur de plus : `/levi/N/state` position, vitesse, état,
origine connue, défaut, tension estimée (g). L'état 9 est le test de rupture.

## Ce que fait le bloc

| | Valeur visée |
|---|---|
| Objets | de 1 à 50 g |
| Course | 10 m de fil, 40 spires sur un seul rang |
| Fil par tour | 251,5 mm |
| Résolution de l'encodeur | 0,015 mm si c'est un 14 bits (à confirmer) |
| Vitesse en montée | jusqu'à 3 m/s (717 tr/min), **à confirmer sur le prototype** |
| Vitesse en descente | limitée à 1,5 m/s, réglable par objet |
| Accélération | 4 m/s² |
| Boîtier | 112 × 135 × 60 mm, moteur et électronique compris |

En simulation, avec un objet de 5 g : arrivée à moins de 0,3 mm de la cible, écart de suivi
de 1,6 mm à 0,9 m/s et de 5 mm à 3 m/s, retard d'environ 8 ms sur une consigne envoyée en
continu. Ces chiffres dépendent de valeurs du moteur que je n'ai pas (résistance, inertie
réelle) : ils donnent un ordre de grandeur, pas une garantie.

## À savoir avant de s'en servir

- **Moteur coupé, l'objet n'est plus retenu.** Un moteur de gimbal ne tient rien sans
  courant. Coupure de courant, arrêt d'urgence ou désarmement : l'objet redescend. Pour une
  bague ou du papier c'est sans danger, mais l'origine est perdue et se refait par
  `/levi/all/home`.
- **Un objet léger ne descend pas plus vite que l'air ne le laisse tomber.** Une bague suit ;
  une feuille plane. Si le treuil déroule plus vite, le fil se détend et s'emmêle. D'où la
  vitesse de descente séparée (`VMAX_DOWN_MM_S`), à régler pour chaque objet.
- **La butée d'origine doit être douce.** L'objet, ou une petite perle souple nouée sur le
  fil au-dessus de lui, vient toucher l'œillet. La tension d'origine doit dépasser le poids
  de l'objet, sinon il ne décolle pas et l'origine est fausse.
- **Tout ce que le fil touche doit être lisse.** Bobine en résine (procédé SLA), pas en
  nylon fritté ni en dépôt de fil. Sortie par un œillet céramique de canne à pêche.
- **Aucune fente.** La bobine est d'une seule pièce et tourne dans une chambre fermée,
  séparée de l'électronique.
- **La précision.** Un fil aussi fin s'allonge de plusieurs millimètres par mètre selon le
  poids. Un même objet revient au même endroit ; l'étalonnage se fait avec l'objet accroché.

## Composants

Références et prix à confirmer ; ce sont des ordres de grandeur.

| Fonction | Composant | Prix indicatif |
|---|---|---|
| Moteur | CubeMars G35 KV100 (encodeur intégré) | à confirmer, 65 à 92 € relevés pour la version avec encodeur |
| Carte de commande du moteur | Carte compatible SimpleFOC, 3 sorties, 12 V, 1 A ou plus (par exemple SimpleFOC Mini) | 15 € |
| Carte | Olimex ESP32-POE (Ethernet) | 25 € |
| Alimentation | Séparateur PoE 12 V (le courant arrive par le câble réseau) et petit convertisseur 5 V | 15 € |
| Sortie du fil | Œillet céramique, diamètre intérieur 2 à 3 mm | 2 € |
| Bobine | Impression résine, 92 mm de diamètre, environ 49 g | à chiffrer |
| Boîtier | Corps et deux couvercles imprimés | à chiffrer |
| Divers | Visserie, connecteurs, mousse | 10 € |
| | **Total par bloc** | **environ 150 à 200 €** |

Il faut un switch réseau PoE pour alimenter les blocs. Le moteur est donné pour 16 V ; voir
« Avant de commander » pour la vitesse en 12 V.

## Câblage

| Carte ESP32 | Vers |
|---|---|
| Broches 4, 5, 13 | les trois entrées de la carte de commande du moteur |
| Broche 14 | activation de la carte de commande |
| Broches 15, 35, 2, 16 | encodeur (horloge, données entrantes, données sortantes, sélection) |
| Broche 33 | boucle d'arrêt d'urgence, ou pont vers le 3,3 V si elle n'est pas câblée |
| Broche 36 | capteur d'origine, facultatif |

## Fixation du moteur

D'après le plan coté du G35 :

| Côté | Sur le plan | Sur la maquette |
|---|---|---|
| Arrière (sortie du câble) | bossage de 32 mm, 3 × M3 sur un cercle de 40 mm et 4 × M3 sur 25 mm, profondeur 4 mm | le bossage se centre dans la cloison, fixation par les 3 × M3 |
| Avant | moyeu avec 4 × M3 sur un cercle de 15 mm, profondeur 6 mm, arbre creux de 6,5 mm | la bobine s'y visse, par 4 vis M3 × 8 |

J'ai lu le plan ainsi : le carter à ailettes est fixe, et c'est le petit moyeu avant qui
tourne. **C'est à faire confirmer par CubeMars avant de commander les pièces**, car tout le
montage en dépend. L'orientation des 3 vis arrière par rapport à la sortie du câble est
aussi à vérifier sur leur fichier 3D.

## Avant de commander

Les valeurs électriques sont dans le firmware, d'après les fiches des revendeurs pour le
GL35 : 7 paires de pôles, 3,6 ohms entre phases, 0,115 N·m par ampère, 82,5 tr/min par volt.
Le G35 contient a priori le même moteur ; c'est à confirmer. L'inertie du rotor reste une
estimation.

À confirmer auprès de CubeMars :

1. Quelle partie tourne (voir ci-dessus).
2. Le modèle d'encodeur, sa liaison, sa tension d'alimentation et le brochage du câble. Le
   firmware suppose un AS5048A en SPI.
3. Le fichier 3D (STEP) du G35.

**Vitesse en 12 V.** Avec 82,5 tr/min par volt, le moteur plafonne vers 990 tr/min à vide
en 12 V, pour 717 nécessaires à 3 m/s. La marge est faible : prévoir une alimentation 16 V
si les 3 m/s comptent, ou accepter environ 2,5 m/s en 12 V.

Restent aussi à dessiner : les vis de fermeture des couvercles et les supports des cartes.

## Fabrication

```
cd cad && python3 treuil.py              # régénère toutes les pièces
cd firmware && ./test/sim/run.sh         # simulation du firmware sur PC
```

| Fichier | Usage |
|---|---|
| `cad/export/bobine.stl` / `.step` | bobine en cloche, à imprimer en résine |
| `cad/export/boitier.step` | corps du boîtier, avec la cloison porte-moteur et les pattes d'accroche |
| `cad/export/couvercle_avant.step`, `couvercle_arriere.step` | les deux couvercles |
| `cad/export/treuil.step` | l'assemblage complet |

## À confirmer sur le prototype

1. La vitesse réellement atteinte en 12 V.
2. Le réglage de l'asservissement (`CTRL_OMEGA`) : plus ferme, il suit mieux mais s'entend.
3. La justesse des tensions en grammes, à comparer avec une balance.
4. La tenue du fil sur la bobine en résine et dans l'œillet.
5. Le bruit à pleine vitesse.
