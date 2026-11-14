"""Bloc treuil micro — pièces du prototype à imprimer en 3D (CadQuery).

    pip install cadquery
    python3 treuil.py

Pour des objets de quelques grammes sur un fil très fin. Moteur de gimbal CubeMars GL35
KV100 avec encodeur, en prise directe : la bobine est une cloche vissée sur la face
tournante du moteur et l'entoure. Le fil sort par un œillet céramique fixe.

Quatre pièces à imprimer, toutes posées à plat et sans supports :
  corps            cloison porte-moteur + chambre du fil + deux bossages pour spigot M10
  capot_arriere    bac qui ferme la chambre de l'électronique
  couvercle_avant  plaque qui ferme la chambre du fil
  bobine           cloche à gorge (à imprimer en résine pour une surface lisse)

Produit dans ./export, pour chaque pièce, un fichier STEP et un fichier STL, plus
l'assemblage complet (treuil.step). Les cotes du moteur viennent du plan coté fourni par
CubeMars pour le GL35 avec encodeur ; le moteur est figuré par un simple cylindre.

Cotes en millimètres. X = axe du moteur, Z = vertical, le fil sort vers le bas.
"""
import math
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 80.0          # diamètre de la bobine, fond de gorge
LINE_D = 0.05          # diamètre du fil
SLOT_W = 2.0           # largeur de la gorge
SLOT_DEPTH = 6.0
TRAVEL_M = 10.0

# ---------- Moteur CubeMars GL35 KV100 avec encodeur (plan coté du fabricant) ----------
MOTOR_D, MOTOR_L = 41.8, 33.5                      # longueur avec l'encodeur, tolérance +/- 0,2
BASE_PCD = 24.0                                    # 4 x M3 à l'arrière (côté fixe), profondeur 5
HUB_PCD, HUB_BORE = 20.0, 6.0                      # face tournante : 4 x M3, profondeur 2,5 seulement
SPIGOT_H = 1.2                                     # téton de centrage dans l'alésage de 6 mm
WIRES_R, WIRES_DEG = 16.5, 135.0                   # sortie des fils sur la face arrière, en diagonale

# ---------- Jeux et visserie ----------
M3_CLEAR, M3_PILOT = 3.4, 2.6                      # trou de passage / avant-trou où la vis M3 forme son filet
FIT = 0.2                                          # jeu d'emboîtement des pièces imprimées
EYELET_OD = 5.8                                    # corps de la bague céramique à collerette (mesuré 5,74 à 5,83)

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = TRAVEL_M * 1000 / LINE_PER_TURN
FLANGE_D = DRUM_D + 2 * SLOT_DEPTH
REEL_W = SLOT_W + 4.0                              # deux joues de 2 mm
WALL, PART_T, DISC_T = 2.5, 3.0, 3.0
BORE_D = 46.0                                      # la cloche entoure le moteur (jeu de 2,1 mm au rayon)
X_MOTOR = PART_T                                   # le moteur est vissé à plat sur la cloison
X_REEL = X_MOTOR + 4.0                             # face arrière de la bobine
X_HUB = X_MOTOR + MOTOR_L + 0.2                    # face tournante = appui de la bobine (tolérance comprise)
X_LINE = X_REEL + REEL_W / 2                       # plan du fil
X_FRONT = round(X_HUB + DISC_T + 3.6, 1)           # face intérieure du couvercle avant
X_REAR = -22.0                                     # fond de la chambre de l'électronique (module PoE de 18 mm)
IN_Y, IN_Z = (-52.0, 55.0), (-66.0, 52.0)          # intérieur du boîtier
OUT_Y, OUT_Z = (IN_Y[0] - WALL, IN_Y[1] + WALL), (IN_Z[0] - WALL, IN_Z[1] + WALL)
EYE_Y = DRUM_D / 2 + LINE_D / 2                    # le fil descend à la verticale du bord de la bobine
FLEET_DEG = math.degrees(math.atan((SLOT_W / 2) / abs(IN_Z[0])))
COL_D = 9.0                                        # colonnes de vissage dans les quatre angles
CORNERS = [(y, z) for y in (IN_Y[0] + 4.5, IN_Y[1] - 4.5) for z in (IN_Z[0] + 4.5, IN_Z[1] - 4.5)]
# Accroche : un spigot de 16 mm à filetage M10 (pour pince type Super Clamp) se visse dans un
# écrou M10 prisonnier. Deux emplacements : sur le dessus, à l'aplomb du moteur, et sur le
# côté opposé à la sortie du fil, à la hauteur de l'axe du moteur. L'emplacement libre
# reçoit un anneau à vis M10 pour l'élingue de sécurité.
SPIGOT_X = 27.0                                    # à l'aplomb du moteur, pour que le bloc pende droit
NUT_AF, NUT_H = 17.0, 8.0                          # écrou M10 : 17 sur plats, 8 d'épaisseur
SPIGOT_THREAD = 20.0                               # longueur du filetage M10 du spigot
BOSS_HALF_W, BOSS_H = 13.0, 12.0
CABLE_Z = (-54.0, -36.0)                           # passage du câble réseau, sur le côté, face au module PoE

