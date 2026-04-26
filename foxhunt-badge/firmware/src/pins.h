// pins.h -- Foxhunt Badge ESP32-C3 pin map
// Single source of truth. Change here, propagate everywhere.
#pragma once

#include <Arduino.h>

// ---- LED chain ----
constexpr uint8_t PIN_LED_DIN   = 0;
constexpr uint8_t NUM_LEDS      = 4;

// ---- OLED (SPI) ----
constexpr uint8_t PIN_OLED_DC   = 1;
constexpr uint8_t PIN_OLED_CS   = 5;
constexpr uint8_t PIN_OLED_SCK  = 6;
constexpr uint8_t PIN_OLED_MOSI = 7;
constexpr uint8_t PIN_OLED_RST  = 8;

// ---- Buttons (active low, internal pullups OK on non-strap pins) ----
constexpr uint8_t PIN_BTN_UP    = 3;
constexpr uint8_t PIN_BTN_SEL   = 9;   // doubles as BOOT
constexpr uint8_t PIN_BTN_DN    = 17;

// ---- SA868 radio ----
constexpr uint8_t PIN_SA868_PTT      = 10;  // active low
constexpr uint8_t PIN_SA868_UART_RX  = 11;  // ESP RX <- module TX
constexpr uint8_t PIN_SA868_UART_TX  = 12;  // ESP TX -> module RX
constexpr uint8_t PIN_SA868_PD       = 13;  // active low (low = sleep)
constexpr uint8_t PIN_SA868_MIC_PWM  = 15;  // PWM -> RC LPF -> MIC_IN
constexpr uint8_t PIN_SA868_RX_AUDIO = 16;  // ADC <- RX_OUT (AC-coupled)

// ---- Debug UART ----
constexpr uint8_t PIN_DBG_RX = 20;
constexpr uint8_t PIN_DBG_TX = 21;

// ---- Other ----
constexpr uint32_t MIC_PWM_FREQ_HZ   = 80000;   // out of audio band
constexpr uint8_t  MIC_PWM_RES_BITS  = 8;
constexpr uint8_t  MIC_PWM_CHANNEL   = 0;
