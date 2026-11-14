# Lévitation — bloc treuil micro

Un boîtier fermé de **112 × 123 × 70 mm**, accroché par un spigot de 16 mm pour faire voler des objets de quelques grammes
(bague, pliage de papier, carton) au bout d'un fil très fin. Le fil sort par un seul œillet.

**État : conception v1.0, pièces du prototype dessinées pour l'impression 3D, rien n'est encore construit.** Le firmware **compile pour
la carte Olimex ESP32-POE** et passe 36 vérifications dans une simulation sur PC qui reproduit
le moteur, la bobine et un objet suspendu. Il n'a pas encore tourné sur une vraie carte ni
sur un moteur.

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
| Arrêt de groupe | automatique | Un bloc en défaut prévient les autres, qui s'arrêtent en douceur sans attendre le logiciel |

**Arrêt de groupe.** Les blocs sont tous identiques et aucun ne commande les autres. Mais dès
qu'un bloc passe en défaut (fil accroché, arrêt d'urgence), il diffuse sur le réseau le
message `/levi/all/groupstop` avec son numéro et son défaut, et le répète 5 fois par seconde
tant qu'il y reste. Les autres blocs s'arrêtent en douceur, tiennent leur objet et refusent
`goto` et `pos` (avertissement 6) jusqu'à un `/levi/all/reset`. Le déplacement manuel `jog`
reste permis pour dégager un fil. Tant que le bloc fautif n'est pas sorti de son défaut, il
continue de prévenir et le groupe reste à l'arrêt. Le dernier argument de `/levi/N/state`
donne le numéro du bloc qui a déclenché l'arrêt, ou 0.

**Régler un fil inconnu.** Faire le test de rupture sur un bout de fil, puis régler la
tension maximale au tiers de la valeur obtenue. Le test coûte quelques centimètres de fil.

**Précision des grammes.** Le courant est estimé, pas mesuré : sans capteur de courant, les
valeurs en grammes sont justes à quelques grammes près, et les frottements du moteur
s'ajoutent. C'est suffisant pour protéger le fil avec une marge de trois ; une carte de
commande avec mesure de courant ferait mieux.

Les autres commandes (`arm`, `goto`, `pos`, `jog`, `stop`, `zero`, `limits`, `reset`) sont
celles des autres versions : voir [`../levitation/README.md`](../levitation/README.md),
section 6. Le retour d'état a deux valeurs de plus : `/levi/N/state` position, vitesse, état,
origine connue, défaut, tension estimée (g), bloc à l'origine d'un arrêt de groupe. L'état 9
est le test de rupture.

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
| Boîtier | 112 × 123 × 70 mm, moteur et électronique compris |

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

Prix en ordres de grandeur, non vérifiés sauf mention contraire.

| Fonction | Composant | Taille | Prix indicatif |
|---|---|---|---|
| Moteur | CubeMars GL35 KV100 avec encodeur | Ø 41,8 × 33,5 mm | 73 $ pièce par 4 (devis), 79,99 $ à l'unité |
| Commande du moteur | SimpleFOC Mini (DRV8313), 8 à 30 V, 2,5 A par phase, sans mesure de courant | 26 × 21 mm | 15 € |
| Carte | Olimex ESP32-POE (Ethernet) | 80 × 28 mm | 25 € |
| Alimentation | Module séparateur PoE 802.3af avec sortie 12 V, 1 A (par exemple Banana Pi BPI-7604) | 38 × 38 × 18 mm | 10 à 15 € |
| Alimentation | Convertisseur 12 V vers 5 V, 1 A | environ 22 × 17 mm | 3 € |
| Sortie du fil | Bague céramique, diamètre extérieur 6 mm, trou de 2 à 3 mm | | 2 € |
| Bobine | Impression résine, 92 mm de diamètre, environ 53 g | | à chiffrer |
| Boîtier | Corps, capot arrière et couvercle avant imprimés | | à chiffrer |
| Accroche | Spigot 16 mm M10, 2 écrous M10, pince Super Clamp, anneau à vis M10, élingue | | 40 à 50 € |
| Divers | Visserie M3, câbles, mousse adhésive | | 10 € |
| | **Total par bloc, hors impression** | | **environ 200 à 230 €** |

