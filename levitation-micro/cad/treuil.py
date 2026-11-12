"""Bloc treuil micro — pièces du prototype à imprimer en 3D (CadQuery).

    pip install cadquery
    python3 treuil.py

Pour des objets de quelques grammes sur un fil très fin. Moteur de gimbal CubeMars G35
(encodeur intégré, carter fixe) en prise directe : la bobine est une cloche vissée sur le
moyeu tournant du moteur et entoure son carter. Le fil sort par un œillet céramique fixe.

Quatre pièces à imprimer, toutes posées à plat et sans supports :
  corps            cloison porte-moteur + chambre du fil + pattes d'accroche
  capot_arriere    bac qui ferme la chambre de l'électronique
  couvercle_avant  plaque qui ferme la chambre du fil
  bobine           cloche à gorge (à imprimer en résine pour une surface lisse)

Produit dans ./export, pour chaque pièce, un fichier STEP et un fichier STL, plus
l'assemblage complet (treuil.step). Les cotes du moteur viennent du fichier 3D du
fabricant (fabricant/G35_sans_driver.stp), repris tel quel dans l'assemblage.

Cotes en millimètres. X = axe du moteur, Z = vertical, le fil sort vers le bas.
"""
import math
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR_STEP = os.path.join(HERE, "fabricant", "G35_sans_driver.stp")

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 80.0          # diamètre de la bobine, fond de gorge
LINE_D = 0.05          # diamètre du fil
SLOT_W = 2.0           # largeur de la gorge
SLOT_DEPTH = 6.0
TRAVEL_M = 10.0

# ---------- Moteur CubeMars G35 (fichier 3D du fabricant) ----------
MOTOR_D, MOTOR_L = 49.8, 31.11
BASE_PCD = 25.0                                    # 4 x M3 à l'arrière, profondeur 4
HUB_D, HUB_PCD, HUB_BORE = 20.0, 15.0, 6.5         # moyeu avant : 4 x M3, profondeur 6, arbre creux
HUB_PROUD = 1.0                                    # le moyeu dépasse de 1 mm de l'épaulement de 32 mm
WIRES_R, WIRES_DEG = 16.6, 135.0                   # sortie des fils sur la face arrière

# ---------- Jeux et visserie ----------
M3_CLEAR, M3_PILOT = 3.4, 2.6                      # trou de passage / avant-trou où la vis M3 forme son filet
FIT = 0.2                                          # jeu d'emboîtement des pièces imprimées
EYELET_OD = 6.0                                    # œillet céramique (à ajuster à la pièce achetée)

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = TRAVEL_M * 1000 / LINE_PER_TURN
FLANGE_D = DRUM_D + 2 * SLOT_DEPTH
REEL_W = SLOT_W + 4.0                              # deux joues de 2 mm
WALL, PART_T, DISC_T = 2.5, 3.0, 3.5
BORE_D = 56.0                                      # la cloche entoure le carter (jeu de 3 mm au rayon)
X_MOTOR = PART_T                                   # le moteur est vissé à plat sur la cloison
X_REEL = X_MOTOR + 4.0                             # face arrière de la bobine
X_HUB = X_MOTOR + MOTOR_L                          # face du moyeu = appui de la bobine
X_LINE = X_REEL + REEL_W / 2                       # plan du fil
X_FRONT = round(X_HUB + DISC_T + 3.6, 1)           # face intérieure du couvercle avant
X_REAR = -18.0                                     # fond de la chambre de l'électronique
IN_Y, IN_Z = (-52.0, 55.0), (-66.0, 52.0)          # intérieur du boîtier
OUT_Y, OUT_Z = (IN_Y[0] - WALL, IN_Y[1] + WALL), (IN_Z[0] - WALL, IN_Z[1] + WALL)
EYE_Y = DRUM_D / 2 + LINE_D / 2                    # le fil descend à la verticale du bord de la bobine
FLEET_DEG = math.degrees(math.atan((SLOT_W / 2) / abs(IN_Z[0])))
COL_D = 9.0                                        # colonnes de vissage dans les quatre angles
CORNERS = [(y, z) for y in (IN_Y[0] + 4.5, IN_Y[1] - 4.5) for z in (IN_Z[0] + 4.5, IN_Z[1] - 4.5)]
LUGS_Y = (IN_Y[0] + 12, IN_Y[1] - 12)              # pattes d'accroche
CABLE_Y = (-8.0, 9.0)                              # passage du câble réseau dans le capot

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
    b = b.cut(cyl_x(10.5, PART_T, 0))                                    # accès à l'arbre creux
    for a in range(4):                                                   # 4 vis M3 x 6 du moteur, sur Ø 25
        ang = a * math.pi / 2
        b = b.cut(cyl_x(M3_CLEAR, PART_T, 0, (BASE_PCD / 2 * math.cos(ang), BASE_PCD / 2 * math.sin(ang))))
    for d in (-10, 10):                                                  # passage des fils du moteur
        ang = math.radians(WIRES_DEG + d)
        b = b.cut(cyl_x(8, PART_T, 0, (WIRES_R * math.cos(ang), WIRES_R * math.sin(ang))))
    eye = (cq.Workplane("XY").workplane(offset=OUT_Z[0]).center(X_LINE, EYE_Y)
           .circle((EYELET_OD + FIT) / 2).extrude(WALL))                 # logement de l'œillet
    b = b.cut(eye)
    for y in LUGS_Y:                                                     # pattes d'accroche, trou de 5,2
        b = b.union(box(0, 12, y - 8, y + 8, OUT_Z[1], OUT_Z[1] + 12))
        b = b.cut(cyl_x(5.2, 12, 0, (y, OUT_Z[1] + 6)))
    return b


