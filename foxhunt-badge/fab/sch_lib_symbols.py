"""
Embedded KiCad 8 Symbol library definitions for the foxhunt badge.

Each function returns an S-expression string for a (symbol ...) entry
that goes inside the (lib_symbols ...) section of the schematic file.
These are minimal but valid: they define pin positions, numbers, names,
electrical types, and a basic graphical representation.

Convention:
  - All units in mils * 0.0254 = mm... actually KiCad schematic uses mm
    natively but pin lengths and grid are typically in 1.27mm steps.
  - Pin orientation: 0=right, 90=up, 180=left, 270=down
  - Electrical types: input, output, bidirectional, tri_state, passive,
    free, unspecified, power_in, power_out, open_collector, open_emitter,
    no_connect
"""


def _box_pin(num, name, x, y, length, orient, etype="passive", hide=False):
    """Emit a single pin definition inside a symbol unit."""
    hide_attr = ' hide' if hide else ''
    safe_name = name.replace('"', '\\"')
    return f'''      (pin {etype} line
        (at {x:.3f} {y:.3f} {orient})
        (length {length:.3f}){hide_attr}
        (name "{safe_name}" (effects (font (size 1.0 1.0))))
        (number "{num}" (effects (font (size 1.0 1.0))))
      )'''


# ---- R ----
SYM_R = '''  (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
    (property "Reference" "R" (at 2.032 0 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "R" (at 0 0 90)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at -1.778 0 90)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "R_0_1"
      (rectangle (start -1.016 -2.54) (end 1.016 2.54)
        (stroke (width 0.254) (type default))
        (fill (type none))
      )
    )
    (symbol "R_1_1"
      (pin passive line (at 0 3.81 270) (length 1.27)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 0 -3.81 90) (length 1.27)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

# ---- C ----
SYM_C = '''  (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
    (property "Reference" "C" (at 0.635 2.54 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Value" "C" (at 0.635 -2.54 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Footprint" "" (at 0.9652 -3.81 0)
      (effects (font (size 1.27 1.27)) (justify left) hide)
    )
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "C_0_1"
      (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
        (stroke (width 0.508) (type default))
        (fill (type none))
      )
      (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))
        (stroke (width 0.508) (type default))
        (fill (type none))
      )
    )
    (symbol "C_1_1"
      (pin passive line (at 0 3.81 270) (length 2.794)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 0 -3.81 90) (length 2.794)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

# ---- LED ----
SYM_LED = '''  (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
    (property "Reference" "D" (at 0 2.54 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "LED" (at 0 -2.54 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "LED_0_1"
      (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol "LED_1_1"
      (pin passive line (at -3.81 0 0) (length 2.54)
        (name "K" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 3.81 0 180) (length 2.54)
        (name "A" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

# ---- SW_Push (tactile) ----
SYM_SW = '''  (symbol "Switch:SW_Push" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
    (property "Reference" "SW" (at 1.27 2.54 0) (effects (font (size 1.27 1.27))))
    (property "Value" "SW_Push" (at 0 -1.524 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "SW_Push_0_1"
      (circle (center -2.032 0) (radius 0.508)
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (circle (center 2.032 0) (radius 0.508)
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline (pts (xy 0 1.27) (xy 0 1.778)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy -2.54 1.778) (xy 2.54 1.778)) (stroke (width 0.1524) (type default)) (fill (type none)))
    )
    (symbol "SW_Push_1_1"
      (pin passive line (at -5.08 0 0) (length 2.54)
        (name "1" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 5.08 0 180) (length 2.54)
        (name "2" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

# ---- Schottky diode (D_Schottky) ----
SYM_DSCHOT = '''  (symbol "Diode:SS14" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
    (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
    (property "Value" "SS14" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "SS14_0_1"
      (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type outline)))
      (polyline (pts (xy 1.27 1.27) (xy 1.778 1.27) (xy 1.778 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 1.27 -1.27) (xy 0.762 -1.27) (xy 0.762 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol "SS14_1_1"
      (pin passive line (at -3.81 0 0) (length 2.54)
        (name "K" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 3.81 0 180) (length 2.54)
        (name "A" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

# ---- Power symbols ----
SYM_PWR_3V3 = '''  (symbol "power:+3V3" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
    (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "+3V3" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "+3V3_0_1"
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "+3V3_1_1"
      (pin power_in line (at 0 0 90) (length 0) hide
        (name "+3V3" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

SYM_PWR_GND = '''  (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
    (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "GND_0_1"
      (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "GND_1_1"
      (pin power_in line (at 0 0 270) (length 0) hide
        (name "GND" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

SYM_PWR_VBAT = '''  (symbol "power:VBAT" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
    (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "VBAT" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "VBAT_0_1"
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "VBAT_1_1"
      (pin power_in line (at 0 0 90) (length 0) hide
        (name "VBAT" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
  )'''

SYM_PWR_VBUS = '''  (symbol "power:VBUS" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
    (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "VBUS" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "VBUS_0_1"
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
    )
    (symbol "VBUS_1_1"
      (pin power_in line (at 0 0 90) (length 0) hide
        (name "VBUS" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
    )
  )'''


# ---- IC builder helper ----
def make_ic_symbol(lib_id, ref_prefix, default_value, pins, body_w_mm=20.32, header_h_mm=2.54):
    """Generate a generic rectangular IC symbol with pins.

    pins: list of dicts with keys:
      num, name, side ('L'|'R'|'T'|'B'), pos_mm (offset along that side from top/left),
      etype (electrical type)
    """
    # Compute body height: max position on either side + 2.54mm padding
    side_pos = {'L': [], 'R': [], 'T': [], 'B': []}
    for p in pins:
        side_pos[p['side']].append(p['pos_mm'])

    max_left  = max(side_pos['L']) if side_pos['L'] else 0
    max_right = max(side_pos['R']) if side_pos['R'] else 0
    body_h_mm = max(max_left, max_right) + 5.08
    # For top/bottom pins, body_w may need to expand
    max_top = max(side_pos['T']) if side_pos['T'] else 0
    max_bot = max(side_pos['B']) if side_pos['B'] else 0
    if max_top > body_w_mm - 5.08:
        body_w_mm = max_top + 5.08
    if max_bot > body_w_mm - 5.08:
        body_w_mm = max_bot + 5.08

    # Body rectangle centered on origin
    half_w = body_w_mm / 2
    half_h = body_h_mm / 2

    # Build pins
    pin_lines = []
    pin_len = 2.54
    for p in pins:
        side = p['side']
        if side == 'L':
            x = -half_w - pin_len
            y = half_h - p['pos_mm']
            orient = 0
        elif side == 'R':
            x = half_w + pin_len
            y = half_h - p['pos_mm']
            orient = 180
        elif side == 'T':
            x = -half_w + p['pos_mm']
            y = half_h + pin_len
            orient = 270
        else:  # 'B'
            x = -half_w + p['pos_mm']
            y = -half_h - pin_len
            orient = 90
        etype = p.get('etype', 'passive')
        hide = p.get('hide', False)
        hide_attr = ' hide' if hide else ''
        safe_name = p['name'].replace('"', '\\"')
        pin_lines.append(
            f'      (pin {etype} line (at {x:.3f} {y:.3f} {orient}) (length {pin_len}){hide_attr}\n'
            f'        (name "{safe_name}" (effects (font (size 1.0 1.0))))\n'
            f'        (number "{p["num"]}" (effects (font (size 1.0 1.0))))\n'
            f'      )'
        )

    body_unit = f'''    (symbol "{lib_id.split(":")[-1]}_0_1"
      (rectangle (start {-half_w:.3f} {-half_h:.3f}) (end {half_w:.3f} {half_h:.3f})
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )'''
    pins_unit = f'''    (symbol "{lib_id.split(":")[-1]}_1_1"
{chr(10).join(pin_lines)}
    )'''

    return f'''  (symbol "{lib_id}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "{ref_prefix}" (at {-half_w:.3f} {half_h + 2.54:.3f} 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Value" "{default_value}" (at {-half_w:.3f} {half_h + 0.508:.3f} 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Footprint" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
{body_unit}
{pins_unit}
  )'''


# ---- ESP32-C3-MINI-1 ----
ESP32_C3_PINS = [
    {'num': 1,  'name': 'GND',     'side': 'L', 'pos_mm': 2.54,  'etype': 'power_in'},
    {'num': 2,  'name': 'GND',     'side': 'L', 'pos_mm': 5.08,  'etype': 'power_in'},
    {'num': 3,  'name': '3V3',     'side': 'L', 'pos_mm': 7.62,  'etype': 'power_in'},
    {'num': 4,  'name': 'NC',      'side': 'L', 'pos_mm': 10.16, 'etype': 'no_connect', 'hide': True},
    {'num': 5,  'name': 'IO2',     'side': 'L', 'pos_mm': 12.70, 'etype': 'bidirectional'},
    {'num': 6,  'name': 'IO3',     'side': 'L', 'pos_mm': 15.24, 'etype': 'bidirectional'},
    {'num': 7,  'name': 'NC',      'side': 'L', 'pos_mm': 17.78, 'etype': 'no_connect', 'hide': True},
    {'num': 8,  'name': 'EN',      'side': 'L', 'pos_mm': 20.32, 'etype': 'input'},
    {'num': 9,  'name': 'NC',      'side': 'L', 'pos_mm': 22.86, 'etype': 'no_connect', 'hide': True},
    {'num': 10, 'name': 'NC',      'side': 'L', 'pos_mm': 25.40, 'etype': 'no_connect', 'hide': True},
    {'num': 11, 'name': 'GND',     'side': 'L', 'pos_mm': 27.94, 'etype': 'power_in'},
    {'num': 12, 'name': 'IO0',     'side': 'L', 'pos_mm': 30.48, 'etype': 'bidirectional'},
    {'num': 13, 'name': 'IO1',     'side': 'L', 'pos_mm': 33.02, 'etype': 'bidirectional'},
    # Right side
    {'num': 14, 'name': 'IO10',    'side': 'R', 'pos_mm': 2.54,  'etype': 'bidirectional'},
    {'num': 15, 'name': 'GND',     'side': 'R', 'pos_mm': 5.08,  'etype': 'power_in'},
    {'num': 16, 'name': 'IO4',     'side': 'R', 'pos_mm': 7.62,  'etype': 'bidirectional'},
    {'num': 17, 'name': 'IO5',     'side': 'R', 'pos_mm': 10.16, 'etype': 'bidirectional'},
    {'num': 18, 'name': 'IO6',     'side': 'R', 'pos_mm': 12.70, 'etype': 'bidirectional'},
    {'num': 19, 'name': 'IO7',     'side': 'R', 'pos_mm': 15.24, 'etype': 'bidirectional'},
    {'num': 20, 'name': 'IO8',     'side': 'R', 'pos_mm': 17.78, 'etype': 'bidirectional'},
    {'num': 21, 'name': 'IO9',     'side': 'R', 'pos_mm': 20.32, 'etype': 'bidirectional'},
    {'num': 22, 'name': 'NC',      'side': 'R', 'pos_mm': 22.86, 'etype': 'no_connect', 'hide': True},
    {'num': 23, 'name': 'IO20',    'side': 'R', 'pos_mm': 25.40, 'etype': 'bidirectional'},
    {'num': 24, 'name': 'IO21',    'side': 'R', 'pos_mm': 27.94, 'etype': 'bidirectional'},
    # Bottom: GPIO11-19 (skip detailing all, group into expected ones)
    {'num': 25, 'name': 'NC',      'side': 'R', 'pos_mm': 30.48, 'etype': 'no_connect', 'hide': True},
    {'num': 26, 'name': 'IO11',    'side': 'B', 'pos_mm': 2.54,  'etype': 'bidirectional'},
    {'num': 27, 'name': 'IO12',    'side': 'B', 'pos_mm': 5.08,  'etype': 'bidirectional'},
    {'num': 28, 'name': 'IO13',    'side': 'B', 'pos_mm': 7.62,  'etype': 'bidirectional'},
    {'num': 29, 'name': 'IO14',    'side': 'B', 'pos_mm': 10.16, 'etype': 'bidirectional'},
    {'num': 30, 'name': 'IO15',    'side': 'B', 'pos_mm': 12.70, 'etype': 'bidirectional'},
    {'num': 31, 'name': 'IO16',    'side': 'B', 'pos_mm': 15.24, 'etype': 'bidirectional'},
    {'num': 32, 'name': 'IO17',    'side': 'B', 'pos_mm': 17.78, 'etype': 'bidirectional'},
    {'num': 33, 'name': 'IO18',    'side': 'B', 'pos_mm': 20.32, 'etype': 'bidirectional'},
    {'num': 34, 'name': 'IO19',    'side': 'B', 'pos_mm': 22.86, 'etype': 'bidirectional'},
    {'num': 35, 'name': 'GND',     'side': 'B', 'pos_mm': 25.40, 'etype': 'power_in'},
]
SYM_ESP32_C3 = make_ic_symbol("RF_Module:ESP32-C3-MINI-1", "U", "ESP32-C3-MINI-1",
                              ESP32_C3_PINS, body_w_mm=30.48)

# ---- SA868 ----
SA868_PINS = [
    {'num': 1,  'name': 'GND',     'side': 'L', 'pos_mm': 2.54,  'etype': 'power_in'},
    {'num': 2,  'name': 'ANT',     'side': 'L', 'pos_mm': 5.08,  'etype': 'passive'},
    {'num': 3,  'name': 'GND',     'side': 'L', 'pos_mm': 7.62,  'etype': 'power_in'},
    {'num': 4,  'name': 'VBAT',    'side': 'L', 'pos_mm': 10.16, 'etype': 'power_in'},
    {'num': 5,  'name': 'H/L',     'side': 'L', 'pos_mm': 12.70, 'etype': 'input'},
    {'num': 6,  'name': 'RX_OUT',  'side': 'L', 'pos_mm': 15.24, 'etype': 'output'},
    {'num': 7,  'name': 'MIC_IN',  'side': 'L', 'pos_mm': 17.78, 'etype': 'input'},
    {'num': 8,  'name': 'PTT',     'side': 'L', 'pos_mm': 20.32, 'etype': 'input'},
    {'num': 9,  'name': 'SQ',      'side': 'R', 'pos_mm': 2.54,  'etype': 'output'},
    {'num': 10, 'name': 'PD',      'side': 'R', 'pos_mm': 5.08,  'etype': 'input'},
    {'num': 11, 'name': 'RXD',     'side': 'R', 'pos_mm': 7.62,  'etype': 'input'},
    {'num': 12, 'name': 'TXD',     'side': 'R', 'pos_mm': 10.16, 'etype': 'output'},
    {'num': 13, 'name': 'GND',     'side': 'R', 'pos_mm': 12.70, 'etype': 'power_in'},
    {'num': 14, 'name': 'GND',     'side': 'R', 'pos_mm': 15.24, 'etype': 'power_in'},
    {'num': 15, 'name': 'GND',     'side': 'R', 'pos_mm': 17.78, 'etype': 'power_in'},
    {'num': 16, 'name': 'GND',     'side': 'R', 'pos_mm': 20.32, 'etype': 'power_in'},
]
SYM_SA868 = make_ic_symbol("RF_Module:SA868", "U", "SA868-V", SA868_PINS, body_w_mm=22.86)

# ---- AP2112K-3.3 (SOT-23-5) ----
AP2112_PINS = [
    {'num': 1, 'name': 'IN',  'side': 'L', 'pos_mm': 2.54,  'etype': 'power_in'},
    {'num': 2, 'name': 'GND', 'side': 'B', 'pos_mm': 5.08,  'etype': 'power_in'},
    {'num': 3, 'name': 'EN',  'side': 'L', 'pos_mm': 5.08,  'etype': 'input'},
    {'num': 4, 'name': 'NC',  'side': 'R', 'pos_mm': 5.08,  'etype': 'no_connect', 'hide': True},
    {'num': 5, 'name': 'OUT', 'side': 'R', 'pos_mm': 2.54,  'etype': 'power_out'},
]
SYM_AP2112 = make_ic_symbol("Regulator_Linear:AP2112K-3.3", "U", "AP2112K-3.3",
                            AP2112_PINS, body_w_mm=10.16)

# ---- WS2812B (4-pin) ----
WS2812_PINS = [
    {'num': 1, 'name': 'VDD',  'side': 'L', 'pos_mm': 2.54, 'etype': 'power_in'},
    {'num': 2, 'name': 'DOUT', 'side': 'R', 'pos_mm': 2.54, 'etype': 'output'},
    {'num': 3, 'name': 'GND',  'side': 'L', 'pos_mm': 5.08, 'etype': 'power_in'},
    {'num': 4, 'name': 'DIN',  'side': 'R', 'pos_mm': 5.08, 'etype': 'input'},
]
SYM_WS2812 = make_ic_symbol("LED:WS2812B", "D", "WS2812B-2020", WS2812_PINS, body_w_mm=10.16)

# ---- USB-C 16-pin (key pins only; many are dupes for redundancy) ----
USBC_PINS = [
    {'num': 'A1', 'name': 'GND', 'side': 'L', 'pos_mm': 2.54,  'etype': 'power_in'},
    {'num': 'A4', 'name': 'VBUS','side': 'L', 'pos_mm': 5.08,  'etype': 'power_out'},
    {'num': 'A5', 'name': 'CC1', 'side': 'L', 'pos_mm': 7.62,  'etype': 'bidirectional'},
    {'num': 'A6', 'name': 'D+',  'side': 'L', 'pos_mm': 10.16, 'etype': 'bidirectional'},
    {'num': 'A7', 'name': 'D-',  'side': 'L', 'pos_mm': 12.70, 'etype': 'bidirectional'},
    {'num': 'A8', 'name': 'SBU1','side': 'L', 'pos_mm': 15.24, 'etype': 'no_connect', 'hide': True},
    {'num': 'A9', 'name': 'VBUS','side': 'R', 'pos_mm': 5.08,  'etype': 'power_out'},
    {'num': 'A12','name': 'GND', 'side': 'R', 'pos_mm': 2.54,  'etype': 'power_in'},
    {'num': 'B5', 'name': 'CC2', 'side': 'R', 'pos_mm': 7.62,  'etype': 'bidirectional'},
    {'num': 'B6', 'name': 'D+',  'side': 'R', 'pos_mm': 10.16, 'etype': 'bidirectional'},
    {'num': 'B7', 'name': 'D-',  'side': 'R', 'pos_mm': 12.70, 'etype': 'bidirectional'},
    {'num': 'B8', 'name': 'SBU2','side': 'R', 'pos_mm': 15.24, 'etype': 'no_connect', 'hide': True},
    {'num': 'S1', 'name': 'SHIELD','side': 'B', 'pos_mm': 7.62, 'etype': 'passive'},
]
SYM_USBC = make_ic_symbol("Connector:USB_C_Receptacle", "J", "USB_C_Receptacle",
                          USBC_PINS, body_w_mm=15.24)

# ---- Generic connector helpers ----
def make_conn(lib_id, ref, value, n_pins, pin_names=None):
    """Generate a 1xN pin header symbol. pin_names is optional list."""
    pins = []
    for i in range(1, n_pins + 1):
        nm = pin_names[i-1] if pin_names else f"Pin_{i}"
        pins.append({'num': i, 'name': nm, 'side': 'R', 'pos_mm': 2.54 * i, 'etype': 'passive'})
    return make_ic_symbol(lib_id, ref, value, pins, body_w_mm=7.62)


# OLED 7-pin module
SYM_OLED = make_conn("Connector_Generic:Conn_01x07", "J", "OLED_SSD1306",
                     7, ["GND","VCC","SCK","MOSI","RST","DC","CS"])
# Debug header 4-pin
SYM_DBG  = make_conn("Connector_Generic:Conn_01x04_Debug", "J", "Debug_UART",
                     4, ["GND","+3V3","RX","TX"])
# JST PH 2P battery
SYM_JST  = make_conn("Connector:Conn_01x02_JST", "J", "Battery",
                     2, ["BAT+","BAT-"])
# TP4056 module 5-pin
SYM_TP   = make_conn("Connector:Conn_01x05_TP4056", "U", "TP4056_Module",
                     5, ["IN+","IN-","BAT+","BAT-","OUT+"])

# 2x3 SAO header
SAO_PINS = [
    {'num': 1, 'name': 'GND',  'side': 'L', 'pos_mm': 2.54, 'etype': 'power_in'},
    {'num': 2, 'name': '+3V3', 'side': 'R', 'pos_mm': 2.54, 'etype': 'power_in'},
    {'num': 3, 'name': 'GPIO1','side': 'L', 'pos_mm': 5.08, 'etype': 'bidirectional'},
    {'num': 4, 'name': 'GPIO2','side': 'R', 'pos_mm': 5.08, 'etype': 'bidirectional'},
    {'num': 5, 'name': 'GPIO3','side': 'L', 'pos_mm': 7.62, 'etype': 'bidirectional'},
    {'num': 6, 'name': 'GPIO4','side': 'R', 'pos_mm': 7.62, 'etype': 'bidirectional'},
]
SYM_SAO = make_ic_symbol("Connector_Generic:Conn_02x03_SAO", "J", "SAO_v1.69bis",
                         SAO_PINS, body_w_mm=10.16)


def all_lib_symbols():
    """Return the assembled (lib_symbols ...) section content."""
    return "\n".join([
        SYM_R, SYM_C, SYM_LED, SYM_SW, SYM_DSCHOT,
        SYM_PWR_3V3, SYM_PWR_GND, SYM_PWR_VBAT, SYM_PWR_VBUS,
        SYM_ESP32_C3, SYM_SA868, SYM_AP2112, SYM_WS2812, SYM_USBC,
        SYM_OLED, SYM_DBG, SYM_JST, SYM_TP, SYM_SAO,
    ])
