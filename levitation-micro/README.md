# Lévitation — bloc treuil micro

Un boîtier fermé de **112 × 123 × 66 mm**, accroché par un spigot de 16 mm pour faire voler des objets de quelques grammes
(bague, pliage de papier, carton) au bout d'un fil très fin. Le fil sort par un seul œillet.

**État : conception v0.8, pièces du prototype dessinées pour l'impression 3D, rien n'est encore construit.** Le firmware passe 31 vérifications
dans une simulation sur PC qui reproduit le moteur, la bobine et un objet suspendu. Il n'a pas
été compilé pour la carte ni essayé sur un moteur.

- `simulation.html` : vue 3D animée (boîtier, objet, salle).
- `cad/` : modèle paramétrique, les quatre pièces à imprimer et leurs planches.
- `firmware/` : le firmware, avec sa simulation dans `firmware/test/sim/`.

## Le moteur

Un moteur de gimbal **CubeMars GL35 KV100 avec encodeur**, en prise directe (41,8 mm de
diamètre, 33,5 mm de long avec l'encodeur). Le G35 envisagé un temps n'est plus fabriqué ;
CubeMars indique le GL35 comme son remplaçant.

- **Il est silencieux** : il tourne en continu, sans pas, et CubeMars le donne pour un
  moteur à faible couple de crantage.
- **Il est court** : la bobine est une cloche vissée sur sa face tournante et l'entoure.
  Il n'y a ni arbre, ni moyeu, ni roulement à ajouter.
- **Il se pilote en force** : le courant qu'on lui donne fixe la tension du fil. Tout ce qui
  suit en découle.

Il n'a pas de carte de commande intégrée : il lui faut une carte séparée, compatible
SimpleFOC.

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
| Résolution de l'encodeur | 0,015 mm de fil (AS5048A, 14 bits) |
| Vitesse en montée | jusqu'à 3 m/s (717 tr/min), **à confirmer sur le prototype** |
| Vitesse en descente | limitée à 1,5 m/s, réglable par objet |
| Accélération | 4 m/s² |
| Boîtier | 112 × 123 × 66 mm, moteur et électronique compris |

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
| Moteur | CubeMars GL35 KV100 avec encodeur | 73 $ pièce par 4 (devis CubeMars), 79,99 $ à l'unité |
| Carte de commande du moteur | Carte compatible SimpleFOC, 3 sorties, 12 V, 1 A ou plus (par exemple SimpleFOC Mini) | 15 € |
| Carte | Olimex ESP32-POE (Ethernet) | 25 € |
| Alimentation | Séparateur PoE 12 V (le courant arrive par le câble réseau) et petit convertisseur 5 V | 15 € |
| Sortie du fil | Œillet céramique, diamètre intérieur 2 à 3 mm | 2 € |
| Bobine | Impression résine, 92 mm de diamètre, environ 53 g | à chiffrer |
| Boîtier | Corps, capot arrière et couvercle avant imprimés | à chiffrer |
| Divers | Visserie, connecteurs, mousse | 10 € |
| | **Total par bloc** | **environ 150 à 200 €** |

Il faut un switch réseau PoE pour alimenter les blocs. Le moteur est donné pour 16 V ; voir
« Ce qui reste à vérifier » pour la vitesse en 12 V.

## Câblage

| Carte ESP32 | Vers |
|---|---|
| Broches 4, 5, 13 | les trois entrées de la carte de commande du moteur |
| Broche 14 | activation de la carte de commande |
| Broches 15, 35, 2, 16 | encodeur (horloge, données entrantes, données sortantes, sélection) |
| Broche 33 | boucle d'arrêt d'urgence, ou pont vers le 3,3 V si elle n'est pas câblée |
| Broche 36 | capteur d'origine, facultatif |

## Accroche du bloc

Le bloc se fixe par un **spigot de 16 mm à filetage M10**, pris dans une pince de type Super
Clamp serrée sur un tube ou une perche. Deux emplacements sont prévus ; on n'en utilise
qu'un à la fois.

| Emplacement | Usage | Comportement |
|---|---|---|
| **Dessus**, à l'aplomb du moteur | sous un tube horizontal | le bloc pend droit, l'œillet vers le bas ; il tourne autour du spigot pour orienter la sortie du fil |
| **Côté**, à la hauteur de l'axe du moteur, à l'opposé de la sortie du fil | contre une perche verticale ou un mur | le bloc est tenu en porte-à-faux ; c'est le serrage de la pince qui l'empêche de pivoter |

- Chaque filetage se visse dans un **écrou M10 prisonnier**, glissé par l'avant dans un
  bossage du corps. Les écrous ne peuvent ni tourner ni sortir une fois le couvercle fermé.
- Monter les deux écrous dès l'assemblage : on change ensuite d'emplacement sans rouvrir.
- L'emplacement resté libre reçoit un **anneau à vis M10**, où passe l'**élingue de
  sécurité** reliée au support, comme pour tout appareil accroché en hauteur. Le boîtier
  n'a donc plus aucune patte qui dépasse. Filetage de l'anneau : 20 mm au plus.
- Le câble réseau sort par l'autre côté du capot, pour ne gêner aucune des deux pinces.

Le filetage du spigot fait 20 mm : il traverse tout l'écrou et s'arrête à 8,5 mm de la
bobine en rotation, sur le dessus comme sur le côté. Ne pas monter un spigot au filetage
plus long.

**Accroche sur le côté.** Avec le spigot à l'horizontale, vérifier après serrage que
l'œillet regarde bien à la verticale : un bloc incliné fait frotter le fil sur le bord de
l'œillet. Serrer la pince fermement, le bloc ne devant pas pouvoir tourner sur lui-même.

## Fixation du moteur

D'après le plan coté du GL35 avec encodeur et la réponse de CubeMars :

| Côté | Sur le plan | Sur les pièces |
|---|---|---|
| Arrière, fixe (encodeur, sortie des fils) | 4 × M3 sur un cercle de 24 mm, profondeur 5 mm | vissé à plat sur la cloison par 4 vis M3 × 6, avec un passage pour les fils |
| Avant, face tournante | 4 × M3 sur un cercle de 20 mm, **profondeur 2,5 mm seulement**, alésage central de 6 mm | la bobine s'y visse par 4 vis M3 × 5 ; un téton la centre dans l'alésage |

**Attention aux vis de la bobine.** Le filetage ne fait que 2,5 mm. Le fond de la bobine
fait 3 mm : une vis M3 × 5 s'engage de 2 mm. Une vis plus longue bute dans le moteur et
peut l'abîmer ; CubeMars le signale aussi.

## Ce qui reste à vérifier

Confirmé par CubeMars : 7 paires de pôles, 3,6 ohms entre phases, 0,115 N·m par ampère,
990 tr/min à vide sous 12 V, encodeur AS5048A en SPI (14 bits, 3,3 ou 5 V), face du rotor
tournante et côté stator fixe. Ces valeurs sont dans le firmware.

Reste à vérifier, moteur en main :

1. **Le brochage de l'encodeur.** CubeMars renvoie à son schéma officiel et prévient de ne
   pas se fier aux couleurs des fils. Je n'ai pas ce schéma.
2. **La profondeur de l'alésage de 6 mm** sur la face tournante. Avec l'encodeur, l'arbre
   n'est plus creux de part en part. Le téton de centrage de la bobine y entre de 1,2 mm ;
   s'il bute, le limer ou régler `SPIGOT_H` dans `cad/treuil.py`.
3. **La position exacte de la sortie des fils** à l'arrière, pour le passage dans la cloison.
   Le fichier 3D reçu de CubeMars est chiffré et illisible : je n'ai travaillé que sur le
   plan en PDF.
4. **L'inertie du rotor**, qui reste une estimation dans le firmware.

**Vitesse en 12 V.** Le moteur plafonne à 990 tr/min à vide en 12 V, pour 717 nécessaires
à 3 m/s. La marge est faible : prévoir une alimentation 16 V si les 3 m/s comptent, ou
accepter environ 2,5 m/s en 12 V.

## Fabrication du prototype

Quatre pièces à imprimer. Chacune se pose à plat sur le plateau et s'imprime sans supports.

| Pièce | Fichiers | Taille | Matière | Sens d'impression |
|---|---|---|---|---|
| Corps | `cad/export/corps.stl` / `.step` | 112 × 123 × 43 mm, 104 cm³ | nylon PA12 (MJF) ou PETG | cloison sur le plateau |
| Capot arrière | `cad/export/capot_arriere.stl` / `.step` | 112 × 123 × 20,5 mm, 58 cm³ | nylon PA12 (MJF) ou PETG | fond sur le plateau |
| Couvercle avant | `cad/export/couvercle_avant.stl` / `.step` | 112 × 123 × 2,5 mm, 34 cm³ | nylon PA12 (MJF) ou PETG | à plat |
| Bobine | `cad/export/bobine.stl` / `.step` | Ø 92 × 32,7 mm, 44 cm³ | **résine (SLA)** | fond de la cloche sur le plateau |

`cad/export/planches.pdf` donne pour chaque pièce trois vues, une perspective et le tableau
de ses cotes. Ce sont des planches de contrôle, sans lignes de cote dessinées : pour
l'impression 3D, les fichiers STL et STEP suffisent et font foi.

Toutes les pièces tiennent sur un plateau de 180 × 180 mm. Chez un imprimeur en ligne
(JLC3DP par exemple), envoyer les fichiers STEP.

### Visserie

| Usage | Vis | Quantité |
|---|---|---|
| Moteur sur la cloison (par l'arrière) | M3 × 6, tête cylindrique | 4 |
| Bobine sur la face tournante du moteur | M3 × 5, tête cylindrique basse | 4 |
| Couvercle avant | M3 × 10 | 4 |
| Capot arrière | M3 × 30 | 4 |
| Accroche | spigot 16 mm à filetage M10 de 20 mm, pince Super Clamp | 1 de chaque |
| Accroche | écrou M10 (17 sur plats, 8 d'épaisseur) | 2 |
| Sécurité | anneau à vis M10 (filetage de 20 mm au plus) et élingue fine avec mousqueton | 1 |

Les vis du couvercle et du capot se vissent directement dans le plastique des colonnes
d'angle (avant-trous de 2,6 mm) : elles y forment leur filet. Cela tient une dizaine de
démontages ; au-delà, passer à des inserts filetés.

**Longueur des vis du moteur.** À l'arrière, le filetage fait 5 mm et la cloison 3 mm : une
vis M3 × 6 s'engage de 3 mm. Côté bobine, voir l'avertissement plus haut : M3 × 5, pas plus.

### Montage

1. Sertir ou coller l'œillet céramique dans le trou du fond du corps. Glisser les deux écrous
   M10 dans leurs logements par l'avant, puis visser le spigot à l'emplacement voulu.
2. Poser le moteur dans le corps, fils vers la cloison, et le visser par l'arrière (4 × M3 × 6).
   Passer ses fils par les deux trous prévus.
3. Nouer le fil dans le trou d'ancrage de la bobine, l'enrouler, puis poser la bobine sur
   la face du moteur : son téton la centre. Visser (4 × M3 × 5).
4. Passer le fil dans l'œillet, visser le couvercle avant.
5. Coller les cartes au dos de la cloison (mousse adhésive double face), câbler, passer le
   câble réseau par l'encoche latérale du capot, visser le capot arrière.

### Ce qui reste approximatif

- **Les cartes électroniques** n'ont pas de support dédié : je n'ai pas leurs cotes
  vérifiées. Le capot offre 18 mm de profondeur, prévus pour la prise réseau de la carte.
  À contrôler sur les cartes achetées avant de lancer l'impression du capot.
- **L'œillet** : le logement fait 6,2 mm, pour un œillet de 6 mm de diamètre extérieur.
  À ajuster à l'œillet acheté (`EYELET_OD` dans `cad/treuil.py`).
- **Les jeux** (0,2 mm) conviennent au nylon MJF et à la résine. En dépôt de fil, les trous
  sortent souvent plus petits : repasser un foret de 3,5 mm dans les trous de passage.

```
cd cad && python3 treuil.py && python3 planches.py     # régénère pièces et planches
cd firmware && ./test/sim/run.sh                       # simulation du firmware sur PC
```

## À confirmer sur le prototype

1. La vitesse réellement atteinte en 12 V.
2. Le réglage de l'asservissement (`CTRL_OMEGA`) : plus ferme, il suit mieux mais s'entend.
3. La justesse des tensions en grammes, à comparer avec une balance.
4. La tenue du fil sur la bobine en résine et dans l'œillet.
5. Le bruit à pleine vitesse.
