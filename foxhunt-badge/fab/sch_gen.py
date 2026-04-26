#!/usr/bin/env python3
"""Generate foxhunt-badge.kicad_sch — clean ERC-passing KiCad 9 schematic.

Convention
----------
* Symbol pin coords stored in symbol files use Y-positive-up.
* Schematic uses Y-positive-down.  Hence:
    abs_pin_x = Cx + sym_pin_x
    abs_pin_y = Cy - sym_pin_y
* For each connected pin, draw a 2.54mm wire stub outward + label at the tip.
* Outward direction (in schematic) by pin angle: 0->(-1,0), 90->(0,1),
  180->(1,0), 270->(0,-1).

GPIO assignment (ESP32-C3-MINI-1, official Espressif footprint)
---------------------------------------------------------------
| Function    | GPIO | Pad |
|-------------|------|-----|
| GND         | -    |  1  |
| GND         | -    |  2  |
| 3V3         | -    |  3  |
| EN          | -    |  6  |
| AUDIO ADC   | 2    |  7  |
| BTN_UP      | 3    |  8  |
| SA868_TX    | 10   | 11  |
| WS2812 DIN  | 0    | 13  |
| OLED_DC     | 1    | 14  |
| USB_DM      | 18   | 16  |
| USB_DP      | 19   | 17  |
| BTN_SEL     | 9    | 19  |
| BTN_DN      | 8    | 20  |
| SA868_RX    | 20   | 23  |
| OLED_RST    | 21   | 24  |
| SA868_PTT   | 4    | 27  |
| OLED_CS     | 5    | 28  |
| OLED_SCK    | 6    | 30  |
| OLED_MOSI   | 7    | 31  |
| GND (EPAD)  | -    | 49  |
"""
from __future__ import annotations
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "foxhunt-badge.kicad_sch"
STOCK = Path("/usr/share/kicad/symbols")
PROJECT_LIB = ROOT / "lib" / "foxhunt.kicad_sym"

sys.path.insert(0, str(Path(__file__).parent))
import lib_gen as LG  # type: ignore


GRID = 1.27
STUB = 2.54


def U(): return str(uuid.uuid4())
def snap(v): return round(v / GRID) * GRID
def C(x, y): return (snap(x), snap(y))


# ---------------------------------------------------------------------------
# Slurp library symbols (with extends)
# ---------------------------------------------------------------------------
def slurp_symbol(libpath: Path, name: str) -> str:
    text = libpath.read_text()
    m = re.search(rf'\n\s+\(symbol "{re.escape(name)}"', text)
    if not m:
        raise RuntimeError(f"symbol {name!r} not in {libpath}")
    start = m.start() + 1
    # advance to opening paren
    while text[start] in ' \t':
        start += 1
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise RuntimeError("unterminated symbol")


def slurp_with_extends(libpath: Path, name: str, accum: dict[str, str]):
    if name in accum:
        return
    blk = slurp_symbol(libpath, name)
    accum[name] = blk
    m = re.search(r'\(extends "([^"]+)"', blk)
    if m:
        slurp_with_extends(libpath, m.group(1), accum)


