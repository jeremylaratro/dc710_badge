// leds.h -- WS2812B chain effects for the foxhunt badge
#pragma once

#include <Arduino.h>
#include <FastLED.h>
#include "pins.h"

class LedRing {
public:
    void begin();

    // Effect routines (each call advances state; call repeatedly from loop)
    void offAll();
    void idleBreath(uint32_t now_ms);          // slow color cycle, low brightness
    void foxBlink(uint32_t now_ms, bool tx);   // pulse red on TX, dim green idle
    void hunterBar(int rssi);                  // light proportional to RSSI
    void rainbowChase(uint32_t now_ms);        // demo / boot

    void setBrightness(uint8_t b) { FastLED.setBrightness(b); FastLED.show(); }

private:
    CRGB _leds[NUM_LEDS];
    uint8_t _hue = 0;
};
