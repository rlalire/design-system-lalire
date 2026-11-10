"""Bloc treuil en prise directe — maquette 3D paramétrique (CadQuery).

    pip install cadquery
    python3 treuil.py

Le tambour est monté directement sur l'arbre du servo, sans courroie.
Produit dans ./export : l'assemblage (treuil.step), la bobine à imprimer
(bobine.stl et bobine.step, avec sa gorge en hélice), le chariot, les deux
flasques et une vue filaire (treuil.svg).

Maquette d'implantation : volumes, entraxes, encombrement. Les perçages de
fixation et les tolérances restent à ajuster sur les composants réels.
Toutes les cotes sont en millimètres ; l'axe du moteur est l'axe X.
"""
import math
import os
import cadquery as cq

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 30.0          # diamètre de la bobine, fond de fil
LINE_D = 1.0           # diamètre du fil
PITCH = 1.2            # pas de la gorge = avance du guide-fil par tour
TRAVEL_M = 10.0        # course de fil utile, en mètres

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = TRAVEL_M * 1000 / LINE_PER_TURN + 5           # 5 tours morts de sécurité
DRUM_W = math.ceil(TURNS * PITCH / 5) * 5             # largeur utile entre joues
FLANGE_D, FLANGE_T = DRUM_D + 20, 4.0
PLATE_T = 8.0
PLATE_Y, PLATE_Z = (-40.0, 72.0), (-40.0, 40.0)       # contour des flasques
MOTOR_FLANGE, MOTOR_LEN, MOTOR_SHAFT_D, MOTOR_SHAFT_L = 60.0, 180.0, 14.0, 30.0
HUB_L, HUB_DISC_T = 18.0, 6.0                         # moyeu de serrage acier + son disque
X_DRUM = PLATE_T + 4 + HUB_L + HUB_DISC_T             # début de la bobine
DRUM_LEN = DRUM_W + 2 * FLANGE_T
X_END = X_DRUM + DRUM_LEN + 4                         # face intérieure du flasque de bout
STUB_D = 12.0                                         # axe acier côté palier
LW_Y, LW_DZ = 48.0, 22.0                              # guide-fil : plan et écart des colonnes
TIES = [(-32.0, 32.0), (-32.0, -32.0), (64.0, -32.0), (64.0, 32.0)]

COLORS = {"alu": (0.80, 0.80, 0.80), "acier": (0.65, 0.67, 0.70), "sombre": (0.30, 0.30, 0.32),
          "bobine": (0.85, 0.65, 0.15), "chariot": (0.25, 0.41, 0.88), "carte": (0.18, 0.55, 0.34)}


def cyl_x(d, length, x, yz=(0.0, 0.0)):
    """Cylindre d'axe X, partant de x."""
    return cq.Workplane("YZ").workplane(offset=x).center(*yz).circle(d / 2).extrude(length)


def box(x, y, z, sx, sy, sz):
    return cq.Workplane("XY").box(sx, sy, sz, centered=False).translate((x, y, z))


def plate(x, center_hole):
    w, h = PLATE_Y[1] - PLATE_Y[0], PLATE_Z[1] - PLATE_Z[0]
    p = (cq.Workplane("YZ").workplane(offset=x)
         .center((PLATE_Y[0] + PLATE_Y[1]) / 2, 0).rect(w, h).extrude(PLATE_T)
         .edges("|X").fillet(6))
    holes = [((0.0, 0.0), center_hole), ((LW_Y, 0.0), 10.0),
             ((LW_Y, LW_DZ), 6.0), ((LW_Y, -LW_DZ), 6.0)] + [(t, 6.0) for t in TIES]
    for yz, d in holes:
        p = p.cut(cyl_x(d, PLATE_T, x, yz))
    return p


def spool(groove=True):
    """Bobine à imprimer, construite le long de X à partir de x = 0 (côté moteur).

    La gorge en hélice est longue à calculer (environ 2 minutes)."""
    s = cyl_x(DRUM_D, DRUM_LEN, 0)
    s = s.union(cyl_x(FLANGE_D, FLANGE_T, 0)).union(cyl_x(FLANGE_D, FLANGE_T, DRUM_LEN - FLANGE_T))
    if groove:
        # Gorge en hélice : le fil s'y couche spire après spire
        r = DRUM_D / 2 + LINE_D / 2 - 0.3
        helix = cq.Wire.makeHelix(PITCH, DRUM_W - 2 * PITCH, r)
        cutter = (cq.Workplane("XZ").center(r, 0).circle(LINE_D / 2 + 0.05)
                  .sweep(cq.Workplane(obj=helix), isFrenet=True))
        cutter = cutter.rotate((0, 0, 0), (0, 1, 0), 90).translate((FLANGE_T + PITCH, 0, 0))
        s = s.cut(cutter)
    s = s.cut(cyl_x(MOTOR_SHAFT_D + 0.1, 4, 0))                      # centrage sur le bout d'arbre
    s = s.cut(cyl_x(STUB_D, 22, DRUM_LEN - 22))                      # logement de l'axe acier
    for a in range(4):                                               # 4 inserts M4 pour le moyeu
        y, z = 19 * math.cos(a * math.pi / 2 + math.pi / 4), 19 * math.sin(a * math.pi / 2 + math.pi / 4)
        s = s.cut(cyl_x(5.6, FLANGE_T + 6, 0, (y, z)))
    anchor = (cq.Workplane("XY").workplane(offset=0).center(FLANGE_T + PITCH / 2, 0)
              .circle(1.0).extrude(DRUM_D))                          # trou d'ancrage du fil
    return s.cut(anchor)


