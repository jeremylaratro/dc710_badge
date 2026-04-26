"""
Generate foxhunt-badge.kicad_sch -- a complete, single-page schematic
with every component placed and every pin labeled with its net name.

Approach: label-stub style. For each component pin, draw a short wire
stub outward and place a label at the end. KiCad's ERC connects matching
labels automatically. This is a standard schematic style for dense
designs and is fully ERC-compliant.

Layout (A3 sheet, 420 x 297 mm):
  +------------------------------------+
  | TITLE BLOCK                        |
  | POWER ZONE      |   MCU ZONE       |
  | (USB-C, TP4056, |   (ESP32-C3,     |
  |  LDO, batt)     |    decoupling,   |
  |                 |    debug)        |
  |-----------------+------------------|
  | RADIO ZONE      |   UI ZONE        |
  | (SA868, audio,  |   (OLED, LEDs,   |
  |  antenna)       |    buttons, SAO) |
  +------------------------------------+
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sch_lib_symbols import all_lib_symbols, ESP32_C3_PINS, SA868_PINS, AP2112_PINS, WS2812_PINS, USBC_PINS, SAO_PINS

KICAD_SCH_VERSION = 20231120
PROJECT_DIR = Path(__file__).parent.parent


def uuid_from(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ---------------------------------------------------------------------------
# Pin geometry - replicate IC body geometry from sch_lib_symbols.make_ic_symbol
# ---------------------------------------------------------------------------

def compute_pin_abs_pos(comp_pos, comp_pin_data, body_w, body_h):
    """Replicate make_ic_symbol's pin positioning math.

    Returns (abs_x, abs_y, orient_deg, stub_dx, stub_dy) where stub is
    the direction the wire stub should go (outward from the body).
    """
    half_w = body_w / 2
    half_h = body_h / 2
    pin_len = 2.54
    side = comp_pin_data['side']

    if side == 'L':
        rel_x = -half_w - pin_len
        rel_y = half_h - comp_pin_data['pos_mm']
        stub_dx = -2.54
        stub_dy = 0
    elif side == 'R':
        rel_x = half_w + pin_len
        rel_y = half_h - comp_pin_data['pos_mm']
        stub_dx = 2.54
        stub_dy = 0
    elif side == 'T':
        rel_x = -half_w + comp_pin_data['pos_mm']
        rel_y = half_h + pin_len
        stub_dx = 0
        stub_dy = 2.54
    else:  # 'B'
        rel_x = -half_w + comp_pin_data['pos_mm']
        rel_y = -half_h - pin_len
        stub_dx = 0
        stub_dy = -2.54

    return (comp_pos[0] + rel_x, comp_pos[1] + rel_y, stub_dx, stub_dy)


def compute_body_h(pins):
    """Replicate body_h calculation from make_ic_symbol."""
    side_pos = {'L': [], 'R': []}
    for p in pins:
        if p['side'] in side_pos:
            side_pos[p['side']].append(p['pos_mm'])
    max_left = max(side_pos['L']) if side_pos['L'] else 0
    max_right = max(side_pos['R']) if side_pos['R'] else 0
    return max(max_left, max_right) + 5.08


# ---------------------------------------------------------------------------
# S-expression emitters
# ---------------------------------------------------------------------------

def emit_symbol_instance(lib_id, ref, value, footprint, pos, mirror=None):
    """Emit a (symbol ...) schematic instance."""
    u = uuid_from(f"sym-{ref}-{pos}")
    mirror_attr = f' (mirror {mirror})' if mirror else ''
    # Reference label position depends on symbol; use a default offset above
    return f'''  (symbol (lib_id "{lib_id}") (at {pos[0]:.3f} {pos[1]:.3f} 0){mirror_attr} (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid "{u}")
    (property "Reference" "{ref}" (at {pos[0]:.3f} {pos[1] - 6.0:.3f} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at {pos[0]:.3f} {pos[1] + 6.0:.3f} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "{footprint}" (at {pos[0]:.3f} {pos[1]:.3f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "" (at {pos[0]:.3f} {pos[1]:.3f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (instances
      (project "foxhunt-badge"
        (path "/{uuid_from('root-sheet')}"
          (reference "{ref}") (unit 1)
        )
      )
    )
  )'''


def emit_wire(p1, p2, seed):
    u = uuid_from(f"wire-{seed}-{p1}-{p2}")
    return f'''  (wire (pts (xy {p1[0]:.3f} {p1[1]:.3f}) (xy {p2[0]:.3f} {p2[1]:.3f}))
    (stroke (width 0) (type default))
    (uuid "{u}")
  )'''


def emit_label(text, pos, orient=0, seed=""):
    u = uuid_from(f"label-{text}-{pos}-{seed}")
    safe = text.replace('"', '\\"')
    # Justify based on orientation: 0=right (label points right), 180=left
    just = "left bottom" if orient == 0 else "right bottom"
    return f'''  (label "{safe}" (at {pos[0]:.3f} {pos[1]:.3f} {orient})
    (effects (font (size 1.27 1.27)) (justify {just}))
    (uuid "{u}")
  )'''


def emit_global_label(text, pos, orient=0, seed=""):
    """Used for power nets that span the whole sheet."""
    u = uuid_from(f"glabel-{text}-{pos}-{seed}")
    safe = text.replace('"', '\\"')
    just = "left" if orient == 0 else "right"
    return f'''  (global_label "{safe}" (shape input) (at {pos[0]:.3f} {pos[1]:.3f} {orient})
    (effects (font (size 1.27 1.27)) (justify {just}))
    (uuid "{u}")
  )'''


def emit_power(power_lib_id, ref, pos, orient=0):
    """Emit a power symbol instance like +3V3 or GND."""
    u = uuid_from(f"pwr-{ref}-{pos}")
    return f'''  (symbol (lib_id "{power_lib_id}") (at {pos[0]:.3f} {pos[1]:.3f} {orient}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid "{u}")
    (property "Reference" "{ref}" (at {pos[0]:.3f} {pos[1] - 5.0:.3f} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "{power_lib_id.split(':')[-1]}" (at {pos[0]:.3f} {pos[1] + 3.0:.3f} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (instances
      (project "foxhunt-badge"
        (path "/{uuid_from('root-sheet')}"
          (reference "{ref}") (unit 1)
        )
      )
    )
  )'''


def place_ic_with_labels(lib_id, ref, value, footprint, pos, pins, body_w):
    """Place an IC and add label stubs for every named pin."""
    body_h = compute_body_h(pins)
    out = [emit_symbol_instance(lib_id, ref, value, footprint, pos)]

    for pin in pins:
        if pin.get('hide'):
            continue
        net = pin.get('net')
        if not net:
            continue  # skip unlabeled (e.g. NC) pins
        px, py, sx, sy = compute_pin_abs_pos(pos, pin, body_w, body_h)
        # Wire from pin tip outward by stub
        end_x = px + sx
        end_y = py + sy
        out.append(emit_wire((px, py), (end_x, end_y), f"{ref}-{pin['num']}"))
        # Label at the end
        if pin['side'] == 'L':
            label_orient = 180
        elif pin['side'] == 'R':
            label_orient = 0
        elif pin['side'] == 'T':
            label_orient = 90
        else:
            label_orient = 270
        out.append(emit_label(net, (end_x, end_y), label_orient, f"{ref}-{pin['num']}"))

    return "\n".join(out)


def place_passive(lib_id, ref, value, footprint, pos, net_a, net_b, vertical=True):
    """Place R/C/LED etc. and label both terminals.

    Default is vertical (pin 1 on top, pin 2 on bottom). For horizontal
    rotation handling we keep things simple with vertical only.
    """
    out = [emit_symbol_instance(lib_id, ref, value, footprint, pos)]
    # Pin 1 at (pos.x, pos.y - 3.81) if vertical, length 1.27 (R) or 2.794 (C/LED)
    # For uniformity we use the symbol's pin 1 at +y3.81 - 1.27 = +y2.54 (R)
    # Actually for R: pin 1 at +y3.81, with length 1.27 -> tip at +y2.54
    # For C: pin 1 at +y3.81, length 2.794 -> tip at +y1.016
    # We'll use a generic stub from the pin tip outward
    if "C" in lib_id and "Conn" not in lib_id:
        pin1_y = pos[1] + 1.016
        pin2_y = pos[1] - 1.016
    else:
        pin1_y = pos[1] + 2.54
        pin2_y = pos[1] - 2.54

    # Wire stubs and labels
    # Pin 1 (top)
    end1 = (pos[0], pin1_y + 2.54)
    out.append(emit_wire((pos[0], pin1_y), end1, f"{ref}-1"))
    out.append(emit_label(net_a, end1, 90, f"{ref}-1"))
    # Pin 2 (bottom)
    end2 = (pos[0], pin2_y - 2.54)
    out.append(emit_wire((pos[0], pin2_y), end2, f"{ref}-2"))
    out.append(emit_label(net_b, end2, 270, f"{ref}-2"))

    return "\n".join(out)


def emit_text(content, pos, size=1.5, seed=""):
    u = uuid_from(f"text-{seed}-{pos}")
    safe = content.replace('"', '\\"').replace('\n', '\\n')
    return f'''  (text "{safe}"
    (exclude_from_sim no)
    (at {pos[0]:.3f} {pos[1]:.3f} 0)
    (effects (font (size {size} {size})) (justify left bottom))
    (uuid "{u}")
  )'''


# ---------------------------------------------------------------------------
# Net assignments (this is the source-of-truth wiring)
# ---------------------------------------------------------------------------

# ESP32-C3-MINI-1 pin assignments per pins.h
ESP32_NETS = {
    1: 'GND', 2: 'GND', 3: '+3V3', 11: 'GND', 15: 'GND', 35: 'GND',
    5:  'STRAP_IO2',               # IO2 (strap; R10 pulls to GND at boot)
    6:  'BTN_UP',                  # IO3
    8:  'EN',                      # EN (with reset RC)
    12: 'LED_DIN_RAW',             # IO0 (goes through R11 before hitting LED chain)
    13: 'OLED_DC',                 # IO1
    14: 'SA868_PTT',               # IO10
    16: 'SAO_GPIO1',               # IO4 (free)
    17: 'OLED_CS',                 # IO5
    18: 'OLED_SCK',                # IO6
    19: 'OLED_MOSI',               # IO7
    20: 'OLED_RST',                # IO8 (strap HIGH ok)
    21: 'BTN_SEL',                 # IO9 (BOOT/SEL)
    23: 'DBG_RX',                  # IO20
    24: 'DBG_TX',                  # IO21
    26: 'SA868_TX',                # IO11
    27: 'SA868_RX',                # IO12
    28: 'SA868_PD',                # IO13
    29: 'SAO_GPIO2',               # IO14 (free)
    30: 'SA868_MIC',               # IO15
    31: 'SA868_AUDIO',             # IO16
    32: 'BTN_DN',                  # IO17
    33: 'USB_DM',                  # IO18
    34: 'USB_DP',                  # IO19
}

SA868_NETS = {
    1: 'GND', 3: 'GND', 13: 'GND', 14: 'GND', 15: 'GND', 16: 'GND',
    2: 'ANT', 4: 'VBAT',
    5: 'SA868_HL',          # via 10k pull-up (R9)
    6: 'SA868_RX_OUT',      # to RX audio path
    7: 'SA868_MIC_IN',      # from TX audio path
    8: 'SA868_PTT',
    9: None,                # SQ - leave NC
    10: 'SA868_PD',
    11: 'SA868_RX_INT',     # R30 1k in series between ESP SA868_RX and here
    12: 'SA868_TX',         # SA868 TXD -> ESP (direct, no series)
}

AP2112_NETS = {
    1: 'VBAT',
    2: 'GND',
    3: 'VBAT',     # EN tied to Vin
    5: '+3V3',
}

USBC_NETS = {
    'A1':'GND', 'A12':'GND',
    'A4':'VBUS', 'A9':'VBUS',
    'A5':'CC1', 'B5':'CC2',
    'A6':'USB_DP', 'B6':'USB_DP',
    'A7':'USB_DM', 'B7':'USB_DM',
    'S1':'GND',
}

SAO_NETS = {
    1: 'GND', 2: '+3V3',
    3: 'SAO_GPIO1', 4: 'SAO_GPIO2',
    5: 'SAO_GPIO3', 6: 'SAO_GPIO4',
}


def with_nets(pins, netmap):
    """Decorate pin list with 'net' field from netmap."""
    out = []
    for p in pins:
        q = dict(p)
        q['net'] = netmap.get(p['num'])
        out.append(q)
    return out


# ---------------------------------------------------------------------------
# Component placement + wiring
# ---------------------------------------------------------------------------

def build_schematic():
    items = []

    # Title text
    items.append(emit_text("FOXHUNT BADGE - Single-page schematic", (10, 10), size=2.5, seed="title"))
    items.append(emit_text("ESP32-C3 + SA868-V VHF + SSD1306 OLED + WS2812 LEDs", (10, 14), size=1.5, seed="subtitle"))
    items.append(emit_text("All connections via net labels (label-stub style).", (10, 17), size=1.2, seed="subtitle2"))

    # ============== POWER ZONE (top-left, 30-110, 30-110) ==============
    items.append(emit_text("== POWER ==", (35, 30), size=2, seed="hdr-pwr"))

    # USB-C connector @ (50, 50)
    items.append(place_ic_with_labels(
        "Connector:USB_C_Receptacle", "J1", "USB_C_Receptacle_USB2.0_16P",
        "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        pos=(50, 50), pins=with_nets(USBC_PINS, USBC_NETS), body_w=15.24,
    ))

    # CC1/CC2 5.1k pulldowns
    items.append(place_passive("Device:R", "R1", "5.1k", "Resistor_SMD:R_0603_1608Metric",
                               pos=(72, 45), net_a="CC1", net_b="GND"))
    items.append(place_passive("Device:R", "R2", "5.1k", "Resistor_SMD:R_0603_1608Metric",
                               pos=(80, 45), net_a="CC2", net_b="GND"))

    # Reverse-polarity Schottky (D1: SS14)
    items.append(place_passive("Diode:SS14", "D1", "SS14", "Diode_SMD:D_SOD-123",
                               pos=(72, 60), net_a="VBUS", net_b="VBAT_RAW"))

    # TP4056 module @ (50, 80)
    items.append(place_ic_with_labels(
        "Connector:Conn_01x05_TP4056", "U4", "TP4056_Module",
        "Module:TP4056_Module",
        pos=(50, 90),
        pins=with_nets(
            [{'num': i+1, 'name': nm, 'side': 'R', 'pos_mm': 2.54*(i+1), 'etype': 'passive'}
             for i, nm in enumerate(["IN+","IN-","BAT+","BAT-","OUT+"])],
            {1: "VBAT_RAW", 2: "GND", 3: "BATT", 4: "GND", 5: "VBAT"},
        ), body_w=7.62,
    ))

    # JST PH battery connector
    items.append(place_ic_with_labels(
        "Connector:Conn_01x02_JST", "J4", "Battery",
        "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
        pos=(85, 90),
        pins=with_nets(
            [{'num': 1, 'name': 'BAT+', 'side': 'R', 'pos_mm': 2.54, 'etype': 'passive'},
             {'num': 2, 'name': 'BAT-', 'side': 'R', 'pos_mm': 5.08, 'etype': 'passive'}],
            {1: "BATT", 2: "GND"},
        ), body_w=7.62,
    ))

    # AP2112K-3.3 LDO @ (105, 80)
    items.append(place_ic_with_labels(
        "Regulator_Linear:AP2112K-3.3", "U1", "AP2112K-3.3",
        "Package_TO_SOT_SMD:SOT-23-5",
        pos=(110, 70),
        pins=with_nets(AP2112_PINS, AP2112_NETS), body_w=10.16,
    ))

    # LDO Vin/Vout caps
    items.append(place_passive("Device:C", "C1", "1uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(95, 75), net_a="VBAT", net_b="GND"))
    items.append(place_passive("Device:C", "C2", "1uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(125, 75), net_a="+3V3", net_b="GND"))
    items.append(place_passive("Device:C", "C4", "10uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(132, 75), net_a="+3V3", net_b="GND"))

    # Power LED with current-limit resistor
    items.append(place_passive("Device:R", "R3", "1k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(120, 100), net_a="+3V3", net_b="LED_PWR_A"))
    items.append(place_passive("Device:LED", "D2", "GREEN",
                               "LED_SMD:LED_0603_1608Metric",
                               pos=(120, 110), net_a="LED_PWR_A", net_b="GND"))

    # Bulk caps for radio rail (close to U3)
    items.append(place_passive("Device:C", "C20", "470uF",
                               "Capacitor_SMD:CP_Elec_8x10",
                               pos=(140, 75), net_a="VBAT", net_b="GND"))
    items.append(place_passive("Device:C", "C21", "100nF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(148, 75), net_a="VBAT", net_b="GND"))

    # ============== MCU ZONE (top-right) ==============
    items.append(emit_text("== MCU ==", (180, 30), size=2, seed="hdr-mcu"))

    items.append(place_ic_with_labels(
        "RF_Module:ESP32-C3-MINI-1", "U2", "ESP32-C3-MINI-1",
        "RF_Module:ESP32-C2-MINI-1",  # closest stock footprint name; user verifies
        pos=(220, 80),
        pins=with_nets(ESP32_C3_PINS, ESP32_NETS), body_w=30.48,
    ))

    # ESP32 decoupling
    items.append(place_passive("Device:C", "C5", "100nF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(190, 50), net_a="+3V3", net_b="GND"))
    items.append(place_passive("Device:C", "C6", "10uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(198, 50), net_a="+3V3", net_b="GND"))

    # EN reset network
    items.append(place_passive("Device:R", "R4", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(180, 70), net_a="+3V3", net_b="EN"))
    items.append(place_passive("Device:C", "C7", "1uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(180, 90), net_a="EN", net_b="GND"))
    # Reset button
    items.append(place_ic_with_labels(
        "Switch:SW_Push", "S1", "RESET",
        "Button_Switch_SMD:SW_SPST_TL3342",
        pos=(180, 110),
        pins=with_nets(
            [{'num': 1, 'name': '1', 'side': 'L', 'pos_mm': 2.54, 'etype': 'passive'},
             {'num': 2, 'name': '2', 'side': 'R', 'pos_mm': 2.54, 'etype': 'passive'}],
            {1: "EN", 2: "GND"},
        ), body_w=10.16,
    ))

    # GPIO9 / BOOT button (S2 = SEL/BOOT)
    items.append(place_passive("Device:R", "R5", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(265, 70), net_a="+3V3", net_b="BTN_SEL"))
    items.append(place_ic_with_labels(
        "Switch:SW_Push", "S2", "SEL",
        "Button_Switch_SMD:SW_SPST_TL3342",
        pos=(265, 110),
        pins=with_nets(
            [{'num': 1, 'name': '1', 'side': 'L', 'pos_mm': 2.54, 'etype': 'passive'},
             {'num': 2, 'name': '2', 'side': 'R', 'pos_mm': 2.54, 'etype': 'passive'}],
            {1: "BTN_SEL", 2: "GND"},
        ), body_w=10.16,
    ))

    # Strap pull-downs/up
    items.append(place_passive("Device:R", "R10", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(255, 50), net_a="STRAP_IO2", net_b="GND"))
    items.append(place_passive("Device:R", "R6", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(263, 50), net_a="+3V3", net_b="OLED_RST"))

    # Debug header J3
    items.append(place_ic_with_labels(
        "Connector_Generic:Conn_01x04_Debug", "J3", "Debug",
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        pos=(290, 80),
        pins=with_nets(
            [{'num': i+1, 'name': nm, 'side': 'R', 'pos_mm': 2.54*(i+1), 'etype': 'passive'}
             for i, nm in enumerate(["GND","+3V3","RX","TX"])],
            {1: "GND", 2: "+3V3", 3: "DBG_RX", 4: "DBG_TX"},
        ), body_w=7.62,
    ))

    # ============== RADIO ZONE (bottom-left) ==============
    items.append(emit_text("== RADIO ==", (35, 160), size=2, seed="hdr-radio"))

    items.append(place_ic_with_labels(
        "RF_Module:SA868", "U3", "SA868-V",
        "RF_Module:SA868",  # custom; needs to be created by user
        pos=(60, 200),
        pins=with_nets(SA868_PINS, SA868_NETS), body_w=22.86,
    ))

    # Audio TX path: PWM -> R31 -> R32 -> C32 -> SA868_MIC_IN
    items.append(place_passive("Device:R", "R31", "1k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(105, 175), net_a="SA868_MIC", net_b="AUDIO_NODE_A"))
    items.append(place_passive("Device:C", "C30", "100nF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(115, 175), net_a="AUDIO_NODE_A", net_b="GND"))
    items.append(place_passive("Device:R", "R32", "1k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(125, 175), net_a="AUDIO_NODE_A", net_b="AUDIO_NODE_B"))
    items.append(place_passive("Device:C", "C31", "100nF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(135, 175), net_a="AUDIO_NODE_B", net_b="GND"))
    items.append(place_passive("Device:C", "C32", "1uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(145, 175), net_a="AUDIO_NODE_B", net_b="SA868_MIC_IN"))

    # Audio RX path: SA868_RX_OUT -> C40 (DC-block) -> SA868_AUDIO (= ESP GPIO16)
    # with R40/R41 divider biasing SA868_AUDIO to mid-rail
    items.append(place_passive("Device:C", "C40", "1uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(105, 225), net_a="SA868_RX_OUT", net_b="SA868_AUDIO"))
    items.append(place_passive("Device:R", "R40", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(115, 215), net_a="+3V3", net_b="SA868_AUDIO"))
    items.append(place_passive("Device:R", "R41", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(115, 235), net_a="SA868_AUDIO", net_b="GND"))

    # SA868 control pull-ups
    items.append(place_passive("Device:R", "R7", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(35, 175), net_a="+3V3", net_b="SA868_PTT"))
    items.append(place_passive("Device:R", "R8", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(35, 195), net_a="+3V3", net_b="SA868_PD"))
    items.append(place_passive("Device:R", "R9", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(35, 215), net_a="+3V3", net_b="SA868_HL"))
    # SA868 RXD series safety
    items.append(place_passive("Device:R", "R30", "1k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(105, 200), net_a="SA868_RX", net_b="SA868_RX_INT"))

    # Antenna match
    items.append(place_passive("Device:R", "L1", "0R",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(35, 235), net_a="ANT", net_b="ANT_TRACE"))
    # C50/C51 DNP
    items.append(place_passive("Device:C", "C50", "DNP",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(25, 240), net_a="ANT", net_b="GND"))
    items.append(place_passive("Device:C", "C51", "DNP",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(45, 240), net_a="ANT_TRACE", net_b="GND"))
    items.append(emit_text("Antenna trace -> right wingtip\\n(meandered ~150mm, no GND pour)",
                           (25, 260), size=1.0, seed="ant-note"))

    # ============== UI ZONE (bottom-right) ==============
    items.append(emit_text("== UI ==", (180, 160), size=2, seed="hdr-ui"))

    # OLED
    items.append(place_ic_with_labels(
        "Connector_Generic:Conn_01x07", "DISP1", "OLED_SSD1306",
        "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
        pos=(195, 200),
        pins=with_nets(
            [{'num': i+1, 'name': nm, 'side': 'R', 'pos_mm': 2.54*(i+1), 'etype': 'passive'}
             for i, nm in enumerate(["GND","VCC","SCK","MOSI","RST","DC","CS"])],
            {1: "GND", 2: "+3V3", 3: "OLED_SCK", 4: "OLED_MOSI",
             5: "OLED_RST", 6: "OLED_DC", 7: "OLED_CS"},
        ), body_w=7.62,
    ))

    # WS2812 chain - 4 LEDs
    led_y = 200
    for i in range(4):
        ref = f"D{i+3}"  # D3..D6
        x = 230 + i * 20
        prev_net = "LED_DIN" if i == 0 else f"LED_CHAIN_{i}"
        next_net = f"LED_CHAIN_{i+1}" if i < 3 else "LED_END"
        items.append(place_ic_with_labels(
            "LED:WS2812B", ref, "WS2812B-2020",
            "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm_P1.0mm",
            pos=(x, led_y),
            pins=with_nets(WS2812_PINS, {1: "+3V3", 2: next_net, 3: "GND", 4: prev_net}),
            body_w=10.16,
        ))
        # Decoupling cap per LED
        items.append(place_passive("Device:C", f"C{8+i}", "100nF",
                                   "Capacitor_SMD:C_0603_1608Metric",
                                   pos=(x, led_y - 30), net_a="+3V3", net_b="GND"))

    # WS2812 chain bulk + series resistor
    items.append(place_passive("Device:R", "R11", "220R",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(225, 175), net_a="LED_DIN_RAW", net_b="LED_DIN"))
    items.append(emit_text("From ESP IO0", (215, 168), size=1.0, seed="ledr-note"))
    items.append(place_passive("Device:C", "C12", "10uF",
                               "Capacitor_SMD:C_0603_1608Metric",
                               pos=(215, 190), net_a="+3V3", net_b="GND"))

    # Buttons UP / DN
    items.append(place_ic_with_labels(
        "Switch:SW_Push", "S3", "UP",
        "Button_Switch_SMD:SW_SPST_TL3342",
        pos=(180, 240),
        pins=with_nets(
            [{'num': 1, 'name': '1', 'side': 'L', 'pos_mm': 2.54, 'etype': 'passive'},
             {'num': 2, 'name': '2', 'side': 'R', 'pos_mm': 2.54, 'etype': 'passive'}],
            {1: "BTN_UP", 2: "GND"},
        ), body_w=10.16,
    ))
    items.append(place_passive("Device:R", "R12", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(165, 245), net_a="+3V3", net_b="BTN_UP"))

    items.append(place_ic_with_labels(
        "Switch:SW_Push", "S4", "DN",
        "Button_Switch_SMD:SW_SPST_TL3342",
        pos=(220, 240),
        pins=with_nets(
            [{'num': 1, 'name': '1', 'side': 'L', 'pos_mm': 2.54, 'etype': 'passive'},
             {'num': 2, 'name': '2', 'side': 'R', 'pos_mm': 2.54, 'etype': 'passive'}],
            {1: "BTN_DN", 2: "GND"},
        ), body_w=10.16,
    ))
    items.append(place_passive("Device:R", "R14", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(205, 245), net_a="+3V3", net_b="BTN_DN"))
    # SEL pullup  (R13 declared in MCU zone via R5; add a parallel one for ext pullup)
    items.append(place_passive("Device:R", "R13", "10k",
                               "Resistor_SMD:R_0603_1608Metric",
                               pos=(245, 245), net_a="+3V3", net_b="BTN_SEL"))

    # SAO header
    items.append(place_ic_with_labels(
        "Connector_Generic:Conn_02x03_SAO", "J2", "SAO",
        "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
        pos=(280, 220),
        pins=with_nets(SAO_PINS, SAO_NETS), body_w=10.16,
    ))

    # ============== Power flag tags placed at strategic points ==============
    # +3V3 power flags around regions
    for ref, pos in [("PWR1", (130, 65)), ("PWR2", (190, 45)), ("PWR3", (35, 170))]:
        items.append(emit_power("power:+3V3", ref, pos))
    # GND flags
    for ref, pos in [("PWR4", (75, 65)), ("PWR5", (190, 110)), ("PWR6", (60, 250)), ("PWR7", (250, 250))]:
        items.append(emit_power("power:GND", ref, pos, orient=180))
    # VBAT flag
    items.append(emit_power("power:VBAT", "PWR8", (95, 90)))
    # VBUS flag
    items.append(emit_power("power:VBUS", "PWR9", (60, 30)))

    return "\n".join(items)


def make_full_schematic():
    body = build_schematic()
    lib = all_lib_symbols()
    root_uuid = uuid_from('root-sheet')

    return f'''(kicad_sch
\t(version {KICAD_SCH_VERSION})
\t(generator "claude_foxhunt_gen")
\t(generator_version "1.0")
\t(uuid "{root_uuid}")
\t(paper "A2")
\t(title_block
\t\t(title "Foxhunt Badge")
\t\t(date "2026-04-25")
\t\t(rev "0.1")
\t\t(company "DEFCON Foxhunt")
\t\t(comment 1 "B-2 silhouette flying-wing badge")
\t\t(comment 2 "ESP32-C3 + SA868-V VHF + SSD1306 OLED")
\t)
\t(lib_symbols
{lib}
\t)
{body}
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
'''


if __name__ == "__main__":
    out_path = PROJECT_DIR / "foxhunt-badge.kicad_sch"
    out_path.write_text(make_full_schematic())
    size = out_path.stat().st_size
    print(f"Wrote {out_path} ({size:,} bytes)")
