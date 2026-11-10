"""Bloc treuil — maquette 3D paramétrique (CadQuery).

    pip install cadquery
    python3 treuil.py

Produit dans ./export : l'assemblage complet (treuil.step), les pièces à faire usiner
(flasques, tambour, chariot) et une vue filaire (treuil.svg).

C'est une maquette d'implantation : elle fixe les volumes, les entraxes et
l'encombrement. Les perçages de fixation, les logements de roulements et les
tolérances restent à dessiner une fois les composants achetés et mesurés.
Toutes les cotes sont en millimètres.
"""
import math
import os
import cadquery as cq

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 40.0          # diamètre du tambour, fond de fil
LINE_D = 1.0           # diamètre du fil
LW_PITCH = 1.2         # avance du guide-fil par tour
TRAVEL_M = 10.0        # course de fil utile, en mètres
BELT_RATIO = 2.0
BELT_PITCH = 3.0       # courroie HTD 3M
MOTOR_TEETH = 20

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = TRAVEL_M * 1000 / LINE_PER_TURN + 5          # 5 tours morts de sécurité
DRUM_W = math.ceil(TURNS * LW_PITCH / 5) * 5 + 5     # largeur utile entre joues
FLANGE_D, FLANGE_T = DRUM_D + 30, 4.0
PLATE_T = 8.0
INNER_W = max(DRUM_W + 2 * FLANGE_T + 12, 170.0)     # entre flasques (le servo fait ~150)
PLATE_Y, PLATE_Z = (-110.0, 95.0), (-70.0, 70.0)     # contour des flasques
DRUM_YZ = (20.0, 10.0)                               # axe du tambour
MOTOR_YZ = (-65.0, -20.0)                            # axe du servo
LW_Y = 72.0                                          # plan du guide-fil
SHAFT_D = 12.0
MOTOR_FLANGE, MOTOR_LEN = 60.0, 150.0
P_MOTOR_D = MOTOR_TEETH * BELT_PITCH / math.pi
P_DRUM_D = P_MOTOR_D * BELT_RATIO
CENTER = math.dist(DRUM_YZ, MOTOR_YZ)
X0, X1 = 0.0, INNER_W                                # faces intérieures des flasques


COLORS = {"lightgray": (0.80, 0.80, 0.80), "silver": (0.65, 0.67, 0.70), "dimgray": (0.30, 0.30, 0.32),
          "black": (0.08, 0.08, 0.08), "gold": (0.85, 0.65, 0.15), "firebrick": (0.70, 0.13, 0.13),
          "royalblue": (0.25, 0.41, 0.88), "seagreen": (0.18, 0.55, 0.34)}


def cyl_x(d, length, x, yz):
    """Cylindre d'axe X, partant de x."""
    return cq.Workplane("YZ").workplane(offset=x).center(*yz).circle(d / 2).extrude(length)


def box(x, y, z, sx, sy, sz):
    return cq.Workplane("XY").box(sx, sy, sz, centered=False).translate((x, y, z))


def plate(x):
    w, h = PLATE_Y[1] - PLATE_Y[0], PLATE_Z[1] - PLATE_Z[0]
    p = (cq.Workplane("YZ").workplane(offset=x)
         .center((PLATE_Y[0] + PLATE_Y[1]) / 2, 0).rect(w, h).extrude(PLATE_T)
         .edges("|X").fillet(8))
    holes = [(DRUM_YZ, 28.0),                        # roulement du tambour (6001 : 28 ext.)
             (MOTOR_YZ, 50.0),                       # centrage du servo
             ((LW_Y, DRUM_YZ[1]), 10.0),             # vis du guide-fil
             ((LW_Y, DRUM_YZ[1] + 25), 6.0), ((LW_Y, DRUM_YZ[1] - 25), 6.0)]  # colonnes de guidage
    holes += [((y, z), 8.0) for y in (PLATE_Y[0] + 12, PLATE_Y[1] - 12)
              for z in (PLATE_Z[0] + 12, PLATE_Z[1] - 12)]                    # entretoises
    for yz, d in holes:
        p = p.cut(cyl_x(d, PLATE_T, x, yz))
    return p


def drum():
    x = (INNER_W - DRUM_W) / 2 - FLANGE_T
    d = cyl_x(DRUM_D, DRUM_W + 2 * FLANGE_T, x, DRUM_YZ)
    d = d.union(cyl_x(FLANGE_D, FLANGE_T, x, DRUM_YZ))
    d = d.union(cyl_x(FLANGE_D, FLANGE_T, x + FLANGE_T + DRUM_W, DRUM_YZ))
    return d.cut(cyl_x(SHAFT_D, DRUM_W + 2 * FLANGE_T, x, DRUM_YZ))