def _scan_subblocks(blk: str, head_re: str):
    """Yield (start, end) byte offsets of each top-level (X ...) subblock
    inside a (symbol "..." ...) wrapper, where head_re is the inner head
    pattern (e.g., r'\\(property "').  Walk balanced parens."""
    n = len(blk)
    # Find inside of outer parens
    i = blk.index("(") + 1
    while i < n:
        m = re.search(head_re, blk[i:])
        if not m:
            return
        start = i + m.start()
        depth = 0
        for j in range(start, n):
            c = blk[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    yield start, j + 1
                    i = j + 1
                    break
        else:
            return


def flatten_extends(libpath: Path, name: str) -> str:
    """If `name` is a derived symbol (has extends), inline its base's body
    geometry under the derived name and drop the extends directive.  Returns
    a single self-contained (symbol "<name>" ...) block."""
    blk = slurp_symbol(libpath, name)
    m = re.search(r'\(extends "([^"]+)"\s*\)', blk)
    if not m:
        return blk

    # Walk chain to base
    base_name = m.group(1)
    base_blk = flatten_extends(libpath, base_name)

    # Strip derived's (extends ...) line
    derived_no_ext = re.sub(r'\(extends "[^"]+"\s*\)\s*\n?', '', blk, count=1)

    # Pull base's body subblocks (ones we want to inherit):
    #   pin_numbers, pin_names, exclude_from_sim, in_bom, on_board,
    #   power, (symbol "<base>_X_Y" ...) units
    inherit_heads = [
        r'\(pin_numbers',
        r'\(pin_names',
        r'\(exclude_from_sim',
        r'\(in_bom',
        r'\(on_board',
        r'\(power\b',
        r'\(symbol "',  # body unit blocks
    ]
    inherited_parts: list[str] = []
    for head in inherit_heads:
        for s, e in _scan_subblocks(base_blk, head):
            inherited_parts.append(base_blk[s:e])

    # Rename body unit blocks: "<base_name>_X_Y" -> "<name>_X_Y"
    fixed_parts = []
    for part in inherited_parts:
        part = re.sub(rf'\(symbol "{re.escape(base_name)}_',
                      f'(symbol "{name}_', part)
        fixed_parts.append(part)

    # Insert inherited parts before the closing ')' of the derived block.
    # First, find the position of the LAST closing paren of derived block
    last_paren = derived_no_ext.rfind(")")
    insert_text = "\n\t\t" + "\n\t\t".join(p.replace("\n", "\n\t\t")
                                           for p in fixed_parts) + "\n\t"
    return derived_no_ext[:last_paren] + insert_text + derived_no_ext[last_paren:]


# ---------------------------------------------------------------------------
# Pin-coord registry (symbol-local, Y-positive-up)
# ---------------------------------------------------------------------------
PIN_COORDS = {
    "Device:R":       {"1": (0, 3.81, 270, "passive"),
                       "2": (0, -3.81, 90, "passive")},
    "Device:C":       {"1": (0, 3.81, 270, "passive"),
                       "2": (0, -3.81, 90, "passive")},
    "Device:C_Polarized":      {"1": (0, 3.81, 270, "passive"),
                       "2": (0, -3.81, 90, "passive")},
    "Device:LED":     {"1": (-3.81, 0, 0,   "passive"),
                       "2": ( 3.81, 0, 180, "passive")},
    "Diode:SS14":     {"1": (-3.81, 0, 0,   "passive"),
                       "2": ( 3.81, 0, 180, "passive")},
    "Switch:SW_Push": {"1": (-5.08, 0, 0,   "passive"),
                       "2": ( 5.08, 0, 180, "passive")},
    "Regulator_Linear:AP2112K-3.3": {
        "1": (-7.62,  2.54, 0,   "power_in"),
        "2": ( 0,    -7.62, 90,  "power_in"),
        "3": (-7.62, -2.54, 0,   "input"),
        "4": ( 7.62, -2.54, 180, "no_connect"),
        "5": ( 7.62,  2.54, 180, "power_out"),
    },
    "LED:WS2812B-2020": {
        "1": ( 7.62,  0,    180, "output"),
        "2": ( 0,    -7.62, 90,  "power_in"),
        "3": (-7.62,  0,    0,   "input"),
        "4": ( 0,     7.62, 270, "power_in"),
    },
    "Connector_Generic:Conn_01x02": {
        "1": (-5.08,  0,    0, "passive"),
        "2": (-5.08, -2.54, 0, "passive"),
    },
    "Connector_Generic:Conn_01x04": {
        "1": (-5.08,  2.54, 0, "passive"),
        "2": (-5.08,  0,    0, "passive"),
        "3": (-5.08, -2.54, 0, "passive"),
        "4": (-5.08, -5.08, 0, "passive"),
    },
    "Connector_Generic:Conn_01x07": {
        "1": (-5.08,  7.62, 0, "passive"),
        "2": (-5.08,  5.08, 0, "passive"),
        "3": (-5.08,  2.54, 0, "passive"),
        "4": (-5.08,  0,    0, "passive"),
        "5": (-5.08, -2.54, 0, "passive"),
        "6": (-5.08, -5.08, 0, "passive"),
        "7": (-5.08, -7.62, 0, "passive"),
    },
    "Connector_Generic:Conn_02x03_Counter_Clockwise": {
        "1": (-5.08,  2.54, 0,   "passive"),
        "2": (-5.08,  0,    0,   "passive"),
        "3": (-5.08, -2.54, 0,   "passive"),
        "6": ( 7.62,  2.54, 180, "passive"),
        "5": ( 7.62,  0,    180, "passive"),
        "4": ( 7.62, -2.54, 180, "passive"),
    },
    # USB-C 16P (USB2.0): pin coords from /usr/share/kicad/symbols/Connector.kicad_sym
    "Connector:USB_C_Receptacle_USB2.0_16P": {
        "S1":  ( -7.62, -22.86, 90,  "passive"),
        "A1":  ( 0,     -22.86, 90,  "passive"),
        "A12": ( 0,     -22.86, 90,  "passive"),
        "B1":  ( 0,     -22.86, 90,  "passive"),
        "B12": ( 0,     -22.86, 90,  "passive"),
        "A4":  ( 15.24,  15.24, 180, "passive"),
        "B4":  ( 15.24,  15.24, 180, "passive"),
        "A9":  ( 15.24,  15.24, 180, "passive"),
        "B9":  ( 15.24,  15.24, 180, "passive"),
        "A5":  ( 15.24,  10.16, 180, "passive"),
        "B5":  ( 15.24,   7.62, 180, "passive"),
        "A6":  ( 15.24,   2.54, 180, "passive"),
        "B6":  ( 15.24,   2.54, 180, "passive"),
        "A7":  ( 15.24,   0,    180, "passive"),
        "B7":  ( 15.24,   0,    180, "passive"),
        "A8":  ( 15.24,  -5.08, 180, "passive"),
        "B8":  ( 15.24,  -7.62, 180, "passive"),
    },
    # Power flag-class symbols
    "power:+3V3":  {"1": (0, 0, 90, "power_in")},
    "power:VBUS":  {"1": (0, 0, 90, "power_in")},
    "power:VBAT":  {"1": (0, 0, 90, "power_in")},
    "power:GND":   {"1": (0, 0, 270, "power_in")},
    "power:PWR_FLAG": {"1": (0, 0, 90, "power_out")},
}


def custom_pins(pins_l, pins_r, pins_b=None, body_w=20.32, pin_len=2.54):
    pins_b = pins_b or []
    body_h = max(len(pins_l), len(pins_r)) * 2.54 + 2.54
    if pins_b:
        body_w = max(body_w, len(pins_b) * 2.54 + 2.54)
    half_w, half_h = body_w / 2, body_h / 2
    out = {}
    for i, p in enumerate(pins_l):
        out[p["num"]] = (-half_w - pin_len,
                         half_h - 2.54 * (i + 1),
                         0, p.get("etype", "passive"))
    for i, p in enumerate(pins_r):
        out[p["num"]] = (half_w + pin_len,
                         half_h - 2.54 * (i + 1),
                         180, p.get("etype", "passive"))
    for i, p in enumerate(pins_b):
        out[p["num"]] = (-half_w + 2.54 * (i + 1),
                         -half_h - pin_len,
                         90, p.get("etype", "passive"))
    return out


PIN_COORDS["foxhunt:ESP32-C3-MINI-1"] = custom_pins(
    LG.ESP32_PINS_LEFT, LG.ESP32_PINS_RIGHT, LG.ESP32_PINS_BOTTOM, body_w=22.86)
PIN_COORDS["foxhunt:SA868"] = custom_pins(
    LG.SA868_PINS_LEFT, LG.SA868_PINS_RIGHT, body_w=20.32)
PIN_COORDS["foxhunt:TP4056_Module"] = custom_pins(
    LG.TP4056_PINS_LEFT, LG.TP4056_PINS_RIGHT, body_w=15.24)
PIN_COORDS["foxhunt:OLED_SSD1306"] = custom_pins(
    LG.OLED_PINS_LEFT, [], body_w=10.16)


def extract_pins_from_block(symbol_block: str) -> dict[str, tuple[float, float, int, str]]:
    """Walk every (pin TYPE line (at X Y A) ... (number "N") ...) inside a
    flattened (symbol "..." ...) block and return {num: (x, y, angle, type)}.
    """
    out: dict[str, tuple[float, float, int, str]] = {}
    for m in re.finditer(
        r'\(pin\s+(\w+)\s+\w+\s*\(at\s+([\d\.\-]+)\s+([\d\.\-]+)\s+(\d+)\)',
        symbol_block, re.S
    ):
        ptype = m.group(1)
        x, y, ang = float(m.group(2)), float(m.group(3)), int(m.group(4))
        # Find the (number "N") that follows this pin
        rest = symbol_block[m.end():]
        nm = re.search(r'\(number "([^"]+)"', rest)
        if not nm:
            continue
        # Make sure the number is INSIDE this pin block (within first balanced
        # close).  Easiest heuristic: the (number ...) shouldn't span past the
        # next (pin start.
        next_pin = re.search(r'\(pin\s+\w+\s+\w+\s*\(at', rest)
        if next_pin and nm.start() > next_pin.start():
            continue
        out[nm.group(1)] = (x, y, ang, ptype)
    return out


def autoload_pin_coords():
    """Override hardcoded entries by parsing the actual library files.
    This ensures wire stub endpoints line up with the symbol's true pin
    positions in lib_symbols."""
    seen_libids = sorted({c["lib_id"] for c in COMPS})
    for libid in seen_libids:
        lib_part, sym_name = libid.split(":", 1)
        if lib_part == "foxhunt":
            libpath = PROJECT_LIB
        else:
            libpath = STOCK / f"{lib_part}.kicad_sym"
        flat = flatten_extends(libpath, sym_name)
        pins = extract_pins_from_block(flat)
        if pins:
            PIN_COORDS[libid] = pins  # always override


# `COMPS` is empty at this point — populate AFTER components are added.
def _compute_post_comps():
    """Call after all comp() calls — overrides stock symbol pin coords from
    the actual stock library files."""
    autoload_pin_coords()
    # Snap all coords to grid
    for libid, pins in PIN_COORDS.items():
        for num in list(pins.keys()):
            x, y, ang, et = pins[num]
            pins[num] = (snap(x), snap(y), ang, et)


# ---------------------------------------------------------------------------
# Outward direction lookup (schematic frame, Y-positive-down)
# ---------------------------------------------------------------------------
OUTWARD = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}


