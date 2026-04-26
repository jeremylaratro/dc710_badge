// leds.cpp -- LED effects
#include "leds.h"

void LedRing::begin()
{
    FastLED.addLeds<WS2812B, PIN_LED_DIN, GRB>(_leds, NUM_LEDS);
    FastLED.setBrightness(40);  // conservative; bumps to ~30mA total at white
    offAll();
}

void LedRing::offAll()
{
    fill_solid(_leds, NUM_LEDS, CRGB::Black);
    FastLED.show();
}

void LedRing::idleBreath(uint32_t now_ms)
{
    // Slow sine breathing on a slowly-rotating hue
    uint8_t v = (uint8_t)(127 + 127 * sin(now_ms / 800.0));
    _hue = (now_ms / 100) & 0xFF;
    for (int i = 0; i < NUM_LEDS; ++i) {
        _leds[i] = CHSV(_hue + i * 16, 200, v);
    }
    FastLED.show();
}

void LedRing::foxBlink(uint32_t now_ms, bool tx)
{
    if (tx) {
        // Red strobe during TX
        bool on = ((now_ms / 100) & 1) == 0;
        fill_solid(_leds, NUM_LEDS, on ? CRGB::Red : CRGB::Black);
    } else {
        // Dim amber idle
        fill_solid(_leds, NUM_LEDS, CRGB(20, 8, 0));
    }
    FastLED.show();
}

void LedRing::hunterBar(int rssi)
{
    // Light up LEDs progressively with RSSI; color shifts red->green as signal gets stronger
    int lit = (rssi * (NUM_LEDS + 1)) / 256;
    if (lit > NUM_LEDS) lit = NUM_LEDS;
    for (int i = 0; i < NUM_LEDS; ++i) {
        if (i < lit) {
            uint8_t hue = map(rssi, 0, 255, 0, 96);  // 0=red, 96=green
            _leds[i] = CHSV(hue, 255, 200);
        } else {
            _leds[i] = CRGB::Black;
        }
    }
    FastLED.show();
}

void LedRing::rainbowChase(uint32_t now_ms)
{
    _hue = (now_ms / 20) & 0xFF;
    for (int i = 0; i < NUM_LEDS; ++i) {
        _leds[i] = CHSV(_hue + i * 64, 255, 200);
    }
    FastLED.show();
}
