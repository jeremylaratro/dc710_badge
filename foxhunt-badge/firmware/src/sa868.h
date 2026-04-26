// sa868.h -- SA868-V VHF transceiver driver
// AT-command interface over UART. Handles frequency, CTCSS, RSSI, PTT, sleep.
#pragma once

#include <Arduino.h>
#include <HardwareSerial.h>

class SA868 {
public:
    // Construct with the HardwareSerial instance you'll dedicate to the radio
    // (NOT the USB CDC serial). On C3, use Serial1.
    explicit SA868(HardwareSerial& uart) : _uart(uart) {}

    // Bring up UART + control lines. Returns true if module ACKs handshake.
    bool begin(uint8_t pin_rx, uint8_t pin_tx, uint8_t pin_ptt,
               uint8_t pin_pd, uint8_t pin_mic_pwm, uint8_t pin_rx_audio);

    // Set TX/RX frequencies (MHz, e.g. 146.520). Both must be in 134-174 range.
    // bandwidth: 0 = 12.5kHz, 1 = 25kHz.  squelch: 0..8 (0 = open).
    // ctcss_tx / ctcss_rx: 0000 = off, 0001..0038 standard CTCSS, 0039+ = DCS
    bool setChannel(float tx_mhz, float rx_mhz,
                    uint8_t bandwidth = 1, uint8_t squelch = 4,
                    uint16_t ctcss_tx = 0, uint16_t ctcss_rx = 0);

    // Read RSSI (0..255). Returns -1 on parse failure.
    int  readRSSI();

    // PTT control: pulls PTT line low (TX) or high (RX).
    void setTX(bool tx);
    bool isTX() const { return _tx_active; }

    // Power down the module (PD pin low). draws ~uA.
    void sleep();
    void wake();

    // Generate a sine-wave tone via PWM into the mic input. Used for CTCSS,
    // beacon tones, CW keying. freq_hz typically 600-2500 for audible.
    void toneStart(uint32_t freq_hz);
    void toneStop();

    // Send raw AT command (no AT+ prefix; just e.g. "DMOSETGROUP=...").
    // Reads response into buf (caller-supplied), returns response length.
    int  sendAT(const char* cmd, char* buf, size_t buf_len, uint32_t timeout_ms = 1000);

private:
    HardwareSerial& _uart;
    uint8_t _pin_ptt = 255;
    uint8_t _pin_pd  = 255;
    uint8_t _pin_mic = 255;
    uint8_t _pin_rxa = 255;
    bool    _tx_active = false;

    void _drainRX();
};