def capot_arriere():
    """Bac qui ferme la chambre de l'électronique ; son fond sert de face d'impression."""
    b = shell(X_REAR - WALL, 0).cut(cavity(X_REAR, 0))
    for c in CORNERS:
        b = b.union(cyl_x(COL_D, -X_REAR, X_REAR, c).intersect(shell(X_REAR, 0)))
    for c in CORNERS:
        b = b.cut(cyl_x(M3_CLEAR, WALL - X_REAR, X_REAR - WALL, c))      # 4 vis M3 x 30 vers le corps
    b = b.cut(box(X_REAR + 4, 0, CABLE_Y[0], CABLE_Y[1], IN_Z[1], OUT_Z[1]))   # passage du câble réseau
    return b


def couvercle_avant():
    b = shell(X_FRONT, X_FRONT + WALL)
    for c in CORNERS:
        b = b.cut(cyl_x(M3_CLEAR, WALL, X_FRONT, c))                     # 4 vis M3 x 10
    return b


def bobine():
    """Bobine en cloche, repère local : x = 0 sur sa face arrière.

    Une jante étroite porte la gorge ; un manchon mince la relie au fond, qui se pose sur le
    moyeu du moteur. Une petite collerette centre la bobine sur ce moyeu."""
    depth = X_HUB + DISC_T - X_REEL
    seat = depth - DISC_T                                                # plan d'appui sur le moyeu
    r = cyl_x(DRUM_D, REEL_W, 0).union(cyl_x(BORE_D + 6, depth, 0))      # jante + manchon
    r = r.union(cyl_x(FLANGE_D, 2, 0)).union(cyl_x(FLANGE_D, 2, REEL_W - 2))   # deux joues
    r = r.cut(cyl_x(BORE_D, seat, 0))                                    # logement du carter
    collar = cyl_x(HUB_D + 4, 0.6, seat - 0.6).cut(cyl_x(HUB_D + FIT, 0.6, seat - 0.6))
    r = r.union(collar)                                                  # collerette de centrage
    r = r.cut(cyl_x(HUB_BORE, depth, 0))                                 # arbre creux
    for a in range(4):                                                   # 4 vis M3 x 8 sur Ø 15
        ang = a * math.pi / 2
        r = r.cut(cyl_x(M3_CLEAR, depth, 0, (HUB_PCD / 2 * math.cos(ang), HUB_PCD / 2 * math.sin(ang))))
    r = r.cut(cyl_x(1.0, 2, 0, (DRUM_D / 2 + 1.5, 0)))                   # trou d'ancrage du fil dans une joue
    return r


def motor_shape():
    """Le moteur : le fichier du fabricant s'il est présent, sinon un simple cylindre."""
    if os.path.exists(VENDOR_STEP):
        m = cq.importers.importStep(VENDOR_STEP)                         # moyeu en x = 0 dans le fichier
        return m.translate((X_MOTOR - m.val().BoundingBox().xmin, 0, 0))
    return cyl_x(MOTOR_D, MOTOR_L - 4, X_MOTOR).union(cyl_x(HUB_D, 4, X_MOTOR + MOTOR_L - 4))


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
        # Cartes : volumes indicatifs, collées au dos de la cloison
        "carte_reseau": (box(-17, -1, -40, 36, 22, 50), "carte"),
        "driver_moteur": (box(-9, -1, -48, -22, -15, 11), "carte"),
        "alimentation_poe": (box(-13, -1, -38, 32, -62, -34), "carte"),
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
          f"(+ 12 mm de pattes d'accroche en hauteur)")
    for name in PRINTED:
        s = (parts[name][0] if name != "bobine" else bobine()).val()
        bb = s.BoundingBox()
        print(f"  {name:16s} {bb.ylen:6.1f} x {bb.zlen:6.1f} x {bb.xlen:5.1f} mm  {s.Volume() / 1000:6.1f} cm3  "
              f"solide valide : {'oui' if s.isValid() else 'NON'}")
    r = bobine().val()
    inertia = cq.Shape.matrixOfInertia(r)[0][0] * 1.2e-12                # autour de l'axe X, kg·m²
    print(f"Inertie de la bobine : {inertia:.1e} kg.m2 (réglage INERTIA_KGM2 du firmware : bobine + rotor)")
    names = list(parts)
    ok_pairs = {("corps", "oeillet")}                                    # l'œillet est serti dans le fond
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) not in ok_pairs and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-2]
    print("Interférences :", clash or "aucune")
    hub_gap = HUB_PROUD - 0.6                                            # la collerette fait 0,6 mm de haut
    print(f"Jeu entre la collerette de la bobine et l'épaulement du moteur : {hub_gap:.1f} mm")
