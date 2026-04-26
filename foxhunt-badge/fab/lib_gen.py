#!/usr/bin/env python3
"""Generate lib/foxhunt.kicad_sym with custom symbols not in stock KiCad libs.

Custom symbols:
  - ESP32-C3-MINI-1  (53-pin module, identical mech to ESP32-C6-MINI-1)
  - SA868           (16-pin VHF/UHF castellated radio module)
  - TP4056_Module   (5-pin LiPo charger breakout PCB)
  - OLED_SSD1306    (7-pin SSD1306 OLED breakout)
"""
from pathlib import Path

OUT = Path(__file__).parent.parent / "lib" / "foxhunt.kicad_sym"

HEADER = '(kicad_symbol_lib (version 20231120) (generator "foxhunt_lib_gen") (generator_version "9.0")\n'
FOOTER = ')\n'


def pin(num, name, x, y, orient, etype="passive", length=2.54, hide=False):
    h = " hide" if hide else ""
    safe_name = name.replace('"', '\\"')
    return (
        f'      (pin {etype} line\n'
        f'        (at {x:.3f} {y:.3f} {orient})\n'
        f'        (length {length:.3f}){h}\n'
        f'        (name "{safe_name}" (effects (font (size 1.27 1.27))))\n'
        f'        (number "{num}" (effects (font (size 1.27 1.27))))\n'
        f'      )'
    )


def make_symbol(name, ref, value, footprint, datasheet, description,
                pins_l, pins_r, pins_t=None, pins_b=None,
                body_w=20.32, extra_props=None, power=False):
    """Generic IC symbol with rectangular body and pins on each side."""
    pins_t = pins_t or []
    pins_b = pins_b or []
    side_l = len(pins_l)
    side_r = len(pins_r)
    side_t = len(pins_t)
    side_b = len(pins_b)
    grid = 2.54
    # body height: rows on left/right at 2.54mm pitch, with one slot of margin
    body_h = max(side_l, side_r) * grid + grid
    if side_t or side_b:
        # body width must accommodate top/bottom pins
        max_horiz = max(side_t, side_b)
        body_w = max(body_w, max_horiz * grid + grid)
    half_w = body_w / 2
    half_h = body_h / 2
    pin_lines = []

    # Left pins, top to bottom
    for i, p in enumerate(pins_l):
        y = half_h - grid * (i + 1)
        pin_lines.append(pin(p["num"], p["name"], -half_w - p.get("len", 2.54), y, 0,
                             p.get("etype", "passive"),
                             length=p.get("len", 2.54), hide=p.get("hide", False)))
    for i, p in enumerate(pins_r):
        y = half_h - grid * (i + 1)
        pin_lines.append(pin(p["num"], p["name"], half_w + p.get("len", 2.54), y, 180,
                             p.get("etype", "passive"),
                             length=p.get("len", 2.54), hide=p.get("hide", False)))
    for i, p in enumerate(pins_t):
        x = -half_w + grid * (i + 1)
        pin_lines.append(pin(p["num"], p["name"], x, half_h + p.get("len", 2.54), 270,
                             p.get("etype", "passive"),
                             length=p.get("len", 2.54), hide=p.get("hide", False)))
    for i, p in enumerate(pins_b):
        x = -half_w + grid * (i + 1)
        pin_lines.append(pin(p["num"], p["name"], x, -half_h - p.get("len", 2.54), 90,
                             p.get("etype", "passive"),
                             length=p.get("len", 2.54), hide=p.get("hide", False)))

    pwr = " (power)" if power else ""

    s = []
    s.append(f'  (symbol "{name}"{pwr}')
    s.append(f'    (exclude_from_sim no)')
    s.append(f'    (in_bom yes)')
    s.append(f'    (on_board yes)')
    s.append(f'    (property "Reference" "{ref}" (at {-half_w:.3f} {half_h + 2.54:.3f} 0)')
    s.append(f'      (effects (font (size 1.27 1.27)) (justify left bottom)))')
    s.append(f'    (property "Value" "{value}" (at {-half_w:.3f} {half_h + 0.508:.3f} 0)')
    s.append(f'      (effects (font (size 1.27 1.27)) (justify left bottom)))')
    s.append(f'    (property "Footprint" "{footprint}" (at 0 0 0)')
    s.append(f'      (effects (font (size 1.27 1.27)) (hide yes)))')
    s.append(f'    (property "Datasheet" "{datasheet}" (at 0 0 0)')
    s.append(f'      (effects (font (size 1.27 1.27)) (hide yes)))')
    s.append(f'    (property "Description" "{description}" (at 0 0 0)')
    s.append(f'      (effects (font (size 1.27 1.27)) (hide yes)))')
    if extra_props:
        for k, v in extra_props.items():
            s.append(f'    (property "{k}" "{v}" (at 0 0 0)')
            s.append(f'      (effects (font (size 1.27 1.27)) (hide yes)))')
    # body
    s.append(f'    (symbol "{name}_0_1"')
    s.append(f'      (rectangle (start {-half_w:.3f} {-half_h:.3f}) (end {half_w:.3f} {half_h:.3f})')
    s.append(f'        (stroke (width 0.254) (type default))')
    s.append(f'        (fill (type background))))')
    # pins unit
    s.append(f'    (symbol "{name}_1_1"')
    for pl in pin_lines:
        s.append(pl)
    s.append(f'    )')
    s.append(f'  )')
    return "\n".join(s) + "\n"


