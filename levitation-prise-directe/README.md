# Lévitation — bloc treuil en prise directe

Variante du bloc décrit dans [`../levitation`](../levitation/README.md) : la bobine est montée
directement sur l'arbre du servo. Plus de courroie, plus de poulies, un bloc long et fin.

**État : conception v0.1, rien n'est encore construit.** Le firmware passe ses 25 vérifications
en simulation sur PC ; il n'a pas été compilé pour la carte ni essayé sur un moteur.

- `simulation.html` : vue 3D animée du mécanisme, à ouvrir dans un navigateur.
- `cad/` : maquette paramétrique, avec la bobine prête à imprimer (`cad/export/bobine.stl`).
- `firmware/` : le même firmware, réglé pour cette mécanique.

Le câblage, le protocole OSC et les consignes de sécurité sont identiques à la version à
courroie et restent décrits dans son README.

## Ce que fait le bloc

| | Prise directe | Rappel : version à courroie |
|---|---|---|
| Bobine | Ø 30 mm, 130 mm utiles | Ø 40 mm, 105 mm utiles |
| Fil par tour | 97,4 mm | 128,8 mm |
| Charge en continu | 8,4 kg | 12,6 kg |
| Charge en pointe | 25 kg | 37 kg |
| Vitesse | 3 m/s (le moteur permettrait 4,9 m/s) | 3,2 m/s |
| Résolution | 0,05 mm | 0,03 mm |
| Course | 10 m sur une seule couche | 10 m |
| Encombrement | 411 × 112 × 80 mm | 291 × 205 × 140 mm |

Calcul : couple nominal 1,27 N·m sur un rayon de 15,5 mm = 82 N, soit 8,4 kg. À 3000 tr/min,
50 tours par seconde × 97,4 mm = 4,9 m/s.

8,4 kg en continu convient à tous les objets légers. Pour des objets de 8 à 9 kg portés par
plusieurs fils, cela suffit tant que les fils restent assez verticaux. Si les fils doivent
travailler très à l'horizontale, passer la bobine en Ø 25 (`DRUM_D` dans `cad/treuil.py` et
`DRUM_DIAMETER_MM` dans `firmware/src/config.h`) : 10 kg en continu, bobine de 155 mm.

## Montage

```
 servo avec frein ─ flasque ─ moyeu de serrage acier ─ BOBINE IMPRIMÉE ─ axe acier Ø 12 ─ roulement ─ flasque
                                                            │
                                    guide-fil : chariot sur 2 colonnes, poussé par une vis
```

- Le frein intégré au servo agit directement sur la bobine : il n'y a plus de courroie qui
  puisse casser entre les deux.
- La bobine est tenue des deux côtés. Sans le roulement du bout, la charge travaillerait en
  porte-à-faux sur les roulements du moteur.
- Le roulement du bout doit pouvoir s'aligner tout seul (roulement à rotule, ou logement
  légèrement souple) : un axe tenu rigidement en trois points force sur le moteur.

## La bobine imprimée en 3D

Oui, c'est faisable, et l'impression apporte un vrai avantage : la **gorge en hélice** au pas
de 1,2 mm est imprimée directement dans la bobine. Le fil s'y couche spire après spire, ce qui
aide le guide-fil et protège le fil. À l'usinage, cette gorge coûterait cher.

Règles à respecter :

- **Matière : PETG, ASA ou nylon chargé carbone. Pas de PLA** : l'arbre du moteur chauffe, et
  le PLA ramollit dès 55 °C et se déforme lentement sous charge.
- **Le plastique ne transmet pas le couple sur l'arbre.** Un moyeu de serrage en acier
  (alésage 14 mm) pince l'arbre du moteur ; la bobine s'y visse par 4 vis M4 dans des inserts
  laiton posés à chaud. De l'autre côté, un axe en acier Ø 12 est collé et goupillé dans la
  bobine.
- **Impression** : axe vertical, couches de 0,12 à 0,16 mm pour une gorge propre, au moins
  5 périmètres, remplissage de 60 à 100 %. Environ 130 g de PETG.
- **Ébavurer la gorge** et le trou d'ancrage : une arête vive use le fil.

Limites :

- Pour les objets de moins d'un kilo, la bobine imprimée convient durablement.
- Pour 8 à 9 kg, elle convient pour le prototype et les essais. Cent spires de fil tendu
  serrent la bobine en permanence et le plastique finit par se déformer. Une fois la forme
  validée, faire usiner la même pièce en aluminium à partir de `cad/export/bobine.step`.
- Au-dessus du public : bobine en aluminium, quelle que soit la charge.

## Composants : ce qui change

| Par rapport à la version à courroie | |
|---|---|
| Supprimés | 2 poulies, la courroie, le frein séparé sur l'axe (environ 70 €) |
| Ajoutés | moyeu de serrage acier à bride, alésage 14 mm (10 €) ; axe acier Ø 12 ; 4 inserts M4 ; filament (3 €) |
| Inchangés | servo JMC iHSV60-30-40-48-SC, alimentation, carte, guide-fil, capteurs |
| Total par bloc | environ 600 à 650 € (ordre de grandeur) |

## Fichiers de fabrication

```
cd cad && python3 treuil.py      # régénère tout après un changement de cote (2 minutes)
```

| Fichier | Usage |
|---|---|
| `cad/export/bobine.stl` | impression 3D de la bobine, gorge comprise |
| `cad/export/bobine.step` | la même pièce pour un usinage en aluminium |
| `cad/export/chariot.step` | chariot du guide-fil, imprimable |
| `cad/export/flasque_*.step` | les deux flasques (imprimables pour le prototype, alu ensuite) |
| `cad/export/treuil.step` | l'assemblage complet |

Ces pièces fixent les volumes et les entraxes. Les perçages de fixation du moteur et les jeux
d'ajustement sont à reprendre une fois les composants reçus et mesurés.
