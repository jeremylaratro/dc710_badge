// =============================================================================
// DC710 DEFCON33 Badge - Song Playback via Piezo Buzzer
// =============================================================================
//
// ASSESSMENT:
//
// The badge is ESP32-based with an EBYTE RF module and TFT display. There is
// no existing audio code. The ESP32 has built-in LEDC (LED Control) PWM
// hardware that can generate precise frequencies on any GPIO pin — perfect
// for driving a piezo buzzer or small speaker.
//
// APPROACH: Use the ESP32 LEDC peripheral to generate square-wave tones at
// musical note frequencies. Songs are defined as arrays of {note, duration}
// pairs. A rest (silence) is represented by frequency 0.
//
// HARDWARE: Connect a piezo buzzer between BUZZER_PIN and GND.
//           Pick any free GPIO — we use GPIO 25 here (not used by RF, SD,
//           or TFT based on the existing pin assignments).
//
// =============================================================================

// ---------------------------------------------------------------------------
// Pin & LEDC Configuration
// ---------------------------------------------------------------------------
#define BUZZER_PIN    25       // GPIO for piezo buzzer
#define LEDC_CHANNEL  0        // LEDC channel (0-15)
#define LEDC_RESOLUTION 8      // 8-bit duty resolution (0-255)

// ---------------------------------------------------------------------------
// Note Frequencies (Hz) — standard equal-temperament tuning (A4 = 440 Hz)
// ---------------------------------------------------------------------------
// Rests
#define REST  0

// Octave 3
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247

// Octave 4
#define NOTE_C4  262
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494

// Octave 5
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988

// Octave 6
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976

// Octave 7
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951

// ---------------------------------------------------------------------------
// Song Data Structure
// ---------------------------------------------------------------------------
struct Note {
  uint16_t frequency;  // Hz (0 = rest/silence)
  uint16_t duration;   // milliseconds
};

// ---------------------------------------------------------------------------
// Example Songs
// ---------------------------------------------------------------------------

// --- "Twinkle Twinkle Little Star" (C major) ---
const Note twinkleTwinkle[] = {
  {NOTE_C4, 400}, {NOTE_C4, 400}, {NOTE_G4, 400}, {NOTE_G4, 400},
  {NOTE_A4, 400}, {NOTE_A4, 400}, {NOTE_G4, 800},
  {NOTE_F4, 400}, {NOTE_F4, 400}, {NOTE_E4, 400}, {NOTE_E4, 400},
  {NOTE_D4, 400}, {NOTE_D4, 400}, {NOTE_C4, 800},
  {NOTE_G4, 400}, {NOTE_G4, 400}, {NOTE_F4, 400}, {NOTE_F4, 400},
  {NOTE_E4, 400}, {NOTE_E4, 400}, {NOTE_D4, 800},
  {NOTE_G4, 400}, {NOTE_G4, 400}, {NOTE_F4, 400}, {NOTE_F4, 400},
  {NOTE_E4, 400}, {NOTE_E4, 400}, {NOTE_D4, 800},
  {NOTE_C4, 400}, {NOTE_C4, 400}, {NOTE_G4, 400}, {NOTE_G4, 400},
  {NOTE_A4, 400}, {NOTE_A4, 400}, {NOTE_G4, 800},
  {NOTE_F4, 400}, {NOTE_F4, 400}, {NOTE_E4, 400}, {NOTE_E4, 400},
  {NOTE_D4, 400}, {NOTE_D4, 400}, {NOTE_C4, 800},
};
const int twinkleTwinkleLen = sizeof(twinkleTwinkle) / sizeof(Note);

