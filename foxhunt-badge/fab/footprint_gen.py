#!/usr/bin/env python3
"""Generate custom footprints in lib/foxhunt.pretty/.

Footprints created:
  - ESP32-C3-MINI-1.kicad_mod  (Espressif 53-pad SMD module, 13.2 x 16.6 mm)
  - SA868.kicad_mod            (NiceRF 16-pad castellated, ~36 x 22 mm)
  - TP4056_Module.kicad_mod    (LiPo charger breakout, 17 x 26 mm, 5-pin header)
  - OLED_SSD1306_7P.kicad_mod  (1x07 0.1" header for 0.96" OLED PCB module)
"""
from pathlib import Path
import uuid as uuidlib

OUT_DIR = Path(__file__).parent.parent / "lib" / "foxhunt.pretty"


def u():
    return str(uuidlib.uuid4())


def fp_header(name, descr, tags, layer="F.Cu"):
    return (
        f'(footprint "{name}"\n'
        f'\t(version 20240108)\n'
        f'\t(generator "foxhunt_fp_gen")\n'
        f'\t(generator_version "9.0")\n'
        f'\t(layer "{layer}")\n'
        f'\t(descr "{descr}")\n'
        f'\t(tags "{tags}")\n'
        f'\t(attr smd)\n'
    )


def fp_props(ref_y, val_y, value):
    return (
        f'\t(property "Reference" "REF**"\n'
        f'\t\t(at 0 {ref_y:.3f} 0)\n'
        f'\t\t(unlocked yes)\n'
        f'\t\t(layer "F.SilkS")\n'
        f'\t\t(uuid "{u()}")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15)))\n'
        f'\t)\n'
        f'\t(property "Value" "{value}"\n'
        f'\t\t(at 0 {val_y:.3f} 0)\n'
        f'\t\t(unlocked yes)\n'
        f'\t\t(layer "F.Fab")\n'
        f'\t\t(uuid "{u()}")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15)))\n'
        f'\t)\n'
    )


def smd_pad(num, x, y, w, h, layer="F.Cu"):
    layers = '"F.Cu" "F.Paste" "F.Mask"' if layer == "F.Cu" else '"B.Cu" "B.Paste" "B.Mask"'
    return (
        f'\t(pad "{num}" smd rect\n'
        f'\t\t(at {x:.3f} {y:.3f})\n'
        f'\t\t(size {w:.3f} {h:.3f})\n'
        f'\t\t(layers {layers})\n'
        f'\t\t(uuid "{u()}")\n'
        f'\t)\n'
    )


def thru_pad(num, x, y, drill, pad_d, shape="circle"):
    return (
        f'\t(pad "{num}" thru_hole {shape}\n'
        f'\t\t(at {x:.3f} {y:.3f})\n'
        f'\t\t(size {pad_d:.3f} {pad_d:.3f})\n'
        f'\t\t(drill {drill:.3f})\n'
        f'\t\t(layers "*.Cu" "*.Mask")\n'
        f'\t\t(remove_unused_layers no)\n'
        f'\t\t(uuid "{u()}")\n'
        f'\t)\n'
    )


def edge_rect(x1, y1, x2, y2, layer="F.Fab", width=0.1):
    """Draw rectangle on layer using 4 fp_lines."""
    out = []
    pts = [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]
    for sx, sy, ex, ey in pts:
        out.append(
            f'\t(fp_line\n'
            f'\t\t(start {sx:.3f} {sy:.3f})\n'
            f'\t\t(end {ex:.3f} {ey:.3f})\n'
            f'\t\t(stroke (width {width:.3f}) (type solid))\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{u()}")\n'
            f'\t)\n'
        )
    return "".join(out)


def silk_circle(x, y, r=0.3, layer="F.SilkS"):
    return (
        f'\t(fp_circle\n'
        f'\t\t(center {x:.3f} {y:.3f})\n'
        f'\t\t(end {x + r:.3f} {y:.3f})\n'
        f'\t\t(stroke (width 0.15) (type solid))\n'
        f'\t\t(fill solid)\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(uuid "{u()}")\n'
        f'\t)\n'
    )


def courtyard_rect(x1, y1, x2, y2):
    return edge_rect(x1, y1, x2, y2, layer="F.CrtYd", width=0.05)


def silk_rect(x1, y1, x2, y2):
    return edge_rect(x1, y1, x2, y2, layer="F.SilkS", width=0.12)


