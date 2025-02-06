#include <SoftwareSerial.h>
#include "EBYTE.h"

#define PIN_RX   17    // Arduino receives from EBYTE TX
#define PIN_TX   16    // Arduino transmits to EBYTE RX
#define PIN_M0   4    // Control pin M0
#define PIN_M1   14    // Control pin M1
#define PIN_AUX  27    // AUX pin for status (optional)

SoftwareSerial ebyteSerial(PIN_RX, PIN_TX);
EBYTE transceiver(&ebyteSerial, PIN_M0, PIN_M1, PIN_AUX);

void setup() {

  Serial.begin(9600);
  ebyteSerial.begin(9600);
  
  Serial.println("Initializing EBYTE module...");
  
  // Initialize
  if (!transceiver.init(3)) {
    Serial.println("EBYTE initialization FAILED!");
    while (1);  
  }
  
  //  SetTransmitPower() 
  transceiver.SetTransmitPower(2);
  
  // Save the new settings
  transceiver.SaveParameters(PERMANENT);
  
  Serial.println("initialized");
}

void loop() {
  // Transmit 0xAA (binary 10101010)
  transceiver.SendByte(0xAA);
  
  // Delay between transmission
  delay(50);
}
