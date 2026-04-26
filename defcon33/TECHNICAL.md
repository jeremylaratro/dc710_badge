# Foxhunt Badge — DEFCON B-2 Edition

ESP32-C3 + SA868-V VHF transceiver in a B-2 Spirit silhouette PCB.
~$16 BOM at qty 100, single-cell LiPo, 100×55mm flying-wing form factor.

> **Status: complete schematic + working firmware + correct outline.**
> Project opens in KiCad 8 with 67 components placed and wired. B-2
> outline has 3 aft-pointing triangles (left-outboard + center + right-
> outboard). Firmware compiles and runs.

---

## What's in the box

### KiCad 8 project
- `foxhunt-badge.kicad_pro` — project settings, three netclasses (Default, Power, RF)
- `foxhunt-badge.kicad_sch` — single-page schematic, A2 paper, 19 embedded symbol library definitions, 67 placed components, 189 wires + 189 labels. Every pin connected via net-label style — ERC-clean.
- `foxhunt-badge.kicad_pcb` — B-2 silhouette on Edge.Cuts, 26 line segments, **3 aft-pointing triangles**. KiCad 6 format; KiCad 8 auto-upgrades on open.

### Wiring correctness
- Audio RX path: C40 DC-block lands on SA868_AUDIO (ESP GPIO16 ADC) with R40/R41 biasing to mid-rail
- LED chain: ESP GPIO0 → R11 220Ω → D3.DIN → D4 → D5 → D6 (terminated)
- SA868 UART: ESP GPIO12 → R30 1kΩ series → SA868 RXD; SA868 TXD → ESP GPIO11 direct
- Strap pins handled: GPIO2 pulled down via R10, GPIO8 (OLED_RST) pulled up via R6, GPIO9 (SEL/BOOT) pulled up via R5

### Documentation
- `docs/netlist-plan.md` — canonical connection reference with audio path ASCII, antenna match, power tree
- `docs/placement-plan.md` — coordinate-level placement on the B-2 outline, antenna keep-outs, routing priority

### Firmware (PlatformIO)
- `firmware/src/pins.h` — single-source pin map
- `firmware/src/sa868.{h,cpp}` — AT command interface, DMOSETGROUP frequency/CTCSS/squelch, RSSI read, PTT, sleep, PWM tone generation for CW keying
- `firmware/src/hunt.{h,cpp}` — FOX/HUNTER/IDLE state machines with full Morse A-Z/0-9 CW callsign beacon
- `firmware/src/display.{h,cpp}` — SSD1306 wrapper with per-mode renderers
- `firmware/src/leds.{h,cpp}` — FastLED effects (idle breath, fox blink, hunter bar, rainbow chase)
- `firmware/src/ui_input.{h,cpp}` — 30ms debounced buttons with 800ms long-press detection
- `firmware/src/anim_frames.h` — 60-frame 128×64 1-bit animation (B-2 flying + radar sweep + FOXHUNT logo reveal), ~60KB PROGMEM
- `firmware/src/main.cpp` — top-level orchestration

### Fab tooling
- `bom.csv` — every component with LCSC PNs for JLCPCB
- `fab/b2_outline.dxf` — DXF of the outline
- `fab/generate_b2_outline.py` — parametric outline generator (tune SPAN_MM, CHORD_MM)
- `fab/generate_full_sch.py` — regenerates the complete schematic
- `fab/sch_lib_symbols.py` — embedded Symbol library definitions
- `fab/generate_anim.py` — regenerate animation frames

## Next steps

1. **Open `foxhunt-badge.kicad_pro`** in KiCad 8. Accept the PCB format upgrade prompt.

2. **Review the schematic.** 67 components laid out in four zones (Power, MCU, Radio, UI). Each pin has a wire stub and a net label. Nets connect by matching label names. Run ERC; expected warnings only for:
   - `LED_END` — WS2812 chain terminator
   - `SAO_GPIO3`, `SAO_GPIO4` — extra SAO pins left floating (C3 pin-budget compromise)

3. **Assign footprints.** Most passives and LEDs already have footprints set in their Symbol properties. Verify and fix:
   - `U2` (ESP32-C3-MINI-1) → use `RF_Module:ESP32-C3-MINI-1` from your installed libs
   - `U3` (SA868) — **no KiCad stock footprint**. Create from datasheet (16 castellated pads, 2.54mm pitch, ~28×40mm body) or import from OSHWLab
   - `J1` (USB-C) — verify against supplier's exact HRO TYPE-C-31-M-12 variant

4. **Update PCB from Schematic** (Tools menu). Components drop next to the B-2 outline.

5. **Place** components per `docs/placement-plan.md`.

6. **Pour ground** on B.Cu, respecting antenna keep-outs (right wingtip = SA868 trace antenna zone; left wingtip = ESP32 module antenna zone).

7. **Route.** Priority order in placement plan.

8. **DRC clean → Plot Gerbers → JLCPCB.**

## Firmware build & flash

```bash
cd firmware
pio run                  # build
pio run -t upload        # flash via USB-C
pio device monitor       # serial console at 115200
```

First boot: rainbow chase LEDs, splash OLED, idle animation.
SEL button cycles modes (IDLE → FOX → HUNTER → IDLE).

**Frequency configuration**: `main.cpp` defaults to 146.520 MHz (US 2m simplex). Transmitting on this freq requires a US Technician ham license. For license-free testing, use a **SA868-U** (UHF) variant on PMR446 with a correspondingly shorter antenna meander.

## Honest disclosures

1. **PCB antenna performance at VHF will be poor.** Meandered trace on a 100mm board at 145 MHz is electrically very short — expect single-digit-negative dBi gain. Fine for in-room foxhunt; not for DX. Next rev: add u.FL footprint for external whip.

2. **SA868 footprint is not in KiCad's stock library.** You'll need to create one from the datasheet or import from OSHWLab. The pinout is documented in `fab/sch_lib_symbols.py` (`SA868_PINS`) and `docs/netlist-plan.md`.

3. **Tone synthesis uses `ledcWriteTone()`.** Works for CW/beacon tones, not arbitrary audio. Voice playback would need an external I²S DAC.

4. **Embedded symbol library is minimal.** Symbol graphics are rectangular bodies with pin numbers. KiCad accepts these and connectivity is correct, but if you want the "pretty" stock KiCad symbols, use **Edit → Symbol Library Links** after opening to re-link each reference (`Device:R`, `RF_Module:ESP32-C3-MINI-1`, etc.) to your installed libraries. The embedded versions are a fallback for environments without the stock libs.

## Next-rev wishlist

- u.FL connector + external whip option
- Piezo or PAM8302 + 8Ω speaker for RX audio
- ESP32-S3 for more flash/GPIO/color OLED option
- Proper SAO v1.69bis compliance (needs 4 free GPIOs; may require dropping a button or adding an I/O expander)
