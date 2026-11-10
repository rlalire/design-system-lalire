# ARIA 2026 : séquence finale (carte + 24 cubes)

Durée 25 s · 30 im/s · 1920×1080 · Blender 5.x · police Inter

| Temps | Ce qui se passe |
|---|---|
| 0 → 3 s | Les contours lumineux de la carte se tracent depuis le centre de l'Europe, puis la carte se remplit. Les 24 cubes sombres apparaissent et flottent. |
| 2,8 → 23,2 s | Relais : un cube part toutes les 0,77 s. Il se retourne en venant au premier plan (il passe du sombre à la couleur de sa catégorie et révèle son titre), reste 1,5 s, puis file sur son pays en s'arrondissant jusqu'à devenir un point lumineux, avec un petit flash à l'atterrissage. Trois emplacements tournent (gauche, centre, droite) pour que les cubes ne se croisent pas. |
| 23,2 → 25 s | Plan final : les 24 points respirent doucement sur la carte. |

## Fichiers

- `aria_final.py` : le script qui construit toute la scène.
- `carte_europe.png` : ta carte (1536×1024).
- `apercu_aria_final.mp4` : aperçu basse définition (640×360, 15 im/s, rendu EEVEE logiciel), pour valider le rythme.

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
| `T_APPROACH`, `T_HOLD`, `T_FLY` | Durées du retournement, de l'arrêt en grand et du vol. La cadence s'adapte toute seule pour finir à `LAST_LANDING`. |
| `FIRST_REVEAL`, `LAST_LANDING` | Début et fin de la valse des cubes. |
| `ORDER` | `"tableau"` (vagues de couleur EP › GE › SA › SE), `"alterne"` (couleurs mélangées) ou `"ouest_est"`. |
| `PALETTE` | `"harmonisee"` (teintes ajustées pour la carte de nuit) ou `"originale"` (couleurs du tableau). |
| `CUBE_SIZE`, `HOLD_HEIGHT`, `SLOTS_X` | Taille et placement des cubes en grand. |
| `POINT_SIZE`, `EMIT_POINT`, `EMIT_PING`, `POINT_BREATHE` | Taille, éclat, flash et respiration des points finaux. |
| `MAP_LINES`, `MAP_FILL`, `REVEAL_ORIGIN_PX`, `GLOW_COLOR` | Dessin de la carte : timing, point de départ, lueur du front. |
| `CUBE_DARK` | Teinte des cubes avant retournement. |

Valeurs animables à la main si besoin : le nœud **Reveal_Lines / Reveal_Fill** du matériau `ARIA_Map`, et **Color_Mix** dans chaque matériau de cube.

## Intégration dans le show

- La scène règle déjà : EEVEE, transformation de vue **Standard** (pour garder les couleurs exactes de la carte), 30 im/s, images 1 à 750.
- **Lueur** : pour le halo des points et des contours, ajoute dans le compositeur un nœud **Glare** (type *Bloom*, seuil ≈ 0,8), ou reprends le même traitement que dans le reste du show.
- **Motion blur** : Propriétés de rendu › Flou de mouvement, à activer comme dans tes autres plans pour que les vols soient raccord.
- **Montage** :
  - soit tu rends ARIA_Final en séquence PNG ou ProRes et tu la poses dans ton montage ;
  - soit tu l'ajoutes comme **bande de scène** dans le Video Sequencer de ton fichier principal ;
  - soit, si ton show est dans un autre .blend : Fichier › **Ajouter** (Append) › `aria.blend` › Scene › ARIA_Final.
- **Raccord avec le plan précédent** : la caméra est en plongée verticale à 20 m (`CAM_HEIGHT`, `FRAME_HEIGHT`). Si ton plan d'avant arrive par un mouvement de caméra, on peut ajouter une entrée de caméra animée dans le script.
