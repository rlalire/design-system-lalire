"""Bloc treuil micro — maquette 3D paramétrique (CadQuery).

    pip install cadquery
    python3 treuil.py

Pour des objets de quelques grammes sur un fil très fin. Moteur de gimbal CubeMars G35
(encodeur intégré, carter fixe), en prise directe : la bobine est une cloche vissée sur le
moyeu tournant du moteur et entoure son carter. Fil qui sort par un œillet céramique fixe. Tout tient dans un boîtier
fermé : moteur, bobine et électronique.

Produit dans ./export : l'assemblage (treuil.step), le boîtier, ses deux couvercles et
la bobine (STEP et STL).

Les perçages sont relevés sur le fichier 3D du fabricant (fabricant/G35_sans_driver.stp),
qui est repris tel quel dans l'assemblage : 4 vis M3 sur un cercle de 25 mm côté cloison,
4 vis M3 sur un cercle de 15 mm côté bobine, sortie des fils à 135 degrés. Les logements
des cartes restent à ajuster sur les pièces achetées.
Cotes en millimètres. X = axe du moteur, Z = vertical, le fil sort vers le bas.
"""
import math
import os
import cadquery as cq

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 80.0          # diamètre de la bobine, fond de gorge
LINE_D = 0.05          # diamètre du fil
SLOT_W = 2.0           # largeur de la gorge
SLOT_DEPTH = 6.0
TRAVEL_M = 10.0

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = TRAVEL_M * 1000 / LINE_PER_TURN
FLANGE_D = DRUM_D + 2 * SLOT_DEPTH
REEL_W = SLOT_W + 4.0                              # deux joues de 2 mm
WALL, PART_T = 2.5, 3.0                            # parois et cloison porte-moteur
MOTOR_D, MOTOR_L = 49.8, 31.11                     # CubeMars G35, relevé sur le fichier 3D du fabricant
BASE_PCD, ROTOR_PCD, ROTOR_BORE = 25.0, 15.0, 6.5  # 4 x M3 côté cloison, 4 x M3 côté moyeu, arbre creux
WIRES_R, WIRES_DEG = 16.6, 135.0                   # sortie des fils sur la face arrière du moteur
VENDOR_STEP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fabricant", "G35_sans_driver.stp")
BORE_D = 56.0                                      # la cloche de la bobine entoure le carter (jeu de 3 mm)
X_MOTOR = PART_T                                   # le moteur est vissé sur la cloison
X_REEL = X_MOTOR + 4.0                             # face arrière de la bobine
X_DISC = X_MOTOR + MOTOR_L                         # face tournante du moteur = fond de la cloche
X_LINE = X_REEL + REEL_W / 2                       # plan du fil
X_FRONT = X_DISC + 2.5 + 3.5                       # face intérieure du couvercle avant
X_REAR = -14.0                                     # face intérieure du couvercle arrière (cartes)
IN_Y, IN_Z = (-52.0, 55.0), (-66.0, 52.0)          # intérieur du boîtier
EYE_Y = DRUM_D / 2 + LINE_D / 2                    # le fil descend à la verticale du bord de la bobine
FLEET_DEG = math.degrees(math.atan((SLOT_W / 2) / abs(IN_Z[0])))

COLORS = {"boitier": (0.20, 0.20, 0.22), "bobine": (0.85, 0.65, 0.15), "acier": (0.65, 0.67, 0.70),
          "moteur": (0.12, 0.12, 0.13), "carte": (0.18, 0.55, 0.34), "oeillet": (0.95, 0.95, 0.92)}


