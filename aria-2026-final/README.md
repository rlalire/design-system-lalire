# ARIA 2026 : séquence finale (carte + 24 cubes)

Durée 46 s · 30 im/s · 1920×1080 · Blender 5.x · police Inter

Calé sur la musique. Tous les temps se règlent dans le bloc **CALAGE MUSICAL** en haut du script.

| Temps | Ce qui se passe | Réglage |
|---|---|---|
| 0 → 15 s | **Intro.** La caméra avance lentement. Les contours de la carte se tracent (1 → 8,5 s), puis la carte se remplit (5 → 12,5 s). Les cubes émergent un à un de la carte en se déroulant (3 → 10 s). Deux contre-jours rasants se lèvent : cubes en silhouette, arêtes qui accrochent la lumière (3 → 9 s). Une lumière chaude traverse le nuage de gauche à droite (6,5 → 12,5 s). La lumière principale monte (10 → 14,5 s). Les cubes font un quart de tour en vague de gauche à droite (12 → 14,7 s). | `MAP_LINES`, `MAP_FILL`, `SWARM_IN`, `CAM_PUSH`, `LIGHT_RIM`, `LIGHT_SWEEP`, `LIGHT_KEY`, `RIPPLE` |
| 15 s | Vague 1 (EP) | `WAVE_TIMES` ligne 1 |
| 22 s | Vague 2 (GE) | ligne 2 |
| 29 s | Vague 3 (SA) | ligne 3 |
| 36 s | Vague 4 (SE). Départ vers la carte à 41 s, tous posés à 44 s. | ligne 4 |
| 44 → 46 s | Plan final, les 24 points respirent. | `DURATION` |

Chaque ligne de `WAVE_TIMES` vaut `(arrivée, départ vers la carte, tous posés)`. La console affiche pour chaque vague le temps de lecture des 6 titres (≈ 4 s), et prévient si un temps est trop serré.

Deux modes, au choix :

- `REVEAL_MODE = "categories"` (par défaut) : 4 vagues de 6 cubes en grille 3 × 2.
- `REVEAL_MODE = "relais"` : un par un entre `FIRST_REVEAL` (15 s) et `LAST_LANDING` (44 s).

`VARIATION` (0 à 1,5) casse le côté mécanique : chaque cube a sa trajectoire courbe, sa façon de se retourner (4 sens, parfois un tour complet), son rebond, sa durée, sa légère inclinaison, son départ et sa rotation à l'atterrissage. `0` = tous identiques. Au-delà de ~1,2, deux cubes peuvent parfois se frôler. Change `SEED` pour tirer une autre combinaison de mouvements.

## Fichiers

- `aria_final.py` : le script qui construit toute la scène.
- `carte_europe.png` : ta carte (1536×1024).
- `apercu_aria_final.mp4` : aperçu du mode catégories, basse définition (640×360, 15 im/s, rendu EEVEE logiciel), pour valider le rythme.

## Sur ton Mac

1. **Installe Inter** si ce n'est pas déjà fait : [rsms.me/inter](https://rsms.me/inter/). Double-clique sur `Inter-SemiBold.ttf` et `Inter-Medium.ttf`, puis « Installer ». Le script les trouve tout seul dans `~/Library/Fonts`.
2. Copie `aria_final.py` et `carte_europe.png` **dans le dossier de ton .blend**.
3. Dans Blender : onglet **Scripting** › **Ouvrir** › `aria_final.py` › **▶ Run Script**.
   - Une nouvelle scène **ARIA_Final** apparaît. Tes autres scènes ne sont pas touchées.
   - La console (Fenêtre › Basculer la console système) affiche « [ARIA] Scène prête ». Si Inter ou la carte manquent, elle le dit aussi.
4. **Ajuste les points** : dans la collection `ARIA_Cibles`, chaque repère `Cible_01_FI`, `Cible_02_FI`… correspond à un projet. Déplace-les en vue de dessus (pavé num. 7).
5. **Relance le script** : les positions des repères sont gardées et toute l'animation est recalculée. Ça prend environ 3 secondes.

> Le script recrée toujours la scène ARIA_Final de zéro. Fais tes réglages **dans le bloc RÉGLAGES du script** et pas à la main sur les objets, sinon la prochaine exécution les effacera. Seule exception : les repères `Cible_xx`, qui sont conservés.

