# Prompt à donner à Claude Code — pilotage des treuils « Lévitation micro »

Copier tout ce qui suit la ligne dans une session Claude Code ouverte sur le dépôt
`rlalire/orchestr-ios` (Orchestr, cible macOS, module Kinetic). La section « Où brancher
dans ce dépôt » est propre à Orchestr ; le reste du protocole vaut pour tout logiciel.

---

Je veux qu'Orchestr pilote mes treuils « Lévitation micro » en OSC, depuis le module
Kinetic. Voici leur protocole exact, tel qu'il est écrit dans leur firmware. Lis d'abord le
code indiqué ci-dessous, puis propose-moi un plan avant de modifier quoi que ce soit.

## Où brancher dans ce dépôt

Le module Kinetic (`Orchestr macOS/Kinetic/`) attend déjà des treuils réels :

- `WinchBackend.swift` définit le protocole `WinchBackend` (`send(target:maxSpeed:maxAcceleration:to:)`,
  `home`, `emergencyStop`, `onStatus`) et son seul backend actuel, `SimulationOnlyBackend`.
  Le commentaire d'en-tête prévoit les backends réels « chacun dans son fichier, sans toucher
  au moteur ». C'est ce qu'il faut écrire : un `LevitationWinchBackend`.
- `KineticModels.swift` définit `WinchOutput` (`.simulationOnly`, `.dmx`, `.osc(host:port:addressPattern:)`)
  avec un décodage résilient : un type inconnu retombe sur `.simulationOnly`. Ajoute un cas
  dédié à ces treuils en gardant cette règle, pour que les anciens fichiers s'ouvrent toujours.
- `KineticEngine.swift` fait tourner la simulation à 120 Hz et détient le `backend`. Regarde
  où et à quelle cadence il l'appelle avant de décider quoi envoyer.
- `Winch` (dans `KineticModels.swift`) porte déjà `anchorPosition`, `softLimitMin`,
  `softLimitMax`, `maxSpeed`, `maxAcceleration`. Il lui manque le numéro de bloc, l'adresse
  réseau, le décalage du zéro et la tension maximale du fil.
- `CableKinematics.swift` et `CableCalibration.swift` calculent les longueurs de câble en
  mètres, repère Y vers le haut. Les treuils attendent des millimètres déroulés depuis leur
  zéro : voir « Les conversions ».
- `Scripts/test-kinetic.sh` compile et lance les tests des modules purs, sans Xcode. Mets la
  logique de conversion et de suivi d'état dans un module pur et ajoute-le à ce script.

Correspondance avec le protocole `WinchBackend` :

| Méthode | Message vers le bloc |
|---|---|
| `send(target:…)` | longueur en mètres → position en millimètres, envoyée en flux par `/levi/all/pos`. Le bloc n'accepte ni vitesse ni accélération par commande : il applique ses propres limites. La simulation d'Orchestr doit donc rester en dessous |
| `home(_:)` | `/levi/N/arm` si le bloc est désarmé, attendre l'état 2, puis `/levi/N/home` |
| `emergencyStop(_:)` | `/levi/all/stop` : arrêt en douceur, le moteur continue de tenir l'objet. Ne pas envoyer `disarm`, qui lâcherait l'objet |
| `onStatus` | alimenté par `/levi/N/state` : longueur = (position + décalage) / 1000, `homed` = 4ᵉ argument, `moving` = état 3 à 7 |

Le moteur de simulation tourne à 120 Hz. N'envoie pas plus de 100 paquets par seconde aux
blocs ; 60 suffisent.

## Le matériel

Chaque treuil est un bloc autonome : un moteur de gimbal avec encodeur entraîne une bobine
de 80 mm, et un fil très fin sort par une bague céramique sous le boîtier. Un bloc porte un
objet de 1 à 50 g. Jusqu'à 4 blocs, numérotés de 1 à 4, tiennent un même objet par 2, 3 ou
4 fils.

Le moteur est piloté en force : il ne tient l'objet que s'il est alimenté et armé. Coupé,
il laisse l'objet redescendre et perd son origine.

## Réseau

- Ethernet filaire, UDP, OSC 1.0. Messages simples ou bundles, les deux sont acceptés.
- Adresse du bloc N : `192.168.10.(10 + N)`, soit `.11` à `.14`. Masque `255.255.255.0`.
- Les blocs écoutent sur le port **9000**, en direct et en diffusion (`192.168.10.255`).
- Chaque bloc répond à l'adresse IP du dernier émetteur qu'il a entendu, sur le port
  **9001**. Le logiciel doit donc écouter en UDP sur 9001.
