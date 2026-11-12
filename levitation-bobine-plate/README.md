# Lévitation — bloc treuil à bobine plate

Troisième variante du bloc, et la plus simple à monter : un servo, un réducteur planétaire, une
bobine plate de 25 cm et une poulie de sortie fixe. **Le fil sort toujours au même point**, ce
qui est indispensable pour faire voler un objet sur plusieurs fils.

**État : conception v0.1, rien n'est encore construit ni commandé.** Le firmware passe ses
vérifications en simulation sur PC ; il compile pour la carte Olimex ESP32-POE, mais n'a pas été essayé sur un
moteur. Les pièces dessinées ne sont pas encore prêtes à être envoyées en fabrication (voir
« Avant de commander »).

- `simulation.html` : vue 3D animée du mécanisme.
- `cad/` : maquette paramétrique et fichiers des pièces.
- `firmware/` : le firmware réglé pour cette mécanique (guide-fil désactivé).

Le câblage, le protocole OSC et les consignes de sécurité sont ceux de la première version :
voir [`../levitation/README.md`](../levitation/README.md).

## Principe

```
 servo avec frein ── réducteur planétaire 10:1 ── platine ── BOBINE Ø 250
                                                                │ fil, presque droit (1,3° au plus)
        profilé aluminium 20 × 40 ──────────────────────── poulie de sortie ── vers l'objet
```

- La bobine enroule **788,5 mm de fil par tour**. Dix mètres tiennent en 13 tours ; avec les
  tours de sécurité, la gorge compte 16 spires et mesure 20 mm de large.
- Une seule couche, dans une gorge en hélice imprimée : un tour vaut toujours la même
  longueur, et le fil se range seul.
- La poulie est à 455 mm de la bobine. Sur cette distance, le fil ne dévie que de 1,3° : il
  n'y a besoin d'aucun guide-fil mobile.
- La bobine est montée directement sur l'arbre de sortie du réducteur, qui est prévu pour
  porter une charge sur le côté. Pas de second palier.

## Ce que fait le bloc

| | Valeur |
|---|---|
| Charge en continu | environ 9,8 kg |
| Charge en pointe | environ 29 kg, à vérifier contre le couple admis par le réducteur |
| Vitesse | 3 m/s (le moteur permettrait 3,9 m/s) |
| Résolution | 0,04 mm |
| Jeu du réducteur ramené au fil | 0,1 mm pour 3 minutes d'arc, rattrapé par le poids de l'objet |
| Bobine | 250 tr/min à 3 m/s ; moteur à 2300 tr/min |
| Encombrement | bloc moteur + bobine 320 × 270 × 330 mm ; 610 mm de long avec le bras de poulie |

Calcul : 1,27 N·m × 10 × 0,95 (rendement supposé) = 12,1 N·m sur un rayon de 125,5 mm, soit
96 N. À 3000 tr/min moteur, la bobine fait 5 tours par seconde × 788,5 mm = 3,9 m/s.

## Composants

| Fonction | Composant | Prix indicatif |
|---|---|---|
| Moteur | Servo intégré JMC iHSV60-30-40-48-SC (400 W, frein 24 V intégré) | 180 € |
| Réducteur | Planétaire à denture hélicoïdale, bride 60 mm, rapport 10. Candidat : StepperOnline AD60-G10-D14 (jeu annoncé 3 minutes d'arc) | 150–250 € |
| Bobine | Imprimée en nylon PA12 (MJF), Ø 266 hors tout, 26 mm d'épaisseur, environ 350 g | à chiffrer |
| Moyeu | Moyeu de serrage acier à bride, à l'alésage de l'arbre du réducteur | 10 € |
| Platine | Aluminium 8 mm, découpe et perçages simples | à chiffrer |
| Bras | Profilé aluminium 20 × 40, 520 mm, coupé à longueur, avec écrous en T | 15 € |
| Poulie de sortie | Poulie sur roulement Ø 40 ; **poulie pivotante** pour les vols à plusieurs fils | 15–40 € |
| Le reste | Alimentation, carte, interface, capteurs : comme la première version | environ 300 € |
| | **Total par bloc** | **environ 750 à 850 €** |

Les prix sont des ordres de grandeur que je n'ai pas vérifiés. Le prix et le niveau de bruit
du réducteur sont les deux chiffres à confirmer sur sa fiche technique avant achat, ainsi que
le diamètre de son arbre de sortie et la charge qu'il admet sur le côté.

### La poulie pivotante

Quand un objet vole sur plusieurs fils, chaque fil part de sa poulie dans une direction qui
change sans cesse. Une poulie ordinaire ne l'accepte pas : le fil frotte sur la joue ou saute.
Il faut une poulie pivotante dont l'axe de pivot est aligné avec le fil qui arrive de la
bobine. Pour un fil qui ne fait que monter et descendre, la poulie simple de la maquette
suffit.

## Faire fabriquer à distance

Rien ne demande d'atelier : tout se commande ou s'assemble avec des clés Allen.

| Pièce | Où | Procédé |
|---|---|---|
| Bobine | JLC3DP | nylon PA12 en MJF. La pièce fait 266 mm et l'enveloppe annoncée est de 370 × 276 × 360 mm : elle tient, avec peu de marge |
| Support de poulie | JLC3DP | nylon PA12 |
| Platine | usinage CNC ou découpe laser aluminium | pièce plate, 8 mm |
| Profilé, écrous en T, visserie | fournisseur de profilés | coupe à longueur à la commande |

La bobine se fixe au moyeu acier par 4 vis M5 traversantes et des écrous freinés : pas
d'insert à poser à chaud, pas de collage.

Une imprimante de bureau courante (plateau de 256 mm) est trop petite pour cette bobine.
Je n'ai pas vérifié l'offre d'usinage aluminium de JLC ; tout atelier d'usinage en ligne
convient pour une pièce aussi simple.

## Montage

1. Visser le réducteur sur le servo (bride et accouplement fournis avec le réducteur).
2. Visser le réducteur sur la platine, la platine sur le profilé.
3. Serrer le moyeu acier sur l'arbre du réducteur, y boulonner la bobine.
4. Fixer le support de poulie au bout du profilé, **dans le plan du milieu de la gorge**.
5. Ancrer le fil dans le trou de la bobine, enrouler 3 tours morts, passer la poulie.

## Avant de commander

Les fichiers de `cad/export` fixent les volumes et les entraxes. Avant de les envoyer en
fabrication, il reste à reporter sur la platine et la bobine les cotes réelles du réducteur
choisi : entraxe et diamètre de ses vis, diamètre de centrage, diamètre et longueur de son
arbre. Une fois le réducteur choisi, ces cotes viennent de sa fiche technique et se changent
dans `cad/treuil.py`.

```
cd cad && python3 treuil.py      # régénère toutes les pièces
```

## Limites connues

- **Bruit** : le réducteur siffle à haute vitesse. La denture hélicoïdale le réduit sans le
  supprimer. À écouter sur le prototype avant de commander les quatre blocs.
- **Bobine en nylon** : elle convient aux objets légers. Pour 8 à 9 kg en usage prolongé, ou
  au-dessus du public, la faire usiner en aluminium à partir de `bobine.step`.
- **Fil détendu** : sans tension, le fil peut sortir de la gorge. Le capteur de fil détendu
  prévu au firmware reste nécessaire.
