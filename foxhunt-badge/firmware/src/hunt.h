// hunt.h -- Foxhunt mode logic
// FOX mode: periodic beacon (CW ID + tone burst) on configured frequency
// HUNTER mode: continuous RSSI sampling with rolling-max bearing indicator
// IDLE mode:   badge demo (LED show + scripted OLED animation)
#pragma once

#include <Arduino.h>

class SA868;
class Display;
class LedRing;

enum class HuntMode : uint8_t {
    IDLE   = 0,
    FOX    = 1,
    HUNTER = 2,
};

struct HuntConfig {
    float    fox_tx_mhz       = 146.520f;   // 2m simplex calling freq
    float    fox_rx_mhz       = 146.520f;
    uint16_t ctcss_subtone    = 0;          // 0 = off, 0001..0038 standard
    uint32_t beacon_period_ms = 15000;      // fox transmits every 15s
    uint32_t beacon_dur_ms    = 1500;       // 1.5s tone burst per beacon
    uint16_t tone_hz          = 1200;       // beacon tone freq
    const char* fox_id        = "DCFOX";    // CW callsign (sent at start of beacon)
};

class HuntController {
public:
    HuntController(SA868& radio, Display& disp, LedRing& leds)
        : _radio(radio), _disp(disp), _leds(leds) {}

    void begin(const HuntConfig& cfg);
    void setMode(HuntMode m);
    HuntMode mode() const { return _mode; }

    // Call from main loop; non-blocking. Drives beaconing, RSSI sampling,
    // and UI updates.
    void tick();

    // For UI to display
    int       lastRSSI() const  { return _last_rssi; }
    int       maxRSSI()  const  { return _max_rssi; }
    uint32_t  msSinceMaxRSSI() const { return millis() - _max_rssi_at; }

private:
    SA868&    _radio;
    Display&  _disp;
    LedRing&  _leds;
    HuntConfig _cfg{};
    HuntMode  _mode = HuntMode::IDLE;

    // FOX state
    uint32_t  _next_beacon_at = 0;
    bool      _beaconing      = false;
    uint32_t  _beacon_started = 0;

    // HUNTER state
    int       _last_rssi    = 0;
    int       _max_rssi     = 0;
    uint32_t  _max_rssi_at  = 0;
    uint32_t  _next_rssi_at = 0;

    void _tickFox();
    void _tickHunter();
    void _tickIdle();
    void _sendCWId();
};
