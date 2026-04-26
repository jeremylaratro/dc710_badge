"""
Generate the hierarchical schematic set for the foxhunt badge.

Strategy: produce a clean, openable KiCad 8 schematic hierarchy with the
four sub-sheets present and navigable. Each sub-sheet contains a title
block plus a structured text block enumerating the components and
connections to be placed there. The user then drops symbols from KiCad's
built-in libraries onto each sheet and wires per the embedded plan.

This is more reliable than auto-placing every component and wire (which
risks subtle format errors that prevent the file from opening at all).
"""

import hashlib
from pathlib import Path

KICAD_SCH_VERSION = 20231120  # KiCad 8 schematic format
PROJECT_DIR = Path(__file__).parent.parent


def uuid_from(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ---------------------------------------------------------------------------
# Sub-sheet content (the planning notes that appear in-schematic)
# ---------------------------------------------------------------------------

POWER_NOTES = """=== POWER SHEET ===

INPUTS:
  USB-C VBUS (5V from host)
  VBAT (1S LiPo, 3.0-4.2V)

OUTPUTS:
  +3V3       -> MCU, OLED, logic
  VBAT_RAW   -> SA868 directly (handles 3.7-5V, large bulk caps required)
  GND        -> star ground at TP4056 module

COMPONENTS:
  J1   USB-C 16-pin receptacle (HRO TYPE-C-31-M-12 or equiv)
       VBUS, GND, CC1+CC2 (each via 5.1k to GND for 5V negotiation)
       Datalines D+/D- to ESP32 USB pins (GPIO18/19)
  TP4056 module (pre-built, mounted on back via 5 castellated pads)
       IN+ <- VBUS via reverse-polarity Schottky D1 (SS14)
       OUT+ -> VBAT
       BAT+ -> JST PH-2 connector to LiPo
  U1   AP2112K-3.3 SOT-23-5 LDO
       Vin <- VBAT,  Vout -> +3V3,  EN tied to Vin
       1uF in, 1uF out (0603 ceramic X7R)
  D2   Power LED (green 0603) on +3V3 via 1k
  C_BULK_RADIO 470uF + 100nF placed adjacent to SA868 VBAT pin

NETS:
  VBUS, VBAT, +3V3, GND, USB_DP, USB_DM, USB_CC1, USB_CC2

NOTES:
  - Bulk cap on radio rail is critical (1.5A TX peaks).
  - LDO only powers logic; never run radio off LDO.
  - Add a 0-ohm jumper between VBAT and SA868_VBAT for cut-trace debugging.
"""

MCU_NOTES = """=== MCU SHEET ===

CORE:
  U2  ESP32-C3-MINI-1 (LCSC C2934569)
      Pre-certified module: integrated antenna, crystal, flash.
      Antenna keepout >= 15mm clear of GND on left wingtip.

DECOUPLING:
  100nF + 10uF on +3V3 pin (pin 3)
  Pull-up 10k on EN (pin 8)
  Reset RC: 10k + 1uF on EN with reset button (S1) to GND

BOOT:
  GPIO9 -> BOOT button (S2) to GND, also internal pullup
  Strapping behavior: GPIO9 LOW at boot => download mode
                      GPIO9 HIGH at boot => normal run
  GPIO9 in firmware: re-purposed as SEL button (read after boot)

USB:
  GPIO18 (D-) and GPIO19 (D+) direct to USB-C J1 datalines
  Optional 5.1k CC pulldowns handled in power sheet
  ESD protection: USBLC6-2SC6 on D+/D- (recommended)

PIN ASSIGNMENT TABLE:
  GPIO0  -> WS2812 DIN (LED chain start)
  GPIO1  -> OLED DC
  GPIO2  -> (strapping) WS2812 fallback / unused; pull-down 10k
  GPIO3  -> Button UP (S3)
  GPIO5  -> OLED CS
  GPIO6  -> SPI SCK -> OLED SCK
  GPIO7  -> SPI MOSI -> OLED MOSI
  GPIO8  -> (strapping HIGH) -> OLED RST (idle high; 10k pull-up)
  GPIO9  -> (strapping) BOOT button + SEL (S2)
  GPIO10 -> SA868 PTT
  GPIO11 -> SA868 UART RX (from module TX)
  GPIO12 -> SA868 UART TX (to module RX)
  GPIO13 -> SA868 PD (active low; pull-up 10k for safe boot)
  GPIO15 -> PWM out -> RC LPF -> SA868 MIC_IN
  GPIO16 -> ADC -> SA868 RX audio
  GPIO17 -> Button DN (S4)
  GPIO18 -> USB D-
  GPIO19 -> USB D+
  GPIO20 -> UART0 RX (debug header)
  GPIO21 -> UART0 TX (debug header)

NETS exiting this sheet:
  +3V3, GND, USB_DP, USB_DM,
  LED_DIN, OLED_{DC,CS,SCK,MOSI,RST}, BTN_{UP,DN,SEL,RST},
  SA868_{PTT,RX,TX,PD,MIC,AUDIO}, DBG_{RX,TX}
"""

RADIO_NOTES = """=== RADIO SHEET ===

MODULE:
  U3  SA868-V (134-174 MHz UART-controlled VHF transceiver)
      Pinout (verify against your supplier datasheet rev):
        1  GND
        2  ANT (RF, 50 ohm)
        3  GND
        4  VBAT (3.7-5V)
        5  H/L power select (HIGH=1W, LOW=0.5W; tie via 10k pull-up)
        6  RX_OUT (audio out, ~600mV pk-pk)
        7  MIC_IN (audio in, AC-coupled, ~100mV pk-pk)
        8  PTT (active low)
        9  SQ (squelch out, optional)
       10  PD (power down, active low)
       11  RXD (UART, into module)
       12  TXD (UART, out of module)
       13-16  GND

POWER ROUTING:
  VBAT -> wide trace direct to pin 4
  C20  470uF electrolytic, low-ESR, near pin 4
  C21  100nF X7R 0603, AS CLOSE TO PIN 4 AS POSSIBLE

UART:
  3V3 logic, but verify SA868 rev: some early units are 5V tolerant
  but native 3.3V. Add series 1k on RXD as safety.
  ESP GPIO12 -> R30 1k -> SA868 RXD
  SA868 TXD -> ESP GPIO11 (direct, level OK)

AUDIO PATHS:

  TX path (ESP DAC-emulation -> SA868 mic):
    ESP GPIO15 (PWM ~80kHz)
      -> R31 1k
      -> Node A
      -> R32 1k -> Node B (= MIC_IN, AC-coupled side)
      C30 100nF Node A to GND
      C31 100nF Node B to GND
    Then DC-block to SA868:
      Node B -> C32 1uF -> SA868 MIC_IN
      Bias: 10k from SA868 MIC_IN to GND (SA868 self-biases internally on most revs)

  RX path (SA868 RX_OUT -> ESP ADC):
    SA868 RX_OUT -> C40 1uF -> R40 10k divider to mid-rail (10k+10k)
                 -> ESP GPIO16 (ADC1_CH4)
    Adds ~1.65V bias for AC-coupled audio sampling.

CONTROL LINES:
  PTT  (pin 8) <- ESP GPIO10. Pull-up 10k to +3V3 (idle = RX).
  PD   (pin 10) <- ESP GPIO13. Pull-up 10k (idle = powered).
  H/L  (pin 5)  -> tie HIGH via 10k for 1W TX (or to GPIO if switchable).

ANTENNA:
  Pin 2 -> short 50ohm trace -> PI match pads (L1/C50/C51) -> antenna
  Default: L1 = 0R jumper, C50/C51 = DNP (try direct first)
  Antenna: meandered PCB trace on right wingtip, NO ground pour beneath.
  Trace length target: ~150mm meandered (lambda/12 short-loaded)
  Add 1pF tuning cap pads near antenna feed for empirical tuning.

  *** Performance disclosure: a meandered PCB trace at 145MHz on a 100mm
      board will be electrically very short. Expect single-digit dBi
      negative gain. Adequate for in-room foxhunt; no DX. ***

NETS:
  VBAT, GND, SA868_PTT, SA868_RX, SA868_TX, SA868_PD,
  SA868_MIC, SA868_AUDIO, ANT
"""

UI_NOTES = """=== UI SHEET ===

DISPLAY:
  D1   SSD1306 0.96" 128x64 OLED, SPI 7-pin module (LCSC C2890710 or AliExpress)
       Pinout (left to right looking at module front):
         GND, VCC(+3V3), SCK(D0), MOSI(D1), RST, DC, CS
       Connect:
         GND  -> GND
         VCC  -> +3V3
         SCK  -> ESP GPIO6
         MOSI -> ESP GPIO7
         RST  -> ESP GPIO8 (with 10k pull-up; strapping pin)
         DC   -> ESP GPIO1
         CS   -> ESP GPIO5

LEDS (WS2812B chain, 4 total):
  LED1..LED4 WS2812B-2020 (5050 footprint also fine; 2020 is smaller)
  VDD (each) -> +3V3, with 100nF decoupling per LED to GND
  Chain:
    ESP GPIO0 -> R10 220 ohm -> LED1.DIN
    LED1.DOUT -> LED2.DIN
    LED2.DOUT -> LED3.DIN
    LED3.DOUT -> LED4.DIN (terminated)
  Add 10uF bulk cap at the chain start.
  Placement: 2 along leading edge per side, mirrored.

BUTTONS:
  All tactile SMD or through-hole, with 10k external pull-ups (or use
  ESP internal pulls; external is more reliable on strap pins).
  All connect to GND when pressed; debounce in firmware.
    S1 RESET -> EN pin (covered in MCU sheet)
    S2 BOOT/SEL -> GPIO9
    S3 UP    -> GPIO3
    S4 DOWN  -> GPIO17

SAO HEADER (Shitty Add-On v1.69bis):
  J2  2x3 0.1" header, 6 pins:
       1  GND
       2  +3V3
       3  SDA  (free GPIO; suggest GPIO4)
       4  SCL  (free GPIO; suggest GPIO2 -- careful: strapping pin)
       5  GPIO (suggest GPIO -- use a free one)
       6  GPIO (suggest GPIO -- use a free one)

  *** With C3's tight pin budget, the SAO will need to share a strap pin
      or you'll need to skip the I2C and only expose GPIO+power. Reasonable
      compromise: power + 2 GPIO + GND, drop I2C breakout. ***

DEBUG HEADER:
  J3  1x4 0.1" pad row: GND, +3V3, GPIO20 (RX), GPIO21 (TX)
  Used for serial console + reflashing fallback.

NETS:
  +3V3, GND,
  OLED_{SCK,MOSI,DC,CS,RST},
  LED_DIN,
  BTN_{UP,DN,SEL,RST},
  SAO_{SDA,SCL,GPIO1,GPIO2}
"""


def text_block(content: str, x: float, y: float, line_height: float = 1.6, char_size: float = 1.27) -> str:
    """Render a multi-line text block as KiCad 8 schematic text items.
    Each line becomes a separate (text ...) entity for reliable rendering."""
    out = []
    for i, line in enumerate(content.rstrip("\n").split("\n")):
        # Escape double-quotes in the text
        safe = line.replace('"', '\\"')
        # Skip empty lines but still advance
        if safe.strip() == "":
            continue
        u = uuid_from(f"text-{x}-{y}-{i}")
        py = y + i * line_height
        out.append(
            f'\t(text "{safe}"\n'
            f'\t\t(exclude_from_sim no)\n'
            f'\t\t(at {x:.2f} {py:.2f} 0)\n'
            f'\t\t(effects\n'
            f'\t\t\t(font (size {char_size} {char_size}))\n'
            f'\t\t\t(justify left bottom)\n'
            f'\t\t)\n'
            f'\t\t(uuid "{u}")\n'
            f'\t)'
        )
    return "\n".join(out)


def make_sheet(name: str, notes: str, sheet_uuid: str) -> str:
    """Build a sub-sheet .kicad_sch file."""
    title_block = f'''\t(title_block
\t\t(title "Foxhunt Badge - {name}")
\t\t(date "2026-04-25")
\t\t(rev "0.1")
\t\t(company "DEFCON Foxhunt")
\t\t(comment 1 "ESP32-C3 + SA868-V foxhunt badge")
\t)'''

    body = text_block(notes, x=20.0, y=20.0)

    sch = f'''(kicad_sch
\t(version {KICAD_SCH_VERSION})
\t(generator "claude_foxhunt_gen")
\t(generator_version "1.0")
\t(uuid "{sheet_uuid}")
\t(paper "A3")
{title_block}
\t(lib_symbols)
{body}
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
'''
    return sch


def make_root(sheets_info) -> str:
    """Build the root schematic with hierarchical sheet symbols."""
    root_uuid = uuid_from("root-sheet")

    # Place 4 sheet symbols in a 2x2 grid on the root
    sheet_blocks = []
    positions = [
        (40,  30, "Power"),
        (140, 30, "MCU"),
        (40,  100, "Radio"),
        (140, 100, "UI"),
    ]
    sheet_w, sheet_h = 60.0, 40.0
    for (x, y, sname), (sname2, sfile, suuid) in zip(positions, sheets_info):
        assert sname == sname2
        block = f'''\t(sheet
\t\t(at {x} {y})
\t\t(size {sheet_w} {sheet_h})
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(stroke (width 0.15) (type solid))
\t\t(fill (color 0 0 0 0.0))
\t\t(uuid "{suuid}")
\t\t(property "Sheetname" "{sname}"
\t\t\t(at {x} {y - 0.5} 0)
\t\t\t(effects (font (size 1.5 1.5)) (justify left bottom))
\t\t)
\t\t(property "Sheetfile" "{sfile}"
\t\t\t(at {x} {y + sheet_h + 1.0} 0)
\t\t\t(effects (font (size 1.0 1.0)) (justify left top))
\t\t)
\t\t(instances
\t\t\t(project "foxhunt-badge"
\t\t\t\t(path "/{root_uuid}"
\t\t\t\t\t(page "1")
\t\t\t\t)
\t\t\t)
\t\t)
\t)'''
        sheet_blocks.append(block)

    intro_text = """=== FOXHUNT BADGE - ROOT SHEET ===

Hierarchical project. Open each sub-sheet below to see the
component plan and netlist for that section.

Topology:
  POWER   -> USB-C charging, LiPo, +3V3 LDO, bulk caps for radio
  MCU     -> ESP32-C3-MINI-1 module, USB, decoupling, pin map
  RADIO   -> SA868-V VHF, audio path, antenna match
  UI      -> SSD1306 OLED, WS2812 LEDs, buttons, SAO, debug header

Common nets carried between sheets via hierarchical labels:
  +3V3, VBAT, GND, USB_DP, USB_DM,
  OLED_{SCK,MOSI,DC,CS,RST}, LED_DIN,
  BTN_{UP,DN,SEL}, SA868_{PTT,RX,TX,PD,MIC,AUDIO}

See docs/netlist-plan.md for the full connection table.
See README.md for build / firmware / next-steps.
"""

    intro = text_block(intro_text, x=20.0, y=170.0, char_size=1.5)

    sheets_block = "\n".join(sheet_blocks)

    sch = f'''(kicad_sch
\t(version {KICAD_SCH_VERSION})
\t(generator "claude_foxhunt_gen")
\t(generator_version "1.0")
\t(uuid "{root_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "Foxhunt Badge - Root")
\t\t(date "2026-04-25")
\t\t(rev "0.1")
\t\t(company "DEFCON Foxhunt")
\t\t(comment 1 "B-2 silhouette flying-wing PCB, 100x55mm")
\t\t(comment 2 "ESP32-C3 + SA868-V VHF + SSD1306 OLED")
\t)
\t(lib_symbols)
{intro}
{sheets_block}
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
'''
    return sch


def main():
    sheets = [
        ("Power", "power.kicad_sch", uuid_from("power-sheet")),
        ("MCU",   "mcu.kicad_sch",   uuid_from("mcu-sheet")),
        ("Radio", "radio.kicad_sch", uuid_from("radio-sheet")),
        ("UI",    "ui.kicad_sch",    uuid_from("ui-sheet")),
    ]

    notes_map = {
        "Power": POWER_NOTES,
        "MCU":   MCU_NOTES,
        "Radio": RADIO_NOTES,
        "UI":    UI_NOTES,
    }

    # Sub-sheets
    for name, fname, suuid in sheets:
        path = PROJECT_DIR / fname
        path.write_text(make_sheet(name, notes_map[name], suuid))
        print(f"Wrote {path}")

    # Root sheet
    root_path = PROJECT_DIR / "foxhunt-badge.kicad_sch"
    root_path.write_text(make_root(sheets))
    print(f"Wrote {root_path}")


if __name__ == "__main__":
    main()