def cyl_x(d, length, x, yz=(0.0, 0.0)):
    return cq.Workplane("YZ").workplane(offset=x).center(*yz).circle(d / 2).extrude(length)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def body():
    """Corps du boîtier : un cadre et une cloison centrale qui porte le moteur."""
    b = box(X_REAR, X_FRONT, IN_Y[0] - WALL, IN_Y[1] + WALL, IN_Z[0] - WALL, IN_Z[1] + WALL)
    b = b.edges("|X").fillet(6)
    b = b.cut(box(PART_T, X_FRONT, IN_Y[0], IN_Y[1], IN_Z[0], IN_Z[1]).edges("|X").fillet(4))   # chambre du fil
    b = b.cut(box(X_REAR, 0, IN_Y[0], IN_Y[1], IN_Z[0], IN_Z[1]).edges("|X").fillet(4))         # chambre technique
    b = b.cut(cyl_x(10.5, PART_T, 0))                                                           # accès à l'arbre creux
    for a in range(4):                                                                          # 4 vis M3 x 6 sur Ø 25
        ang = a * math.pi / 2
        b = b.cut(cyl_x(3.4, PART_T, 0, (BASE_PCD / 2 * math.cos(ang), BASE_PCD / 2 * math.sin(ang))))
    for d in (-10, 10):                                                                         # passage des fils du moteur
        ang = math.radians(WIRES_DEG + d)
        b = b.cut(cyl_x(8, PART_T, 0, (WIRES_R * math.cos(ang), WIRES_R * math.sin(ang))))
    eye = (cq.Workplane("XY").workplane(offset=IN_Z[0] - WALL).center(X_LINE, EYE_Y)
           .circle(3.05).extrude(WALL))                                                         # logement de l'œillet
    b = b.cut(eye)
    rj = box(X_REAR, -4, -8, 9, IN_Z[1], IN_Z[1] + WALL)                                        # passage du câble réseau
    b = b.cut(rj)
    for y in (IN_Y[0] + 12, IN_Y[1] - 12):                                                      # 2 pattes d'accroche
        lug = box(-6, 6, y - 8, y + 8, IN_Z[1] + WALL, IN_Z[1] + WALL + 12)
        hole = cyl_x(5.2, 12, -6, (y, IN_Z[1] + WALL + 6))
        b = b.union(lug).cut(hole)
    return b


def cover(x):
    return (box(x, x + WALL, IN_Y[0] - WALL, IN_Y[1] + WALL, IN_Z[0] - WALL, IN_Z[1] + WALL)
            .edges("|X").fillet(6))


def reel():
    """Bobine en cloche, repère local : x = 0 sur sa face arrière.

    Une jante étroite porte la gorge ; un manchon mince la relie au fond, vissé sur la face
    tournante du moteur. Le fil s'y range sur un ou deux rangs."""
    depth = X_DISC + 2.5 - X_REEL                                                               # longueur totale
    r = cyl_x(DRUM_D, REEL_W, 0).union(cyl_x(BORE_D + 6, depth, 0))                             # jante + manchon
    r = r.union(cyl_x(BORE_D + 6, 2.5, depth - 2.5))
    r = r.union(cyl_x(FLANGE_D, 2, 0)).union(cyl_x(FLANGE_D, 2, REEL_W - 2))                    # deux joues
    r = r.cut(cyl_x(BORE_D, depth - 2.5, 0))                                                    # logement du moteur
    r = r.cut(cyl_x(ROTOR_BORE, depth, 0))                                                      # arbre creux
    for a in range(4):                                                                          # 4 vis M3 x 8 sur Ø 15
        ang = a * math.pi / 2
        r = r.cut(cyl_x(3.4, depth, 0, (ROTOR_PCD / 2 * math.cos(ang), ROTOR_PCD / 2 * math.sin(ang))))
    anchor = (cq.Workplane("XZ").workplane(offset=-(FLANGE_D / 2 + 1)).center(1, 0)
              .circle(0.5).extrude(SLOT_DEPTH + 3))                                             # trou d'ancrage dans une joue
    return r.cut(anchor)