# === ESP32-C3-MINI-1 (53 pads per official Espressif datasheet v1.1) ===
# Pad numbering matches the official Espressif KiCad footprint
# (https://github.com/espressif/kicad-libraries):
#   Pads  1..11 : LEFT side (top to bottom in physical layout)
#   Pads 12..24 : BOTTOM row (left to right)
#   Pads 25..35 : RIGHT side (bottom to top)
#   Pads 36..48 : TOP row, antenna side (right to left)
#   Pad  49     : center thermal/GND EPAD
#   Pads 50..53 : corner mechanical pads (NC)
# Schematic symbol layout: we put the side pads on left/right of the
# rectangle, top-row pads on top, bottom-row pads on bottom.  Corner
# pads (50-53) and most NCs are hidden.
ESP32_PINS_LEFT = [
    {"num": "1",  "name": "GND",     "etype": "power_in"},
    {"num": "2",  "name": "GND",     "etype": "power_in"},
    {"num": "3",  "name": "3V3",     "etype": "power_in"},
    {"num": "4",  "name": "NC",      "etype": "no_connect", "hide": True},
    {"num": "5",  "name": "NC",      "etype": "no_connect", "hide": True},
    {"num": "6",  "name": "EN",      "etype": "input"},
    {"num": "7",  "name": "IO2",     "etype": "bidirectional"},  # ADC1_CH2, strap
    {"num": "8",  "name": "IO3",     "etype": "bidirectional"},  # ADC2_CH0
    {"num": "9",  "name": "NC",      "etype": "no_connect", "hide": True},
    {"num": "10", "name": "NC",      "etype": "no_connect", "hide": True},
    {"num": "11", "name": "IO10",    "etype": "bidirectional"},
]
# Bottom row 12..24 — IO0/1 + USB pads + IO8/9/20/21
_bot_map = {
    12: ("NC",        "no_connect",    True),
    13: ("IO0",       "bidirectional", False),  # ADC1_CH0, strap, WS2812 DIN
    14: ("IO1",       "bidirectional", False),  # ADC1_CH1
    15: ("NC",        "no_connect",    True),
    16: ("IO18/D-",   "bidirectional", False),  # USB D-
    17: ("IO19/D+",   "bidirectional", False),  # USB D+
    18: ("NC",        "no_connect",    True),
    19: ("IO9",       "bidirectional", False),  # strap, BOOT, BTN_SEL
    20: ("IO8",       "bidirectional", False),  # strap, BTN_DN
    21: ("NC",        "no_connect",    True),
    22: ("NC",        "no_connect",    True),
    23: ("IO20",      "bidirectional", False),  # U0RXD, SA868_RX
    24: ("IO21",      "bidirectional", False),  # U0TXD, OLED_RST
}
ESP32_PINS_BOTTOM = []
for n in range(12, 25):
    nm, et, hide = _bot_map.get(n, (f"NC{n}", "no_connect", True))
    ESP32_PINS_BOTTOM.append({"num": str(n), "name": nm, "etype": et, "hide": hide})
# Right side 25..35 — exposed: GPIO4-7
_right_map = {
    25: ("NC",        "no_connect",    True),
    26: ("NC",        "no_connect",    True),
    27: ("IO4",       "bidirectional", False),  # SA868_PTT
    28: ("IO5",       "bidirectional", False),  # OLED_CS
    29: ("NC",        "no_connect",    True),
    30: ("IO6",       "bidirectional", False),  # OLED_SCK
    31: ("IO7",       "bidirectional", False),  # OLED_MOSI
}
ESP32_PINS_RIGHT = []
for n in range(25, 36):
    nm, et, hide = _right_map.get(n, (f"NC{n}", "no_connect", True))
    ESP32_PINS_RIGHT.append({"num": str(n), "name": nm, "etype": et, "hide": hide})
# Top row 36..48 (antenna side) — all NC for the C3 module
ESP32_PINS_TOP = []
for n in range(36, 49):
    ESP32_PINS_TOP.append({"num": str(n), "name": f"NC{n}",
                           "etype": "no_connect", "hide": True})
# Pad 49 = center GND EPAD
ESP32_PINS_BOTTOM.append({"num": "49", "name": "GND_EPAD", "etype": "power_in"})
# Corner pads 50..53 — mechanical, NC
for n in range(50, 54):
    ESP32_PINS_BOTTOM.append({"num": str(n), "name": f"MNT{n-49}",
                              "etype": "no_connect", "hide": True})

ESP32_SYM = make_symbol(
    "ESP32-C3-MINI-1", "U", "ESP32-C3-MINI-1",
    "foxhunt:ESP32-C3-MINI-1",
    "https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf",
    "ESP32-C3 Wi-Fi/BLE module, integrated antenna, 53-pad SMD",
    ESP32_PINS_LEFT, ESP32_PINS_RIGHT,
    pins_t=ESP32_PINS_TOP, pins_b=ESP32_PINS_BOTTOM,
    body_w=33.02,
    extra_props={"ki_keywords": "ESP32 ESP32-C3 WiFi BLE Espressif",
                 "MPN": "ESP32-C3-MINI-1",
                 "LCSC": "C2934560"},
)