COLORS = {"boitier": (0.20, 0.20, 0.22), "capot": (0.26, 0.26, 0.29), "bobine": (0.85, 0.65, 0.15),
          "moteur": (0.12, 0.12, 0.13), "carte": (0.18, 0.55, 0.34), "oeillet": (0.95, 0.95, 0.92)}


def cyl_x(d, length, x, yz=(0.0, 0.0)):
    """Cylindre d'axe X, partant de x."""
    return cq.Workplane("YZ").workplane(offset=x).center(*yz).circle(d / 2).extrude(length)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def shell(x0, x1):
    """Enveloppe extérieure du boîtier entre deux abscisses, angles arrondis."""
    return box(x0, x1, OUT_Y[0], OUT_Y[1], OUT_Z[0], OUT_Z[1]).edges("|X").fillet(6)


def cavity(x0, x1):
    return box(x0, x1, IN_Y[0], IN_Y[1], IN_Z[0], IN_Z[1]).edges("|X").fillet(4)


def corps():
    """Cloison porte-moteur (sert de fond à l'impression) et chambre du fil."""
    b = shell(0, X_FRONT).cut(cavity(PART_T, X_FRONT))
    for c in CORNERS:                                                    # colonnes de vissage
        b = b.union(cyl_x(COL_D, X_FRONT - PART_T, PART_T, c).intersect(shell(0, X_FRONT)))
    for c in CORNERS:
        b = b.cut(cyl_x(M3_PILOT, X_FRONT, 0, c))                        # vis du capot (arrière) et du couvercle (avant)
    for a in range(4):                                                   # 4 vis M3 x 6 du moteur, sur Ø 24
        ang = a * math.pi / 2
        b = b.cut(cyl_x(M3_CLEAR, PART_T, 0, (BASE_PCD / 2 * math.cos(ang), BASE_PCD / 2 * math.sin(ang))))
    for d in (-10, 10):                                                  # passage des fils du moteur
        ang = math.radians(WIRES_DEG + d)
        b = b.cut(cyl_x(8, PART_T, 0, (WIRES_R * math.cos(ang), WIRES_R * math.sin(ang))))
    eye = (cq.Workplane("XY").workplane(offset=OUT_Z[0]).center(X_LINE, EYE_Y)
           .circle((EYELET_OD + FIT) / 2).extrude(WALL))                 # logement de l'œillet
    b = b.cut(eye)
    # Bossages des spigots : chacun loge un écrou M10 glissé par l'avant, au-dessus ou à côté
    # de la cloche de la bobine. L'écrou garde 2 mm de matière côté intérieur.
    half = (NUT_AF + 0.4) / 2
    back = SPIGOT_X - NUT_AF / math.sqrt(3) - 0.3                        # fond de la glissière (pointe de l'écrou)
    hole = cq.Workplane("XY").circle(5.25).extrude(BOSS_H + WALL)        # passage du filetage M10
    # Dessus
    b = b.union(box(16, X_FRONT, -BOSS_HALF_W, BOSS_HALF_W, IN_Z[1] - BOSS_H, IN_Z[1]))
    b = b.cut(box(back, X_FRONT, -half, half, IN_Z[1] - BOSS_H + 2.0, IN_Z[1] - BOSS_H + 2.6 + NUT_H))
    b = b.cut(hole.translate((SPIGOT_X, 0, IN_Z[1] - BOSS_H)))
    # Côté (paroi y négatif, à l'opposé de la sortie du fil)
    b = b.union(box(16, X_FRONT, IN_Y[0], IN_Y[0] + BOSS_H, -BOSS_HALF_W, BOSS_HALF_W))
    b = b.cut(box(back, X_FRONT, IN_Y[0] + BOSS_H - 2.6 - NUT_H, IN_Y[0] + BOSS_H - 2.0, -half, half))
    b = b.cut(hole.rotate((0, 0, 0), (1, 0, 0), 90).translate((SPIGOT_X, IN_Y[0] + BOSS_H, 0)))
    return b


