# -*- coding: utf-8 -*-
"""
ARIA 2026 — Séquence finale (25 s @ 30 im/s)
============================================

La carte de l'Europe se dessine, 24 cubes sombres flottent devant.
Un par un (en relais), chaque cube vient au premier plan en se retournant :
il se colore et révèle le titre du projet, reste 1,5 s, puis file se poser
sur son pays en se réduisant jusqu'à devenir un point lumineux.

UTILISATION (Blender 5.x)
  1. Mets ce script et carte_europe.png à côté de ton .blend (ou règle MAP_IMAGE).
  2. Onglet Scripting > Ouvrir > aria_final.py > ▶ Run Script.
  3. Une scène « ARIA_Final » est créée (tes autres scènes ne sont pas touchées).
  4. Déplace les repères « Cible_xx » (collection ARIA_Cibles) sur les bons pays,
     puis relance le script : les positions des repères sont conservées
     et toute l'animation est recalculée.

Tout ce qui est réglable est dans le bloc RÉGLAGES ci-dessous.
"""

import bpy
import bmesh
import math
import os
import random
import itertools
from mathutils import Vector

# ═════════════════════════════════════════════════════════════════════════════
# RÉGLAGES
# ═════════════════════════════════════════════════════════════════════════════

SCENE_NAME = "ARIA_Final"
FPS = 30
DURATION = 25.0                     # secondes
RESOLUTION = (1920, 1080)

# Carte ----------------------------------------------------------------------
MAP_IMAGE = "//carte_europe.png"    # "//" = dossier du .blend ; ou chemin absolu
MAP_PX = (1536, 1024)               # taille de l'image en pixels
MAP_WIDTH = 16.0                    # largeur du plan carte (unités Blender)
REVEAL_ORIGIN_PX = (800, 540)       # point d'où part le dessin de la carte

# Polices (vide = recherche automatique d'Inter dans les dossiers de polices)
FONT_TITLE = ""                     # ex. "/Users/moi/Library/Fonts/Inter-SemiBold.ttf"
FONT_SMALL = ""                     # ex. ".../Inter-Medium.ttf"

# Timeline (secondes) --------------------------------------------------------
MAP_LINES = (0.0, 2.2)              # les contours lumineux se tracent
MAP_FILL = (0.7, 3.0)               # puis la carte se remplit
SWARM_IN = (0.2, 2.0)               # les cubes sombres apparaissent
FIRST_REVEAL = 2.8                  # départ du 1er cube
LAST_LANDING = 23.2                 # le dernier point se pose ici ; puis plan final
T_APPROACH = 0.55                   # vol + retournement vers le premier plan
T_HOLD = 1.5                        # temps affiché en grand
T_FLY = 0.75                        # vol vers le pays + réduction en point

# Géométrie / caméra ---------------------------------------------------------
CAM_HEIGHT = 20.0                   # caméra en plongée verticale
FRAME_HEIGHT = 10.2                 # hauteur de carte visible à l'image
HOLD_HEIGHT = 13.0                  # altitude des cubes « en grand »
CUBE_SIZE = 1.35                    # taille d'un cube en grand
SLOTS_X = (-2.0, 0.0, 2.0)          # 3 emplacements en relais (gauche, centre, droite)
SWARM_SIZE = 0.7                    # taille des cubes qui flottent
SWARM_Z = (3.0, 7.0)                # altitudes du nuage de cubes
SWARM_AREA = (11.5, 5.8)            # étendue du nuage (x, y)
POINT_SIZE = 0.16                   # taille finale des points sur la carte
POINT_Z = 0.08
CLUSTER_RADIUS = 0.17               # écart entre plusieurs points d'un même pays

# Lumière des cubes ----------------------------------------------------------
EMIT_HOLD = 0.10                    # éclat de la couleur quand le cube est en grand
EMIT_PING = 5.0                     # flash à l'atterrissage
EMIT_POINT = 1.6                    # éclat des points posés
POINT_BREATHE = 0.25                # respiration lente des points (0 = aucune)

# Couleurs -------------------------------------------------------------------
PALETTE = "harmonisee"              # "harmonisee" ou "originale" (celle du tableau)
PALETTES = {
    "originale":  {"EP": "#9CCC65", "GE": "#A28AC1", "SA": "#8A97A2", "SE": "#D936A3"},
    "harmonisee": {"EP": "#74BF55", "GE": "#9677D4", "SA": "#4A95C8", "SE": "#E2458F"},
}
CUBE_DARK = "#0D1422"               # couleur des cubes avant retournement
TEXT_COLOR = "#FFFFFF"
GLOW_COLOR = "#FFD9A8"              # lueur chaude au front du dessin de la carte

ORDER = "tableau"                   # "tableau" | "alterne" (catégories mélangées) | "ouest_est"
SEED = 7