def abs_pin(c, pin_num):
    """Return (abs_x, abs_y, angle, etype) for a pin of placed component c."""
    libid = c["lib_id"]
    if libid not in PIN_COORDS:
        raise RuntimeError(f"missing pin coords for {libid}")
    if pin_num not in PIN_COORDS[libid]:
        raise RuntimeError(f"pin {pin_num} not in {libid}; have "
                           f"{sorted(PIN_COORDS[libid].keys())[:8]}")
    sx, sy, ang, et = PIN_COORDS[libid][pin_num]
    return (snap(c["x"] + sx), snap(c["y"] - sy), ang, et)


# ===========================================================================
# Components
# ===========================================================================
COMPS = []


def comp(ref, lib_id, value, footprint, x, y):
    px, py = C(x, y)
    COMPS.append(dict(ref=ref, lib_id=lib_id, value=value,
                      footprint=footprint, x=px, y=py, uuid=U()))


# Power flag drivers (each driver has a one-pin power_out at (x,y))
def pflag(ref, libid, x, y):
    px, py = C(x, y)
    COMPS.append(dict(ref=ref, lib_id=libid, value=libid.split(":")[-1],
                      footprint="", x=px, y=py, uuid=U(), is_power=True))


# --- Zone 1: USB-C input + Schottky + CC pulldowns ---
comp("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB_C_USB2.0_16P",
     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 60, 100)