def carriage(x):
    c = box(x - 12, LW_Y - 9, -LW_DZ - 7, 24, 18, 2 * LW_DZ + 14)
    c = c.union(box(x - 6, LW_Y + 9, DRUM_D / 2 - 6, 12, 10, 12))    # bras de l'œillet
    for dz, d in ((0, 8.0), (LW_DZ, 6.0), (-LW_DZ, 6.0)):
        c = c.cut(cyl_x(d, 24, x - 12, (LW_Y, dz)))
    eye = (cq.Workplane("XZ").workplane(offset=-(LW_Y + 19)).center(x, DRUM_D / 2)
           .circle(2).extrude(10))                                   # œillet céramique
    return c.cut(eye)


def build():
    sp = spool(groove=False)                 # bobine lisse dans l'assemblage, pour un fichier léger
    parts = {
        "servo": (box(-MOTOR_LEN, -MOTOR_FLANGE / 2, -MOTOR_FLANGE / 2, MOTOR_LEN, MOTOR_FLANGE, MOTOR_FLANGE)
                  .union(cyl_x(MOTOR_SHAFT_D, PLATE_T + MOTOR_SHAFT_L, 0)), "sombre"),
        "flasque_moteur": (plate(0, 50.0), "alu"),
        "moyeu": (cyl_x(26, HUB_L, PLATE_T + 4).union(cyl_x(FLANGE_D, HUB_DISC_T, PLATE_T + 4 + HUB_L))
                  .cut(cyl_x(MOTOR_SHAFT_D, HUB_L + HUB_DISC_T, PLATE_T + 4)), "acier"),
        "bobine": (sp.translate((X_DRUM, 0, 0)), "bobine"),
        "axe_palier": (cyl_x(STUB_D, 22 + 4 + PLATE_T + 2, X_DRUM + DRUM_LEN - 22), "acier"),
        "flasque_palier": (plate(X_END, 28.0), "alu"),
        "vis_guide": (cyl_x(5, X_END + PLATE_T - PLATE_T, PLATE_T, (LW_Y, 0)), "acier"),
        "colonne_haute": (cyl_x(6, X_END - PLATE_T, PLATE_T, (LW_Y, LW_DZ)), "acier"),
        "colonne_basse": (cyl_x(6, X_END - PLATE_T, PLATE_T, (LW_Y, -LW_DZ)), "acier"),
        "moteur_guide": (box(X_END + PLATE_T, LW_Y - 14, -14, 45, 28, 28), "sombre"),
        "chariot": (carriage(X_DRUM + FLANGE_T + DRUM_W * 0.35), "chariot"),
        "electronique": (box(-MOTOR_LEN + 8, 34, -30, MOTOR_LEN - 16, 34, 60), "carte"),
    }
    for i, t in enumerate(TIES):
        parts[f"entretoise_{i + 1}"] = (cyl_x(8, X_END - PLATE_T, PLATE_T, t), "acier")
    return parts, sp


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
    os.makedirs(out, exist_ok=True)
    parts, sp = build()
    asm = cq.Assembly(name="treuil_prise_directe")
    for name, (shape, color) in parts.items():
        asm.add(shape, name=name, color=cq.Color(*COLORS[color]))
    asm.save(os.path.join(out, "treuil.step"))
    printed = spool(groove=True)
    cq.exporters.export(printed, os.path.join(out, "bobine.step"))
    cq.exporters.export(printed, os.path.join(out, "bobine.stl"), tolerance=0.04, angularTolerance=0.25)
    for name in ("flasque_moteur", "flasque_palier", "chariot"):
        cq.exporters.export(parts[name][0], os.path.join(out, f"{name}.step"))
    cq.exporters.export(asm.toCompound(), os.path.join(out, "treuil.svg"),
                        opt={"width": 1100, "height": 650, "projectionDir": (0.7, 1.0, 0.8),
                             "showAxes": False, "strokeWidth": 0.4, "showHidden": False})

    bb = asm.toCompound().BoundingBox()
    vol = printed.val().Volume() / 1000
    print(f"Gorge : {(sp.val().Volume() - printed.val().Volume()) / 1000:.1f} cm3 retirés")
    print(f"Course {TRAVEL_M:.0f} m -> {TURNS:.0f} tours, bobine utile {DRUM_W:.0f} mm, longueur {DRUM_LEN:.0f} mm")
    print(f"Fil par tour {LINE_PER_TURN:.2f} mm ; bobine pleine : {vol:.0f} cm3 (~{vol * 1.27:.0f} g en PETG)")
    print(f"Encombrement hors tout : {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm")
    names = ["servo", "moyeu", "bobine", "chariot", "electronique", "moteur_guide", "flasque_moteur", "flasque_palier"]
    ok_pairs = {("servo", "moyeu"), ("servo", "bobine"), ("servo", "flasque_moteur")}   # l'arbre traverse
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) not in ok_pairs and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-3]
    print("Interférences :", clash or "aucune")