Pour l'ensemble : un **switch réseau PoE à la norme 802.3af**, au moins 5 ports pour quatre
blocs et l'ordinateur (40 à 60 € en 8 ports), et des câbles réseau de catégorie 5e ou 6.

## Alimentation

Un seul câble réseau arrive à chaque bloc. Il apporte le courant (PoE) et les commandes.

```
 switch PoE ── câble réseau ── module séparateur PoE
                                 ├─ 12 V ──> SimpleFOC Mini ──> moteur
                                 ├─ 12 V ──> convertisseur 5 V ──> carte ESP32
                                 └─ réseau ─> carte ESP32 (court câble interne)
```

- Le PoE fournit environ 12 W par bloc. Le moteur en consomme moins d'un pour tenir 50 g,
  l'électronique environ 1,5 W.
- Prendre un séparateur **actif, norme 802.3af**. Les modèles « passifs », moins chers, ne
  suivent pas la norme et peuvent endommager une carte.
- La carte Olimex sait s'alimenter seule par le câble réseau, mais seulement en 5 V : cette
  fonction ne sert pas ici, puisque le moteur a besoin de 12 V. Une carte ESP32 Ethernet plus
  petite (WT32-ETH01, 60 × 25 mm) conviendrait aussi, au prix d'une adaptation des broches
  dans le firmware.

**Pour les premiers essais sur table**, le plus simple est de se passer du PoE : un bloc
secteur 12 V, 2 A sur la carte de commande et le convertisseur, et un câble réseau ordinaire.

**Ce qui est vérifié et ce qui ne l'est pas.** Les tailles des cartes viennent de leurs
fiches et tiennent sans se toucher dans le capot, profond de 22 mm. Je n'ai pas vérifié
la hauteur réelle des prises réseau, la place des connecteurs et des câbles internes, ni le
fait que le module Banana Pi soit isolé. Le capot est donc à imprimer une fois les cartes
en main. Pour 3 m/s, le passage en 16 V demandera une autre alimentation.

## Câblage

| Carte ESP32 (Olimex ESP32-POE) | Vers |
|---|---|
| Broches 4, 5, 13 | `IN1`, `IN2`, `IN3` de la carte de commande du moteur |
| Broche 14 | `EN` de la carte de commande |
| Broche 15 | horloge de l'encodeur (SCK / CLK) |
| Broche 36 | données venant de l'encodeur (MISO / DO) |
| Broche 2 | données vers l'encodeur (MOSI / DI) |
| Broche 16 | sélection de l'encodeur (CS / CSn) |
| `3.3V` | alimentation de l'encodeur. **Pas le 5 V** : ses signaux reviendraient en 5 V sur la carte |
| `GND` | masse de l'encodeur, de la carte de commande et du 12 V, toutes reliées |
| `+5V` | sortie du convertisseur 5 V |
| Broche 33 | pont vers `3.3V`, tant qu'aucune boucle d'arrêt d'urgence n'est câblée. Sans ce pont, le bloc reste en défaut |

Le 12 V va sur la carte de commande du moteur et sur l'entrée du convertisseur 5 V. Les
trois fils de phase du moteur vont sur les trois sorties de la carte de commande, dans
n'importe quel ordre.

### Trois précautions

1. **Ne jamais brancher la carte Olimex directement sur un port PoE du switch tant qu'elle
   est aussi alimentée autrement** (câble USB ou convertisseur 5 V). Cette carte sait prendre
   son courant sur le câble réseau, et Olimex prévient que la version non isolée ne doit pas
   être reliée en même temps au PoE et à un ordinateur par USB. Pour les essais sur table,
   utiliser un port non PoE (ports 5 à 8 du TL-SG1008P). En service, le séparateur PoE est
   entre le switch et la carte : la sortie réseau du séparateur ne porte plus de courant.
