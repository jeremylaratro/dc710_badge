#!/usr/bin/env python3
"""Generate foxhunt-badge.kicad_pcb using pcbnew Python API.

Steps:
  1. Create a new empty board.
  2. Add B-2 silhouette outline on Edge.Cuts.
  3. For each component in COMPS, load its footprint from the appropriate
     KiCad library and place at the placement-plan coordinate.
  4. Wire up the netlist from NETS — assign each pad's net.
  5. Add 4 mounting holes.
  6. Add ground pour (front + back), with antenna keep-out zones.
  7. Save.
"""
from __future__ import annotations
from pathlib import Path
import math
import sys
import pcbnew

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "foxhunt-badge.kicad_pcb"
STOCK_FP = Path("/usr/share/kicad/footprints")
PROJECT_FP = ROOT / "lib" / "foxhunt.pretty"

sys.path.insert(0, str(Path(__file__).parent))
import sch_gen as SG  # type: ignore


def IU(mm):  # mm to KiCad internal units (nm)
    return pcbnew.FromMM(mm)


def IUv(x_mm, y_mm):
    return pcbnew.VECTOR2I(IU(x_mm), IU(y_mm))


# ---------------------------------------------------------------------------
# Placement plan: ref -> (x_mm, y_mm, rotation_deg, layer)
# Coordinates in PCB space (KiCad: origin top-left, Y down).
# Board is the 178x71 mm B-2 silhouette; nose at (89, 0); wingtips at
# (0, 53.25) and (178, 53.25); aft apexes at y=71.
# Useful interior at any x: y > 0.598*|x-89| (leading edge) and bounded
# below by the trailing-edge zigzag.  Centerline trailing notch at y=55.4.
# ---------------------------------------------------------------------------
#
# Footprint courtyard sizes (rough, mm):
#   ESP32-C3-WROOM-02: 28.6 x 25.6 (antenna on -Y end of footprint)
#   OLED_SSD1306 7P:  30.6 x 28.1   (header 1x07 vertical, body extends +X)
#   SA868:            38.1 x 24.1
#   TP4056_Module:    31.1 x 20.1
#   USB-C HRO:        10.7 x  9.5
#   CP_Elec_8x10:     10.6 x  8.9
#   JST_PH 2P:         7.0 x  8.7
#   2x03 SAO header:   6.2 x  8.7
#   1x04 debug header: 3.6 x 11.3
#   1x07 (OLED hdr):   3.6 x 18.9
#   TL3342 button:     8.6 x  6.1
#   SOD-123:           4.8 x  2.4
#   SOT-23-5:          4.2 x  3.5
#   WS2812B-2020:      3.1 x  2.6
#   0603:              3.1 x  1.6
#
# Board: 100mm x 55mm B-2 silhouette (origin top-left).  Useful rect
# x in [2, 98], y in [2, 42] (trailing-edge triangles cut beyond y=42).
#
# Layer split:
#   F.Cu (front)  : OLED + ESP32 + USB-C + buttons + status LEDs +
#                   WS2812 RGB strip + RESET button
#   B.Cu (back)   : SA868 module + TP4056 charger + battery + regulator +
#                   most decoupling caps + audio LPF/bias + antenna match
#                   + headers (debug, SAO)
#
# OLED is anchored by its 1x07 header pins at x=37; the OLED PCB sits to
# +X of the header, occupying x ~= [39, 64], y ~= [14, 42].  We avoid
# placing F.Cu courtyards in that rect.
#
#
# Placement designed around the corrected B-2 outline:
#   - Leading edges are straight lines from nose (50, 0) to wingtips
#     (0, 27.5) and (100, 27.5); leading-edge Y at any X = 0.55*|X-50|.
#   - Trailing-edge sawtooth has 4 aft apexes at Y=55 and 3 forward
#     notches; centerline trailing notch at Y=30.25.
#
# Practical placement zones:
#   F.Cu (front, viewer-facing):
#     OLED in center (header pins at X=37, body to +X);
#     buttons in the central trailing-edge "shelf" (Y≈25-29);
#     WS2812 strip just below the leading edge.
#   B.Cu (back):
#     SA868 in the center-back (the big one);
#     TP4056 + battery to the left;
#     decoupling, audio chain, antenna match around the central rectangle.
#
# Placement on the 178x71mm board.  Center is x=89.
# Leading-edge slope: at X, Y must be > 0.598 * |X-89| for the point to
# be inside the wing's swept leading edge.
# Trailing-edge sawtooth: Y < 71 always; centerline trailing Y < 55.38.
#
# All placements respect:
#   - Leading-edge constraint:  Y > 0.598 * |X - 89| at every body corner.
#   - Trailing-edge sawtooth:   stay above the local trailing-edge segment.
#   - Center forward notch:     Y < 55.4 at X=89.
# Components can sit on either F.Cu or B.Cu; the layer split keeps big
# modules on the back so the front face shows the OLED + LEDs + buttons.
#
#
# Placement v2 — designed for the 3-spike B-2 (200x80).  Key changes vs v1:
#   - Wider spacing between dense clusters (no overlapping courtyards)
#   - LDO chain moved AWAY from SA868's back-shadow to the right wing
#   - Audio LPF chain spread out beneath SA868 with breathing room
#   - Button pull-ups moved BELOW their buttons (deeper into trailing area)
#   - WS2812 LEDs placed along leading edge with their decoupling caps
#     directly underneath them on the back side
#
#
# Placement v3 — designed for the STL-extracted B-2 outline (200x77).
# Useful zones:
#   Center wide:   X∈[84,116], Y∈[12,76]   - widest area, holds big modules
#   Inner notches: at X≈84 and X≈116, trailing edge curves up to y=64.67
#   Spike peaks:   at X≈72 and X≈128, trailing reaches y=72.91 (deep aft)
#   Engine cutout: at X≈46 and X≈154, trailing notches up to y=54.62
#   Outboard:      X∈[13,46] / [154,187], moderate
#   Wingtip:       X∈[0,13] / [187,200], narrow strip
#   Leading edge:  Y_top(X) = 0.598*|X-100|
#
PLACEMENT = {
    # ============================================================
    # FRONT (F.Cu) — viewer-facing
    # ============================================================
    # Nose region
    "S1":     (100,   9,   0, "F.Cu"),    # RESET at nose
    "D2":     ( 92,  18,   0, "F.Cu"),    # status LED
    "R3":     ( 96,  18,   0, "F.Cu"),
    # OLED display — header pins at x=78, body extends +X to ~103.
    "DISP1":  ( 78,  35,   0, "F.Cu"),
    # MCU (ESP32-C3-MINI-1) — center-left of OLED, in the wide central area
    "U2":     (115,  43,   0, "F.Cu"),
    # USB-C — right wingtip area (slightly inboard for clearance)
    "J1":     (175,  60, 270, "F.Cu"),
    # Schottky + CC pulldowns — between USB-C and ESP32
    "D1":     (160,  44,   0, "F.Cu"),
    "R1":     (160,  47,   0, "F.Cu"),
    "R2":     (160,  50,   0, "F.Cu"),
    # WS2812 RGB LED chain along leading edge.
    # Constraint: Y > 0.678*|X-100| at every body corner.
    "D3":     ( 32,  52,   0, "F.Cu"),    # outer left (lead@30=47.5, body y_min=50.7)
    "D4":     ( 65,  35,   0, "F.Cu"),    # inner left (lead@63=25.1, body y=33.7)
    "D5":     (135,  35,   0, "F.Cu"),    # inner right
    "D6":     (168,  52,   0, "F.Cu"),    # outer right
    "R11":    ( 36,  56,   0, "F.Cu"),    # 220R LED series
    # Buttons in central trailing shelf (must clear y_trail at body corners)
    "S2":     (100,  68,   0, "F.Cu"),    # SEL center
    "S3":     ( 92,  60,   0, "F.Cu"),    # UP
    "S4":     (108,  60,   0, "F.Cu"),    # DN

    # ============================================================
    # BACK (B.Cu)
    # ============================================================
    # SA868 — center back, body 38x24mm; center at y=27 (body y=15-39)
    "U3":     (100,  27,   0, "B.Cu"),
    # TP4056 — left wing back; pins at x=72, body x=48-72
    "U4":     ( 72,  46,   0, "B.Cu"),
    # Battery JST — right wing back (between spike and notch)
    "J4":     (135,  58,   0, "B.Cu"),
    # AP2112 LDO chain — center back below SA868
    "C20":    ( 90,  44,   0, "B.Cu"),
    "C1":     ( 96,  46,   0, "B.Cu"),
    "U1":     (100,  46,   0, "B.Cu"),
    "C2":     (104,  46,   0, "B.Cu"),
    # ESP32 decoupling (back of U2)
    "C5":     (113,  47,   0, "B.Cu"),
    "C6":     (113,  50,   0, "B.Cu"),
    "C21":    (113,  53,   0, "B.Cu"),
    # Reset RC near nose
    "R4":     ( 88,  10,   0, "B.Cu"),
    "C7":     ( 92,  10,   0, "B.Cu"),
    # SA868 control pull-ups (top center area)
    "R7":     (104,  10,   0, "B.Cu"),
    "R8":     (108,  10,   0, "B.Cu"),
    "R30":    (112,  10,   0, "B.Cu"),
    # Audio TX LPF chain — back center below LDO
    "R31":    ( 86,  56,   0, "B.Cu"),
    "C30":    ( 90,  56,   0, "B.Cu"),
    "R32":    ( 94,  56,   0, "B.Cu"),
    "C31":    ( 98,  56,   0, "B.Cu"),
    "C32":    (102,  56,   0, "B.Cu"),
    # Audio RX bias
    "C40":    (106,  56,   0, "B.Cu"),
    "R40":    (110,  56,   0, "B.Cu"),
    "R41":    (114,  56,   0, "B.Cu"),
    # Antenna match — right wing inboard area (clear of outer notch)
    "L1":     (170,  60,   0, "B.Cu"),
    "C50":    (170,  57,   0, "B.Cu"),
    "C51":    (170,  63,   0, "B.Cu"),
    # WS2812 decoupling — directly under each LED on back
    "C8":     ( 32,  55,   0, "B.Cu"),
    "C9":     ( 65,  38,   0, "B.Cu"),
    "C10":    (135,  38,   0, "B.Cu"),
    "C11":    (168,  55,   0, "B.Cu"),
    "C12":    ( 40,  56,   0, "B.Cu"),
    # GPIO0 LED-strap pull-down
    "R9":     ( 56,  56,   0, "B.Cu"),
    # Button pull-ups — under their buttons on back
    "R12":    ( 92,  64,   0, "B.Cu"),
    "R5":     ( 96,  68,   0, "B.Cu"),
    "R13":    (104,  68,   0, "B.Cu"),
    "R14":    (108,  64,   0, "B.Cu"),
    "R6":     (100,  72,   0, "B.Cu"),
    # Headers
    "J2":     ( 30,  56,   0, "B.Cu"),    # SAO 2x3 — left wing back
    "J3":     ( 60,  32,   0, "B.Cu"),    # Debug 1x4 — left of center
}


