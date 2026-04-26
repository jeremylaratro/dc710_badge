// display.h -- OLED UI for the foxhunt badge
// Wraps Adafruit_SSD1306 with mode-aware rendering helpers.
#pragma once

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

class Display {
public:
    Display();
    bool begin();

    void clear();
    void show();

    // Mode UIs (each builds a complete frame + show())
    void renderSplash(const char* version);
    void renderIdleAnimation(uint32_t frame_idx);   // scripted
    void renderFox(float freq_mhz, bool tx_active, uint32_t next_beacon_in_ms);
    void renderHunter(int rssi, int rssi_max, uint32_t since_max_ms);
    void renderMenu(const char* const* items, uint8_t n, uint8_t selected);

    Adafruit_SSD1306& gfx() { return _oled; }

private:
    Adafruit_SSD1306 _oled;
    void _drawSignalBar(int rssi);
};
