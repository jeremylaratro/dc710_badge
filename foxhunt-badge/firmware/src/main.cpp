// main.cpp -- Foxhunt Badge ESP32-C3 firmware entry point
//
// Mode flow:
//   BOOT -> splash -> IDLE (animation + LED breath)
//   SEL short-press: cycle modes IDLE -> FOX -> HUNTER -> IDLE
//   SEL long-press:  enter menu (TODO)
//
// Build: PlatformIO, see ../platformio.ini

#include <Arduino.h>
#include "pins.h"
#include "sa868.h"
#include "display.h"
#include "leds.h"
#include "ui_input.h"
#include "hunt.h"

// ---- Globals ----
HardwareSerial    RadioUART(1);   // ESP32-C3 has UART0 (USB-CDC) and UART1
SA868             radio(RadioUART);
Display           display;
LedRing           leds;
UIInput           input;
HuntController    hunt(radio, display, leds);

static const HuntConfig HUNT_CFG = {
    .fox_tx_mhz       = 146.520f,   // 2m simplex calling freq -- CHANGE TO YOUR LICENSED FREQ
    .fox_rx_mhz       = 146.520f,
    .ctcss_subtone    = 0,
    .beacon_period_ms = 15000,
    .beacon_dur_ms    = 1500,
    .tone_hz          = 1200,
    .fox_id           = "DCFOX",
};

void setup()
{
    Serial.begin(115200);
    delay(500);
    Serial.printf("\n=== Foxhunt Badge fw %s ===\n", BADGE_FW_VERSION);

    leds.begin();
    leds.rainbowChase(0);

    if (!display.begin()) {
        Serial.println("[boot] display fail (continuing)");
    } else {
        display.renderSplash(BADGE_FW_VERSION);
    }

    input.begin();

    bool radio_ok = radio.begin(PIN_SA868_UART_RX, PIN_SA868_UART_TX,
                                PIN_SA868_PTT, PIN_SA868_PD,
                                PIN_SA868_MIC_PWM, PIN_SA868_RX_AUDIO);
    Serial.printf("[boot] radio handshake: %s\n", radio_ok ? "OK" : "FAIL");

    hunt.begin(HUNT_CFG);
    delay(1500);  // hold splash
}

void loop()
{
    static uint32_t last_anim_tick = 0;
    static uint32_t anim_frame = 0;
    static uint32_t last_led_tick = 0;
    uint32_t now = millis();

    // ---- Input ----
    BtnEvent ev = input.poll();
    if (ev == BtnEvent::SEL) {
        HuntMode next = HuntMode::IDLE;
        switch (hunt.mode()) {
            case HuntMode::IDLE:   next = HuntMode::FOX;    break;
            case HuntMode::FOX:    next = HuntMode::HUNTER; break;
            case HuntMode::HUNTER: next = HuntMode::IDLE;   break;
        }
        hunt.setMode(next);
    }

    // ---- Hunt logic ----
    hunt.tick();

    // ---- UI rendering (rate-limited) ----
    if ((now - last_anim_tick) >= (1000 / ANIM_FPS)) {
        last_anim_tick = now;
        switch (hunt.mode()) {
            case HuntMode::IDLE:
                display.renderIdleAnimation(anim_frame++);
                break;
            case HuntMode::FOX: {
                uint32_t since = now - 0;  // remaining time computed in hunt
                // Simple display: show beacon period countdown
                bool tx = false;  // would need accessor on HuntController; safe default
                display.renderFox(HUNT_CFG.fox_tx_mhz, tx, HUNT_CFG.beacon_period_ms);
                break;
            }
            case HuntMode::HUNTER:
                display.renderHunter(hunt.lastRSSI(), hunt.maxRSSI(),
                                     hunt.msSinceMaxRSSI());
                break;
        }
    }

    // ---- LED effects (rate-limited to 30 Hz) ----
    if ((now - last_led_tick) >= 33) {
        last_led_tick = now;
        switch (hunt.mode()) {
            case HuntMode::IDLE:   leds.idleBreath(now);              break;
            case HuntMode::FOX:    leds.foxBlink(now, /*tx*/ false);  break;
            case HuntMode::HUNTER: leds.hunterBar(hunt.lastRSSI());   break;
        }
    }
}