def capot_arriere():
    """Bac qui ferme la chambre de l'électronique ; son fond sert de face d'impression."""
    b = shell(X_REAR - WALL, 0).cut(cavity(X_REAR, 0))
    for c in CORNERS:
        b = b.union(cyl_x(COL_D, -X_REAR, X_REAR, c).intersect(shell(X_REAR, 0)))
    for c in CORNERS:
        b = b.cut(cyl_x(M3_CLEAR, WALL - X_REAR, X_REAR - WALL, c))      # 4 vis M3 x 30 vers le corps
    b = b.cut(box(X_REAR + 4, 0, IN_Y[1], OUT_Y[1], CABLE_Z[0], CABLE_Z[1]))   # passage du câble réseau, sur le côté
    return b


def couvercle_avant():
    b = shell(X_FRONT, X_FRONT + WALL)
    for c in CORNERS:
        b = b.cut(cyl_x(M3_CLEAR, WALL, X_FRONT, c))                     # 4 vis M3 x 10
    return b


def bobine():
    """Bobine en cloche, repère local : x = 0 sur sa face arrière.

    Une jante étroite porte la gorge ; un manchon mince la relie au fond, qui se pose sur la
    face tournante du moteur. Un téton la centre dans l'alésage de 6 mm de cette face."""
    depth = X_HUB + DISC_T - X_REEL
    seat = depth - DISC_T                                                # plan d'appui sur le moyeu
    r = cyl_x(DRUM_D, REEL_W, 0).union(cyl_x(BORE_D + 6, depth, 0))      # jante + manchon
    r = r.union(cyl_x(FLANGE_D, 2, 0)).union(cyl_x(FLANGE_D, 2, REEL_W - 2))   # deux joues
    r = r.cut(cyl_x(BORE_D, seat, 0))                                    # logement du carter
    r = r.union(cyl_x(HUB_BORE - FIT, SPIGOT_H, seat - SPIGOT_H))        # téton de centrage
    for a in range(4):                                                   # 4 vis M3 x 5 sur Ø 20
        ang = a * math.pi / 2
        r = r.cut(cyl_x(M3_CLEAR, depth, 0, (HUB_PCD / 2 * math.cos(ang), HUB_PCD / 2 * math.sin(ang))))
    r = r.cut(cyl_x(1.0, 2, 0, (DRUM_D / 2 + 1.5, 0)))                   # trou d'ancrage du fil dans une joue
    return r


def motor_shape():
    """Le moteur, figuré par son enveloppe : Ø 41,8 x 33,5 avec l'alésage de 6 mm en bout."""
    return cyl_x(MOTOR_D, MOTOR_L, X_MOTOR).cut(cyl_x(HUB_BORE, 3, X_MOTOR + MOTOR_L - 3))


# Pièces à imprimer : nom -> (fonction, direction d'impression, matière conseillée)
PRINTED = {
    "corps": (corps, "cloison sur le plateau", "nylon PA12 (MJF) ou PETG"),
    "capot_arriere": (capot_arriere, "fond sur le plateau", "nylon PA12 (MJF) ou PETG"),
    "couvercle_avant": (couvercle_avant, "à plat", "nylon PA12 (MJF) ou PETG"),
    "bobine": (bobine, "fond de la cloche sur le plateau", "résine (SLA), surface lisse"),
}


