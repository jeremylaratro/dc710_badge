# DC710 Badge — DEF CON 34 (B-2 Spirit)

Flying-wing PCB badge in a real B-2 Spirit silhouette.  ESP32-C3 +
SA868-V VHF transceiver, single-cell LiPo, USB-C charging, OLED display,
4× WS2812 RGB LEDs, 3× tactile buttons, SAO header.

**Board:** 200 × 77 mm (≈ 7.87" tip-to-tip), real B-2 proportions
(wingspan/length ≈ 2.5).  Outline extracted from a real B-2 STL mesh —
3 aft-pointing spikes, engine-cutout notches, sharp swept wingtips.

![Top view](images/badge_top.png)

![Bottom view](images/badge_bottom.png)

---

## What's in the project

### Hardware
- **MCU:** ESP32-C3-MINI-1 module (official Espressif footprint, 53 pads)
- **Radio:** G-NiceRF SA868-V VHF (134–174 MHz) walkie-talkie module
- **Display:** SSD1306 0.96" OLED, 7-pin SPI
- **Power:** USB-C → SS14 Schottky → TP4056 LiPo charger → AP2112K-3.3 LDO
- **Battery:** Single-cell LiPo via JST-PH 2-pin
- **UI:** 4× WS2812B-2020 RGB LEDs, 3× TL3342 tactile (RESET / SEL / UP / DN), green status LED
- **Expansion:** SAO v1.69bis 2x3 header, 1×4 debug UART header

### KiCad 9 project (`foxhunt-badge/`)
| File | What it is |
|---|---|
| `foxhunt-badge.kicad_pro` | KiCad 9 project (3 netclasses: Default, Power, RF) |
| `foxhunt-badge.kicad_sch` | Schematic (ERC-clean, 0 errors / 0 warnings) |
| `foxhunt-badge.kicad_pcb` | PCB, freerouted (128 of 131 nets) |
| `lib/foxhunt.kicad_sym` | Custom symbols (SA868, TP4056_Module, OLED) |
| `lib/foxhunt.pretty/` | Custom + official Espressif ESP32-C3-MINI-1 footprint |
| `sym-lib-table` / `fp-lib-table` | Project library registration |

### Generators (`foxhunt-badge/fab/`)
The schematic, PCB, and outline are reproducible from Python:
| Script | Output |
|---|---|
| `lib_gen.py` | `lib/foxhunt.kicad_sym` |
| `footprint_gen.py` | `lib/foxhunt.pretty/*.kicad_mod` |
| `sch_gen.py` | `foxhunt-badge.kicad_sch` |
| `pcb_gen.py` | `foxhunt-badge.kicad_pcb` (placement + GND pours + via stitching) |
| `generate_b2_outline.py` | Outline polygon, extracted from `b2.stl` and scaled |

### Fab outputs (`foxhunt-badge/fab/output/`)
Regenerated from KiCad 9 via `kicad-cli`:
- 26 Gerber files (F.Cu, B.Cu, mask, paste, silk, fab, courtyard, edge cuts)
- Excellon drill file (`.drl`)
- BOM CSV (`foxhunt-badge-bom.csv`) grouped by value, with MPN / LCSC fields
- Position CSV for pick-and-place (`foxhunt-badge-pos.csv`)

### Firmware (`foxhunt-badge/firmware/`)
PlatformIO ESP-IDF project — see `defcon33/README.md` for details on the
firmware modules (largely unchanged from DEF CON 33: `sa868`, `hunt`,
`display`, `leds`, `ui_input`, `anim_frames`).

---

## ESP32-C3 GPIO map

| GPIO | Pad | Function |
|---|---|---|
| EN  |  6 | Reset (S1 + R4 + C7 RC) |
| 0   | 13 | WS2812 LED chain DIN (R11 220Ω series) |
| 1   | 14 | OLED DC |
| 2   |  7 | SA868 audio RX (ADC1_CH2, mid-rail biased) |
| 3   |  8 | UP button |
| 4   | 27 | SA868 PTT |
| 5   | 28 | OLED CS |
| 6   | 30 | OLED SCK |
| 7   | 31 | OLED MOSI |
| 8   | 20 | DOWN button (strap, pull-up at boot) |
| 9   | 19 | SEL / BOOT (strap, pull-up) |
| 10  | 11 | SA868 UART TX (UART1) |
| 18  | 16 | USB D− |
| 19  | 17 | USB D+ |
| 20  | 23 | SA868 UART RX |
| 21  | 24 | OLED RES |

---

## Routing summary

- **577 routed track segments** (freerouting v2.1.0, 60 passes, ~2 min)
- **63 GND stitching vias** auto-placed inside the polygon
- **128 of 131 nets routed** automatically; 3 unrouted (audio LPF cluster) are quick hand-fixes in pcbnew
- Front and back GND pours fill the entire wing area, with antenna keep-outs at both wingtips (left = ESP32 module antenna, right = SA868 trace antenna)

---

## Building from source

```bash
cd foxhunt-badge

# Regenerate symbol library, footprints, schematic, and PCB
python3 fab/lib_gen.py
python3 fab/footprint_gen.py
python3 fab/sch_gen.py
python3 fab/pcb_gen.py            # places components, draws Edge.Cuts,
                                   # adds GND pours + via stitching

# Validate
kicad-cli sch erc -o /tmp/erc.rpt foxhunt-badge.kicad_sch    # 0 violations
kicad-cli pcb drc -o /tmp/drc.rpt foxhunt-badge.kicad_pcb

# Route (requires java + freerouting.jar in ~/apps/programs/freerouting/)
python3 -c "import pcbnew; b = pcbnew.LoadBoard('foxhunt-badge.kicad_pcb'); \
            print(pcbnew.ExportSpecctraDSN(b, '/tmp/foxhunt.dsn'))"
java -jar ~/apps/programs/freerouting/freerouting.jar \
    -de /tmp/foxhunt.dsn -do /tmp/foxhunt.ses -mp 60 -mt 1
python3 -c "import pcbnew; b = pcbnew.LoadBoard('foxhunt-badge.kicad_pcb'); \
            pcbnew.ImportSpecctraSES(b, '/tmp/foxhunt.ses'); \
            pcbnew.ZONE_FILLER(b).Fill(list(b.Zones())); \
            b.Save('foxhunt-badge.kicad_pcb')"

# Generate fab outputs
mkdir -p fab/output
kicad-cli pcb export gerbers --output fab/output/ foxhunt-badge.kicad_pcb
kicad-cli pcb export drill   --output fab/output/ foxhunt-badge.kicad_pcb
kicad-cli pcb export pos     --output fab/output/foxhunt-badge-pos.csv \
                             --format csv --units mm foxhunt-badge.kicad_pcb
kicad-cli sch export bom     --output fab/output/foxhunt-badge-bom.csv \
                             --fields "Reference,Value,Footprint,MPN,LCSC" \
                             --group-by Value foxhunt-badge.kicad_sch
```

---

## What's left to hand-finish

1. Route the 3 remaining nets in pcbnew (audio LPF cluster).
2. Move 4 short traces out of the antenna keep-out zones (RF perf).
3. Reposition silkscreen reference designators that overlap pads.
4. Order Gerbers from JLCPCB (or your preferred fab) — black solder mask
   strongly recommended for the stealth-bomber aesthetic.

---

## Honest disclosures

1. **PCB trace antenna performance at VHF will be poor.**  ~150 mm of
   meander on a flying-wing PCB at 145 MHz is electrically short — expect
   single-digit-negative dBi gain.  Fine for in-room foxhunt; not for DX.
   The match network has DNP shunts (C50 / C51) for VNA tuning.
2. **SA868 footprint is hand-built from the NiceRF datasheet.**  Verify
   pad geometry against your actual modules before fab.
3. **Audio TX synthesis uses `ledcWriteTone()`.**  Adequate for CW /
   beacon tones, not arbitrary audio.
4. **Frequency configuration:** firmware defaults to 146.520 MHz (US 2 m
   simplex).  Transmitting on this freq requires a US Technician ham
   license.  For license-free testing, swap to a SA868-U (UHF) variant
   on PMR446 with a shorter antenna meander.

---

## Previous edition

The DEF CON 33 design (smaller 100 × 55 mm board, 3-triangle outline,
hand-rolled symbols) lives in [`defcon33/`](defcon33/).