2. **Vérifier le 12 V au multimètre**, polarité comprise, avant de le relier aux cartes.
3. **Régler l'adresse réseau de l'ordinateur** sur `192.168.10.2`, masque `255.255.255.0`.
   Les blocs sont en `192.168.10.11` à `.14` et ne répondent pas sur un autre réseau.

### Soudure

Les cartes sont livrées avec leurs barrettes de broches à part. Il faut les souder sur la
carte Olimex (deux rangées de 10), sur la carte de commande et sur le convertisseur 5 V.
Les fils du moteur et de l'encodeur peuvent aussi demander une soudure ou un connecteur,
selon la façon dont le moteur est livré.

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
| Capot arrière | `cad/export/capot_arriere.stl` / `.step` | 112 × 123 × 24,5 mm, 63 cm³ | nylon PA12 (MJF) ou PETG | fond sur le plateau |
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

1. Enfiler la bague céramique par l'intérieur dans le trou du fond du corps, collerette en
   appui sur le fond, et la coller. Glisser les deux écrous
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
  vérifiées. Le capot offre 22 mm de profondeur, pour le module PoE et les prises réseau.
  À contrôler sur les cartes achetées avant de lancer l'impression du capot.
- **La bague céramique** : le logement fait 6,0 mm, pour une bague à collerette dont le
  corps mesure 5,8 mm (modèles vendus comme « OD6 »). Elle s'enfile par l'intérieur, la
  collerette en appui sur le fond, et dépasse sous le boîtier. À ajuster à la bague reçue
  (`EYELET_OD` dans `cad/treuil.py`).
- **Les jeux** (0,2 mm) conviennent au nylon MJF et à la résine. En dépôt de fil, les trous
  sortent souvent plus petits : repasser un foret de 3,5 mm dans les trous de passage.

```
cd cad && python3 treuil.py && python3 planches.py     # régénère pièces et planches
cd firmware && ./test/sim/run.sh                       # simulation du firmware sur PC
cd firmware && pio run                                 # compilation pour la carte
cd firmware && pio run -t upload                       # envoi dans la carte, par USB
```

### Envoyer le firmware sans rien installer

`firmware/binaires/` contient un fichier prêt à l'emploi par bloc (`treuil-micro-bloc1.bin`
à `bloc4.bin`), chacun avec son numéro et son adresse réseau.

1. Relier la carte à l'ordinateur par USB, **sans câble réseau PoE branché**.
2. Ouvrir l'outil en ligne d'Espressif, [esptool-js](https://espressif.github.io/esptool-js/),
   dans Chrome ou Edge.
3. Cliquer « Connect », choisir le port de la carte, puis envoyer le fichier à l'adresse
   `0x0`.

Ces fichiers contiennent les réglages actuels de `config.h`. Tout changement de réglage
(sens de rotation, raideur, vitesses) demande de recompiler : c'est là que PlatformIO
devient nécessaire, ou bien je régénère les fichiers.

Je n'ai vérifié ni cette procédure ni ces fichiers sur une vraie carte.

### Versions utilisées pour la compilation

Plateforme PlatformIO `espressif32` 6.9.0 et bibliothèque SimpleFOC 2.3.3. La version 2.3.4
de SimpleFOC ne compile pas avec cette plateforme : ne pas la mettre à jour sans changer
les deux.

## À confirmer sur le prototype

1. La vitesse réellement atteinte en 12 V.
2. Le réglage de l'asservissement (`CTRL_OMEGA`) : plus ferme, il suit mieux mais s'entend.
3. La justesse des tensions en grammes, à comparer avec une balance.
4. La tenue du fil sur la bobine en résine et dans l'œillet.
5. Le bruit à pleine vitesse.