## Réglages utiles (en haut du script)

| Réglage | Effet |
|---|---|
| `REVEAL_MODE`, `VARIATION`, `SEED` | Mode de révélation, dose de variété, tirage aléatoire. |
| `WAVE_TIMES` | Temps de chaque vague : arrivée, départ vers la carte, tous posés. |
| `WAVE_APPROACH`, `WAVE_STAGGER_IN/OUT` | Durée du retournement, étalement des arrivées et des départs dans une vague. |
| `KEY_ENERGY`, `RIM_ENERGY`, `SIDE_RIM_ENERGY`, `SWEEP_ENERGY` | Puissance des lumières (principale, contre-jour du dessus, contre-jours rasants, lumière qui traverse). |
| `WAVE_CUBE_SIZE`, `WAVE_GRID`, `WAVE_HOLD_HEIGHT`, `WAVE_ORDER` | Mode catégories : taille et espacement de la grille, ordre des vagues. |
| `T_APPROACH`, `T_HOLD`, `T_FLY` | Durées du retournement, de l'arrêt en grand et du vol. La cadence s'adapte toute seule pour finir à `LAST_LANDING`. |
| `ORDER` | `"tableau"` (vagues de couleur EP › GE › SA › SE), `"alterne"` (couleurs mélangées) ou `"ouest_est"`. |
| `PALETTE` | `"harmonisee"` (teintes ajustées pour la carte de nuit) ou `"originale"` (couleurs du tableau). |
| `CUBE_SIZE`, `HOLD_HEIGHT`, `SLOTS_X` | Taille et placement des cubes en grand. |
| `POINT_SIZE`, `EMIT_POINT`, `EMIT_PING`, `POINT_BREATHE` | Taille, éclat, flash et respiration des points finaux. |
| `MAP_LINES`, `MAP_FILL`, `REVEAL_ORIGIN_PX`, `GLOW_COLOR` | Dessin de la carte : timing, point de départ, lueur du front. |
| `CUBE_DARK` | Teinte des cubes avant retournement. |
| `CUBE_ROUGHNESS`, `CUBE_METALLIC`, `CUBE_COAT` | Matière : brillant ↔ mat, plastique ↔ métal, vernis laqué. |
| `TITLE_TEXT_SIZE`, `COUNTRY_TEXT_SIZE`, `COUNTRY_LETTER_SPACING` | Taille des titres et du nom de pays, espacement des lettres du pays. Le titre s'adapte à la place restante. |
| `CUBE_STYLE`, `GLASS_ROUGHNESS`, `GLASS_IOR`, `GLASS_DARK`, `GLASS_GLOW` | `"verre"` : cubes en verre teinté de la couleur du projet (verre fumé avant retournement), la carte se voit à travers. Le rendu est plus lent (raytracing EEVEE activé automatiquement). |
| `CUBE_BEVEL`, `CUBE_BEVEL_SEGMENTS` | Arrondi des arêtes (0 = arêtes vives) et finesse de l'arrondi. |

Valeurs animables à la main si besoin : le nœud **Reveal_Lines / Reveal_Fill** du matériau `ARIA_Map`, et **Color_Mix** dans chaque matériau de cube.

## Intégration dans le show

- La scène règle déjà : EEVEE, transformation de vue **Standard** (pour garder les couleurs exactes de la carte), 30 im/s, images 1 à 1380.
- **Lueur** : pour le halo des points et des contours, ajoute dans le compositeur un nœud **Glare** (type *Bloom*, seuil ≈ 0,8), ou reprends le même traitement que dans le reste du show.
- **Motion blur** : Propriétés de rendu › Flou de mouvement, à activer comme dans tes autres plans pour que les vols soient raccord.
- **Montage** :
  - soit tu rends ARIA_Final en séquence PNG ou ProRes et tu la poses dans ton montage ;
  - soit tu l'ajoutes comme **bande de scène** dans le Video Sequencer de ton fichier principal ;
  - soit, si ton show est dans un autre .blend : Fichier › **Ajouter** (Append) › `aria.blend` › Scene › ARIA_Final.
- **Raccord avec le plan précédent** : la caméra est en plongée verticale à 20 m (`CAM_HEIGHT`, `FRAME_HEIGHT`). Si ton plan d'avant arrive par un mouvement de caméra, on peut ajouter une entrée de caméra animée dans le script.