# Données --------------------------------------------------------------------
PROJECTS = [
    ("FI", "The Bad Boat Recycling Campaign", "EP"),
    ("FI", "The Carbon-Neutral Lunch Project", "EP"),
    ("HU", "Saving Phacelia", "EP"),
    ("IE", "Breeding Waders EIP", "EP"),
    ("IT", "AGRI-RINNOVA", "EP"),
    ("PT", "Monte Silveira Farm", "EP"),
    ("AT", "Agricultural technology for women", "GE"),
    ("AT", "Together for STEM", "GE"),
    ("ES", "LIDER-ESAS", "GE"),
    ("HU", "SheSpeaks", "GE"),
    ("PL", "Strengthening the competencies of women", "GE"),
    ("PT", "Mainova", "GE"),
    ("BG", "Building the Future of Dairy Sheep Farming", "SA"),
    ("BE-FL", "ZoBio", "SA"),
    ("EE", "HIVET", "SA"),
    ("FI", "Remote Pathology", "SA"),
    ("IT", "Open School Copernicus", "SA"),
    ("NL", "Blossom", "SA"),
    ("CY", "Antelia Bee Park", "SE"),
    ("CZ", "Staré Hutě Glassworks", "SE"),
    ("CZ", "Jurtissimo", "SE"),
    ("FR", "Koolookoo", "SE"),
    ("NL", "Buurderij van Dam", "SE"),
    ("PL", "Kobylnica library", "SE"),
]

COUNTRY_NAMES = {
    "AT": "AUSTRIA", "BE-FL": "BELGIUM · FLANDERS", "BG": "BULGARIA", "CY": "CYPRUS",
    "CZ": "CZECHIA", "EE": "ESTONIA", "ES": "SPAIN", "FI": "FINLAND", "FR": "FRANCE",
    "HU": "HUNGARY", "IE": "IRELAND", "IT": "ITALY", "NL": "NETHERLANDS",
    "PL": "POLAND", "PT": "PORTUGAL",
}

# Position approximative de chaque pays sur l'image (en pixels, origine en haut à gauche).
# Ce ne sont que des positions de départ : ajuste ensuite les repères dans Blender.
COUNTRY_PX = {
    "FI": (985, 245), "EE": (985, 338), "IE": (385, 412), "NL": (648, 445),
    "BE-FL": (612, 480), "FR": (540, 580), "ES": (370, 752), "PT": (262, 765),
    "IT": (835, 690), "AT": (815, 572), "CZ": (808, 522), "PL": (910, 462),
    "HU": (900, 585), "BG": (1040, 680), "CY": (1240, 885),
}

# ═════════════════════════════════════════════════════════════════════════════
# OUTILS
# ═════════════════════════════════════════════════════════════════════════════

PREFIX = "ARIA_"
MAP_HEIGHT = MAP_WIDTH * MAP_PX[1] / MAP_PX[0]
N_FRAMES = int(round(DURATION * FPS))


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def smoothstep(e0, e1, x):
    x = clamp01((x - e0) / (e1 - e0))
    return x * x * (3 - 2 * x)


def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_cubic(x):
    return 1 - (1 - clamp01(x)) ** 3


def ease_in_cubic(x):
    return clamp01(x) ** 3


def ease_out_back(x, s=1.5):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def hex_to_linear(h, alpha=1.0):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, alpha)


def px_to_world(px, py, z=0.0):
    return Vector(((px / MAP_PX[0] - 0.5) * MAP_WIDTH,
                   (0.5 - py / MAP_PX[1]) * MAP_HEIGHT, z))


def frame_of(t):
    return int(round(t * FPS)) + 1


def time_of(f):
    return (f - 1) / FPS


def candidate_dirs():
    dirs = []
    try:
        if __file__ and os.path.isfile(__file__):
            dirs.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    # Script ouvert dans l'éditeur de texte de Blender : on prend son dossier sur le disque
    for txt in bpy.data.texts:
        if txt.filepath and os.path.isfile(bpy.path.abspath(txt.filepath)):
            dirs.append(os.path.dirname(bpy.path.abspath(txt.filepath)))
    if bpy.data.filepath:
        dirs.append(os.path.dirname(bpy.data.filepath))
    home = os.path.expanduser("~")
    dirs += [os.path.join(home, "Downloads"), os.path.join(home, "Téléchargements"),
             os.path.join(home, "Desktop"), os.path.join(home, "Bureau")]
    return [d for i, d in enumerate(dirs) if d not in dirs[:i] and os.path.isdir(d)]


def find_file(path_setting, fallback_names):
    if path_setting:
        p = bpy.path.abspath(path_setting)
        if os.path.isfile(p):
            return p
        for d in candidate_dirs():
            q = os.path.join(d, os.path.basename(path_setting))
            if os.path.isfile(q):
                return q
    for d in candidate_dirs():
        for n in fallback_names:
            q = os.path.join(d, n)
            if os.path.isfile(q):
                return q
    return None