def motor_shape():
    """Le moteur : le fichier du fabricant s'il est présent, sinon un simple cylindre."""
    if os.path.exists(VENDOR_STEP):
        # Dans le fichier, le moyeu est en x = 0 ; on pose la face arrière sur la cloison
        m = cq.importers.importStep(VENDOR_STEP)
        return m.translate((X_MOTOR - m.val().BoundingBox().xmin, 0, 0))
    return cyl_x(MOTOR_D, MOTOR_L - 4, X_MOTOR).union(cyl_x(20, 4, X_MOTOR + MOTOR_L - 4))


def build():
    eye = (cq.Workplane("XY").workplane(offset=IN_Z[0] - WALL - 1).center(X_LINE, EYE_Y)
           .circle(3.0).circle(1.25).extrude(WALL + 2))
    return {
        "boitier": (body(), "boitier"),
        "moteur": (motor_shape(), "moteur"),
        "bobine": (reel().translate((X_REEL, 0, 0)), "bobine"),
        "oeillet": (eye, "oeillet"),
        "carte_reseau": (box(-12, -2, -40, 36, 22, 50), "carte"),
        "driver_moteur": (box(-10, -2, -48, -22, -15, 11), "carte"),
        "alimentation_poe": (box(-12, -2, -48, 22, -62, -34), "carte"),
    }


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
    os.makedirs(out, exist_ok=True)
    parts = build()
    asm = cq.Assembly(name="treuil_micro")
    for name, (shape, color) in parts.items():
        asm.add(shape, name=name, color=cq.Color(*COLORS[color]))
    asm.save(os.path.join(out, "treuil.step"))
    cq.exporters.export(parts["boitier"][0], os.path.join(out, "boitier.step"))
    cq.exporters.export(cover(X_FRONT), os.path.join(out, "couvercle_avant.step"))
    cq.exporters.export(cover(X_REAR - WALL), os.path.join(out, "couvercle_arriere.step"))
    r = reel()
    cq.exporters.export(r, os.path.join(out, "bobine.step"))
    cq.exporters.export(r, os.path.join(out, "bobine.stl"), tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(asm.toCompound(), os.path.join(out, "treuil.svg"),
                        opt={"width": 900, "height": 700, "projectionDir": (1.0, -0.8, 0.6),
                             "showAxes": False, "strokeWidth": 0.3, "showHidden": True})

    bb = parts["boitier"][0].val().BoundingBox()
    depth = (X_FRONT + WALL) - (X_REAR - WALL)
    vol = r.val().Volume() / 1000
    print(f"Course {TRAVEL_M:.0f} m -> {TURNS:.0f} tours ; fil par tour {LINE_PER_TURN:.1f} mm")
    print(f"Rangs de fil dans la gorge : {TURNS * LINE_D / SLOT_W:.1f} ; angle du fil vers l'oeillet {FLEET_DEG:.2f} degrés")
    print(f"Bobine : diamètre {FLANGE_D:.0f} mm, {vol:.1f} cm3 (~{vol * 1.2:.0f} g en résine)")
    inertia = cq.Shape.matrixOfInertia(r.val())[0][0] * 1.2e-12            # autour de l'axe X, kg·m²
    print(f"Inertie de la bobine : {inertia:.1e} kg.m2 (réglage INERTIA_KGM2 du firmware : bobine + rotor)")
    print(f"Boîtier fermé : {bb.ylen:.0f} x {bb.zlen:.0f} x {depth:.0f} mm (largeur x hauteur avec pattes x épaisseur)")
    names = list(parts)
    ok_pairs = {("boitier", "oeillet")}                       # l'œillet est serti dans le fond
    gap = parts["boitier"][0].intersect(parts["moteur"][0]).val().Volume()
    print("Moteur sans interférence avec la cloison :", "oui" if gap < 1e-3 else f"NON ({gap:.1f} mm3)")
    hub = parts["bobine"][0].intersect(parts["moteur"][0]).val().Volume()
    print("Bobine posée sur le moyeu sans interférence :", "oui" if hub < 1e-3 else f"NON ({hub:.1f} mm3)")
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) not in ok_pairs and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-3]
    print("Interférences :", clash or "aucune")
