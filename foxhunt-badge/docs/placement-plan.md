# Component Placement Plan (B-2 Silhouette)

PCB origin in KiCad is at **(100, 50)** mm — corresponds to the nose tip
of the B-2 outline. X spans ±50mm (wingtip to wingtip), Y goes 0 to 55mm
(nose to trailing edge centerline).

## Placement Zones (top view, looking at F.Cu)

```
          NOSE (0, 0)
              ▼
   ┌──────────────────────────┐
   │       LEDs along         │   y = 12-20
   │     leading edges        │   D3 (left), D6 (right)
   │  D3 ◇          ◇ D6      │
   │                          │
   │     ┌──────────────┐     │
   │ D4 ◇│   ESP32-C3   │◇ D5 │   y = 20-30
   │     │   (U2)       │     │
   │     └──────┬───────┘     │
   │        ┌───┴────┐        │
   │        │ OLED   │        │   y = 30-40
   │        │ (DISP1)│        │   centered, 27x27mm
   │        └────────┘        │
   │  ┌────────────────────┐  │
   │  │   SA868 (U3)       │  │   y = 38-50
   │  │   28x40mm module   │  │   centered
   │  └─────────┬──────────┘  │
   │  S3 □    [J2]    □ S4    │   y = 47-52
   │  UP    SAO       DN      │
   │       □ S2 SEL/BOOT      │
   │   ╱╲   ╱╲   ╱╲   ╱╲      │   trailing-edge sawtooth
   └──╱──╲─╱──╲─╱──╲─╱──╲─────┘
   wingtip      center      wingtip
```

## Specific Placements

| Component | Position (x,y mm) | Layer | Notes |
|-----------|-------------------|-------|-------|
| U2 (ESP32-C3-MINI-1) | (-7, 24) | F.Cu | Antenna pointing -X (left wingtip) |
| U3 (SA868)           | ( 0, 42) | F.Cu | RF pin (pin 2) toward +X (right) |
| DISP1 (OLED)         | ( 0, 32) | F.Cu | Bezel centered on Y axis |
| D3 (WS2812 #1)       | (-30, 14)| F.Cu | Outer left leading edge |
| D4 (WS2812 #2)       | (-15, 18)| F.Cu | Inner left |
| D5 (WS2812 #3)       | ( 15, 18)| F.Cu | Inner right |
| D6 (WS2812 #4)       | ( 30, 14)| F.Cu | Outer right leading edge |
| S1 (RESET)           | ( 0,  4) | F.Cu | Nose, small footprint, recessed |
| S2 (SEL/BOOT)        | ( 0, 50) | F.Cu | Center trailing edge |
| S3 (UP)              | (-15, 49)| F.Cu | Left of SEL |
| S4 (DN)              | ( 15, 49)| F.Cu | Right of SEL |
| J1 (USB-C)           | ( 35, 50)| Edge-mount | Right wingtip trailing edge |
| J2 (SAO)             | ( 0, 52) | B.Cu | Back side, near trailing center |
| J3 (Debug)           | (-35, 50)| B.Cu | Left wingtip, back side |
| TP4056 module        | ( 0, 30) | B.Cu | Centered on back |
| BAT1 (LiPo)          | ( 0, 42) | B.Cu | Tucked under SA868 footprint |
| ANT (PCB trace)      | ( 35-50, 5-30) | F.Cu | Right wingtip, NO ground pour |

## Antenna Keep-Out Zones

Two antennas competing for ground-free real estate:

1. **ESP32-C3 module antenna** (built-in, on the module itself):
   Module's antenna end points toward LEFT wingtip.
   Keep-out: 15mm × 8mm zone immediately to the LEFT (–X) of U2.
   No ground pour, no traces, no copper in this zone, both layers.

2. **SA868 PCB trace antenna**:
   On RIGHT wingtip, fed from L1 match position.
   Keep-out: ~50×30mm zone covering the right wingtip.
   No ground pour beneath the meandered trace, both layers.

The B-2 wingtips happen to be the natural locations for these zones — happy coincidence with the form factor.

## Routing Priority Order

1. **Edge.Cuts** — already laid in (B-2 outline).
2. **GND pour** on B.Cu (everywhere except antenna keep-outs).
3. **VBAT trace** from TP4056 to U3 pin 4 — wide (≥0.5mm), short.
4. **+3V3 trace** from U1 to all loads — moderate (≥0.4mm).
5. **RF trace** from U3 pin 2 to L1 to antenna — 50Ω controlled
   if you want to be precise (on 1.6mm FR-4, 2-layer, 50Ω microstrip
   over solid GND is ~2.9mm wide; relax this for the meandered antenna trace).
6. **Audio paths** (MIC, RX_AUDIO) — keep away from WS2812 data line and crystal.
7. **WS2812 chain** — daisy-chain shortest path along leading edge.
8. **OLED SPI bus** — group SCK/MOSI/DC/CS together; RST can route separately.
9. **UART to SA868** — group RX/TX, 8mil OK at 9600 baud.
10. **Buttons** — single-trace per button to ESP, freedom of route.