comp("R1", "Device:R", "5.1k", "Resistor_SMD:R_0603_1608Metric", 90, 100)
comp("R2", "Device:R", "5.1k", "Resistor_SMD:R_0603_1608Metric", 95, 115)
comp("D1", "Diode:SS14", "SS14", "Diode_SMD:D_SOD-123", 105, 90)

# --- Zone 2: TP4056 + battery JST + 470uF bulk ---
comp("U4", "foxhunt:TP4056_Module", "TP4056_Module",
     "foxhunt:TP4056_Module", 130, 95)
comp("J4", "Connector_Generic:Conn_01x02", "Battery",
     "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", 130, 125)
comp("C20", "Device:C_Polarized", "470uF/10V", "Capacitor_SMD:CP_Elec_8x10", 155, 100)

# --- Zone 3: AP2112K-3.3 LDO + decoupling ---
comp("C1", "Device:C", "1uF",  "Capacitor_SMD:C_0603_1608Metric", 175, 100)
comp("U1", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3",
     "Package_TO_SOT_SMD:SOT-23-5", 195, 100)
comp("C2", "Device:C", "1uF",  "Capacitor_SMD:C_0603_1608Metric", 215, 100)

# --- Zone 4: ESP32-C3-MINI-1 + decoupling + reset RC + strap pulls ---
comp("U2", "foxhunt:ESP32-C3-MINI-1", "ESP32-C3-MINI-1",
     "foxhunt:ESP32-C3-MINI-1", 250, 110)
