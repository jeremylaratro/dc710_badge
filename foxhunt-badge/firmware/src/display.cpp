// display.cpp -- OLED rendering for foxhunt modes + scripted idle animation
#include "display.h"
#include "pins.h"
#include "anim_frames.h"   // PROGMEM bitmap frame data

#define SCREEN_W 128
#define SCREEN_H 64

Display::Display()
    : _oled(SCREEN_W, SCREEN_H, &SPI, PIN_OLED_DC, PIN_OLED_RST, PIN_OLED_CS)
{}

bool Display::begin()
{
    SPI.begin(PIN_OLED_SCK, /*MISO*/ -1, PIN_OLED_MOSI, PIN_OLED_CS);
    if (!_oled.begin(SSD1306_SWITCHCAPVCC)) {
        Serial.println("[disp] SSD1306 init failed");
        return false;
    }
    _oled.clearDisplay();
    _oled.setTextColor(SSD1306_WHITE);
    _oled.setTextSize(1);
    _oled.display();
    return true;
}

void Display::clear() { _oled.clearDisplay(); }
void Display::show()  { _oled.display(); }

void Display::renderSplash(const char* version)
{
    clear();
    _oled.setTextSize(2);
    _oled.setCursor(8, 8);
    _oled.print("FOXHUNT");
    _oled.setTextSize(1);
    _oled.setCursor(8, 32);
    _oled.print("B-2 Badge");
    _oled.setCursor(8, 48);
    _oled.printf("fw %s", version);
    show();
}

void Display::renderIdleAnimation(uint32_t frame_idx)
{
    clear();
    // Pull frame from PROGMEM table; wrap on overflow.
    const uint8_t* fb = anim_frame(frame_idx % ANIM_FRAME_COUNT);
    _oled.drawBitmap(0, 0, fb, SCREEN_W, SCREEN_H, SSD1306_WHITE);
    show();
}

void Display::renderFox(float freq_mhz, bool tx_active, uint32_t next_beacon_in_ms)
{
    clear();
    _oled.setTextSize(2);
    _oled.setCursor(0, 0);
    _oled.print("FOX");
    if (tx_active) {
        _oled.setCursor(70, 0);
        _oled.print("TX");
    }
    _oled.setTextSize(1);
    _oled.setCursor(0, 22);
    _oled.printf("%.4f MHz", freq_mhz);
    _oled.setCursor(0, 36);
    _oled.printf("Next: %lus", next_beacon_in_ms / 1000);
    // TX activity blinker
    if (tx_active) _oled.fillCircle(120, 4, 4, SSD1306_WHITE);
    show();
}

void Display::renderHunter(int rssi, int rssi_max, uint32_t since_max_ms)
{
    clear();
    _oled.setTextSize(2);
    _oled.setCursor(0, 0);
    _oled.print("HUNT");
    _oled.setTextSize(1);
    _oled.setCursor(0, 22);
    _oled.printf("RSSI:%3d  MAX:%3d", rssi, rssi_max);
    _oled.setCursor(0, 34);
    _oled.printf("Hold@max: %lus", since_max_ms / 1000);
    _drawSignalBar(rssi);
    show();
}

void Display::renderMenu(const char* const* items, uint8_t n, uint8_t selected)
{
    clear();
    _oled.setTextSize(1);
    _oled.setCursor(0, 0);
    _oled.print("== MENU ==");
    for (uint8_t i = 0; i < n; ++i) {
        _oled.setCursor(0, 16 + i * 10);
        _oled.print(i == selected ? "> " : "  ");
        _oled.print(items[i]);
    }
    show();
}

void Display::_drawSignalBar(int rssi)
{
    // RSSI 0..255 mapped to 0..120 px wide bar at y=50, height 12
    int w = (rssi * 120) / 255;
    if (w < 0) w = 0; if (w > 120) w = 120;
    _oled.drawRect(2, 50, 124, 12, SSD1306_WHITE);
    _oled.fillRect(4, 52, w, 8, SSD1306_WHITE);
}
