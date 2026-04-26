// sa868.cpp -- SA868-V driver implementation
// Reference: SA868 AT command set (Nicerf datasheet rev 2.x):
//   AT+DMOCONNECT           -> handshake
//   AT+DMOSETGROUP=W,TX,RX,Tcss,SQ,Rcss
//   AT+DMOSETVOLUME=V       -> 0..8
//   AT+DMOSETMIC=N,SC,SCO   -> mic gain + scrambler
//   AT+RSSI?                -> RSSI in 0..255
//   S=0                     -> handshake response means OK
#include "sa868.h"
#include "pins.h"
#include <math.h>

bool SA868::begin(uint8_t pin_rx, uint8_t pin_tx, uint8_t pin_ptt,
                  uint8_t pin_pd, uint8_t pin_mic_pwm, uint8_t pin_rx_audio)
{
    _pin_ptt = pin_ptt;
    _pin_pd  = pin_pd;
    _pin_mic = pin_mic_pwm;
    _pin_rxa = pin_rx_audio;

    pinMode(_pin_ptt, OUTPUT);
    pinMode(_pin_pd,  OUTPUT);
    digitalWrite(_pin_ptt, HIGH); // RX (idle high)
    digitalWrite(_pin_pd,  HIGH); // powered

    // PWM channel for tone generation
    ledcSetup(MIC_PWM_CHANNEL, MIC_PWM_FREQ_HZ, MIC_PWM_RES_BITS);
    ledcAttachPin(_pin_mic, MIC_PWM_CHANNEL);
    ledcWrite(MIC_PWM_CHANNEL, 1 << (MIC_PWM_RES_BITS - 1)); // mid-rail (silence)

    // ADC for RX audio
    analogReadResolution(12);

    // UART up
    _uart.begin(9600, SERIAL_8N1, pin_rx, pin_tx);
    delay(500); // module boot

    // Handshake: send a few times; module sometimes misses the first
    char buf[64];
    for (int i = 0; i < 3; ++i) {
        if (sendAT("DMOCONNECT", buf, sizeof(buf), 500) > 0) {
            if (strstr(buf, "0") || strstr(buf, "OK")) return true;
        }
        delay(200);
    }
    return false;
}

bool SA868::setChannel(float tx_mhz, float rx_mhz,
                       uint8_t bandwidth, uint8_t squelch,
                       uint16_t ctcss_tx, uint16_t ctcss_rx)
{
    if (tx_mhz < 134.0f || tx_mhz > 174.0f) return false;
    if (rx_mhz < 134.0f || rx_mhz > 174.0f) return false;
    if (squelch > 8) squelch = 8;

    char cmd[80];
    // Format: DMOSETGROUP=W,TXF,RXF,Tcss,SQ,Rcss
    snprintf(cmd, sizeof(cmd),
             "DMOSETGROUP=%u,%.4f,%.4f,%04u,%u,%04u",
             bandwidth, tx_mhz, rx_mhz, ctcss_tx, squelch, ctcss_rx);

    char resp[64];
    int n = sendAT(cmd, resp, sizeof(resp), 1500);
    return n > 0 && strstr(resp, "0");
}

int SA868::readRSSI()
{
    char resp[32];
    int n = sendAT("RSSI?", resp, sizeof(resp), 500);
    if (n <= 0) return -1;
    // Response format: "RSSI=NNN\r\n"
    char* eq = strchr(resp, '=');
    if (!eq) return -1;
    return atoi(eq + 1);
}

void SA868::setTX(bool tx)
{
    if (tx) {
        toneStop();                 // ensure mic is silent before keying
        digitalWrite(_pin_ptt, LOW);
        _tx_active = true;
        delay(20);                  // allow PA to settle
    } else {
        digitalWrite(_pin_ptt, HIGH);
        _tx_active = false;
    }
}

void SA868::sleep()  { digitalWrite(_pin_pd, LOW);  }
void SA868::wake()   { digitalWrite(_pin_pd, HIGH); delay(500); }

void SA868::toneStart(uint32_t freq_hz)
{
    // Re-configure PWM at audio carrier frequency would be wrong for tone
    // synthesis. Instead, we KEEP the PWM at ~80kHz and update duty cycle
    // at the audio rate via a timer ISR. For a simple square-wave tone in
    // the audio band, we just temporarily reconfigure PWM frequency to
    // freq_hz and 50% duty -- the RC LPF will round it.
    ledcWriteTone(MIC_PWM_CHANNEL, freq_hz);
}

void SA868::toneStop()
{
    ledcWriteTone(MIC_PWM_CHANNEL, 0);
    ledcWrite(MIC_PWM_CHANNEL, 1 << (MIC_PWM_RES_BITS - 1)); // back to mid-rail
}

int SA868::sendAT(const char* cmd, char* buf, size_t buf_len, uint32_t timeout_ms)
{
    _drainRX();
    _uart.print("AT+");
    _uart.print(cmd);
    _uart.print("\r\n");
    _uart.flush();

    size_t got = 0;
    uint32_t start = millis();
    while ((millis() - start) < timeout_ms && got < (buf_len - 1)) {
        while (_uart.available() && got < (buf_len - 1)) {
            buf[got++] = (char)_uart.read();
        }
        // Cheap end-of-response heuristic: trailing \n
        if (got >= 2 && buf[got - 1] == '\n') break;
        delay(2);
    }
    buf[got] = '\0';
    return (int)got;
}

void SA868::_drainRX()
{
    while (_uart.available()) _uart.read();
}
