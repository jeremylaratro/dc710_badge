# Foxhunt Badge — DEFCON B-2 Edition

ESP32-C3 + SA868-V VHF transceiver in a B-2 Spirit silhouette PCB.
~$16 BOM at qty 100, single-cell LiPo, **200×80mm** flying-wing form
factor (~7.87" tip-to-tip, real B-2 proportions: wingspan/length ≈ 2.5,
~31° leading-edge sweep).

> **Status (2026-04-25, v1.2): KiCad 9 schematic ERC-clean (0 errors,
> 0 warnings).  PCB on 200×80 mm B-2 outline (4 aft-pointing apexes + 3
> forward notches including center notch).  All 56 footprints inside the
> outline.  U2 uses the **official Espressif ESP32-C3-MINI-1 footprint**
> (53 pads, fetched from github.com/espressif/kicad-libraries).  The
> netlist pin numbers match the official datasheet pinout exactly.
> Freerouting v2.1.0 routed **119 of 131 nets (350 track segments)** in
> a 30-pass autoroute.  12 nets remain unrouted in the dense central
> module area; these need hand-finishing in pcbnew.**

---

## Project layout

```
foxhunt-badge/
├── foxhunt-badge.kicad_pro      # KiCad 9 project file
├── foxhunt-badge.kicad_sch      # schematic (ERC-clean)
├── foxhunt-badge.kicad_pcb      # PCB (placed, ground-poured, awaiting routing)
├── sym-lib-table                # registers project symbol library
├── fp-lib-table                 # registers project footprint library
├── lib/
│   ├── foxhunt.kicad_sym        # custom symbols (ESP32-C3-MINI-1, SA868,
│   │                            #                 TP4056_Module, OLED_SSD1306)
│   └── foxhunt.pretty/          # custom footprints
├── docs/                        # netlist + placement reference
├── fab/
│   ├── lib_gen.py               # regenerate lib/foxhunt.kicad_sym
│   ├── footprint_gen.py         # regenerate lib/foxhunt.pretty/
│   ├── sch_gen.py               # regenerate the schematic
│   ├── pcb_gen.py               # regenerate the PCB
│   ├── generate_b2_outline.py   # parametric B-2 outline generator
│   └── output/                  # Gerbers, drill, BOM, position files
└── firmware/                    # PlatformIO ESP-IDF firmware
```

## What's in the schematic (59 components, 43 nets)

* **Power tree:** USB-C 16P → SS14 Schottky → TP4056 LiPo charger → AP2112K-3.3
  LDO → 3.3 V rail.  3 PWR_FLAG drivers (VBUS, VBAT_RAW, GND) keep ERC happy.
* **MCU:** ESP32-C3-MINI-1 with EN reset RC, 10 µF / 1 µF / 100 nF decoupling,
  RESET / SEL / UP / DN tactiles, USB-C as native USB 2.0 (CDC) plus UART debug
  pass-through (J3).
* **Radio:** SA868-V (VHF) module with PTT / PD pull-ups, UART1 control, audio
  TX low-pass network (R-C-R-C-C), audio RX bias network (DC-block + mid-rail
  divider), trace-antenna match (L1 + DNP shunt caps for VNA tuning).
* **UI:** SSD1306 SPI 0.96" OLED, four WS2812B-2020 RGB LEDs in a chain along
  the leading edge, status LED, 2×3 SAO header, 1×4 debug header.

## ESP32-C3 pin map

| GPIO | Function          |
|------|-------------------|
| 0    | WS2812 DIN        |
| 1    | OLED_DC           |
| 2    | SA868_AUDIO (ADC) |
| 3    | BTN_UP            |
| 4    | SA868_PTT         |
| 5    | OLED_CS           |
| 6    | OLED_SCK          |
| 7    | OLED_MOSI         |
| 8    | BTN_DN            |
| 9    | BTN_SEL (boot)    |
| 10   | SA868_TX (UART1)  |
| 18   | USB_DM            |
| 19   | USB_DP            |
| 20   | SA868_RX (UART1)  |
| 21   | OLED_RST          |

## What still needs hand-finishing

The auto-generated PCB has all footprints positioned and nets assigned, but
the following still need attention in the KiCad GUI:

