"""Planches des pièces imprimées : trois vues à l'échelle et un tableau de cotes par pièce.

    python3 planches.py        # écrit export/planches.html

Ce sont des planches de contrôle, à ouvrir dans un navigateur et à imprimer en PDF au
besoin. Les fichiers STEP et STL restent la référence pour la fabrication.
"""
import os
import re
import cadquery as cq
import treuil as t

VIEWS = [("Face (vue de l'avant)", (1, 0, 0)), ("Dessus", (0, 0, 1)), ("Côté", (0, -1, 0)), ("Perspective", (1, -0.8, 0.6))]

NOTES = {
    "corps": [
        ("Encombrement", "{y:.0f} × {z:.0f} × {x:.1f} mm"),
        ("Cloison porte-moteur", f"épaisseur {t.PART_T:.0f} mm"),
        ("Fixation du moteur", f"4 trous Ø {t.M3_CLEAR} sur un cercle de {t.BASE_PCD:.0f} mm (vis M3 × 6)"),
        ("Passage des fils du moteur", f"2 trous Ø 8 au rayon {t.WIRES_R} mm, autour de {t.WIRES_DEG:.0f}°"),
        ("Colonnes de vissage", f"4 avant-trous Ø {t.M3_PILOT} traversants, dans les angles"),
        ("Logement de l'œillet", f"Ø {t.EYELET_OD + t.FIT:.1f} dans le fond, à {t.EYE_Y:.1f} mm de l'axe"),
        ("Accroche", f"bossage avec écrou M10 prisonnier (17 sur plats), trou Ø 10,5 dans la paroi du haut, à {t.SPIGOT_X:.0f} mm de la cloison"),
        ("Élingue de sécurité", "1 patte de 16 × 12 × 12 mm, trou Ø 5,2"),
        ("Parois", f"{t.WALL} mm"),
    ],
    "capot_arriere": [
        ("Encombrement", "{y:.0f} × {z:.0f} × {x:.1f} mm"),
        ("Profondeur utile pour les cartes", f"{-t.X_REAR:.0f} mm"),
        ("Fixation sur le corps", f"4 trous Ø {t.M3_CLEAR} dans les colonnes d'angle (vis M3 × 30)"),
        ("Passage du câble réseau", f"encoche de {t.CABLE_Z[1] - t.CABLE_Z[0]:.0f} × 14 mm dans une paroi latérale"),
        ("Parois et fond", f"{t.WALL} mm"),
    ],
    "couvercle_avant": [
        ("Encombrement", "{y:.0f} × {z:.0f} × {x:.1f} mm"),
        ("Fixation sur le corps", f"4 trous Ø {t.M3_CLEAR} dans les angles (vis M3 × 10)"),
    ],
    "bobine": [
        ("Encombrement", "Ø {y:.0f} × {x:.1f} mm"),
        ("Fond de gorge", f"Ø {t.DRUM_D:.0f} mm, soit {t.LINE_PER_TURN:.1f} mm de fil par tour"),
        ("Gorge", f"{t.SLOT_W:.0f} mm de large, {t.SLOT_DEPTH:.0f} mm de profondeur, joues de 2 mm"),
        ("Logement du moteur", f"Ø {t.BORE_D:.0f} mm (moteur de {t.MOTOR_D} mm)"),
        ("Fond de la cloche", f"{t.DISC_T} mm d'épaisseur"),
        ("Fixation sur le moteur", f"4 trous Ø {t.M3_CLEAR} sur un cercle de {t.HUB_PCD:.0f} mm (vis M3 × 5, pas plus longues)"),
        ("Téton de centrage", f"Ø {t.HUB_BORE - t.FIT:.1f} × {t.SPIGOT_H} mm, dans l'alésage de {t.HUB_BORE:.0f} mm du moteur"),
        ("Ancrage du fil", "trou Ø 1 dans la joue arrière"),
    ],
}


def view_svg(shape, direction, size=360):
    svg = cq.exporters.getSVG(shape, opts={"width": size, "height": size, "marginLeft": 12, "marginTop": 12,
                                           "projectionDir": direction, "showAxes": False,
                                           "strokeWidth": 0.35, "showHidden": False,
                                           "strokeColor": (30, 30, 30)})
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    return svg


def main():
    out = os.path.join(t.HERE, "export")
    os.makedirs(out, exist_ok=True)
    sections = []
    for name, (fn, orientation, material) in t.PRINTED.items():
        shape = fn().val()
        bb = shape.BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}
        rows = "".join(f"<tr><th>{k}</th><td>{v.format(**dims)}</td></tr>" for k, v in NOTES[name])
        rows += f"<tr><th>Volume</th><td>{shape.Volume() / 1000:.1f} cm³</td></tr>"
        rows += f"<tr><th>Matière conseillée</th><td>{material}</td></tr>"
        rows += f"<tr><th>Sens d'impression</th><td>{orientation}, sans supports</td></tr>"
        views = "".join(f"<figure>{view_svg(shape, d)}<figcaption>{label}</figcaption></figure>" for label, d in VIEWS)
        sections.append(f"<section><h2>{name.replace('_', ' ')}</h2><p class='file'>export/{name}.step · export/{name}.stl</p>"
                        f"<div class='views'>{views}</div><table>{rows}</table></section>")
    html = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Treuil micro — planches des pièces</title>
<style>
body{{font-family:Inter,system-ui,sans-serif;color:#222;margin:24px;font-size:13px}}
h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:17px;text-transform:capitalize;margin:0 0 2px}}
.lede{{color:#555;max-width:70ch;margin:0 0 24px}} .file{{color:#777;margin:0 0 8px;font-size:12px}}
section{{page-break-after:always;border-top:1px solid #ccc;padding-top:14px;margin-top:22px}}
.views{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}
figure{{margin:0;border:1px solid #ddd;background:#fff}} figure svg{{width:100%;height:auto;display:block}}
figcaption{{font-size:11px;color:#666;padding:4px 6px;border-top:1px solid #eee}}
table{{border-collapse:collapse;margin-top:12px;width:100%}} th,td{{text-align:left;padding:5px 8px;border-bottom:1px solid #e4e4e4;vertical-align:top}}
th{{width:32%;font-weight:600}}
@media (max-width:800px){{.views{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body>
<h1>Treuil micro — planches des pièces à imprimer</h1>
<p class="lede">Quatre pièces, trois vues et une perspective chacune. Les cotes viennent du modèle paramétrique
(cad/treuil.py) ; les fichiers STEP et STL restent la référence pour la fabrication. Les vues d'une même pièce
sont cadrées séparément : elles ne sont pas à la même échelle entre elles.</p>
{''.join(sections)}
</body></html>"""
    with open(os.path.join(out, "planches.html"), "w") as f:
        f.write(html)
    print("planches écrites :", len(sections), "pièces")


if __name__ == "__main__":
    main()
