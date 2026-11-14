# Treuil micro — liste d'achat

Quantités pour **un bloc prototype**. Pour quatre blocs, multiplier les lignes « par bloc »
par quatre ; le switch, l'alimentation d'essai et les câbles de programmation ne s'achètent
qu'une fois.

Les liens ont été relevés par recherche le 12 novembre 2026. Je n'ai pas pu ouvrir les pages
des boutiques : **prix, stock et frais de port sont à vérifier** au moment de commander.

## Moteur

| Article | Qté | Où | Prix relevé |
|---|---|---|---|
| CubeMars GL35 KV100 **avec encodeur** | 1 | [CubeMars](https://www.cubemars.com/product/gl35-kv100-gimbal-motor.html) (Chine, virement ou boutique en ligne) · [OpenELAB](https://openelab.io/products/cubemars-gl35-kv100-bldc-motor?variant=44696317264070) (Europe) · [RobotShop](https://www.robotshop.com/products/cubemars-gl35-kv100-w-encoder) | 79,99 $ à l'unité chez CubeMars, 73 $ par 4 |

Choisir la variante avec encodeur. Depuis la Chine, compter la TVA et les frais de douane.

## Électronique (par bloc)

| Article | Qté | Où | Prix relevé |
|---|---|---|---|
| Carte de commande SimpleFOC Mini (DRV8313, 8 à 30 V) | 1 | [Elecrow](https://www.elecrow.com/simple-foc-mini-v1-0-drv8313-dc-brushless-motor-driver-board-foc-control-driver-svpwm-control-dc-8-30v-module.html) · [version DFRobot DRI0058](https://wiki.dfrobot.com/dri0058/) · [copies génériques sur Fruugo](https://www.fruugo.fr/8-30v-drv8313-simple-foc-mini-brushless-motor-driver-board/p-419484362-884055159) | environ 10 à 15 € |
| Carte Olimex ESP32-POE | 1 | [Olimex](https://olimex.com/Products/IoT/ESP32/ESP32-POE) (Bulgarie) · [TME](https://www.tme.com/th/en/details/esp32-poe/development-kits-for-data-transmission/olimex/) | environ 25 € |
| Convertisseur 12 V vers 5 V, 1 A : Pololu D24V10F5 | 1 | [Pololu](https://www.pololu.com/product/2831) · [MCHobby](https://shop.mchobby.be/en/regulator/554-regul-5v-500ma-step-updown-s7v7f5-3232100005549-pololu.html) (Belgique) · [liste des distributeurs](https://www.pololu.com/product/2831/distributors) | 12,95 $ |
| Séparateur PoE 802.3af, sortie 12 V | 1 | Prototype : un boîtier externe, par exemple [TP-Link POE10R](https://www.omadanetworks.com/au/business-networking/omada-accessory-poe-adapter/poe10r/) (sortie 5, 9 ou 12 V) ou [Adafruit 3238](https://www.adafruit.com/products/3238). Version intégrée : module nu [Banana Pi BPI-7604](https://wiki.banana-pi.org/BPI-7604_IEEE_802.3af_PoE_Splitter_module), pour lequel je n'ai pas trouvé de revendeur européen | 10 à 20 € |
| Fils de câblage à connecteurs (type Dupont), femelle-femelle, 20 cm | 1 lot | boutique d'électronique | 5 € |

Attention à la version de la carte de commande : la v1 utilise un DRV8313, la v2 un DRV8316
avec mesure de courant. Le firmware est écrit pour la v1 ; la v2 conviendrait mais demande
une adaptation.

## Pour l'ensemble (une seule fois)

| Article | Qté | Où | Prix relevé |
|---|---|---|---|
| Switch PoE : TP-Link TL-SG1008P (8 ports, dont **4 en PoE**) | 1 | [LDLC](https://www.ldlc.com/fr-be/fiche/PB00266981.html) · [Fnac](https://www.fnac.com/Commutateur-Reseau-de-Bureau-TP-Link-TL-SG1008P-8-ports-Gigabit-avec-4-ports-PoE-Gris/a15732133/w-4) · [Grosbill](https://www.grosbill.com/index.php/tp-link-8-ports-10-100-1000mbps-tl-sg1008p-4-poe-46031) | 43 à 47 € |
| Câbles réseau cat. 5e ou 6, à la longueur voulue | 1 par bloc + 1 | magasin d'informatique | |
| Bloc secteur 12 V, 2 A, pour les essais sur table | 1 | magasin d'électronique | 10 € |
| Câble USB pour programmer la carte ESP32 : micro-USB ou USB-C selon la révision, à vérifier sur la carte reçue | 1 | | |

Le TL-SG1008P n'a que quatre ports PoE : il suffit pour quatre blocs, pas pour un cinquième.

## Accroche (par bloc)

| Article | Qté | Où | Prix relevé |
|---|---|---|---|
| Spigot 16 mm à filetage M10 avec écrou papillon : Stairville Mini TV Pin 264M10 | 1 | [Thomann](https://www.thomann.de/be/stairville_mini_tv_pin_16_mm_m10_264m10.htm) | |
| Pince Manfrotto 035 Super Clamp | 1 | Thomann, à chercher par son nom ([fiche de référence](https://www.tsllighting.com/equipment/rigging/accessories/manfrotto-035-super-clamp/)) | environ 30 € |
| Écrou M10 standard (17 sur plats, 8 d'épaisseur) | 2 | quincaillerie | |
| Anneau à vis M10, filetage de 20 mm au plus | 1 | quincaillerie | |
| Élingue de sécurité fine avec mousqueton | 1 | Thomann ou magasin de matériel scénique | |

Vérifier que le filetage du spigot ne dépasse pas 20 mm.

## Visserie (par bloc)

| Article | Qté | Usage |
|---|---|---|
| Vis M3 × 6, tête cylindrique | 4 | moteur sur la cloison |
| Vis M3 × 5, tête cylindrique basse | 4 | bobine sur le moteur. **Pas plus longues** |
| Vis M3 × 10 | 4 | couvercle avant |
| Vis M3 × 30 | 4 | capot arrière |

Un coffret d'assortiment de vis M3 inox couvre toutes ces longueurs.

## Fil et sortie du fil (par bloc)

| Article | Qté | Où |
|---|---|---|
| Bague céramique à collerette, corps de 6 mm (« OD6 »), trou de 3 mm de préférence | 1 | assortiment d'anneaux de canne à pêche, ou fabricant de guide-fils textiles ([MOBAC](https://www.usinenouvelle.com/expo/illets-ceramique-p98019.html), [Texera](https://www.expometals.net/en-gb/product-detail-texera-srl/ceramic-wire-guides)). Pas de référence exacte trouvée |
| Mousse adhésive double face | 1 rouleau | pour coller les cartes |
| Colle cyanoacrylate | 1 tube | pour la bague céramique |

## Impression 3D (par bloc)

| Pièce | Fichier | Matière |
|---|---|---|
| Corps | `cad/export/corps.step` | nylon PA12 (MJF) ou PETG |
| Capot arrière | `cad/export/capot_arriere.step` | nylon PA12 (MJF) ou PETG |
| Couvercle avant | `cad/export/couvercle_avant.step` | nylon PA12 (MJF) ou PETG |
| Bobine | `cad/export/bobine.step` | résine (SLA) |

Service en ligne : [JLC3DP](https://jlc3dp.com/capabilities/3d-printing-service). Je n'ai pas de devis.

## Outillage et petit matériel (une seule fois)

| Article | Pourquoi |
|---|---|
| Kit de soudure : fer, étain fin, support, tresse à dessouder | les barrettes de broches des trois cartes arrivent non soudées |
| Multimètre basique | vérifier le 12 V et sa polarité, les continuités |
| Bornes à levier (type Wago 221), 3 entrées | répartir le 12 V et les masses sans soudure |
| Jeu de clés Allen (2 et 2,5 mm) | vis M3 |
| Rondelles M3 | sous les têtes de vis de la bobine en résine |
| Petites perles souples | butée d'origine sur le fil, plus grosse que le trou de la bague |
| Gaine thermorétractable, colliers fins | isoler et tenir les fils |
| Ordinateur avec VS Code et PlatformIO (gratuits) | envoyer le firmware dans la carte |

Vis de la bobine : préférer des vis M3 × 5 à **tête bombée**, plus basses. Il n'y a que
3,6 mm entre le fond de la bobine et le couvercle avant.

## Dans quel ordre commander

1. **D'abord** : le moteur, la carte de commande, la carte ESP32, le convertisseur 5 V, le
   bloc secteur 12 V, la bague céramique. De quoi faire tourner le moteur sur table et
   mesurer les pièces réelles.
2. **Ensuite**, une fois le moteur et la bague mesurés : l'impression du corps, de la bobine
   et du couvercle avant, plus la visserie et l'accroche.
3. **En dernier**, cartes en main : le capot arrière, puis le switch et le séparateur PoE.