# ============================================================================
# ESP32-C3-MINI-1 module footprint
# 13.2 x 16.6 mm body, 53 pads (52 castellated + 1 EPAD center).
# Pad layout per Espressif ESP32-C3-MINI-1 datasheet rev 1.1.
# ============================================================================
def esp32_c3_mini():
    name = "ESP32-C3-MINI-1"
    out = fp_header(name,
                    "ESP32-C3-MINI-1 Wi-Fi/BLE module, integrated antenna, 53-pad SMD",
                    "ESP32-C3 ESP32 WiFi BLE Espressif")
    out += fp_props(-9.5, 9.5, name)

    # Module body (13.2 x 16.6 mm).  Antenna is on +Y end.
    body_w = 13.2
    body_h = 16.6
    half_w = body_w / 2
    half_h = body_h / 2
    # Edge pads: 1.6 x 0.45 mm on the long sides at 0.8mm pitch.
    # The C3-MINI-1 has pins 1..13 along left, 14..26 along right (top),
    # 27..52 along bottom. Pad spacing 0.8 mm.
    # x-coord of edge-pad centerline = ±(body_w/2 + 0.5/2) = ±6.85 mm but the pad
    # sits straddling the edge: pad center at ±(half_w - 0.8) ≈ ±5.8mm...
    # Actually per datasheet, pad center is at half_w - 0.4 (pad width 1.6, half = 0.8):
    # pad straddles edge so center is at half_w - 0.8 = 5.8.
    pad_w = 1.6
    pad_h = 0.45
    pad_pitch = 0.8
    # Y-positions of left-side pads 1..13 (top to bottom)
    # First pad at y_top - 0.4 (offset 0.4mm from top edge per datasheet)
    # 13 pads spanning ~9.6mm so total run = (13-1)*0.8 = 9.6mm
    # Center the run: y_first = -(9.6/2) = -4.8 ... but let's use datasheet exact
    pads = []
    # Top edge: pads 1..13 on the left side of module (going from top-left down)
    # Datasheet "Pin 1" is at upper-left. 13 pads on left side, from y=-7.4 to y=2.2
    # Actually the C3-MINI-1 datasheet shows:
    # - 13 pads on bottom edge (pins 1-13)... no wait, let me use the C6 layout
    #   since the modules are physically identical.
    # We'll lay out pads:
    #   Pins 1-13: bottom edge, left-to-right at y = +half_h - 0.4
    #   Pins 14-26: right edge, bottom-to-top at x = +half_w - 0.4
    #   Pins 27-52: top edge, right-to-left at y = -half_h + 0.4
    #   Pin 53: center pad (EPAD, GND)
    # Edge pad center sits on the body edge:
    edge_off = pad_w / 2  # 0.8 -> pad straddles edge

    # Bottom row: pin 1 leftmost, pin 13 rightmost
    bot_y = half_h - edge_off + (pad_w / 2 - 0.4)  # straddling outward
    bot_y = half_h - 0.4  # center 0.4mm inside the edge so 0.8mm of pad is outside
    n_bot = 13
    bot_xs = [(-((n_bot - 1) * pad_pitch) / 2 + i * pad_pitch) for i in range(n_bot)]
    for i, x in enumerate(bot_xs):
        pads.append((str(i + 1), x, bot_y, pad_h, pad_w))  # rotated 90 (h<w on horizontal edge)

    # Right column: pin 14 bottom, pin 26 top
    right_x = half_w - 0.4
    n_right = 13
    right_ys = [(((n_right - 1) * pad_pitch) / 2 - i * pad_pitch) for i in range(n_right)]
    for i, y in enumerate(right_ys):
        pads.append((str(14 + i), right_x, y, pad_w, pad_h))

    # Top row: pin 27 rightmost, pin 52 leftmost (26 pads)
    top_y = -half_h + 0.4
    n_top = 26
    top_xs = [(((n_top - 1) * pad_pitch) / 2 - i * pad_pitch) for i in range(n_top)]
    for i, x in enumerate(top_xs):
        pads.append((str(27 + i), x, top_y, pad_h, pad_w))

    # Center EPAD (pad 53): one large 3.7 x 3.2 mm thermal pad
    pads.append(("53", 0.0, 0.0, 3.7, 3.2))

    for num, x, y, w, h in pads:
        out += smd_pad(num, x, y, w, h)

    # Body outline (F.Fab)
    out += edge_rect(-half_w, -half_h, half_w, half_h, "F.Fab", 0.1)
    # Silkscreen body (slightly outside pads)
    out += silk_rect(-half_w - 0.2, -half_h - 0.2, half_w + 0.2, half_h + 0.2)
    # Pin 1 marker on silk (top-left)
    out += silk_circle(-half_w - 0.7, half_h - 0.4, 0.3)
    # Courtyard
    out += courtyard_rect(-half_w - 1.0, -half_h - 1.0, half_w + 1.0, half_h + 1.0)

    out += ")\n"
    return out


