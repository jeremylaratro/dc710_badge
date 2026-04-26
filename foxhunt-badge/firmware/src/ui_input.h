// ui_input.h -- Button debouncing and event dispatch
#pragma once

#include <Arduino.h>

enum class BtnEvent : uint8_t { NONE, UP, DOWN, SEL, BACK_LONG };

class UIInput {
public:
    void begin();
    BtnEvent poll();   // call every loop(); returns events as they're detected

private:
    struct Btn {
        uint8_t  pin;
        bool     stable_state;       // true = released (idle high)
        bool     last_raw;
        uint32_t last_change_ms;
        uint32_t pressed_at;
    };
    Btn _up, _dn, _sel;
    static constexpr uint32_t DEBOUNCE_MS = 30;
    static constexpr uint32_t LONG_PRESS_MS = 800;

    bool _readDebounced(Btn& b, uint32_t now);
};