def build():
    eye = (cq.Workplane("XY").workplane(offset=OUT_Z[0] - 1).center(X_LINE, EYE_Y)
           .circle(EYELET_OD / 2).circle(1.25).extrude(WALL + 2))
    return {
        "corps": (corps(), "boitier"),
        "capot_arriere": (capot_arriere(), "capot"),
        "couvercle_avant": (couvercle_avant(), "capot"),
        "moteur": (motor_shape(), "moteur"),
        "bobine": (bobine().translate((X_REEL, 0, 0)), "bobine"),
        "oeillet": (eye, "oeillet"),
        "ecrou_m10": (cq.Workplane("XY").workplane(offset=IN_Z[1] - BOSS_H + 2.2).center(SPIGOT_X, 0)
                      .polygon(6, NUT_AF * 2 / math.sqrt(3)).circle(5).extrude(NUT_H), "oeillet"),
        "ecrou_m10_cote": (cq.Workplane("XY").polygon(6, NUT_AF * 2 / math.sqrt(3)).circle(5).extrude(NUT_H)
                           .rotate((0, 0, 0), (1, 0, 0), 90)
                           .translate((SPIGOT_X, IN_Y[0] + BOSS_H - 2.2, 0)), "oeillet"),
        "spigot": (cq.Workplane("XY").workplane(offset=OUT_Z[1]).center(SPIGOT_X, 0).circle(11).extrude(4)
                   .faces(">Z").workplane().circle(8).extrude(21.4)
                   .union(cq.Workplane("XY").workplane(offset=OUT_Z[1] - SPIGOT_THREAD).center(SPIGOT_X, 0)
                          .circle(4.9).extrude(SPIGOT_THREAD)), "oeillet"),
        # Cartes, aux cotes relevées sur les fiches, collées au dos de la cloison
        "carte_esp32": (box(-17, -1, -40, 40, 22, 50), "carte"),            # Olimex ESP32-POE, 80 x 28
        "commande_moteur": (box(-9, -1, -50, -24, -12, 9), "carte"),        # SimpleFOC Mini, 26 x 21
        "module_poe": (box(-19, -1, -12, 26, -64, -26), "carte"),           # séparateur PoE 12 V, 38 x 38 x 18
        "convertisseur_5v": (box(-9, -1, -40, -18, -50, -33), "carte"),     # 12 V vers 5 V, 22 x 17
    }


if __name__ == "__main__":
    out = os.path.join(HERE, "export")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):                                            # on repart d'un dossier propre
        os.remove(os.path.join(out, f))
    parts = build()
    asm = cq.Assembly(name="treuil_micro")
    for name, (shape, color) in parts.items():
        asm.add(shape, name=name, color=cq.Color(*COLORS[color]))
    asm.save(os.path.join(out, "treuil.step"))
    for name in PRINTED:
        shape = parts[name][0] if name != "bobine" else bobine()
        cq.exporters.export(shape, os.path.join(out, f"{name}.step"))
        cq.exporters.export(shape, os.path.join(out, f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(asm.toCompound(), os.path.join(out, "treuil.svg"),
                        opt={"width": 900, "height": 700, "projectionDir": (1.0, -0.8, 0.6),
                             "showAxes": False, "strokeWidth": 0.3, "showHidden": True})

    print(f"Course {TRAVEL_M:.0f} m -> {TURNS:.0f} tours ; fil par tour {LINE_PER_TURN:.1f} mm")
    print(f"Rangs de fil dans la gorge : {TURNS * LINE_D / SLOT_W:.1f} ; angle du fil vers l'oeillet {FLEET_DEG:.2f} degrés")
    depth = (X_FRONT + WALL) - (X_REAR - WALL)
    print(f"Boîtier fermé : {OUT_Y[1] - OUT_Y[0]:.0f} x {OUT_Z[1] - OUT_Z[0]:.0f} x {depth:.1f} mm "
          f"(+ 25 mm de spigot au-dessus)")
    tip = OUT_Z[1] - SPIGOT_THREAD                                       # bas du filetage M10 dans le boîtier
    print(f"Spigot : le filetage traverse tout l'écrou et s'arrête à {tip - (BORE_D + 6) / 2:.1f} mm "
          f"de la cloche tournante (dessus) et {-(OUT_Y[0] + SPIGOT_THREAD) - (BORE_D + 6) / 2:.1f} mm (côté)")
    for name in PRINTED:
        s = (parts[name][0] if name != "bobine" else bobine()).val()
        bb = s.BoundingBox()
        print(f"  {name:16s} {bb.ylen:6.1f} x {bb.zlen:6.1f} x {bb.xlen:5.1f} mm  {s.Volume() / 1000:6.1f} cm3  "
              f"solide valide : {'oui' if s.isValid() else 'NON'}")
    r = bobine().val()
    inertia = cq.Shape.matrixOfInertia(r)[0][0] * 1.2e-12                # autour de l'axe X, kg·m²
    print(f"Inertie de la bobine : {inertia:.1e} kg.m2 (réglage INERTIA_KGM2 du firmware : bobine + rotor)")
    names = list(parts)
    ok_pairs = {("corps", "oeillet"), ("ecrou_m10", "spigot")}           # œillet serti, filetage dans l'écrou
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) not in ok_pairs and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-2]
    print("Interférences :", clash or "aucune")
    print(f"Jeu entre la bobine et le moteur : {(BORE_D - MOTOR_D) / 2:.1f} mm au rayon, "
          f"{X_HUB - X_MOTOR - MOTOR_L:.1f} mm en bout (tolérance de longueur du moteur)")