# ---------------------------------------------------------------------------
# B-2 silhouette outline points (clockwise) — translate from the existing
# fab/b2_outline.dxf into KiCad-space (mm, with origin at top-left).
# The original DXF is centered at (100, 50) with span ±50, so we shift by
# subtracting (50, 50) and using these absolute mm coords on a 100x55 board.
# ---------------------------------------------------------------------------
B2_OUTLINE_MM = [
    # B-2 silhouette extracted from real B-2 STL mesh and scaled to a
    # 200mm wingspan badge.  See fab/generate_b2_outline.py.
    # 3 aft spikes (left + center + right) with 2 forward notches between
    # each pair, plus an outer "engine cutout" notch on each wingtip side.
    (100.00,  0.00),   # nose
    (199.99, 67.78),   # right wingtip (sharp)
    (186.91, 77.13),   # outboard right aft step (after wing edge)
    (153.75, 54.62),   # outer right forward notch (engine cutout)
    (128.36, 72.91),   # right aft spike peak
    (116.16, 64.67),   # inner right forward notch
    (100.00, 76.32),   # CENTER aft spike peak
    ( 83.84, 64.67),   # inner left forward notch
    ( 71.64, 72.91),   # left aft spike peak
    ( 46.25, 54.62),   # outer left forward notch (engine cutout)
    ( 13.15, 77.12),   # outboard left aft step
    (  0.00, 67.82),   # left wingtip (sharp)
    (100.00,  0.00),   # back to nose
]


