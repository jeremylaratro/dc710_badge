// ui_input.cpp -- button debouncing
#include "ui_input.h"
#include "pins.h"

void UIInput::begin()
{
    _up  = {PIN_BTN_UP,  true, true, 0, 0};
    _dn  = {PIN_BTN_DN,  true, true, 0, 0};
    _sel = {PIN_BTN_SEL, true, true, 0, 0};
    pinMode(_up.pin,  INPUT_PULLUP);
    pinMode(_dn.pin,  INPUT_PULLUP);
    pinMode(_sel.pin, INPUT_PULLUP);
}

bool UIInput::_readDebounced(Btn& b, uint32_t now)
{
    bool raw = digitalRead(b.pin);  // active low
    if (raw != b.last_raw) {
        b.last_raw = raw;
        b.last_change_ms = now;
    }
    if ((now - b.last_change_ms) >= DEBOUNCE_MS && raw != b.stable_state) {
        b.stable_state = raw;
        return true;  // edge detected
    }
    return false;
}

BtnEvent UIInput::poll()
{
    uint32_t now = millis();
    if (_readDebounced(_up, now) && !_up.stable_state) return BtnEvent::UP;
    if (_readDebounced(_dn, now) && !_dn.stable_state) return BtnEvent::DOWN;
    if (_readDebounced(_sel, now)) {
        if (!_sel.stable_state) {
            _sel.pressed_at = now;
            return BtnEvent::SEL;       // fire on press
        }
    }
    // long-press detection on SEL while held
    if (!_sel.stable_state && _sel.pressed_at != 0
        && (now - _sel.pressed_at) >= LONG_PRESS_MS) {
        _sel.pressed_at = 0;  // one-shot
        return BtnEvent::BACK_LONG;
    }
    return BtnEvent::NONE;
}