# === SA868 (16-pin VHF/UHF embedded radio module) ===
# G-NICERF SA868-V (VHF 134-174 MHz) / SA868-U (UHF 400-480 MHz)
# Castellated 16 pads, ~28 x 40 mm body, 2.54mm pad pitch
SA868_PINS_LEFT = [
    {"num": "1",  "name": "GND",       "etype": "power_in"},
    {"num": "2",  "name": "ANT",       "etype": "passive"},
    {"num": "3",  "name": "GND",       "etype": "power_in"},
    {"num": "4",  "name": "VBAT",      "etype": "power_in"},
    {"num": "5",  "name": "H/L",       "etype": "input"},
    {"num": "6",  "name": "RX_AUDIO",  "etype": "output"},
    {"num": "7",  "name": "MIC_IN",    "etype": "input"},
    {"num": "8",  "name": "PTT",       "etype": "input"},
]
SA868_PINS_RIGHT = [
    {"num": "16", "name": "GND",       "etype": "power_in"},
    {"num": "15", "name": "GND",       "etype": "power_in"},
    {"num": "14", "name": "GND",       "etype": "power_in"},
    {"num": "13", "name": "GND",       "etype": "power_in"},
    {"num": "12", "name": "TXD",       "etype": "output"},
    {"num": "11", "name": "RXD",       "etype": "input"},
    {"num": "10", "name": "PD",        "etype": "input"},
    {"num": "9",  "name": "SQ",        "etype": "output"},
]
SA868_SYM = make_symbol(
    "SA868", "U", "SA868-V",
    "foxhunt:SA868",
    "https://www.nicerf.com/sa868-uhf-vhf-walkie-talkie-module.html",
    "G-NiceRF SA868 VHF/UHF embedded walkie-talkie module, UART AT control",
    SA868_PINS_LEFT, SA868_PINS_RIGHT,
    body_w=20.32,
    extra_props={"ki_keywords": "VHF UHF radio walkie-talkie SA868 NiceRF",
                 "MPN": "SA868-V",
                 "LCSC": "C5184093"},
)

# === TP4056 charger module (5-pin breakout) ===
# Common LiPo charger breakout PCB with USB-MicroB, fits 17x26mm, 5 castellated pads:
# IN+, IN-, BAT+, BAT-, OUT+ (some variants add OUT- too; we use 5-pin convention)
TP4056_PINS_LEFT = [
    {"num": "1", "name": "IN+",  "etype": "power_in"},
    {"num": "2", "name": "IN-",  "etype": "passive"},
    {"num": "3", "name": "BAT+", "etype": "power_out"},
]
TP4056_PINS_RIGHT = [
    {"num": "5", "name": "OUT+", "etype": "power_out"},
    {"num": "4", "name": "BAT-", "etype": "passive"},
]
TP4056_SYM = make_symbol(
    "TP4056_Module", "U", "TP4056_Module",
    "foxhunt:TP4056_Module",
    "https://datasheet.lcsc.com/lcsc/2110150030_TPOWER-TP4056_C16581.pdf",
    "TP4056 LiPo charger breakout module, 1A USB charging, 5-pin castellated",
    TP4056_PINS_LEFT, TP4056_PINS_RIGHT,
    body_w=15.24,
    extra_props={"ki_keywords": "TP4056 LiPo charger breakout module",
                 "MPN": "TP4056_MODULE_5P",
                 "LCSC": "C16581"},
)

# === SSD1306 OLED 7-pin breakout ===
# 7-pin SPI version (more common): GND, VCC, SCK, MOSI, RES, DC, CS
OLED_PINS_LEFT = [
    {"num": "1", "name": "GND",  "etype": "power_in"},
    {"num": "2", "name": "VCC",  "etype": "power_in"},
    {"num": "3", "name": "SCK",  "etype": "input"},
    {"num": "4", "name": "MOSI", "etype": "input"},
    {"num": "5", "name": "RES",  "etype": "input"},
    {"num": "6", "name": "DC",   "etype": "input"},
    {"num": "7", "name": "CS",   "etype": "input"},
]
OLED_SYM = make_symbol(
    "OLED_SSD1306", "DISP", "OLED_SSD1306_128x64",
    "foxhunt:OLED_SSD1306_128x64_7P",
    "https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf",
    "0.96 inch 128x64 SSD1306 OLED breakout module, SPI, 7-pin header",
    OLED_PINS_LEFT, [],
    body_w=10.16,
    extra_props={"ki_keywords": "OLED display SSD1306 128x64",
                 "MPN": "SSD1306_OLED_096_SPI",
                 "LCSC": "C424116"},
)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = HEADER + ESP32_SYM + SA868_SYM + TP4056_SYM + OLED_SYM + FOOTER
    OUT.write_text(body)
    print(f"Wrote {OUT} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