def find_font(setting, names):
    if setting and os.path.isfile(bpy.path.abspath(setting)):
        return bpy.path.abspath(setting)
    home = os.path.expanduser("~")
    roots = candidate_dirs() + [
        os.path.join(home, "Library", "Fonts"), "/Library/Fonts", "/System/Library/Fonts",
        os.path.join(home, ".fonts"), os.path.join(home, ".local", "share", "fonts"),
        "/usr/share/fonts", "/usr/local/share/fonts", "C:\\Windows\\Fonts",
        os.path.join(home, "AppData", "Local", "Microsoft", "Windows", "Fonts"),
    ]
    wanted = [n.lower() for n in names]
    found = {}
    for r in roots:
        if not os.path.isdir(r):
            continue
        for dp, _dn, fns in os.walk(r):
            for fn in fns:
                low = fn.lower()
                if low in wanted and low not in found:
                    found[low] = os.path.join(dp, fn)
            if dp.count(os.sep) - r.count(os.sep) > 3:
                break
    for n in wanted:
        if n in found:
            return found[n]
    return None


def load_font(setting, names, label):
    path = find_font(setting, names)
    if path:
        print(f"[ARIA] Police {label} : {path}")
        return bpy.data.fonts.load(path, check_existing=True)
    print(f"[ARIA] ⚠ Inter introuvable pour {label} — police par défaut de Blender utilisée. "
          f"Installe Inter ou renseigne FONT_{label.upper()}.")
    return bpy.data.fonts.get("Bfont Regular") or (bpy.data.fonts[0] if bpy.data.fonts else None)


TITLE_FONT_NAMES = ["Inter-SemiBold.ttf", "Inter-SemiBold.otf", "Inter_18pt-SemiBold.ttf",
                    "Inter_24pt-SemiBold.ttf", "Inter_28pt-SemiBold.ttf", "Inter-Medium.ttf",
                    "InterVariable.ttf", "Inter-VariableFont_opsz,wght.ttf",
                    "Inter-Regular.ttf", "Inter.ttc"]
SMALL_FONT_NAMES = ["Inter-Medium.ttf", "Inter-Medium.otf", "Inter_18pt-Medium.ttf",
                    "Inter-Regular.ttf", "Inter_18pt-Regular.ttf", "InterVariable.ttf",
                    "Inter-VariableFont_opsz,wght.ttf", "Inter-SemiBold.ttf", "Inter.ttc"]


def new_material(name):
    mat = bpy.data.materials.new(PREFIX + name)
    if mat.node_tree is None:
        mat.use_nodes = True        # Blender < 5 ; en 5.x les matériaux ont toujours des nœuds
    mat.node_tree.nodes.clear()
    return mat


def link(nt, a, b):
    nt.links.new(a, b)


