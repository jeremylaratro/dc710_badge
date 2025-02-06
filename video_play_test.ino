#include <TFT_eSPI.h>      // Graphics library for the TFT display
#include <JPEGDecoder.h>   // JPEGDecoder library by Bodmer
#include <SD.h>            // SD card library
#include <SPI.h>

// -----------------------------------------------------------------------------
// SD Card Pin Definitions (using default VSPI)
// -----------------------------------------------------------------------------
#define SD_MISO 19    // SD card MISO
#define SD_CLK  18    // SD card Clock (SCK)
#define SD_MOSI 23    // SD card MOSI
#define SD_CS   5     // SD card Chip Select

// -----------------------------------------------------------------------------
// TFT Display:  
// TFT_eSPI’s User_Setup.h must define:
//   #define TFT_MOSI  21
//   #define TFT_SCLK  22
//   #define TFT_CS    15
//   #define TFT_DC    2
//   #define TFT_RST   12
// -----------------------------------------------------------------------------

// using settings from User_Setup.h
TFT_eSPI tft = TFT_eSPI();

void drawJpegImage(int16_t x, int16_t y) {
  Serial.println("Drawing image");
  for (uint16_t row = 0; row < JpegDec.height; row++) {
    tft.startWrite();
    tft.setAddrWindow(x, y + row, JpegDec.width, 1);
    tft.pushColors(JpegDec.pImage + (row * JpegDec.width), JpegDec.width, false);
    tft.endWrite();
  }
}


void setup() {
  Serial.begin(115200);
  while(!Serial) { delay(10); } 
  Serial.println("Starting Single JPEG Image Display");

  // Initialize the SD card
  Serial.println("Initializing SD card...");
  SPI.begin(18, 19, 23, 5);
  if (!SD.begin(5)) {
    Serial.println("SD Card Initialization Failed!");
    while (true);
  }
  Serial.println("SD Card Initialized.");

  Serial.println("Listing SD card files:");
  File root = SD.open("/");
  if (root) {
    File entry = root.openNextFile();
    while (entry) {
      Serial.print("File: ");
      Serial.println(entry.name());
      entry.close();
      entry = root.openNextFile();
    }
    root.close();
  } else {
    Serial.println("Failed to open root directory.");
  }

  // Initialize the TFT display
  Serial.println("Initializing TFT...");
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);
  Serial.println("TFT Initialized.");
  
  // Attempt to decode the JPEG file.
  Serial.println("Decoding /test.jpg...");
  if (JpegDec.decodeSdFile("/test.jpg")) {
    Serial.print("Decoded Image Dimensions: ");
    Serial.print(JpegDec.width);
    Serial.print(" x ");
    Serial.println(JpegDec.height);
    
    // 128x128
    if (JpegDec.width > 0 && JpegDec.height > 0) {
      // Draw 
      drawJpegImage(0, 0);
      Serial.println("Image drawn.");
    } else {
      Serial.println("Decoded image dimensions are zero or invalid.");
    }
  } else {
    Serial.println("Failed to decode /test.jpg");
  }
}

void loop() {

}
