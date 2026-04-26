"""
Generate foxhunt-badge.kicad_pcb (KiCad 8) with B2 outline on Edge.Cuts.
Sets up a 2-layer stackup, design rules, and origin at the badge centerline-nose.
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_b2_outline import full_outline


def uuid_from(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def gen_edge_cuts(points, offset_x=100.0, offset_y=50.0):
    """Build gr_line entries for closed polyline. Offset places badge in
    KiCad's positive-coordinate workspace (top-left of A4-ish drawing area)."""
    lines = []
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        x1 += offset_x; x2 += offset_x
        y1 += offset_y; y2 += offset_y
        u = uuid_from(f"edge-{i}")
        lines.append(
            f'\t(gr_line\n'
            f'\t\t(start {x1:.3f} {y1:.3f})\n'
            f'\t\t(end {x2:.3f} {y2:.3f})\n'
            f'\t\t(stroke (width 0.1) (type default))\n'
            f'\t\t(layer "Edge.Cuts")\n'
            f'\t\t(uuid "{u}")\n'
            f'\t)'
        )
    return "\n".join(lines)


def build_pcb():
    edge = gen_edge_cuts(full_outline())

    # KiCad 8 PCB version: 20240108 corresponds to 8.0
    pcb = f'''(kicad_pcb
\t(version 20240108)
\t(generator "claude_foxhunt_gen")
\t(generator_version "1.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(title_block
\t\t(title "Foxhunt Badge")
\t\t(date "2026-04-25")
\t\t(rev "0.1")
\t\t(company "DEFCON Foxhunt")
\t\t(comment 1 "B-2 silhouette flying-wing badge")
\t\t(comment 2 "ESP32-C3 + SA868-V VHF + SSD1306 OLED")
\t)
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(40 "Dwgs.User" user "User.Drawings")
\t\t(41 "Cmts.User" user "User.Comments")
\t\t(42 "Eco1.User" user "User.Eco1")
\t\t(43 "Eco2.User" user "User.Eco2")
\t\t(44 "Edge.Cuts" user)
\t\t(45 "Margin" user)
\t\t(46 "B.CrtYd" user "B.Courtyard")
\t\t(47 "F.CrtYd" user "F.Courtyard")
\t\t(48 "B.Fab" user)
\t\t(49 "F.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(viasonmask no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plotreference yes)
\t\t\t(plotvalue yes)
\t\t\t(plotfptext yes)
\t\t\t(plotinvisibletext no)
\t\t\t(sketchpadsonfab no)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "fab/gerbers")
\t\t)
\t)
\t(net 0 "")
{edge}
\t(gr_text "Foxhunt Badge"
\t\t(at 100.0 30.0 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{uuid_from("title-text")}")
\t\t(effects
\t\t\t(font (size 1.5 1.5) (thickness 0.25))
\t\t)
\t)
\t(gr_text "v0.1 // DC"
\t\t(at 100.0 33.5 0)
\t\t(layer "F.SilkS")
\t\t(uuid "{uuid_from("rev-text")}")
\t\t(effects
\t\t\t(font (size 0.8 0.8) (thickness 0.15))
\t\t)
\t)
\t(gr_text "PCB ANT KEEPOUT"
\t\t(at 145.0 90.0 0)
\t\t(layer "Cmts.User")
\t\t(uuid "{uuid_from("ant-keepout-r")}")
\t\t(effects
\t\t\t(font (size 0.8 0.8) (thickness 0.15))
\t\t)
\t)
\t(gr_text "ESP32 ANT KEEPOUT"
\t\t(at 55.0 90.0 0)
\t\t(layer "Cmts.User")
\t\t(uuid "{uuid_from("ant-keepout-l")}")
\t\t(effects
\t\t\t(font (size 0.8 0.8) (thickness 0.15))
\t\t)
\t)
)
'''
    return pcb


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "foxhunt-badge.kicad_pcb"
    out.write_text(build_pcb())
    print(f"Wrote {out}")
