"""Bloc treuil à bobine plate — maquette 3D paramétrique (CadQuery).

    pip install cadquery
    python3 treuil.py

Servo + réducteur planétaire 10:1, bobine de 250 mm à une seule couche, fil guidé
vers une poulie de sortie fixe au bout d'un profilé aluminium. Pas de guide-fil mobile.

Produit dans ./export : l'assemblage (treuil.step), la bobine à faire imprimer
(bobine.step / bobine.stl, gorge en hélice comprise), la platine et le support de poulie.

Maquette d'implantation. Les perçages de fixation du réducteur et le diamètre de son
arbre de sortie sont à reprendre sur sa fiche technique avant toute commande.
Cotes en millimètres. X = axe du moteur, Y = vers la poulie de sortie, Z = vertical.
"""
import math
import os
import cadquery as cq

# ---------- Paramètres (les mêmes que firmware/src/config.h) ----------
DRUM_D = 250.0         # diamètre de la bobine, fond de fil
LINE_D = 1.0           # diamètre du fil
PITCH = 1.2            # pas de la gorge
TRAVEL_M = 10.0        # course de fil utile, en mètres
GEAR_RATIO = 10
PULLEY_DIST = 455.0    # distance entre l'axe de la bobine et la poulie de sortie
PULLEY_D = 40.0

# ---------- Cotes dérivées ----------
LINE_PER_TURN = math.pi * (DRUM_D + LINE_D)
TURNS = math.ceil(TRAVEL_M * 1000 / LINE_PER_TURN + 3)      # 3 tours morts de sécurité
GROOVE_W = math.ceil(TURNS * PITCH)                         # largeur utile entre joues
FLANGE_D, FLANGE_T = DRUM_D + 16, 3.0
REEL_W = GROOVE_W + 2 * FLANGE_T
RIM_T, WEB_T, HUB_D = 6.0, 5.0, 56.0
PLATE_T = 8.0
SHAFT_D, SHAFT_L = 14.0, 30.0                               # arbre de sortie du réducteur (à vérifier)
X_REEL = PLATE_T + 6                                        # face arrière de la bobine
X_LINE = X_REEL + REEL_W / 2                                # plan moyen du fil = plan de la poulie
R_LINE = DRUM_D / 2 + LINE_D / 2
FLEET_DEG = math.degrees(math.atan((GROOVE_W / 2) / PULLEY_DIST))
BEAM_Z = (-FLANGE_D / 2 - 62, -FLANGE_D / 2 - 22)            # profilé 2040 sous la bobine
BEAM_Y = (-90.0, PULLEY_DIST - 30)

COLORS = {"alu": (0.80, 0.80, 0.80), "acier": (0.65, 0.67, 0.70), "sombre": (0.30, 0.30, 0.32),
          "bobine": (0.85, 0.65, 0.15), "poulie": (0.25, 0.41, 0.88)}


def cyl_x(d, length, x, yz=(0.0, 0.0)):
    return cq.Workplane("YZ").workplane(offset=x).center(*yz).circle(d / 2).extrude(length)


def box(x, y, z, sx, sy, sz):
    return cq.Workplane("XY").box(sx, sy, sz, centered=False).translate((x, y, z))


def reel(groove=True):
    """Bobine à imprimer, face arrière en x = 0."""
    r = cyl_x(DRUM_D, REEL_W, 0)
    r = r.union(cyl_x(FLANGE_D, FLANGE_T, 0)).union(cyl_x(FLANGE_D, FLANGE_T, REEL_W - FLANGE_T))
    inner = DRUM_D - 2 * RIM_T
    r = r.cut(cyl_x(inner, REEL_W - WEB_T, WEB_T))                       # évidement : il reste un voile
    r = r.union(cyl_x(HUB_D, REEL_W, 0))                                 # moyeu
    for a in range(6):                                                   # 6 lumières d'allègement
        ang = a * math.pi / 3
        rad = (inner / 2 + HUB_D / 2) / 2
        r = r.cut(cyl_x(58, WEB_T, 0, (rad * math.cos(ang), rad * math.sin(ang))))
    if groove:
        rg = DRUM_D / 2 + LINE_D / 2 - 0.3
        helix = cq.Wire.makeHelix(PITCH, (TURNS - 1) * PITCH, rg)
        cutter = (cq.Workplane("XZ").center(rg, 0).circle(LINE_D / 2 + 0.05)
                  .sweep(cq.Workplane(obj=helix), isFrenet=True))
        r = r.cut(cutter.rotate((0, 0, 0), (0, 1, 0), 90).translate((FLANGE_T + PITCH / 2, 0, 0)))
    r = r.cut(cyl_x(SHAFT_D + 0.1, REEL_W, 0))                           # centrage sur l'arbre
    for a in range(4):                                                   # 4 vis M5 traversantes vers le moyeu acier
        ang = a * math.pi / 2 + math.pi / 4
        r = r.cut(cyl_x(5.5, REEL_W, 0, (20 * math.cos(ang), 20 * math.sin(ang))))
    anchor = (cq.Workplane("XY").workplane(offset=DRUM_D / 2 - RIM_T - 1)
              .center(FLANGE_T + PITCH / 2, 0).circle(1.0).extrude(RIM_T + 2))   # trou d'ancrage du fil
    return r.cut(anchor)