def math_node(nt, op, a=None, b=None, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.location = loc
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            link(nt, v, n.inputs[i])
    return n.outputs[0]


def map_range(nt, value, fmin, fmax, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeMapRange")
    n.clamp = True
    n.location = loc
    for i, v in ((0, value), (1, fmin), (2, fmax)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            link(nt, v, n.inputs[i])
    n.inputs[3].default_value = 0.0
    n.inputs[4].default_value = 1.0
    return n.outputs[0]


def vec_math(nt, op, a, b=None, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    n.location = loc
    link(nt, a, n.inputs[0])
    if b is not None:
        if op == "SCALE":
            if isinstance(b, (int, float)):
                n.inputs["Scale"].default_value = b
            else:
                link(nt, b, n.inputs["Scale"])
        elif isinstance(b, (tuple, list)):
            n.inputs[1].default_value = b
        else:
            link(nt, b, n.inputs[1])
    return n.outputs[0] if op not in ("DISTANCE", "LENGTH", "DOT_PRODUCT") else n.outputs["Value"]


def const_vec(nt, v, loc=(0, 0)):
    n = nt.nodes.new("ShaderNodeCombineXYZ")
    n.location = loc
    for i in range(3):
        n.inputs[i].default_value = v[i]
    return n.outputs[0]


def key_value(socket, frame, value):
    socket.default_value = value
    socket.keyframe_insert("default_value", frame=frame)


# ═════════════════════════════════════════════════════════════════════════════
# NETTOYAGE (en gardant les positions des repères déjà ajustés)
# ═════════════════════════════════════════════════════════════════════════════

def collect_saved_targets():
    saved = {}
    scn = bpy.data.scenes.get(SCENE_NAME)
    if scn:
        for ob in scn.objects:
            if ob.type == "EMPTY" and "aria_index" in ob:
                saved[int(ob["aria_index"])] = ob.location.copy()
    return saved


def clear_previous():
    scn = bpy.data.scenes.get(SCENE_NAME)
    if scn:
        for ob in list(scn.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for coll in list(scn.collection.children_recursive):
            bpy.data.collections.remove(coll)
        win = bpy.context.window
        if win and win.scene == scn:
            others = [s for s in bpy.data.scenes if s != scn]
            win.scene = others[0] if others else bpy.data.scenes.new("Scene")
        bpy.data.scenes.remove(scn)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras,
                 bpy.data.lights, bpy.data.worlds, bpy.data.actions):
        for block in list(coll):
            if block.name.startswith(PREFIX) and block.users == 0:
                coll.remove(block)


# ═════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION
# ═════════════════════════════════════════════════════════════════════════════

def setup_scene():
    scn = bpy.data.scenes.new(SCENE_NAME)
    scn.render.fps = FPS
    scn.render.fps_base = 1.0
    scn.render.resolution_x, scn.render.resolution_y = RESOLUTION
    scn.render.resolution_percentage = 100
    scn.frame_start = 1
    scn.frame_end = N_FRAMES
    scn.frame_current = 1
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scn.render.engine = engine
            break
        except TypeError:
            continue
    try:
        scn.view_settings.view_transform = "Standard"   # couleurs de la carte fidèles
        scn.view_settings.look = "None"
    except TypeError:
        pass

    world = bpy.data.worlds.new(PREFIX + "World")
    if world.node_tree is None:
        world.use_nodes = True
    world.color = (0, 0, 0)
    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.0015, 0.002, 0.004, 1)
            bg.inputs["Strength"].default_value = 1.0
    scn.world = world

    win = bpy.context.window
    if win:
        win.scene = scn
    return scn


def make_collection(scn, name):
    coll = bpy.data.collections.new(PREFIX + name)
    scn.collection.children.link(coll)
    return coll


def build_camera_and_lights(coll):
    cam_data = bpy.data.cameras.new(PREFIX + "Camera")
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36.0
    frame_w = FRAME_HEIGHT * RESOLUTION[0] / RESOLUTION[1]
    cam_data.lens = 36.0 * CAM_HEIGHT / frame_w
    cam_data.clip_start = 0.1
    cam_data.clip_end = 200
    cam = bpy.data.objects.new(PREFIX + "Camera", cam_data)
    cam.location = (0, 0, CAM_HEIGHT)
    coll.objects.link(cam)

    def area(name, loc, energy, color, size):
        ld = bpy.data.lights.new(PREFIX + name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        ob = bpy.data.objects.new(PREFIX + name, ld)
        ob.location = loc
        d = Vector((0, 0, HOLD_HEIGHT * 0.6)) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        coll.objects.link(ob)

    area("Key_Warm", (-9, 8, 22), 3500, (1.0, 0.86, 0.7), 6)     # lueur chaude haut-gauche
    area("Rim_Cool", (10, -7, 18), 1400, (0.6, 0.75, 1.0), 8)    # contre-jour froid
    return cam


def build_map(coll):
    me = bpy.data.meshes.new(PREFIX + "Map")
    w, h = MAP_WIDTH / 2, MAP_HEIGHT / 2
    me.from_pydata([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for li, co in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = co
    ob = bpy.data.objects.new(PREFIX + "Map", me)
    coll.objects.link(ob)

    mat = new_material("Map")
    nt = mat.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (1600, 0)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.location = (1400, 0)
    link(nt, emit.outputs[0], out.inputs["Surface"])

    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1200, 0)
    uvs = tc.outputs["UV"]

    global MAP_FOUND
    path = find_file(MAP_IMAGE, ["carte_europe.png", "carte_europe.jpg"])
    MAP_FOUND = path
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-900, 300)
    tex.extension = "EXTEND"
    if path:
        tex.image = bpy.data.images.load(path, check_existing=True)
        print(f"[ARIA] Carte : {path}")
    else:
        print("[ARIA] ⚠ Image de carte introuvable — règle MAP_IMAGE. Plan gris en attendant.")
    link(nt, uvs, tex.inputs["Vector"])
    img = tex.outputs["Color"]

    # Luminance -> masque des contours lumineux
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    bw.location = (-600, 400)
    link(nt, img, bw.inputs[0])
    line_key = map_range(nt, bw.outputs[0], 0.20, 0.55, loc=(-400, 400))

    # Distance (corrigée de l'aspect) au point d'origine + bruit = front organique
    aspect = MAP_WIDTH / MAP_HEIGHT
    uv_a = vec_math(nt, "MULTIPLY", uvs, (aspect, 1.0, 1.0), loc=(-900, -100))
    ox, oy = REVEAL_ORIGIN_PX[0] / MAP_PX[0] * aspect, 1 - REVEAL_ORIGIN_PX[1] / MAP_PX[1]
    dist = vec_math(nt, "DISTANCE", uv_a, (ox, oy, 0.0), loc=(-700, -100))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-900, -350)
    noise.inputs["Scale"].default_value = 3.5
    noise.inputs["Detail"].default_value = 4.0
    link(nt, uv_a, noise.inputs["Vector"])
    n_c = math_node(nt, "SUBTRACT", noise.outputs["Fac"], 0.5, loc=(-700, -350))
    d = math_node(nt, "MULTIPLY_ADD", n_c, 0.35, loc=(-500, -200))   # d = noise*0.35 + dist
    link(nt, dist, d.node.inputs[2])

    rl_node = nt.nodes.new("ShaderNodeValue")
    rl_node.name = rl_node.label = "Reveal_Lines"
    rl_node.location = (-500, 100)
    rf_node = nt.nodes.new("ShaderNodeValue")
    rf_node.name = rf_node.label = "Reveal_Fill"
    rf_node.location = (-500, -500)
    rl, rf = rl_node.outputs[0], rf_node.outputs[0]

    mask_l = map_range(nt, d, rl, math_node(nt, "SUBTRACT", rl, 0.03, loc=(-300, 150)), loc=(-100, 100))
    near = map_range(nt, d, math_node(nt, "SUBTRACT", rl, 0.16, loc=(-300, 0)), rl, loc=(-100, -50))
    glow = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", near, mask_l, loc=(100, -50)),
                     line_key, loc=(300, -50))
    mask_f = map_range(nt, d, rf, math_node(nt, "SUBTRACT", rf, 0.22, loc=(-300, -500)), loc=(-100, -450))

    lines = math_node(nt, "MULTIPLY", mask_l, line_key, loc=(100, 200))
    m = math_node(nt, "MAXIMUM", lines, mask_f, loc=(300, 200))

    # Vignettage des bords du plan pour le fondre dans le noir
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-900, -650)
    link(nt, uvs, sep.inputs[0])
    eu = math_node(nt, "MINIMUM", sep.outputs[0],
                   math_node(nt, "SUBTRACT", 1.0, sep.outputs[0], loc=(-700, -700)), loc=(-500, -650))
    ev = math_node(nt, "MINIMUM", sep.outputs[1],
                   math_node(nt, "SUBTRACT", 1.0, sep.outputs[1], loc=(-700, -800)), loc=(-500, -780))
    edge = map_range(nt, math_node(nt, "MINIMUM", eu, ev, loc=(-300, -700)), 0.0, 0.07, loc=(-100, -700))
    m = math_node(nt, "MULTIPLY", m, edge, loc=(500, 200))

    col = vec_math(nt, "SCALE", img, m, loc=(800, 200))
    gcol = const_vec(nt, hex_to_linear(GLOW_COLOR)[:3], loc=(500, -200))
    g = vec_math(nt, "SCALE", gcol, math_node(nt, "MULTIPLY", glow, edge, loc=(500, -50)), loc=(800, -100))
    g = vec_math(nt, "SCALE", g, 2.5, loc=(1000, -100))
    final = vec_math(nt, "ADD", col, g, loc=(1200, 100))
    link(nt, final, emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 1.0

    ob.data.materials.append(mat)

    # Animation du dessin : la valeur de révélation parcourt toute la carte
    max_d = 1.9
    for node, (t0, t1) in ((rl_node, MAP_LINES), (rf_node, MAP_FILL)):
        f0, f1 = frame_of(t0), frame_of(t1)
        key_value(node.outputs[0], 1, -0.3)
        for f in range(max(f0, 1), f1 + 1):
            x = (f - f0) / max(1, f1 - f0)
            key_value(node.outputs[0], f, lerp(-0.3, max_d, ease_in_out_cubic(x)))
        key_value(node.outputs[0], N_FRAMES, max_d)
    return ob


def balanced_lines(text, box_w=0.80, box_h=0.50, max_lines=4):
    words = text.split()
    best, best_score = [text], -1
    for n in range(1, min(max_lines, len(words)) + 1):
        for cuts in itertools.combinations(range(1, len(words)), n - 1):
            idx = (0,) + cuts + (len(words),)
            lines = [" ".join(words[idx[i]:idx[i + 1]]) for i in range(n)]
            longest = max(len(l) for l in lines)
            score = min(box_w / (longest * 0.58), box_h / (n * 1.15))
            if score > best_score * 1.04:
                best, best_score = lines, score
    return best


def make_text(name, body, font, size, coll, mat, space_char=1.0):
    cu = bpy.data.curves.new(PREFIX + name, "FONT")
    cu.body = body
    if font:
        cu.font = font
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 0.92
    cu.space_character = space_char
    ob = bpy.data.objects.new(PREFIX + name, cu)
    coll.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def fit_text(scn, ob, box_w, box_h, max_size):
    scn.view_layers[0].update()
    dx, dy = ob.dimensions.x, ob.dimensions.y
    if dx <= 1e-6 or dy <= 1e-6:
        return
    k = min(box_w / dx, box_h / dy)
    ob.data.size = min(ob.data.size * k, max_size)


def build_cube_mesh():
    me = bpy.data.meshes.new(PREFIX + "Cube")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def build_cubes(scn, coll_cubes, coll_targets, saved_targets):
    palette = PALETTES[PALETTE]
    font_t = load_font(FONT_TITLE, TITLE_FONT_NAMES, "title")
    font_s = load_font(FONT_SMALL, SMALL_FONT_NAMES, "small")

    text_mat = new_material("Text")
    nt = text_mat.node_tree
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = hex_to_linear(TEXT_COLOR)
    e.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    link(nt, e.outputs[0], o.inputs["Surface"])

    mesh = build_cube_mesh()

    # Regroupement des projets d'un même pays
    by_country = {}
    for i, (c, _t, _k) in enumerate(PROJECTS):
        by_country.setdefault(c, []).append(i)

    cubes = []
    for i, (country, title, cat) in enumerate(PROJECTS):
        tag = f"{i + 1:02d}_{country}"

        # Repère cible (positions conservées entre deux exécutions)
        if i in saved_targets:
            target = saved_targets[i]
        else:
            group = by_country[country]
            k, j = len(group), group.index(i)
            base = px_to_world(*COUNTRY_PX[country], POINT_Z)
            if k > 1:
                a = 2 * math.pi * j / k + (math.pi if k == 2 else math.pi / 2)
                base += Vector((math.cos(a), math.sin(a), 0)) * CLUSTER_RADIUS
            target = base
        emp = bpy.data.objects.new(f"Cible_{tag}", None)
        emp.empty_display_type = "SPHERE"
        emp.empty_display_size = 0.12
        emp.location = target
        emp["aria_index"] = i
        emp["projet"] = title
        coll_targets.objects.link(emp)

        # Matériau : sombre -> couleur du projet (piloté par la valeur « Color_Mix »)
        mat = new_material(f"Cube_{tag}")
        nt = mat.node_tree
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (600, 0)
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (300, 0)
        bsdf.inputs["Roughness"].default_value = 0.32
        link(nt, bsdf.outputs[0], out.inputs["Surface"])
        mix = nt.nodes.new("ShaderNodeValue")
        mix.name = mix.label = "Color_Mix"
        mix.location = (-500, 100)
        dark = Vector(hex_to_linear(CUBE_DARK)[:3])
        colr = Vector(hex_to_linear(palette[cat])[:3])
        diff = const_vec(nt, colr - dark, loc=(-500, 300))
        base = vec_math(nt, "ADD", vec_math(nt, "SCALE", diff, mix.outputs[0], loc=(-250, 300)),
                        tuple(dark), loc=(0, 300))
        link(nt, base, bsdf.inputs["Base Color"])
        ecol = vec_math(nt, "SCALE", const_vec(nt, colr, loc=(-500, -100)), mix.outputs[0], loc=(0, -100))
        link(nt, ecol, bsdf.inputs["Emission Color"])
        mix.outputs[0].default_value = 0.0
        bsdf.inputs["Emission Strength"].default_value = 0.0

        ob = bpy.data.objects.new(f"{PREFIX}Cube_{tag}", mesh.copy())
        ob.data.name = f"{PREFIX}Cube_{tag}"
        ob.data.materials.append(mat)
        coll_cubes.objects.link(ob)
        bev = ob.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.06
        bev.segments = 5
        bev.limit_method = "NONE"
        try:
            bev.harden_normals = True
        except Exception:
            pass

        # Textes sur la face du dessous (révélée par le retournement autour de X)
        lines = balanced_lines(title)
        t_ob = make_text(f"Title_{tag}", "\n".join(lines), font_t, 0.1, coll_cubes, text_mat, 1.0)
        fit_text(scn, t_ob, 0.80, 0.50, 0.19)
        c_ob = make_text(f"Country_{tag}", COUNTRY_NAMES.get(country, country), font_s, 0.075,
                         coll_cubes, text_mat, 1.25)
        fit_text(scn, c_ob, 0.80, 0.08, 0.075)
        for txt, ty in ((t_ob, 0.05), (c_ob, -0.37)):
            txt.parent = ob
            txt.location = (0, -ty, -0.5 - 0.004)   # y inversé : le cube se retourne
            txt.rotation_euler = (math.pi, 0, 0)

        cubes.append(dict(index=i, ob=ob, mix=mix.outputs[0], emit=bsdf.inputs["Emission Strength"],
                          bevel=bev, texts=(t_ob, c_ob), target=Vector(target), cat=cat))
    return cubes


# ═════════════════════════════════════════════════════════════════════════════
# ANIMATION
# ═════════════════════════════════════════════════════════════════════════════

def reveal_order():
    idx = list(range(len(PROJECTS)))
    if ORDER == "ouest_est":
        idx.sort(key=lambda i: COUNTRY_PX[PROJECTS[i][0]][0])
    elif ORDER == "alterne":
        cats = {}
        for i in idx:
            cats.setdefault(PROJECTS[i][2], []).append(i)
        idx, queues = [], list(cats.values())
        while any(queues):
            for q in queues:
                if q:
                    idx.append(q.pop(0))
    return idx


def animate(cubes):
    rng = random.Random(SEED)
    n = len(cubes)
    order = reveal_order()
    per_cube = T_APPROACH + T_HOLD + T_FLY
    cadence = (LAST_LANDING - per_cube - FIRST_REVEAL) / max(1, n - 1)
    print(f"[ARIA] Cadence : un cube toutes les {cadence:.2f} s "
          f"(≈{T_HOLD / cadence + 0.5:.1f} cubes en grand simultanément)")

    # Nuage de départ : grille 6 x 4 légèrement désordonnée
    cols, rows = 6, 4
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)
    appear_rank = list(range(n))
    rng.shuffle(appear_rank)

    order_cubes = [cubes[k] for k in order]
    for rank, cube in enumerate(order_cubes):
        c, r = cells[rank % len(cells)]
        sx = (c + 0.5) / cols - 0.5
        sy = (r + 0.5) / rows - 0.5
        cube["swarm"] = Vector((sx * SWARM_AREA[0] + rng.uniform(-0.45, 0.45),
                                sy * SWARM_AREA[1] + rng.uniform(-0.4, 0.4),
                                rng.uniform(*SWARM_Z)))
        cube["phase"] = rng.uniform(0, 2 * math.pi)
        cube["spin"] = rng.choice((-1, 1)) * math.pi / 2
        cube["start"] = FIRST_REVEAL + rank * cadence
        cube["slot"] = Vector((SLOTS_X[rank % len(SLOTS_X)], 0.0, HOLD_HEIGHT))
        cube["appear"] = SWARM_IN[0] + (SWARM_IN[1] - SWARM_IN[0]) * appear_rank[rank] / max(1, n - 1)

    def float_pos(cb, t):
        p, s = cb["phase"], cb["swarm"]
        return s + Vector((0.10 * math.sin(0.7 * t + p), 0.08 * math.cos(0.55 * t + 1.3 * p),
                           0.22 * math.sin(0.9 * t + 2.1 * p)))

    def float_rot(cb, t):
        p = cb["phase"]
        return Vector((0.16 * math.sin(0.6 * t + p), 0.14 * math.cos(0.5 * t + 1.7 * p),
                       0.35 * math.sin(0.3 * t + 0.4 * p) + p * 0.2))

    def hold_pos(cb, t):
        p = cb["phase"]
        return cb["slot"] + Vector((0.025 * math.sin(1.1 * t + p), 0.03 * math.sin(0.9 * t + 2 * p),
                                    0.05 * math.sin(1.3 * t + p)))

    def hold_rot(cb, t):
        p = cb["phase"]
        return Vector((math.pi + 0.07 * math.sin(1.2 * t + p), 0.09 * math.sin(0.9 * t + 1.5 * p),
                       0.03 * math.sin(0.7 * t + p)))

    def state(cb, t):
        s = cb["start"]
        t_hold, t_fly = s + T_APPROACH, s + T_APPROACH + T_HOLD
        t_land = t_fly + T_FLY
        st = dict(text=1.0, bevel=0.06, mix=0.0, emit=0.0)
        if t < s:
            a = ease_out_back((t - cb["appear"]) / 0.6, 1.7) if t > cb["appear"] else 0.0
            st.update(loc=float_pos(cb, t), rot=float_rot(cb, t), scale=SWARM_SIZE * max(a, 0.0))
        elif t < t_hold:
            x = (t - s) / T_APPROACH
            e = ease_in_out_cubic(x)
            st.update(loc=vlerp(float_pos(cb, t), hold_pos(cb, t), e),
                      rot=vlerp(float_rot(cb, t), hold_rot(cb, t), ease_out_back(x, 1.1)),
                      scale=lerp(SWARM_SIZE, CUBE_SIZE, ease_out_cubic(x)),
                      mix=smoothstep(0.2, 0.8, x), emit=EMIT_HOLD * smoothstep(0.2, 0.8, x))
        elif t < t_fly:
            st.update(loc=hold_pos(cb, t), rot=hold_rot(cb, t), scale=CUBE_SIZE, mix=1.0, emit=EMIT_HOLD)
        elif t < t_land:
            x = (t - t_fly) / T_FLY
            e = ease_in_out_cubic(x)
            final_rot = Vector((math.pi, 0, cb["spin"]))
            st.update(loc=vlerp(hold_pos(cb, t_fly), cb["target"], e),
                      rot=vlerp(hold_rot(cb, t_fly), final_rot, e),
                      scale=CUBE_SIZE * (POINT_SIZE / CUBE_SIZE) ** e,
                      text=1.0 - smoothstep(0.0, 0.45, x),
                      bevel=lerp(0.06, 0.45, smoothstep(0.25, 1.0, x)),
                      mix=1.0, emit=lerp(EMIT_HOLD, EMIT_POINT, e))
        else:
            dt = t - t_land
            pop = 1.0 + 0.6 * math.exp(-dt * 9) * math.sin(min(dt * 18, math.pi))
            breathe = POINT_BREATHE * math.sin(1.6 * t + cb["phase"]) * smoothstep(0, 0.8, dt)
            st.update(loc=cb["target"], rot=Vector((math.pi, 0, cb["spin"])),
                      scale=POINT_SIZE * pop, text=0.0, bevel=0.45, mix=1.0,
                      emit=EMIT_POINT + EMIT_PING * math.exp(-dt * 5) + breathe)
        return st, (s, t_hold, t_fly, t_land)

    for cb in cubes:
        ob = cb["ob"]
        s, t_hold, t_fly, t_land = state(cb, 0)[1]
        f_s, f_h, f_fly, f_land = frame_of(s), frame_of(t_hold), frame_of(t_fly), frame_of(t_land)
        f_appear0, f_appear1 = frame_of(cb["appear"]) - 1, frame_of(cb["appear"] + 0.6) + 1
        f_pop_end = min(N_FRAMES, f_land + int(0.5 * FPS))
        for f in range(1, N_FRAMES + 1):
            st, _ = state(cb, time_of(f))

            # Transformations : chaque image tant que ça bouge, puis seulement aux bords
            if f <= f_pop_end or f == N_FRAMES:
                ob.location = st["loc"]
                ob.rotation_euler = st["rot"]
                ob.scale = (st["scale"],) * 3
                ob.keyframe_insert("location", frame=f)
                ob.keyframe_insert("rotation_euler", frame=f)
                if f <= f_appear1 or f >= f_s:
                    ob.keyframe_insert("scale", frame=f)

            # Couleur : pendant le retournement
            if f in (1, N_FRAMES) or f_s - 1 <= f <= f_h + 1:
                key_value(cb["mix"], f, st["mix"])
            # Lumière : retournement, vol, atterrissage, respiration
            if f in (1, N_FRAMES) or f_s - 1 <= f <= f_h + 1 or f >= f_fly - 1:
                if f < f_land or f <= f_pop_end or f % 2 == 0 or f == N_FRAMES:
                    key_value(cb["emit"], f, st["emit"])
            # Arrondi + disparition du texte pendant le vol
            if f in (1, N_FRAMES) or f_fly - 1 <= f <= f_land + 1:
                cb["bevel"].width = st["bevel"]
                cb["bevel"].keyframe_insert("width", frame=f)
                for txt in cb["texts"]:
                    txt.scale = (st["text"],) * 3
                    txt.keyframe_insert("scale", frame=f)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

MAP_FOUND = None


def notify(message, icon="INFO"):
    print("[ARIA] " + message)
    wm = bpy.context.window_manager
    if bpy.context.window and wm:
        wm.popup_menu(lambda self, _ctx: self.layout.label(text=message), title="ARIA", icon=icon)


def show_in_viewport(cam):
    """Passe les vues 3D en « Aperçu matériau » et en vue caméra :
    en mode Solide la carte n'apparaît pas (c'est un shader)."""
    screen = bpy.context.screen
    if not screen:
        return
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D":
                if space.shading.type in ("SOLID", "WIREFRAME"):
                    space.shading.type = "MATERIAL"
                space.region_3d.view_perspective = "CAMERA"
        area.tag_redraw()


def main():
    prefs = bpy.context.preferences.edit
    old_interp = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"   # les courbes sont calculées image par image
    try:
        saved = collect_saved_targets()
        clear_previous()
        scn = setup_scene()
        c_map = make_collection(scn, "Carte")
        c_cubes = make_collection(scn, "Cubes")
        c_targets = make_collection(scn, "Cibles")
        cam = build_camera_and_lights(c_map)
        scn.camera = cam
        build_map(c_map)
        cubes = build_cubes(scn, c_cubes, c_targets, saved)
        animate(cubes)
        # On se place après le dessin de la carte (à l'image 1 elle est encore noire)
        scn.frame_set(frame_of(MAP_FILL[1]) + 1)
        show_in_viewport(cam)
        if not MAP_FOUND:
            notify("Carte introuvable : mets carte_europe.png à côté du .blend "
                   "(et enregistre le .blend), ou renseigne MAP_IMAGE en haut du script.", "ERROR")
        print(f"[ARIA] Scène « {SCENE_NAME} » prête : {len(cubes)} cubes, {N_FRAMES} images. "
              f"{len(saved)} repère(s) ajusté(s) conservé(s).")
    finally:
        prefs.keyframe_new_interpolation_type = old_interp


if __name__ == "__main__":
    main()