def find_footprint_path(libname: str, fpname: str) -> Path:
    """Locate {lib}.pretty/{fp}.kicad_mod under stock or project libs."""
    if libname == "foxhunt":
        return PROJECT_FP / f"{fpname}.kicad_mod"
    return STOCK_FP / f"{libname}.pretty" / f"{fpname}.kicad_mod"


def load_footprint(board: pcbnew.BOARD, fp_id: str, ref: str) -> pcbnew.FOOTPRINT:
    """Load a footprint from a library and add it to the board."""
    libname, fpname = fp_id.split(":", 1)
    if libname == "foxhunt":
        lib_path = str(PROJECT_FP)
    else:
        lib_path = str(STOCK_FP / f"{libname}.pretty")
    fp = pcbnew.FootprintLoad(lib_path, fpname)
    if fp is None:
        raise RuntimeError(f"Failed to load {fp_id}")
    fp.SetReference(ref)
    board.Add(fp)
    return fp


def add_edge_cuts(board: pcbnew.BOARD):
    """Draw the B-2 silhouette on Edge.Cuts."""
    edge = board.GetLayerID("Edge.Cuts")
    pts = B2_OUTLINE_MM
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(IUv(x1, y1))
        line.SetEnd(IUv(x2, y2))
        line.SetLayer(edge)
        line.SetWidth(IU(0.1))
        board.Add(line)


