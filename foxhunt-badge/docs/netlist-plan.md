# Foxhunt Badge — Netlist Plan

This document is the **source of truth** for connections. The KiCad
sub-sheets contain text annotations that mirror this content, but
this file is the canonical reference when wiring up the schematic.

## Power Tree

```
                     +5V (USB)                    +VBAT (3.0-4.2V)         +3V3
USB-C VBUS ──D1──> TP4056 IN+         TP4056 OUT+ ────┬─────► U1 (AP2112) ──┬──►
                   TP4056 BAT+ ◄──BAT── J4 (LiPo)     │                     │
                                                       └──► SA868 VBAT (pin 4)
                                                       └──► WS2812 chain
                                                            (only if you
                                                            pick high-current
                                                            LDO; otherwise
                                                            +3V3 for LEDs)
```

Decision: route LEDs from **+3V3** (lower current draw, cleaner) — AP2112 600mA is enough for 4× WS2812 + ESP32 + OLED.

## Critical Net Table

| Net       | Class | Source        | Sinks                                        | Notes |
|-----------|-------|---------------|----------------------------------------------|-------|
| VBUS      | Power | J1 pin A4/B4  | D1 anode                                     | 5V from host |
| VBAT      | Power | TP4056 OUT+   | U1 Vin, SA868 pin 4 (radio)                  | wide trace, ≥0.5mm |
| +3V3      | Power | U1 Vout       | U2 pin 3, OLED VCC, WS2812 VDD, all pull-ups | bulk 10µF + 1µF |
| GND       | Power | TP4056 GND    | every component, copper pour                 | star at TP4056 |
| USB_DP    | Sig   | J1 A6/B6      | U2 GPIO19                                    | optional U5 ESD |
| USB_DM    | Sig   | J1 A7/B7      | U2 GPIO18                                    | optional U5 ESD |

## ESP32-C3 → SA868 Connections

| ESP Pin | SA868 Pin | Direction | Net Name      | Series   | Pull   |
|---------|-----------|-----------|---------------|----------|--------|
| GPIO11  | 12 (TXD)  | RX (in)   | SA868_TX      | direct   | none   |
| GPIO12  | 11 (RXD)  | TX (out)  | SA868_RX      | R30 1k   | none   |
| GPIO10  | 8  (PTT)  | out       | SA868_PTT     | direct   | R7 10k pullup |
| GPIO13  | 10 (PD)   | out       | SA868_PD      | direct   | R8 10k pullup |
| GPIO15  | 7  (MIC)  | out (PWM) | SA868_MIC     | LPF stage| —      |
| GPIO16  | 6  (RX_OUT)| in (ADC) | SA868_AUDIO   | DC-block | bias mid-rail |

## ESP32-C3 → OLED (SPI)

| ESP Pin | OLED Pin | Net      |
|---------|----------|----------|
| GPIO6   | SCK (D0) | OLED_SCK |
| GPIO7   | MOSI (D1)| OLED_MOSI|
| GPIO5   | CS       | OLED_CS  |
| GPIO1   | DC       | OLED_DC  |
| GPIO8   | RST      | OLED_RST | (10k pull-up, strap pin must be HIGH at boot — RST idle high satisfies this) |
| —       | VCC      | +3V3     |
| —       | GND      | GND      |

## WS2812B Chain (4 LEDs)

```
GPIO0 ──[R11 220R]──► D3.DIN
                     D3.DOUT ──► D4.DIN
                                 D4.DOUT ──► D5.DIN
                                             D5.DOUT ──► D6.DIN  (terminated)
```

Decoupling: 100nF per LED (C8–C11) between VDD and GND, plus 10µF bulk (C12) at chain start.

## Buttons

| Reference | Function | ESP Pin | Pull   | Active |
|-----------|----------|---------|--------|--------|
| S1        | RESET    | EN      | R4 10k | low    |
| S2        | BOOT/SEL | GPIO9   | R5 10k + R13 10k | low |
| S3        | UP       | GPIO3   | R12 10k| low    |
| S4        | DOWN     | GPIO17  | R14 10k| low    |

All buttons pull their pin to GND when pressed. External pull-ups recommended over internal (more reliable across boot/strap timing).

## Audio TX Path Detail

```
ESP GPIO15 (PWM 80kHz, 8-bit duty)
   │
   R31 1k
   │
   ├── C30 100nF ── GND        (1st-order pole at ~1.6 kHz)
   │
   R32 1k
   │
   ├── C31 100nF ── GND        (2nd-order; -3dB ~1.6 kHz)
   │
   C32 1uF (DC block)
   │
   ▼
SA868 MIC_IN (pin 7)
```

Cutoff is intentional: keeps audio in 300Hz–3kHz voice band, kills PWM carrier. For CTCSS subtones (67–250 Hz), increase cap values 10× or use a separate path.

## Audio RX Path Detail

```
SA868 RX_OUT (pin 6, ~600mVpp AC-coupled internally)
   │
   C40 1uF (DC block, in case module isn't AC-coupling)
   │
   Node ──── R40 10k ──── +3V3
   │
   ├── R41 10k ──── GND        (mid-rail bias = 1.65V)
   │
   ▼
ESP GPIO16 (ADC1_CH4)
```

## Antenna

```
SA868 pin 2 (ANT)
   │
   ── short 50Ω trace (~5mm) ──
   │
   L1 (0R jumper, default; replace with inductor if VNA tuning calls for it)
   │
   ── meandered trace, ~150mm total length, on right wingtip ──
   ── NO ground pour beneath antenna trace ──
   ── 5mm clearance from any other copper ──
```

C50, C51 are DNP (do-not-place) pads in shunt configuration on either side of L1, populated only if a VNA pull shows return loss > –10 dB at 145 MHz.

## SAO Header (J2, 2x3 0.1")

| Pin | Net      | Note |
|-----|----------|------|
| 1   | GND      | spec |
| 2   | +3V3     | spec |
| 3   | SAO_GPIO1| (was SDA) — connected to a free GPIO; recommend leaving unconnected unless explicitly needed |
| 4   | SAO_GPIO2| (was SCL) — same |
| 5   | SAO_GPIO3| spec |
| 6   | SAO_GPIO4| spec |

Honest note: with C3's tight pin budget and strap-pin constraints, the SAO is power+passthrough only on this rev. Move to S3/full SAO compliance when board respins.

## Debug Header (J3, 1x4 0.1")

| Pin | Net   |
|-----|-------|
| 1   | GND   |
| 2   | +3V3  |
| 3   | GPIO20 (UART0 RX) |
| 4   | GPIO21 (UART0 TX) |

## Reset Circuit

```
+3V3 ── R4 10k ──┬── EN (pin 8 of U2)
                 │
                 └── S1 ── GND      (RESET button)
                 │
                 └── C7 1uF ── GND  (power-on reset RC)
```