- Arguments numériques : `f` (float32) ou `i` (int32), indifféremment. `d`, `T` et `F` sont
  aussi lus. Les chaînes ne sont pas acceptées.

## Unités et repère

- **Position = longueur de fil déroulée, en millimètres.** 0 = origine haute, valeur
  positive = l'objet descend.
- Course par défaut : 0 à 10 000 mm, bornée par des butées logicielles.
- Vitesses en mm/s, durées en secondes, tensions de fil en grammes.

## Commandes

`N` est le numéro du bloc (1 à 4). `all` adresse tous les blocs à la fois.

| Adresse | Arguments | Effet |
|---|---|---|
| `/levi/N/arm` ou `/levi/all/arm` | aucun | Met le moteur sous tension ; il tient l'objet là où il est. Obligatoire avant tout mouvement. |
| `/levi/N/disarm` ou `/levi/all/disarm` | aucun | Coupe le moteur. L'objet redescend, l'origine est perdue. Accepté seulement à l'arrêt. |
| `/levi/N/home` ou `/levi/all/home` | aucun | Prise d'origine : remonte à 60 mm/s avec une force plafonnée jusqu'à ce qu'une perle nouée sur le fil bute sous la bague, met la position à 0, puis redescend à 20 mm. Accepté seulement armé et à l'arrêt. |
| `/levi/N/zero` ou `/levi/all/zero` | aucun | La position actuelle devient 0. Accepté seulement armé et à l'arrêt. |
| `/levi/N/goto` | position, durée (facultative) | Va à la position en courbe douce (polynôme de degré 5, départ et arrivée à vitesse nulle) dans la durée donnée. Durée absente ou trop courte : le bloc prend la durée minimale que ses limites permettent. |
| `/levi/all/goto` | p1, p2, p3, p4, durée | Un seul paquet pour les 4 blocs : chacun prend la position de son rang. Les **5 arguments sont obligatoires**, même avec moins de 4 blocs. |
| `/levi/N/pos` | position | Consigne en flux continu. À envoyer de 50 à 100 fois par seconde. |
| `/levi/all/pos` | p1, p2, p3, p4 | Le flux pour les 4 blocs en un paquet. |
| `/levi/N/jog` | vitesse | Déplacement manuel en vitesse. S'arrête seul si le message n'est pas renvoyé toutes les 300 ms. Limité à ±200 mm/s tant que l'origine n'est pas faite. |
| `/levi/N/stop` ou `/levi/all/stop` | aucun | Arrêt en douceur, à 4000 mm/s². Ce n'est pas un arrêt d'urgence. |
| `/levi/N/reset` ou `/levi/all/reset` | aucun | Acquitte un défaut, une fois sa cause disparue. |
| `/levi/N/tension` | grammes | Tension maximale que le moteur exerce sur le fil. Mémorisée. De 0 à 300, 30 par défaut. Par bloc uniquement. |
| `/levi/N/hometension` | grammes | Tension pendant la prise d'origine. Doit dépasser le poids porté par ce fil. 15 par défaut. Par bloc uniquement. |
| `/levi/N/limits` | min, max | Butées logicielles en mm. Mémorisées. Par bloc uniquement. |
| `/levi/N/measure` | grammes (facultatif) | Mesure de longueur : remonte à 60 mm/s avec la tension donnée (celle de prise d'origine par défaut) jusqu'à ce que le fil se tende, renvoie la position, puis rend 20 mm de mou. Ne change pas l'origine. Accepté seulement armé et à l'arrêt. Par bloc uniquement. |
| `/levi/N/breaktest` | aucun | Test de rupture : fil attaché à un point fixe, le moteur tire de plus en plus fort (10 g/s, 300 g au plus) et renvoie la tension à laquelle le fil a cassé. Par bloc uniquement. |

### Limites à respecter côté logiciel

| | Valeur |
|---|---|
| Vitesse en montée (position qui diminue) | 3000 mm/s au plus. En 12 V, viser 2500 |
| Vitesse en descente (position qui augmente) | 1500 mm/s au plus, à baisser pour un objet qui plane |
| Accélération | 4000 mm/s² |

Si une consigne les dépasse, le bloc ne la suit pas : en `goto` il allonge la durée, en flux
il prend du retard. **Les autres blocs ne s'alignent pas d'eux-mêmes.** Le logiciel doit donc
vérifier ces limites sur chaque fil avant d'envoyer une trajectoire, et la ralentir en
entier si un seul fil les dépasse.

### Comportement du flux

- Le bloc estime la vitesse de la consigne d'un paquet au suivant et prolonge le mouvement
  entre deux paquets. Il suit avec environ 8 ms de retard, identique sur tous les blocs.
- Sans nouveau paquet pendant plus de deux intervalles, il vise la dernière consigne reçue
  et s'y arrête.
- Un `goto` reçu pendant un mouvement est rejoint en douceur, sans respecter sa durée.

## Retours

Sur le port 9001, vers le dernier émetteur.

`/levi/N/state`, 20 fois par seconde, 7 arguments :

| Rang | Type | Sens |
|---|---|---|
| 1 | f | position mesurée, mm |
| 2 | f | vitesse mesurée, mm/s |
| 3 | i | état (voir ci-dessous) |
| 4 | i | 1 si l'origine est connue, 0 sinon |
| 5 | i | défaut : 0 aucun, 1 arrêt d'urgence, 3 fil accroché ou objet trop lourd |
| 6 | f | tension estimée du fil, en grammes (approximative) |
| 7 | i | arrêt de groupe : numéro du bloc en défaut qui l'a déclenché, 0 sinon |

États : 0 désarmé · 2 armé à l'arrêt · 3 `goto` en cours · 4 flux · 5 `jog` · 6 prise
d'origine · 7 arrêt en cours · 8 défaut · 9 test de rupture · 10 mesure de longueur.

`/levi/N/warn` avec un entier, quand une commande est refusée ou modifiée : 1 bloc non armé,
2 origine non faite, 3 durée allongée, 4 consigne hors course ramenée à la butée, 5 commande
refusée pendant un mouvement, 6 mouvement refusé parce qu'un arrêt de groupe est en cours.

`/levi/N/homed` avec un flottant, à la fin de chaque prise d'origine : la distance remontée
entre le départ et la butée, en mm.

`/levi/N/measured` avec trois flottants, à la fin d'une mesure de longueur : la position où
le fil s'est tendu (mm, dans le repère courant du bloc), la distance parcourue (mm) et la
tension appliquée (g).

`/levi/N/break` avec la tension en grammes et un entier (1 = le fil a cassé, 0 = maximum
atteint sans casser), à la fin d'un test de rupture.

### Arrêt de groupe

Les blocs sont tous identiques, sans maître. Mais un bloc qui passe en défaut prévient
lui-même les autres : il diffuse `/levi/all/groupstop` (numéro du bloc, défaut) sur
`192.168.10.255:9000`, et le répète 5 fois par seconde tant qu'il reste en défaut. Chaque
autre bloc s'arrête alors en douceur, tient son objet, et refuse `goto` et `pos`
(avertissement 6) jusqu'à recevoir un `reset`. `jog` et `home` restent acceptés.

Conséquences pour le logiciel :

- Il n'a pas à envoyer lui-même l'arrêt aux autres blocs, mais il doit **cesser d'envoyer le
  flux** dès qu'un bloc est en défaut ou que le 7ᵉ argument de l'état est non nul.
- Pour repartir : faire disparaître la cause, envoyer `/levi/all/reset`, vérifier que tous
  les blocs sont revenus à l'état 2 avec le 7ᵉ argument à 0, puis ramener l'ensemble en
  douceur avant de reprendre.
- Si le bloc fautif est encore en défaut après le `reset`, il continue de prévenir et les
  autres se remettent à l'arrêt : c'est voulu.
- Le logiciel ne doit pas envoyer `groupstop` lui-même ; pour arrêter, il envoie `stop`.

### Règles d'état

- `goto` et `pos` sont refusés tant que le bloc n'est pas armé (avertissement 1) ou que
  l'origine n'est pas faite (avertissement 2).
- Après une coupure de courant, un désarmement ou un arrêt d'urgence, l'origine est perdue :
  il faut armer puis refaire `home`.
- Défaut 3 (fil accroché) : le bloc s'arrête et tient en place sans forcer. `reset` le
  remet armé à l'arrêt, origine conservée.
- Défaut 1 (arrêt d'urgence) : moteur coupé. `reset` le remet désarmé, origine perdue.

## Calibration du montage

Je calibre aujourd'hui mon installation ainsi, et je veux garder ce déroulé :

1. **Hauteur et zéro de chaque bloc.** Un petit objet est accroché au fil et posé au sol.
   J'envoie `home` : le bloc remonte jusqu'à la butée et renvoie `/levi/N/homed` avec la
   distance remontée. C'est la hauteur de la bague au-dessus de l'objet posé, et le bloc a
   son zéro.
2. **Distance entre blocs, paire par paire.** Le bout du fil du bloc A est accroché à la
   bague du bloc B. J'envoie `/levi/A/measure` : la position renvoyée par `/levi/A/measured`
   est la longueur de fil entre les deux bagues, au décalage de l'accroche près. Trois
   paires pour trois blocs, six pour quatre.
3. **Reconstruction.** Les hauteurs et les distances donnent la position des blocs.
   `CableCalibration.swift` reconstruit déjà la géométrie à partir des distances, mais
   suppose les blocs à la même hauteur : il faut l'étendre pour prendre les hauteurs
   mesurées.

Le fil est très fin et s'allonge sous la tension. Prévoir de faire chaque mesure à deux
tensions (par exemple 5 et 10 g) et d'extrapoler la longueur à tension nulle, et laisser la
possibilité de saisir une distance à la main, mesurée au télémètre laser.

## Du logiciel aux treuils : les conversions

Le logiciel calcule pour chaque fil une longueur L, en mètres, entre le point de sortie du
treuil et le point d'accroche sur l'objet. Le treuil attend une position p en millimètres :

```
p_mm = L_m × 1000 − décalage_mm
```

`décalage_mm` est la longueur de fil entre la bague céramique et le point d'accroche quand
le bloc est à la position 0, c'est-à-dire perle en butée. Il dépend de l'endroit où la perle
est nouée et se mesure une fois par fil. Il doit être un réglage par fil, enregistré avec le
projet.

Le point de sortie du fil est la bague céramique sous le boîtier. Il est fixe : il ne se
déplace pas quand la bobine tourne.

Les blocs sont numérotés à partir de **1**. Si le logiciel numérote ses fils à partir de 0,
prévoir une table de correspondance fil → bloc plutôt qu'un simple décalage, car je peux
brancher les blocs dans un autre ordre que les fils.

## Ce que je veux dans le logiciel

1. **Une sortie « Treuils Lévitation »**, à côté des sorties OSC existantes, qui envoie à
   chaque image `/levi/all/pos p1 p2 p3 p4` avec les conversions ci-dessus. Envoyer ce même
   paquet à l'adresse de chaque bloc actif, l'un après l'autre sans attente, plutôt qu'en
   diffusion : la diffusion UDP n'est pas toujours autorisée par le système. Mettre 0 pour
   un rang sans bloc.
2. **Un panneau par bloc** : état, origine connue ou non, défaut en clair, position, vitesse,
   tension estimée, et les avertissements reçus. Un bloc qui ne répond plus depuis une
   seconde doit apparaître hors ligne.
3. **Les commandes de mise en route** : armer, désarmer, prise d'origine (pour un bloc ou
   pour tous), zéro, acquittement, réglage de la tension maximale et de la tension d'origine.
4. **Un déplacement manuel** par bloc avec `jog`, renvoyé tant que le bouton est maintenu.
5. **Des garde-fous** : ne pas démarrer l'envoi d'une trajectoire si un bloc actif n'est pas
   armé, n'a pas son origine, est en défaut ou en arrêt de groupe ; arrêter l'envoi si un
   bloc passe en défaut pendant la lecture (les blocs s'arrêtent déjà entre eux) ; refuser ou ralentir une trajectoire qui
   dépasse les limites de vitesse et d'accélération sur un fil.
6. **Une arrivée en douceur** : avant de lancer un flux, amener chaque bloc à sa position de
   départ par un `/levi/all/goto` avec une durée calculée, et n'enchaîner le flux qu'une fois
   tous les blocs revenus à l'état 2.

## Ce qu'il ne faut pas supposer

- Le firmware compile et passe ses tests en simulation, mais n'a pas encore tourné sur un
  vrai moteur. Prévoir que les limites et les décalages restent des réglages modifiables,
  pas des constantes.
- La tension renvoyée en grammes est une estimation à quelques grammes près, sans capteur.
  L'afficher, ne pas s'en servir pour asservir.
- Le bouton d'arrêt du logiciel n'est pas un arrêt d'urgence : il envoie un arrêt en
  douceur. L'arrêt d'urgence est une boucle câblée sur les blocs.

## Pour tester sans matériel

Écris un faux bloc qui tourne sur la même machine : il écoute sur le port 9000, applique les
règles d'état ci-dessus, suit les consignes avec les limites de vitesse et d'accélération,
et renvoie `/levi/N/state` sur le port 9001. Il servira aux tests automatiques et à la mise
au point de l'interface.