def carriage(x):
    c = box(x - 12, LW_Y - 9, DRUM_YZ[1] - 32, 24, 18, 64)
    c = c.union(box(x - 6, LW_Y + 9, DRUM_YZ[1] + DRUM_D / 2 - 6, 12, 10, 12))   # bras de l'œillet
    for dz, d in ((0, 8.0), (25, 6.0), (-25, 6.0)):
        c = c.cut(cyl_x(d, 24, x - 12, (LW_Y, DRUM_YZ[1] + dz)))
    eye = (cq.Workplane("XY").workplane(offset=DRUM_YZ[1] + DRUM_D / 2 - 6)
           .center(x, LW_Y + 14).circle(2).extrude(12))                           # œillet céramique
    return c.cut(eye)


parts = {
    "flasque_gauche": (plate(X0 - PLATE_T), "lightgray"),
    "flasque_droit": (plate(X1), "lightgray"),
    "tambour": (drum(), "gold"),
    "axe": (cyl_x(SHAFT_D, INNER_W + 2 * PLATE_T + 80, X0 - PLATE_T - 30, DRUM_YZ), "silver"),
    "servo": (box(X0, MOTOR_YZ[0] - MOTOR_FLANGE / 2, MOTOR_YZ[1] - MOTOR_FLANGE / 2,
                  MOTOR_LEN, MOTOR_FLANGE, MOTOR_FLANGE)
              .union(cyl_x(14, PLATE_T + 28, X0 - PLATE_T - 28, MOTOR_YZ)), "dimgray"),
    "poulie_moteur": (cyl_x(P_MOTOR_D, 12, X0 - PLATE_T - 20, MOTOR_YZ), "black"),
    "poulie_tambour": (cyl_x(P_DRUM_D, 12, X0 - PLATE_T - 20, DRUM_YZ), "black"),
    "frein": (cyl_x(56, 32, X1 + PLATE_T + 2, DRUM_YZ), "firebrick"),
    "vis_guide": (cyl_x(5, INNER_W + PLATE_T, X0, (LW_Y, DRUM_YZ[1])), "silver"),
    "colonne_haute": (cyl_x(6, INNER_W, X0, (LW_Y, DRUM_YZ[1] + 25)), "silver"),
    "colonne_basse": (cyl_x(6, INNER_W, X0, (LW_Y, DRUM_YZ[1] - 25)), "silver"),
    "moteur_guide": (box(X1 + PLATE_T, LW_Y - 14, DRUM_YZ[1] - 14, 45, 28, 28), "dimgray"),
    "chariot": (carriage((INNER_W - DRUM_W) / 2 + DRUM_W * 0.3), "royalblue"),
    "electronique": (box(X0 + 10, PLATE_Y[0] + 5, 25, INNER_W - 20, 70, 35), "seagreen"),
}
for i, (y, z) in enumerate((y, z) for y in (PLATE_Y[0] + 12, PLATE_Y[1] - 12)
                           for z in (PLATE_Z[0] + 12, PLATE_Z[1] - 12)):
    parts[f"entretoise_{i + 1}"] = (cyl_x(10, INNER_W, X0, (y, z)), "silver")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
    os.makedirs(out, exist_ok=True)
    asm = cq.Assembly(name="treuil")
    for name, (shape, color) in parts.items():
        asm.add(shape, name=name, color=cq.Color(*COLORS[color]))
    asm.save(os.path.join(out, "treuil.step"))
    for name in ("flasque_gauche", "flasque_droit", "tambour", "chariot"):
        cq.exporters.export(parts[name][0], os.path.join(out, f"{name}.step"))
    cq.exporters.export(asm.toCompound(), os.path.join(out, "treuil.svg"),
                        opt={"width": 1000, "height": 700, "projectionDir": (-0.9, 0.8, 1.3),
                             "showAxes": False, "strokeWidth": 0.4, "showHidden": False})

    bb = asm.toCompound().BoundingBox()
    print(f"Course {TRAVEL_M:.0f} m -> {TURNS:.0f} tours, tambour utile {DRUM_W:.0f} mm de large")
    print(f"Fil par tour {LINE_PER_TURN:.2f} mm ; entraxe courroie {CENTER:.1f} mm ; "
          f"poulies {MOTOR_TEETH}/{int(MOTOR_TEETH * BELT_RATIO)} dents")
    print(f"Encombrement hors tout : {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm")
    # Contrôles d'interférence entre les volumes principaux
    names = ["tambour", "servo", "chariot", "electronique", "frein", "moteur_guide", "poulie_moteur", "poulie_tambour"]
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) != ("servo", "poulie_moteur")          # la poulie est sur l'arbre du servo
             and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-3]
    print("Interférences :", clash or "aucune")
