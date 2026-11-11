# Lévitation — bloc treuil micro

Un boîtier fermé de **112 × 135 × 50 mm** pour faire voler des objets de quelques grammes
(bague, pliage de papier, carton) au bout d'un fil très fin. Le fil sort par un seul œillet.

**État : conception v0.1, rien n'est encore construit.** Le firmware passe 26 vérifications en
simulation sur PC ; il n'a pas été compilé pour la carte ni essayé sur un moteur.

- `simulation.html` : vue 3D animée (boîtier, objet, salle).
- `cad/` : maquette paramétrique, boîtier, couvercles et bobine.
- `firmware/` : le firmware réglé pour cette mécanique.

Le protocole OSC est celui des autres versions : voir
[`../levitation/README.md`](../levitation/README.md), section 6.

## Pourquoi cette version est si simple

Avec des objets de quelques grammes, presque tout ce qui compliquait les grands blocs disparaît :

| Grands blocs | Bloc micro |
|---|---|
| Servo 400 W et réducteur | petit moteur pas-à-pas plat, en prise directe |
| Frein à manque de courant | inutile : moteur éteint, il retient encore quelques dizaines de grammes |
| Guide-fil mobile ou poulie éloignée | inutile : 40 spires d'un fil de 0,05 mm tiennent sur un seul rang dans une gorge de 2 mm |
| Alimentation 48 V | **un seul câble réseau**, qui apporte le courant et les commandes (PoE) |

Le fil est si fin que l'empiler ne change presque pas le diamètre de la bobine : un rang
entier n'ajoute que 0,05 mm sur un rayon de 40 mm. C'est ce qui permet une bobine étroite et
un œillet de sortie placé juste en dessous, à 7 cm.

## Ce que fait le bloc

| | Valeur visée |
|---|---|
| Objets | de 1 à 50 g |
| Course | 10 m de fil |
| Fil par tour | 251,5 mm |
| Résolution | 0,08 mm |
| Vitesse en montée | jusqu'à 3 m/s (717 tr/min), **à confirmer sur le prototype** |
| Vitesse en descente | limitée à 1,5 m/s, réglable par objet |
| Accélération | 4 m/s² |
| Boîtier | 112 × 135 × 50 mm, moteur et électronique compris |

## Ce que le fil cheveu impose

- **Il casse avant de prévenir.** Le courant du moteur se règle pour qu'il cale avant
  d'atteindre la charge de rupture du fil. Si l'objet s'accroche quelque part, le moteur
  s'arrête au lieu de casser le fil. Ce réglage demande la charge de rupture du fil.
- **Un objet léger ne descend pas plus vite que l'air ne le laisse tomber.** Une bague suit
  sans problème ; une feuille de papier plane. Si le treuil déroule plus vite que l'objet ne
  descend, le fil se détend et s'emmêle. D'où la vitesse de descente séparée
  (`VMAX_DOWN_MM_S`), à régler pour chaque objet.
- **Aucun capteur ne peut sentir un fil détendu** avec si peu de poids. La seule protection
  est de ne pas dérouler trop vite.
- **Tout ce que le fil touche doit être lisse.** La bobine est à imprimer en résine (procédé
  SLA) ou à tourner dans du plastique plein, pas en nylon fritté ni en dépôt de fil : leur
  grain accroche un fil aussi fin. La sortie se fait par un œillet céramique de canne à pêche.
- **Aucune fente.** Un fil de 0,05 mm se glisse dans le moindre jeu. La bobine est d'une
  seule pièce et tourne dans une chambre fermée, séparée de l'électronique.
- **La précision.** Le treuil place le fil à 0,08 mm près, mais un fil de nylon aussi fin
  s'allonge de plusieurs millimètres par mètre selon le poids. Un même objet revient au même
  endroit ; l'étalonnage se fait avec l'objet accroché.

## Composants

Références et prix à confirmer ; ce sont des ordres de grandeur.

| Fonction | Composant | Prix indicatif |
|---|---|---|
| Moteur | Pas-à-pas NEMA 17 plat (20 mm d'épaisseur, environ 0,15 N·m) | 15 € |
| Driver | TMC2209, mode silencieux | 8 € |
| Carte | Olimex ESP32-POE (Ethernet) | 25 € |
| Alimentation | Séparateur PoE 12 V (le courant arrive par le câble réseau) et petit convertisseur 5 V | 15 € |
| Moyeu | Moyeu à bride, alésage 5 mm | 3 € |
| Sortie du fil | Œillet céramique, diamètre intérieur 2 à 3 mm | 2 € |
| Bobine | Impression résine, 92 mm de diamètre, 6 mm d'épaisseur, environ 30 g | à chiffrer |
| Boîtier | Corps et deux couvercles imprimés (nylon ou résine) | à chiffrer |
| Divers | Visserie M3, connecteurs, mousse | 10 € |
| | **Total par bloc** | **environ 100 à 130 €** |

Il faut un switch réseau PoE pour alimenter les blocs.

## Câblage

| Carte | Vers |
|---|---|
| Broche 4 (pas), 5 (direction), 13 (activation) | entrées STEP, DIR, EN du TMC2209, en direct (3,3 V) |
| Broche 33 (arrêt d'urgence) | pont vers le 3,3 V si aucune boucle d'arrêt n'est câblée |
| Broche 34 (alarme) | résistance de tirage vers le 3,3 V (entrée inutilisée ici) |
| Broche 35 (origine) | capteur d'origine, facultatif (voir ci-dessous) |
| Broche 14 (frein) | non câblée |

**Origine.** Le plus simple : monter l'objet à la main avec la commande `jog` jusqu'à un
repère, puis envoyer `/levi/N/zero`. La position est ensuite mémorisée à chaque arrêt et
retrouvée à la mise sous tension. Moteur éteint, il se cale sur un cran : l'erreur possible
est de 0,6 mm.

## Bruit

Le driver choisi rend un pas-à-pas pratiquement inaudible à basse vitesse, ce qui correspond
à la plupart des mouvements de lévitation. À 3 m/s, le moteur tourne à 717 tr/min et émettra
un léger sifflement. Le boîtier fermé, le moteur monté sur une cloison et une mousse collée à
l'intérieur le réduisent. Je n'ai pas de mesure : c'est à écouter sur le prototype.

## Fabrication

```
cd cad && python3 treuil.py      # régénère toutes les pièces
```

| Fichier | Usage |
|---|---|
| `cad/export/bobine.stl` / `.step` | bobine, à imprimer en résine |
| `cad/export/boitier.step` | corps du boîtier, avec la cloison porte-moteur et les pattes d'accroche |
| `cad/export/couvercle_avant.step`, `couvercle_arriere.step` | les deux couvercles |
| `cad/export/treuil.step` | l'assemblage complet |

Les perçages du moteur suivent le standard NEMA 17 et peuvent être repris tels quels. Il
reste à dessiner avant commande : les vis de fermeture des couvercles, les perçages du moyeu
(ils dépendent du modèle acheté) et les supports des cartes.

## À confirmer sur le prototype

1. La vitesse réellement atteinte en 12 V. Si 3 m/s ne passe pas, un séparateur PoE 24 V
   règle la question.
2. La tenue du fil sur la bobine en résine et dans l'œillet.
3. Le réglage du courant pour que le moteur cale avant la rupture du fil.
4. Le bruit à pleine vitesse.