# ============================================================================
# SA868 footprint — 16-pad castellated, ~36 x 22 mm body, 2.54 mm pad pitch
# Pad layout: 8 pads on each long side (left=1-8, right=16-9 from top)
# Per NiceRF SA868 datasheet
# ============================================================================
def sa868():
    name = "SA868"
    out = fp_header(name,
                    "NiceRF SA868 VHF/UHF embedded walkie-talkie module",
                    "VHF UHF radio walkie-talkie SA868 NiceRF")
    out += fp_props(-12.5, 12.5, name)

    body_w = 36.0
    body_h = 22.0
    half_w = body_w / 2
    half_h = body_h / 2
    pad_pitch = 2.54
    pad_w = 1.5
    pad_h = 2.4
    # 8 pads on each side
    n = 8
    # Y positions: top to bottom
    ys = [(((n - 1) * pad_pitch) / 2 - i * pad_pitch) for i in range(n)]

    # Left side: pins 1..8 (top to bottom)
    left_x = -half_w + 0.5  # pad center, straddling left edge
    for i, y in enumerate(ys):
        out += smd_pad(str(i + 1), left_x, y, pad_w, pad_h)
    # Right side: pins 16..9 (top to bottom; pin 9 at bottom, pin 16 at top)
    right_x = half_w - 0.5
    for i, y in enumerate(ys):
        out += smd_pad(str(16 - i), right_x, y, pad_w, pad_h)

    # Body & silk
    out += edge_rect(-half_w, -half_h, half_w, half_h, "F.Fab", 0.1)
    out += silk_rect(-half_w - 0.2, -half_h - 0.2, half_w + 0.2, half_h + 0.2)
    # Pin 1 marker (top-left)
    out += silk_circle(-half_w - 1.0, ys[0], 0.3)
    out += courtyard_rect(-half_w - 1.0, -half_h - 1.0, half_w + 1.0, half_h + 1.0)
    out += ")\n"
    return out


# ============================================================================
# TP4056_Module footprint — small breakout PCB header.
# Module is ~17 x 26 mm with 5 castellated pads on one short edge.
# We create a 1x05 2.54mm THT header pattern + module silhouette outline
# so the user can solder the breakout PCB on top via female header.
# ============================================================================
def tp4056_module():
    name = "TP4056_Module"
    out = fp_header(name,
                    "TP4056 LiPo charger breakout module, 5-pin 2.54mm header (IN+ IN- BAT+ BAT- OUT+)",
                    "TP4056 LiPo charger breakout 5-pin")
    out += fp_props(-15.0, 15.0, name)

    # 5-pin 2.54mm header along Y axis at x=0
    pad_pitch = 2.54
    n = 5
    drill = 1.0
    pad_d = 1.7
    ys = [(((n - 1) * pad_pitch) / 2 - i * pad_pitch) for i in range(n)]
    for i, y in enumerate(ys):
        # pin 1 = square pad
        shape = "rect" if i == 0 else "circle"
        out += thru_pad(str(i + 1), 0.0, y, drill, pad_d, shape)

    # Module outline silhouette (assumes module sits on top: 17 x 26 mm board
    # with the 5 pin header at one short edge that matches our header position)
    mod_x = -3.0  # header is near right edge of the module
    out += edge_rect(mod_x - 24.0, -8.5, mod_x + 0.0, 8.5, "F.Fab", 0.1)
    out += silk_rect(mod_x - 24.0, -8.5, mod_x + 0.0, 8.5)
    out += courtyard_rect(mod_x - 25.0, -10.0, 3.0, 10.0)
    # Pin 1 indicator
    out += silk_circle(-2.5, ys[0], 0.3)
    out += ")\n"
    return out


# ============================================================================
# OLED_SSD1306_7P — 1x07 2.54mm header for 0.96" SSD1306 OLED breakout.
# Module is ~27 x 27 mm.
# ============================================================================
def oled_ssd1306():
    name = "OLED_SSD1306_128x64_7P"
    out = fp_header(name,
                    "0.96 inch 128x64 SSD1306 OLED, 7-pin 2.54mm header (GND VCC SCK MOSI RES DC CS)",
                    "OLED SSD1306 0.96 7-pin display")
    out += fp_props(-16.0, 16.0, name)

    pad_pitch = 2.54
    n = 7
    drill = 1.0
    pad_d = 1.7
    ys = [(((n - 1) * pad_pitch) / 2 - i * pad_pitch) for i in range(n)]
    for i, y in enumerate(ys):
        shape = "rect" if i == 0 else "circle"
        out += thru_pad(str(i + 1), 0.0, y, drill, pad_d, shape)

    # Module silhouette (sits to +X side of the header, ~27mm wide x 27mm tall)
    out += edge_rect(2.5, -13.5, 2.5 + 25.0, 13.5, "F.Fab", 0.1)
    out += silk_rect(2.5, -13.5, 2.5 + 25.0, 13.5)
    out += courtyard_rect(-2.0, -14.0, 28.5, 14.0)
    out += silk_circle(-2.0, ys[0], 0.3)
    out += ")\n"
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fps = {
        "ESP32-C3-MINI-1": esp32_c3_mini(),
        "SA868": sa868(),
        "TP4056_Module": tp4056_module(),
        "OLED_SSD1306_128x64_7P": oled_ssd1306(),
    }
    for name, body in fps.items():
        path = OUT_DIR / f"{name}.kicad_mod"
        path.write_text(body)
        print(f"Wrote {path} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