// --- "Imperial March" (Star Wars) ---
const Note imperialMarch[] = {
  {NOTE_A4, 500}, {NOTE_A4, 500}, {NOTE_A4, 500},
  {NOTE_F4, 350}, {NOTE_C5, 150},
  {NOTE_A4, 500}, {NOTE_F4, 350}, {NOTE_C5, 150}, {NOTE_A4, 1000},
  {NOTE_E5, 500}, {NOTE_E5, 500}, {NOTE_E5, 500},
  {NOTE_F5, 350}, {NOTE_C5, 150},
  {NOTE_GS4, 500}, {NOTE_F4, 350}, {NOTE_C5, 150}, {NOTE_A4, 1000},
};
const int imperialMarchLen = sizeof(imperialMarch) / sizeof(Note);

// --- Scale Demo (C major ascending) ---
const Note cMajorScale[] = {
  {NOTE_C4, 300}, {NOTE_D4, 300}, {NOTE_E4, 300}, {NOTE_F4, 300},
  {NOTE_G4, 300}, {NOTE_A4, 300}, {NOTE_B4, 300}, {NOTE_C5, 600},
};
const int cMajorScaleLen = sizeof(cMajorScale) / sizeof(Note);

// --- "Happy Birthday" ---
const Note happyBirthday[] = {
  {NOTE_C4, 300}, {NOTE_C4, 100}, {NOTE_D4, 400}, {NOTE_C4, 400},
  {NOTE_F4, 400}, {NOTE_E4, 800},
  {NOTE_C4, 300}, {NOTE_C4, 100}, {NOTE_D4, 400}, {NOTE_C4, 400},
  {NOTE_G4, 400}, {NOTE_F4, 800},
  {NOTE_C4, 300}, {NOTE_C4, 100}, {NOTE_C5, 400}, {NOTE_A4, 400},
  {NOTE_F4, 400}, {NOTE_E4, 400}, {NOTE_D4, 800},
  {NOTE_AS4, 300}, {NOTE_AS4, 100}, {NOTE_A4, 400}, {NOTE_F4, 400},
  {NOTE_G4, 400}, {NOTE_F4, 800},
};
const int happyBirthdayLen = sizeof(happyBirthday) / sizeof(Note);

// ---------------------------------------------------------------------------
// Playback Functions
// ---------------------------------------------------------------------------

// Play a single tone for the specified duration (ms). freq=0 means silence.
void playTone(uint16_t freq, uint16_t duration) {
  if (freq > 0) {
    ledcWriteTone(LEDC_CHANNEL, freq);
  } else {
    ledcWriteTone(LEDC_CHANNEL, 0);  // silence
  }
  delay(duration);
}

// Play a song: array of Notes with a brief gap between notes for articulation.
void playSong(const Note* song, int length, int gapMs = 30) {
  for (int i = 0; i < length; i++) {
    playTone(song[i].frequency, song[i].duration);
    // Brief silence between notes so repeated notes are distinguishable
    ledcWriteTone(LEDC_CHANNEL, 0);
    delay(gapMs);
  }
  // Ensure buzzer is silent after song ends
  ledcWriteTone(LEDC_CHANNEL, 0);
}

// ---------------------------------------------------------------------------
// Setup & Loop
// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("DC710 Badge - Song Playback");

  // Configure LEDC for tone generation
  ledcSetup(LEDC_CHANNEL, 2000, LEDC_RESOLUTION);  // initial freq doesn't matter
  ledcAttachPin(BUZZER_PIN, LEDC_CHANNEL);

  // Play a startup jingle
  Serial.println("Playing C Major Scale...");
  playSong(cMajorScale, cMajorScaleLen);
  delay(500);

  Serial.println("Playing Twinkle Twinkle Little Star...");
  playSong(twinkleTwinkle, twinkleTwinkleLen);
  delay(1000);

  Serial.println("Playing Imperial March...");
  playSong(imperialMarch, imperialMarchLen);
  delay(1000);

  Serial.println("Playing Happy Birthday...");
  playSong(happyBirthday, happyBirthdayLen);

  Serial.println("Done.");
}

void loop() {
  // Songs play once in setup. Add button-triggered playback here if desired.
  // Example: read a button, call playSong() to replay.
}