def add_mounting_holes(board: pcbnew.BOARD):
    """Add 4 NPTH 2.5mm mounting holes inset from each wingtip area."""
    # Mounting holes — clear of notches and trailing edge
    holes = [(35, 55), (165, 55), (90, 64), (110, 64)]
    fp_path = str(STOCK_FP / "MountingHole.pretty")
    for i, (x, y) in enumerate(holes, start=1):
        fp = pcbnew.FootprintLoad(fp_path, "MountingHole_2.5mm")
        if fp is None:
            print(f"  warning: MountingHole_2.5mm not found, skipping")
            return
        fp.SetReference(f"H{i}")
        fp.SetPosition(IUv(x, y))
        board.Add(fp)


def add_ground_pour(board: pcbnew.BOARD, gnd_net):
    """Pour ground on F.Cu and B.Cu within the B-2 outline.  Antenna keep-out
    zones (right wingtip for SA868 trace antenna, left wingtip for ESP32 module
    antenna) are NOT poured."""
    # Build outline polygon from B2_OUTLINE_MM
    pts = [pcbnew.VECTOR2I(IU(x), IU(y)) for x, y in B2_OUTLINE_MM[:-1]]

    for layer_name in ("F.Cu", "B.Cu"):
        layer = board.GetLayerID(layer_name)
        zone = pcbnew.ZONE(board)
        zone.SetNet(gnd_net)
        zone.SetLayer(layer)
        zone.SetIsFilled(False)
        zone.SetAssignedPriority(0)
        zone.SetMinThickness(IU(0.2))
        zone.SetThermalReliefGap(IU(0.3))
        zone.SetThermalReliefSpokeWidth(IU(0.3))
        zone.SetLocalClearance(IU(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)

        outline = zone.Outline()
        # Use AddOutline (poly path)
        polyset = pcbnew.SHAPE_POLY_SET()
        polyset.NewOutline()
        for p in pts:
            polyset.Append(p.x, p.y)
        zone.SetOutline(polyset)
        board.Add(zone)

    # Antenna keep-outs: rectangles on right wingtip (SA868 antenna) and left
    # wingtip (ESP32 module antenna), copper-poured-zone disabled, all layers.
    for keepout_name, x1, y1, x2, y2 in [
        ("ANT_RIGHT_KO", 165, 50, 200, 70),  # right wingtip area — SA868 trace antenna
        ("ESP_ANT_KO",     0, 50,  35, 70),  # left wingtip area — ESP module antenna
    ]:
        ko = pcbnew.ZONE(board)
        ko.SetIsRuleArea(True)
        ko.SetDoNotAllowCopperPour(True)
        ko.SetDoNotAllowTracks(False)
        ko.SetDoNotAllowVias(True)
        ko.SetLayerSet(pcbnew.LSET().AddLayer(board.GetLayerID("F.Cu"))
                                     .AddLayer(board.GetLayerID("B.Cu")))
        polyset = pcbnew.SHAPE_POLY_SET()
        polyset.NewOutline()
        polyset.Append(IU(x1), IU(y1))
        polyset.Append(IU(x2), IU(y1))
        polyset.Append(IU(x2), IU(y2))
        polyset.Append(IU(x1), IU(y2))
        ko.SetOutline(polyset)
        board.Add(ko)


def inject_ground_pours(pcb_path: Path):
    """Append two GND zones (F.Cu + B.Cu) plus a grid of GND via stitching
    to a saved PCB.  Uses raw S-exp insertion to bypass pcbnew zone API
    segfaults."""
    import re
    text = pcb_path.read_text()

    # Outline polygon — share the B-2 outline coords
    pts = "\n\t\t\t\t\t".join(
        f"(xy {x:.3f} {y:.3f})" for x, y in B2_OUTLINE_MM[:-1]
    )

    def zone_block(layer: str, idx: int, ko: bool = False) -> str:
        if ko:
            extra = (
                "(name \"ANT_KO\")\n"
                "\t\t(rule_area\n"
                "\t\t\t(keepout\n"
                "\t\t\t\t(tracks not_allowed)\n"
                "\t\t\t\t(vias not_allowed)\n"
                "\t\t\t\t(pads allowed)\n"
                "\t\t\t\t(copperpour not_allowed)\n"
                "\t\t\t\t(footprints allowed)\n"
                "\t\t\t)\n"
                "\t\t)\n"
            )
        else:
            extra = ""
        return (
            f"\t(zone\n"
            f"\t\t(net 1)\n"
            f"\t\t(net_name \"GND\")\n"
            f"\t\t(layer \"{layer}\")\n"
            f"\t\t(uuid \"{generate_uuid()}\")\n"
            f"\t\t(hatch edge 0.5)\n"
            f"\t\t(connect_pads (clearance 0.5))\n"
            f"\t\t(min_thickness 0.25)\n"
            f"\t\t(filled_areas_thickness no)\n"
            f"\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))\n"
            f"\t\t(polygon\n"
            f"\t\t\t(pts\n"
            f"\t\t\t\t\t{pts}\n"
            f"\t\t\t)\n"
            f"\t\t)\n"
            f"\t)\n"
        )

    zone_text = zone_block("F.Cu", 0) + zone_block("B.Cu", 1)

    # GND via stitching: drop a grid of vias INSIDE the polygon to bond
    # the F.Cu and B.Cu pours to each other.  10mm spacing.
    def in_poly(p, poly):
        x, y = p; n = len(poly); inside = False; j = n - 1
        for i in range(n):
            xi, yi = poly[i]; xj, yj = poly[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
                inside = not inside
            j = i
        return inside
    poly = [(x, y) for x, y in B2_OUTLINE_MM[:-1]]
    via_lines = []
    for x in range(10, 200, 10):
        for y in range(10, 80, 10):
            # Only place inside the polygon with 4mm margin
            if not in_poly((x, y), poly):
                continue
            # 4mm margin to edges (skip if any near-corner is outside)
            if not all(in_poly((x + dx, y + dy), poly)
                       for dx in (-4, 4) for dy in (-4, 4)):
                continue
            via_lines.append(
                f'\t(via (at {x:.1f} {y:.1f}) (size 0.6) (drill 0.3) '
                f'(layers "F.Cu" "B.Cu") (net 1) (uuid "{generate_uuid()}"))\n'
            )
    via_text = "".join(via_lines)

    # Find the GND net's net number in the PCB file
    m = re.search(r'\(net (\d+) "GND"\)', text)
    if m:
        gnd_idx = m.group(1)
        zone_text = zone_text.replace('(net 1)', f'(net {gnd_idx})')
        via_text = via_text.replace('(net 1)', f'(net {gnd_idx})')

    # Insert before the closing `)` of the kicad_pcb wrapper
    text = text.rstrip()
    if text.endswith(")"):
        text = text[:-1] + zone_text + via_text + ")"
    pcb_path.write_text(text + "\n")


def generate_uuid():
    import uuid as _uuid
    return str(_uuid.uuid4())


def main():
    # Run schematic generator first to ensure COMPS/NETS are current
    board = pcbnew.NewBoard(str(OUT_PATH))

    # Edge cuts
    add_edge_cuts(board)

    # Build footprint instances per COMPS
    placed: dict[str, pcbnew.FOOTPRINT] = {}
    for c in SG.COMPS:
        if c.get("is_power"):
            continue
        ref = c["ref"]
        fp_id = c["footprint"]
        if not fp_id:
            continue
        if ref not in PLACEMENT:
            print(f"  no placement for {ref}; skipping")
            continue
        x, y, rot, layer = PLACEMENT[ref]
        fp = load_footprint(board, fp_id, ref)
        # set value
        fp.SetValue(c["value"])
        fp.SetPosition(IUv(x, y))
        # rotate
        if rot:
            fp.SetOrientationDegrees(rot)
        # flip to back if needed
        if layer == "B.Cu":
            fp.Flip(IUv(x, y), False)
        placed[ref] = fp

    # Build nets from NETS dict
    netinfo: dict[str, pcbnew.NETINFO_ITEM] = {}
    for net_name in SG.NETS:
        ni = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(ni)
        netinfo[net_name] = ni

    # Assign net to each pad
    for net_name, pins in SG.NETS.items():
        ni = netinfo[net_name]
        for ref, num in pins:
            if ref not in placed:
                continue
            fp = placed[ref]
            for pad in fp.Pads():
                if pad.GetPadName() == num or pad.GetNumber() == num:
                    pad.SetNet(ni)
                    break

    # Mounting holes
    add_mounting_holes(board)

    # Save
    board.Save(str(OUT_PATH))

    # Inject ground pour zones via direct S-expression patching (the pcbnew
    # ZONE API segfaults in the bundled SWIG bindings).
    inject_ground_pours(OUT_PATH)
    print(f"Wrote {OUT_PATH}")
    print(f"  {len(placed)}/{len(SG.COMPS)} footprints placed")
    print(f"  {len(netinfo)} nets")


if __name__ == "__main__":
    main()