def plate():
    z0, z1 = BEAM_Z[0], 75.0
    p = (cq.Workplane("YZ").center(0, (z0 + z1) / 2).rect(140, z1 - z0).extrude(PLATE_T)
         .edges("|X").fillet(8))
    p = p.cut(cyl_x(50, PLATE_T, 0))                                     # centrage du réducteur
    for y in (-50, 50):                                                  # fixation sur le profilé
        for z in (BEAM_Z[0] + 10, BEAM_Z[1] - 10):
            p = p.cut(cyl_x(5.5, PLATE_T, 0, (y, z)))
    return p


def pulley_bracket():
    """Chape imprimée, vissée en bout de profilé, qui porte la poulie de sortie."""
    zc = -R_LINE - PULLEY_D / 2
    b = box(PLATE_T, BEAM_Y[1] - 40, BEAM_Z[1], 20, 40, 8)               # semelle sur le profilé
    for x in (X_LINE - 10, X_LINE + 6):                                  # deux joues
        b = b.union(box(x, BEAM_Y[1] - 12, BEAM_Z[1], 4, 62, zc + 14 - BEAM_Z[1]))
    return b.cut(cyl_x(5, 40, PLATE_T, (PULLEY_DIST, zc)))


def build():
    zc = -R_LINE - PULLEY_D / 2
    parts = {
        "servo": (box(-275, -30, -30, 180, 60, 60), "sombre"),
        "reducteur": (box(-95, -30, -30, 95, 60, 60).union(cyl_x(SHAFT_D, PLATE_T + 6 + SHAFT_L, 0)), "acier"),
        "platine": (plate(), "alu"),
        "moyeu_acier": (cyl_x(46, 6, X_REEL - 6).cut(cyl_x(SHAFT_D, 6, X_REEL - 6)), "acier"),
        "bobine": (reel(groove=False).translate((X_REEL, 0, 0)), "bobine"),
        "profile_2040": (box(PLATE_T, BEAM_Y[0], BEAM_Z[0], 20, BEAM_Y[1] - BEAM_Y[0], 40), "alu"),
        "support_poulie": (pulley_bracket(), "sombre"),
        "poulie": (cyl_x(PULLEY_D, 8, X_LINE - 4, (PULLEY_DIST, zc))
                   .cut(cyl_x(5, 8, X_LINE - 4, (PULLEY_DIST, zc))), "poulie"),
        "electronique": (box(-270, 34, -30, 170, 34, 60), "sombre"),
    }
    return parts


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export")
    os.makedirs(out, exist_ok=True)
    parts = build()
    asm = cq.Assembly(name="treuil_bobine_plate")
    for name, (shape, color) in parts.items():
        asm.add(shape, name=name, color=cq.Color(*COLORS[color]))
    asm.save(os.path.join(out, "treuil.step"))
    printed = reel(groove=True)
    cq.exporters.export(printed, os.path.join(out, "bobine.step"))
    cq.exporters.export(printed, os.path.join(out, "bobine.stl"), tolerance=0.05, angularTolerance=0.2)
    cq.exporters.export(parts["platine"][0], os.path.join(out, "platine.step"))
    cq.exporters.export(parts["support_poulie"][0], os.path.join(out, "support_poulie.step"))
    cq.exporters.export(asm.toCompound().rotate((0, 0, 0), (1, 0, 0), -90), os.path.join(out, "treuil.svg"),
                        opt={"width": 1100, "height": 650, "projectionDir": (1.0, 0.9, 0.5),
                             "showAxes": False, "strokeWidth": 0.5, "showHidden": False})

    bb = asm.toCompound().BoundingBox()
    vol = printed.val().Volume() / 1000
    smooth = reel(groove=False).val().Volume() / 1000
    print(f"Course {TRAVEL_M:.0f} m -> {TURNS} tours, gorge de {GROOVE_W:.0f} mm, bobine de {REEL_W:.0f} mm d'épaisseur")
    print(f"Fil par tour {LINE_PER_TURN:.1f} mm ; angle du fil vers la poulie : {FLEET_DEG:.2f} degrés au maximum")
    print(f"Bobine : {vol:.0f} cm3 (~{vol * 1.01:.0f} g en nylon PA12), gorge {smooth - vol:.1f} cm3, diamètre hors tout {FLANGE_D:.0f} mm")
    print(f"Encombrement hors tout : {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm")
    names = ["servo", "reducteur", "platine", "bobine", "profile_2040", "support_poulie", "poulie", "electronique", "moyeu_acier"]
    ok_pairs = {("reducteur", "platine"), ("reducteur", "bobine"), ("reducteur", "moyeu_acier")}   # l'arbre traverse
    clash = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
             if (a, b) not in ok_pairs and parts[a][0].intersect(parts[b][0]).val().Volume() > 1e-3]
    print("Interférences :", clash or "aucune")