1. **Routing.** 132 ratsnest connections remain.  Suggested order:
   1. VBUS / VBAT / +3V3 power tree (use 0.5 mm tracks, Power netclass).
   2. RF chain U3.ANT → L1 → trace antenna (Right wingtip, RF netclass).
   3. Audio paths (MIC / RX_OUT) — keep away from WS2812 DIN.
   4. WS2812 daisy-chain along the leading edge.
   5. OLED SPI bus (group SCK/MOSI together).
   6. Buttons, debug header, SAO.
2. **Placement refinement.** ~10 components have minor courtyard overlaps
   from the auto-placer; spread them slightly in the GUI.
3. **Silkscreen.** Reference designators may need to be moved off pads
   (silk-on-copper warnings).
4. **Final DRC pass** before plotting fab outputs.

## Regenerating the project from scratch

```bash
# Library
python3 fab/lib_gen.py
python3 fab/footprint_gen.py

# Schematic + PCB
python3 fab/sch_gen.py
python3 fab/pcb_gen.py

# Validation
kicad-cli sch erc -o /tmp/erc.rpt foxhunt-badge.kicad_sch   # 0 violations
kicad-cli pcb drc -o /tmp/drc.rpt foxhunt-badge.kicad_pcb   # 132 unconnected (ratsnest)

# Fab outputs (after routing in GUI)
mkdir -p fab/output
kicad-cli pcb export gerbers --output fab/output/ foxhunt-badge.kicad_pcb
kicad-cli pcb export drill   --output fab/output/ foxhunt-badge.kicad_pcb
kicad-cli pcb export pos     --output fab/output/foxhunt-badge-pos.csv \
                             --format csv --units mm foxhunt-badge.kicad_pcb
kicad-cli sch export bom     --output fab/output/foxhunt-badge-bom.csv \
                             --fields "Reference,Value,Footprint,MPN,LCSC" \
                             --group-by Value foxhunt-badge.kicad_sch
```

## Custom libraries

Because KiCad's stock libraries don't ship the exact parts we use, four
custom symbols and four custom footprints live in `lib/`:

| Item                          | Symbol | Footprint | Source                             |
|-------------------------------|--------|-----------|------------------------------------|
| ESP32-C3-MINI-1 (53-pad MSMD) | ✓      | ✓         | Espressif datasheet rev 1.1        |
| SA868-V (16-pin castellated)  | ✓      | ✓         | NiceRF SA868 datasheet             |
| TP4056_Module (5-pin breakout)| ✓      | ✓         | LCSC C16581 module                 |
| OLED_SSD1306 7-pin SPI        | ✓      | ✓         | Generic 0.96" OLED breakout        |

These are registered via `sym-lib-table` and `fp-lib-table` and pinned in
the project preferences so they show up first in the picker.

## Firmware build & flash

```bash
cd firmware
pio run                  # build
pio run -t upload        # flash via USB-C
pio device monitor       # serial console at 115200
```

First boot: rainbow chase LEDs, splash OLED, idle animation.
SEL button cycles modes (IDLE → FOX → HUNTER → IDLE).

**Frequency configuration**: `main.cpp` defaults to 146.520 MHz (US 2m
simplex).  Transmitting on this freq requires a US Technician ham license.
For license-free testing, use a SA868-U (UHF) on PMR446 with a shorter
antenna meander.

## Honest disclosures

1. **PCB trace antenna performance at VHF will be poor.**  ~150 mm of meander
   on a 100 mm board at 145 MHz is electrically short — single-digit-negative
   dBi gain expected.  Fine for in-room foxhunt; not for DX.  The match
   network has DNP shunts (C50 / C51) for VNA tuning.  Next rev: add a u.FL
   footprint for an external whip.
2. **SA868 footprint is hand-built from the datasheet.**  Verify the pad
   geometry against your actual modules before fab.
3. **Audio TX synthesis uses ledcWriteTone().**  Adequate for CW/beacon tones,
   not arbitrary audio.  Voice TX would need an external I²S DAC.
4. **Routing is hand-finishing work.**  This generator places components and
   wires nets in the schematic; track routing is left to the GUI (or to a
   freerouting/specctra round-trip).  The placement plan in `docs/` is the
   intended ground truth for layout.

## Next-rev wishlist

* u.FL connector + external VHF whip
* PAM8302 + 8 Ω speaker for RX audio
* ESP32-S3 for more flash / GPIO / color OLED
* Full SAO v1.69bis compliance (needs 4 free GPIOs — likely requires an I/O
  expander on this rev's pin budget)