comp("C5", "Device:C", "10uF", "Capacitor_SMD:C_0603_1608Metric", 235, 75)
comp("C6", "Device:C", "1uF",  "Capacitor_SMD:C_0603_1608Metric", 245, 75)
comp("C21", "Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 255, 75)
comp("S1", "Switch:SW_Push", "RESET",
     "Button_Switch_SMD:SW_SPST_TL3342", 230, 150)
comp("R4", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 215, 145)
comp("C7", "Device:C", "1uF", "Capacitor_SMD:C_0603_1608Metric", 205, 145)

# --- Zone 5: SA868 + audio LPF + RX bias + antenna match + pulls ---
comp("U3", "foxhunt:SA868", "SA868-V", "foxhunt:SA868", 350, 115)
comp("R7", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 320, 90)
comp("R8", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 320, 75)
comp("R30","Device:R", "1k",  "Resistor_SMD:R_0603_1608Metric", 320, 105)
# Audio TX low-pass
comp("R31","Device:R", "1k",  "Resistor_SMD:R_0603_1608Metric", 305, 145)
comp("C30","Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 315, 155)
comp("R32","Device:R", "1k",  "Resistor_SMD:R_0603_1608Metric", 325, 145)
comp("C31","Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 335, 155)
comp("C32","Device:C", "1uF", "Capacitor_SMD:C_0603_1608Metric", 345, 145)
# Audio RX bias
comp("C40","Device:C", "1uF", "Capacitor_SMD:C_0603_1608Metric", 305, 175)
comp("R40","Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 320, 175)
comp("R41","Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 320, 190)
# Antenna match
comp("L1", "Device:R", "0R",  "Resistor_SMD:R_0603_1608Metric", 385, 110)
comp("C50","Device:C", "DNP", "Capacitor_SMD:C_0603_1608Metric", 380, 125)
comp("C51","Device:C", "DNP", "Capacitor_SMD:C_0603_1608Metric", 395, 125)

# --- Zone 6: OLED display + status LED ---
comp("DISP1", "foxhunt:OLED_SSD1306", "OLED_SSD1306",
     "foxhunt:OLED_SSD1306_128x64_7P", 430, 80)
comp("D2", "Device:LED", "GREEN", "LED_SMD:LED_0603_1608Metric", 440, 50)
comp("R3", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 455, 50)

# --- Zone 7: WS2812B chain + decoupling ---
comp("R11","Device:R", "220R", "Resistor_SMD:R_0603_1608Metric", 405, 145)
comp("D3", "LED:WS2812B-2020", "WS2812B-2020",
     "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", 420, 145)
comp("D4", "LED:WS2812B-2020", "WS2812B-2020",
     "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", 445, 145)
comp("D5", "LED:WS2812B-2020", "WS2812B-2020",
     "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", 470, 145)
comp("D6", "LED:WS2812B-2020", "WS2812B-2020",
     "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", 495, 145)
comp("C12","Device:C", "10uF", "Capacitor_SMD:C_0603_1608Metric", 415, 165)
comp("C8", "Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 425, 165)
comp("C9", "Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 450, 165)
comp("C10","Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 475, 165)
comp("C11","Device:C", "100nF","Capacitor_SMD:C_0603_1608Metric", 500, 165)

# --- Zone 8: Buttons + pull-ups ---
comp("S2", "Switch:SW_Push", "SEL/BOOT",
     "Button_Switch_SMD:SW_SPST_TL3342", 465, 200)
comp("S3", "Switch:SW_Push", "UP",
     "Button_Switch_SMD:SW_SPST_TL3342", 440, 200)
comp("S4", "Switch:SW_Push", "DOWN",
     "Button_Switch_SMD:SW_SPST_TL3342", 490, 200)
comp("R12","Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 440, 185)
comp("R5", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 465, 185)
comp("R13","Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 475, 185)
comp("R14","Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 490, 185)
comp("R6", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 500, 185)
# GPIO0 (LED chain) keep-low-at-boot pull-down
comp("R9", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 280, 75)

# --- Zone 9: Headers ---
comp("J2", "Connector_Generic:Conn_02x03_Counter_Clockwise", "SAO",
     "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical", 530, 200)
comp("J3", "Connector_Generic:Conn_01x04", "Debug",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", 545, 130)

# --- Power flag drivers ---
pflag("#FLG_VBUS",     "power:PWR_FLAG", 50, 88)
pflag("#FLG_VBAT_RAW", "power:PWR_FLAG", 110, 78)
pflag("#FLG_GND",      "power:PWR_FLAG", 50, 145)


# ===========================================================================
# Net assignments  (net_name -> [(ref, pin_num), ...])
# Pin numbers reference the schematic symbol's pin numbers (which match the
# footprint pad numbers).
# ===========================================================================
NETS = {
    # ---- Power rails ----
    "VBUS": [
        ("J1", "A4"), ("J1", "B4"), ("J1", "A9"), ("J1", "B9"),
        ("D1", "2"),
        ("#FLG_VBUS", "1"),
    ],
    "VBAT_RAW": [
        ("D1", "1"),
        ("U4", "1"),
        ("#FLG_VBAT_RAW", "1"),
    ],
    "VBAT": [
        ("U4", "3"), ("J4", "1"),
        ("C20", "1"),
        ("C1", "1"),
        ("U1", "1"), ("U1", "3"),
        ("U3", "4"),
        ("R7", "1"), ("R8", "1"),
    ],
    "USB_OUT": [("U4", "5")],
    "+3V3": [
        ("U1", "5"),
        ("C2", "1"), ("C5", "1"), ("C6", "1"), ("C21", "1"),
        ("R4", "1"),
        ("U2", "3"),
        ("DISP1", "2"),
        ("D3", "4"), ("D4", "4"), ("D5", "4"), ("D6", "4"),
        ("C8", "1"), ("C9", "1"), ("C10", "1"), ("C11", "1"), ("C12", "1"),
        ("R5", "1"), ("R6", "1"), ("R12", "1"), ("R13", "1"), ("R14", "1"),
        ("R40", "1"),
        ("R3", "1"),
        ("J2", "6"), ("J3", "2"),
    ],
    "GND": [
        ("J1", "A1"), ("J1", "A12"), ("J1", "B1"), ("J1", "B12"), ("J1", "S1"),
        ("R1", "2"), ("R2", "2"),
        ("U4", "2"), ("U4", "4"),
        ("J4", "2"),
        ("C20", "2"), ("U1", "2"),
        ("C1", "2"), ("C2", "2"), ("C5", "2"), ("C6", "2"), ("C7", "2"), ("C21", "2"),
        ("U2", "1"), ("U2", "2"), ("U2", "49"),
        ("U3", "1"), ("U3", "3"), ("U3", "13"), ("U3", "14"),
        ("U3", "15"), ("U3", "16"),
        ("U3", "5"),  # H/L tied to GND for low power mode
        ("R10_PRESERVED_PLACEHOLDER_unused", "x"),  # removed below
        ("R41", "2"),
        ("C30", "2"), ("C31", "2"),
        ("C50", "2"), ("C51", "2"),
        ("D2", "1"),
        ("S1", "1"), ("S2", "1"), ("S3", "1"), ("S4", "1"),
        ("D3", "2"), ("D4", "2"), ("D5", "2"), ("D6", "2"),
        ("C8", "2"), ("C9", "2"), ("C10", "2"), ("C11", "2"), ("C12", "2"),
        ("DISP1", "1"),
        ("J2", "1"), ("J3", "1"),
        ("R9", "2"),
        ("#FLG_GND", "1"),
    ],
    # ---- USB-C CC ----
    "CC1": [("J1", "A5"), ("R1", "1")],
    "CC2": [("J1", "B5"), ("R2", "1")],
    # ---- USB D+/D- ----
    "USB_DP": [("J1", "A6"), ("J1", "B6"), ("U2", "17")],   # GPIO19 = pad 17
    "USB_DM": [("J1", "A7"), ("J1", "B7"), ("U2", "16")],   # GPIO18 = pad 16
    # ---- EN reset RC ----
    "EN": [("U2", "6"), ("R4", "2"), ("S1", "2"), ("C7", "1")],   # CHIP_PU = pad 6
    # ---- Status LED chain ----
    "STAT_LED_NODE": [("R3", "2"), ("D2", "2")],
    # ---- WS2812 chain (GPIO0 -> R11 220R -> D3..D6) ----
    "LED_DIN_RAW": [("U2", "13"), ("R11", "1"), ("R9", "1")], # GPIO0 = pad 13
    "LED_DIN":     [("R11", "2"), ("D3", "3")],
    "LED_C1":      [("D3", "1"), ("D4", "3")],
    "LED_C2":      [("D4", "1"), ("D5", "3")],
    "LED_C3":      [("D5", "1"), ("D6", "3")],
    "LED_END":     [("D6", "1")],
    # ---- OLED SPI ----
    "OLED_CS":   [("U2", "28"), ("DISP1", "7")],   # GPIO5 = pad 28
    "OLED_SCK":  [("U2", "30"), ("DISP1", "3")],   # GPIO6 = pad 30
    "OLED_MOSI": [("U2", "31"), ("DISP1", "4")],   # GPIO7 = pad 31
    "OLED_DC":   [("U2", "14"), ("DISP1", "6")],   # GPIO1 = pad 14
    "OLED_RST":  [("U2", "24"), ("DISP1", "5")],   # GPIO21 = pad 24
    # ---- SA868 control ----
    "SA868_PTT": [("U2", "27"), ("U3", "8"),  ("R7", "2")],   # GPIO4 = pad 27
    "SA868_PD":  [("U3", "10"), ("R8", "2")],                  # PD held high via R8
    "SA868_TX":  [("U2", "11"), ("R30", "1")],                 # GPIO10 = pad 11
    "SA868_RX":  [("U2", "23"), ("U3", "12"), ("J3", "3")],   # GPIO20 = pad 23; debug tap
    "SA868_TX_INT": [("R30", "2"), ("U3", "11")],              # series resistor to RXD
    "SA868_SQ":  [("U3", "9")],                                # squelch — leave as NC
    # ---- Audio TX path (GPIO not assigned in this rev — direct GPIO would
    #      need an extra pin; TX audio is optional. For revs with mic, route
    #      from a free GPIO. Mark MIC chain orphan-but-driven via NC for now.)
    "TX_LPF_A":  [("R31", "2"), ("C30", "1"), ("R32", "1")],
    "TX_LPF_B":  [("R32", "2"), ("C31", "1"), ("C32", "1")],
    "SA868_MIC": [("C32", "2"), ("U3", "7")],
    "TX_LPF_IN": [("R31", "1")],   # optional MIC drive — tied to GND via R10 below to avoid float
    # ---- Audio RX path (SA868 RX_OUT -> C40 -> bias node -> ESP GPIO2 ADC) ----
    "SA868_RX_OUT": [("U3", "6"), ("C40", "1")],
    "SA868_AUDIO":  [("C40", "2"), ("R40", "2"), ("R41", "1"),
                     ("U2", "7")],   # GPIO2 = pad 7 (ADC1_CH2)
    # ---- Antenna ----
    "ANT_OUT":   [("U3", "2"), ("L1", "1"), ("C50", "1")],
    "ANT_TRACE": [("L1", "2"), ("C51", "1")],
    # ---- Buttons ----
    "BTN_UP":    [("U2", "8"),  ("S3", "2"), ("R12", "2")],   # GPIO3 = pad 8
    "BTN_SEL":   [("U2", "19"), ("S2", "2"), ("R5", "2"),
                  ("R13", "2")],                                # GPIO9 = pad 19
    "BTN_DN":    [("U2", "20"), ("S4", "2"), ("R14", "2"),
                  ("R6", "2")],                                 # GPIO8 = pad 20
    # ---- SAO ----
    "SAO_GPIO1": [("J2", "3")],
    "SAO_GPIO2": [("J2", "2")],
    "SAO_GPIO3": [("J2", "5")],
    "SAO_GPIO4": [("J2", "4")],
    # ---- Debug header ----
    "DBG_RX_PROBE": [("J3", "4")],   # tied to nothing else — labeled probe pad
}

# `R10` was placeholder; we removed strap pull from GPIO2 since GPIO2 is now
# the ADC input.  Drop the placeholder entry above.
NETS["GND"] = [pp for pp in NETS["GND"] if pp[0] != "R10_PRESERVED_PLACEHOLDER_unused"]

# Use R10 (kept in COMPS list further up?  Not added.) — remove from BoM by
# not including it.  Drop the unused R10 reference.
# (R10 is not in COMPS; nothing to do.)

# ---- Tie GND to TX_LPF_IN (so unused MIC chain endpoint is grounded) ----
NETS["GND"].append(("R31", "1"))     # TX path input grounded; future MIC source can replace
del NETS["TX_LPF_IN"]

# ---- DBG_RX_PROBE is unused; drop the net so J3 pin 4 gets a NoConnect ----
del NETS["DBG_RX_PROBE"]


# Override hardcoded coords with actual stock library pin coords.
_compute_post_comps()


# ===========================================================================
# Validate: every pin appears in at most one net.
# ===========================================================================
def validate_nets():
    seen = {}
    for net, pins in NETS.items():
        for ref, num in pins:
            key = (ref, num)
            if key in seen:
                raise RuntimeError(
                    f"pin {ref}.{num} in both {seen[key]!r} and {net!r}")
            seen[key] = net
    return seen


pin_to_net = validate_nets()


# ===========================================================================
# Emit: lib_symbols section, components, wires, labels, no_connects.
# ===========================================================================
def build_lib_symbols() -> str:
    """Read all needed (symbol ...) blocks; assemble lib_symbols section.
    Derived symbols (extends) are flattened so each lib_symbols entry is
    self-contained."""
    needed_libids = set(c["lib_id"] for c in COMPS)
    # Also include the power symbols we use for net-port labels
    needed_libids.update(POWER_SYMBOL_NET.values())
    needed_libids = sorted(needed_libids)
    blocks: dict[str, str] = {}  # by qualified lib_id
    for libid in needed_libids:
        lib_part, sym_name = libid.split(":", 1)
        if lib_part == "foxhunt":
            libpath = PROJECT_LIB
        else:
            libpath = STOCK / f"{lib_part}.kicad_sym"
        flat = flatten_extends(libpath, sym_name)
        # Rename header to qualified lib_id
        flat = re.sub(rf'^\(symbol "{re.escape(sym_name)}"',
                      f'(symbol "{lib_part}:{sym_name}"', flat, count=1)
        blocks[f"{lib_part}:{sym_name}"] = flat

    parts = ["\t(lib_symbols"]
    for name in sorted(blocks):
        body = blocks[name]
        for line in body.splitlines():
            parts.append("\t\t" + line)
    parts.append("\t)")
    return "\n".join(parts)


def emit_component(c) -> str:
    """Emit (symbol ...) instance for a placed component."""
    libid = c["lib_id"]
    is_power = c.get("is_power", False)
    # Default property positions
    px, py = c["x"], c["y"]
    parts = []
    parts.append(f'\t(symbol')
    parts.append(f'\t\t(lib_id "{libid}")')
    parts.append(f'\t\t(at {px:.3f} {py:.3f} 0)')
    parts.append(f'\t\t(unit 1)')
    parts.append(f'\t\t(exclude_from_sim no)')
    parts.append(f'\t\t(in_bom yes)')
    parts.append(f'\t\t(on_board yes)')
    parts.append(f'\t\t(dnp no)')
    parts.append(f'\t\t(uuid "{c["uuid"]}")')
    parts.append(f'\t\t(property "Reference" "{c["ref"]}"')
    parts.append(f'\t\t\t(at {px + 5:.3f} {py - 6:.3f} 0)')
    parts.append(f'\t\t\t(effects (font (size 1.27 1.27))'
                 f'{" (hide yes)" if is_power else ""})')
    parts.append(f'\t\t)')
    parts.append(f'\t\t(property "Value" "{c["value"]}"')
    parts.append(f'\t\t\t(at {px + 5:.3f} {py - 3:.3f} 0)')
    parts.append(f'\t\t\t(effects (font (size 1.27 1.27)))')
    parts.append(f'\t\t)')
    parts.append(f'\t\t(property "Footprint" "{c.get("footprint","")}"')
    parts.append(f'\t\t\t(at {px:.3f} {py:.3f} 0)')
    parts.append(f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes))')
    parts.append(f'\t\t)')
    parts.append(f'\t\t(property "Datasheet" ""')
    parts.append(f'\t\t\t(at {px:.3f} {py:.3f} 0)')
    parts.append(f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes))')
    parts.append(f'\t\t)')
    parts.append(f'\t\t(property "Description" ""')
    parts.append(f'\t\t\t(at {px:.3f} {py:.3f} 0)')
    parts.append(f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes))')
    parts.append(f'\t\t)')
    # pin uuid map — each pin needs a (pin "<num>" (uuid ...)) entry
    if libid in PIN_COORDS:
        for pn in sorted(PIN_COORDS[libid].keys()):
            parts.append(f'\t\t(pin "{pn}" (uuid "{U()}"))')
    parts.append(f'\t\t(instances')
    parts.append(f'\t\t\t(project "foxhunt-badge"')
    parts.append(f'\t\t\t\t(path "/{SHEET_UUID}"')
    parts.append(f'\t\t\t\t\t(reference "{c["ref"]}") (unit 1)')
    parts.append(f'\t\t\t\t)')
    parts.append(f'\t\t\t)')
    parts.append(f'\t\t)')
    parts.append(f'\t)')
    return "\n".join(parts)


def emit_wire(x1, y1, x2, y2) -> str:
    return (f'\t(wire (pts (xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f}))'
            f'\n\t\t(stroke (width 0) (type default))'
            f'\n\t\t(uuid "{U()}"))')


def emit_label(x, y, text, angle=0) -> str:
    return (f'\t(label "{text}" (at {x:.3f} {y:.3f} {angle})'
            f'\n\t\t(effects (font (size 1.27 1.27)) (justify left bottom))'
            f'\n\t\t(uuid "{U()}"))')


def emit_no_connect(x, y) -> str:
    return f'\t(no_connect (at {x:.3f} {y:.3f}) (uuid "{U()}"))'


def emit_junction(x, y) -> str:
    return (f'\t(junction (at {x:.3f} {y:.3f}) (diameter 0)'
            f'\n\t\t(color 0 0 0 0) (uuid "{U()}"))')


# Schematic UUID — used in (path "/<uuid>") for instances
SHEET_UUID = U()


def emit_power_symbol(x, y, libid, ref_id, ang):
    """Emit a power port symbol (power:GND, power:+3V3, etc.) anchored at
    a wire endpoint.  Rotation chosen so the label sits AWAY from the pin
    (outward).  ang is the OUTWARD direction in degrees:
        0 = +X (right), 90 = -Y (up), 180 = -X (left), 270 = +Y (down)."""
    sym_name = libid.split(":", 1)[1]
    rot = {0: 90, 90: 0, 180: 270, 270: 180}.get(ang, 0)
    return (
        f'\t(symbol\n'
        f'\t\t(lib_id "{libid}")\n'
        f'\t\t(at {x:.3f} {y:.3f} {rot})\n'
        f'\t\t(unit 1)\n'
        f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
        f'\t\t(uuid "{U()}")\n'
        f'\t\t(property "Reference" "#PWR{ref_id}" (at {x:.3f} {y - 3:.3f} 0)\n'
        f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'\t\t(property "Value" "{sym_name}" (at {x:.3f} {y - 1.5:.3f} {rot})\n'
        f'\t\t\t(effects (font (size 1.27 1.27))))\n'
        f'\t\t(property "Footprint" "" (at {x:.3f} {y:.3f} 0)\n'
        f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'\t\t(property "Datasheet" "" (at {x:.3f} {y:.3f} 0)\n'
        f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))\n'
        f'\t\t(pin "1" (uuid "{U()}"))\n'
        f'\t\t(instances\n'
        f'\t\t\t(project "foxhunt-badge"\n'
        f'\t\t\t\t(path "/{SHEET_UUID}"\n'
        f'\t\t\t\t\t(reference "#PWR{ref_id}") (unit 1))))\n'
        f'\t)'
    )


# Power nets that should use power symbols instead of net labels at every
# pin (KiCad convention).  Stock power lib has GND, +3V3, VBUS but no
# VBAT; VBAT/VBAT_RAW remain as net labels.
POWER_SYMBOL_NET = {
    "GND":      "power:GND",
    "+3V3":     "power:+3V3",
    "VBUS":     "power:VBUS",
}


def build_wires_labels():
    """For each (component, pin) in NETS, emit wire stub + either a net
    label (signal) or a power symbol (GND, +3V3, etc.)."""
    out = []
    covered_pins = set()
    pwr_id_counter = [100]  # for unique #PWR refs

    def next_pwr_id():
        pwr_id_counter[0] += 1
        return pwr_id_counter[0]

    label_orient = {  # outward direction -> KiCad label angle
        ( 1,  0): 0,    # right
        ( 0,  1): 270,  # down
        (-1,  0): 180,  # left
        ( 0, -1): 90,   # up
    }
    outward_deg = {(1,0): 0, (0,1): 270, (-1,0): 180, (0,-1): 90}
    for net, pins in NETS.items():
        # Single-pin nets become NoConnect markers (no label, no wire)
        if len(pins) == 1:
            ref, num = pins[0]
            c = next(c for c in COMPS if c["ref"] == ref)
            ax, ay, ang, et = abs_pin(c, num)
            covered_pins.add((ref, num))
            out.append(emit_no_connect(ax, ay))
            continue
        is_power = net in POWER_SYMBOL_NET
        for ref, num in pins:
            c = next(c for c in COMPS if c["ref"] == ref)
            ax, ay, ang, et = abs_pin(c, num)
            covered_pins.add((ref, num))
            dx, dy = OUTWARD[ang]
            ex, ey = snap(ax + dx * STUB), snap(ay + dy * STUB)
            out.append(emit_wire(ax, ay, ex, ey))
            if is_power:
                pwr_libid = POWER_SYMBOL_NET[net]
                out.append(emit_power_symbol(
                    ex, ey, pwr_libid, next_pwr_id(),
                    outward_deg[(dx, dy)]))
            else:
                out.append(emit_label(ex, ey, net,
                                      angle=label_orient[(dx, dy)]))
    # NoConnect every visible pin not in any net
    for c in COMPS:
        libid = c["lib_id"]
        if libid not in PIN_COORDS:
            continue
        # Hidden pins (NC pins on ESP32) — skip.  Use lib_gen pin meta to
        # find which pins are hidden.
        hidden = set()
        if libid == "foxhunt:ESP32-C3-MINI-1":
            for p in (LG.ESP32_PINS_LEFT + LG.ESP32_PINS_RIGHT
                      + LG.ESP32_PINS_TOP + LG.ESP32_PINS_BOTTOM):
                if p.get("hide"):
                    hidden.add(p["num"])
        if libid == "Regulator_Linear:AP2112K-3.3":
            hidden.add("4")  # NC pin on AP2112; mark NoConnect explicitly below
        for pn in PIN_COORDS[libid]:
            if (c["ref"], pn) in covered_pins:
                continue
            if pn in hidden:
                continue
            ax, ay, _, _ = abs_pin(c, pn)
            out.append(emit_no_connect(ax, ay))
    # AP2112 pin 4 is NC — explicitly NoConnect it
    return "\n".join(out)


def build_schematic() -> str:
    out = []
    out.append("(kicad_sch")
    out.append('\t(version 20250114)')
    out.append('\t(generator "foxhunt_sch_gen")')
    out.append('\t(generator_version "9.0")')
    out.append(f'\t(uuid "{SHEET_UUID}")')
    out.append('\t(paper "A2")')
    out.append('\t(title_block')
    out.append('\t\t(title "Foxhunt Badge")')
    out.append('\t\t(date "2026-04-25")')
    out.append('\t\t(rev "1.0")')
    out.append('\t\t(company "DEFCON Foxhunt")')
    out.append('\t\t(comment 1 "B-2 silhouette flying-wing badge")')
    out.append('\t\t(comment 2 "ESP32-C3 + SA868-V VHF + SSD1306 OLED + WS2812 + LiPo")')
    out.append('\t)')
    out.append(build_lib_symbols())
    for c in COMPS:
        out.append(emit_component(c))
    out.append(build_wires_labels())
    # sheet_instances (required for KiCad 9 single-sheet schematic)
    out.append('\t(sheet_instances')
    out.append('\t\t(path "/" (page "1"))')
    out.append('\t)')
    out.append('\t(embedded_fonts no)')
    out.append(")")
    return "\n".join(out) + "\n"


def main():
    text = build_schematic()
    OUT_PATH.write_text(text)
    print(f"Wrote {OUT_PATH} ({len(text)} bytes); "
          f"{len(COMPS)} components, {len(NETS)} nets")


if __name__ == "__main__":
    main()
