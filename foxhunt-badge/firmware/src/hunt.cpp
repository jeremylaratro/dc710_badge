// hunt.cpp -- foxhunt mode state machine implementation
#include "hunt.h"
#include "sa868.h"
#include "display.h"
#include "leds.h"

// CW (Morse) timing -- standard PARIS at 20 WPM => dit = 60ms
static constexpr uint32_t CW_DIT_MS = 60;

// Morse table for A-Z, 0-9. Each entry: '.' or '-' followed by '\0'.
static const char* MORSE[] = {
    /* A */ ".-",   /* B */ "-...", /* C */ "-.-.", /* D */ "-..",
    /* E */ ".",    /* F */ "..-.", /* G */ "--.",  /* H */ "....",
    /* I */ "..",   /* J */ ".---", /* K */ "-.-",  /* L */ ".-..",
    /* M */ "--",   /* N */ "-.",   /* O */ "---",  /* P */ ".--.",
    /* Q */ "--.-", /* R */ ".-.",  /* S */ "...",  /* T */ "-",
    /* U */ "..-",  /* V */ "...-", /* W */ ".--",  /* X */ "-..-",
    /* Y */ "-.--", /* Z */ "--.."
};
static const char* MORSE_NUM[] = {
    "-----", ".----", "..---", "...--", "....-",
    ".....", "-....", "--...", "---..", "----."
};

static const char* morseFor(char c) {
    c = toupper(c);
    if (c >= 'A' && c <= 'Z') return MORSE[c - 'A'];
    if (c >= '0' && c <= '9') return MORSE_NUM[c - '0'];
    return nullptr;
}

void HuntController::begin(const HuntConfig& cfg)
{
    _cfg = cfg;
    bool ok = _radio.setChannel(_cfg.fox_tx_mhz, _cfg.fox_rx_mhz,
                                /*bw*/ 1, /*sq*/ 4,
                                _cfg.ctcss_subtone, _cfg.ctcss_subtone);
    Serial.printf("[hunt] radio.setChannel(%.4f, %.4f) => %s\n",
                  _cfg.fox_tx_mhz, _cfg.fox_rx_mhz, ok ? "OK" : "FAIL");
    _next_beacon_at = millis() + 2000;  // first beacon 2s after boot
    _next_rssi_at   = millis();
}

void HuntController::setMode(HuntMode m)
{
    if (m == _mode) return;
    Serial.printf("[hunt] mode %d -> %d\n", (int)_mode, (int)m);
    // Always release PTT and stop tone when changing modes
    _radio.toneStop();
    _radio.setTX(false);
    _beaconing = false;

    _mode = m;
    if (m == HuntMode::HUNTER) {
        _max_rssi = 0;
        _max_rssi_at = millis();
    }
}

void HuntController::tick()
{
    switch (_mode) {
        case HuntMode::IDLE:   _tickIdle();   break;
        case HuntMode::FOX:    _tickFox();    break;
        case HuntMode::HUNTER: _tickHunter(); break;
    }
}

void HuntController::_tickIdle()
{
    // Idle mode: animation is driven elsewhere. Nothing to do here for radio.
}

void HuntController::_tickFox()
{
    uint32_t now = millis();
    if (!_beaconing && now >= _next_beacon_at) {
        // Start beacon: key TX, send CW ID, then steady tone
        _beaconing = true;
        _beacon_started = now;
        _radio.setTX(true);
        _sendCWId();
        // CW ID is blocking; after it returns, transmit steady tone for the
        // remainder of beacon_dur_ms
        _radio.toneStart(_cfg.tone_hz);
    } else if (_beaconing && (now - _beacon_started) >= _cfg.beacon_dur_ms) {
        // End beacon
        _radio.toneStop();
        _radio.setTX(false);
        _beaconing = false;
        _next_beacon_at = now + _cfg.beacon_period_ms;
    }
}

void HuntController::_tickHunter()
{
    uint32_t now = millis();
    if (now < _next_rssi_at) return;
    _next_rssi_at = now + 100;  // 10 Hz sample rate

    int r = _radio.readRSSI();
    if (r < 0) return;
    _last_rssi = r;
    if (r > _max_rssi) {
        _max_rssi = r;
        _max_rssi_at = now;
    }
    // Decay max if we haven't seen stronger in a while (allows re-seek)
    if ((now - _max_rssi_at) > 5000) {
        _max_rssi = (_max_rssi * 9) / 10;
    }
}

void HuntController::_sendCWId()
{
    // Each character: send dits/dahs by toggling tone on/off.
    // Inter-element gap = 1 dit, inter-letter gap = 3 dits, word gap = 7 dits.
    for (const char* p = _cfg.fox_id; *p; ++p) {
        const char* m = morseFor(*p);
        if (!m) {
            delay(CW_DIT_MS * 7);  // unknown char treated as word break
            continue;
        }
        for (const char* s = m; *s; ++s) {
            _radio.toneStart(_cfg.tone_hz);
            delay((*s == '-') ? (CW_DIT_MS * 3) : CW_DIT_MS);
            _radio.toneStop();
            delay(CW_DIT_MS);  // intra-letter gap
        }
        delay(CW_DIT_MS * 2);  // inter-letter gap (already 1 from element)
    }
}
