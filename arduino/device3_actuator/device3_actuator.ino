// Device 3 — Actuator Node (Sunny)
// Receives alert level via Serial, drives buzzer + RGB LED.
// Placeholder — wire up to match actual pin assignments.
// device3_actuator.ino — Phase 2: Actuator Intelligence Layer

const int RED    = 9;
const int GREEN  = 10;
const int BLUE   = 11;   // unused in this version
const int BUZZER = 6;
const int BUTTON = 2;

// 0 = normal, 1 = warning, 2 = critical
int alertLevel = 0;
bool lastButtonState = HIGH;
unsigned long lastDebounce = 0;

// Timing state for non-blocking patterns
unsigned long patternTimer = 0;
int patternStep = 0;

void setup() {
  Serial.begin(9600);
  pinMode(RED,    OUTPUT);
  pinMode(GREEN,  OUTPUT);
  pinMode(BLUE,   OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  applyNormal();
}

void loop() {
  handleButton();
  handleSerial();
  runPattern();
}

// ─── Button: cycle through states for demo ───────────────────────────────────
void handleButton() {
  bool current = digitalRead(BUTTON);
  if (current == LOW && lastButtonState == HIGH && millis() - lastDebounce > 200) {
    lastDebounce = millis();
    alertLevel = (alertLevel + 1) % 3;
    patternTimer = 0;
    patternStep = 0;
  }
  lastButtonState = current;
}

// ─── Serial: receive "normal" / "warning" / "critical" from bridge ───────────
void handleSerial() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    int prev = alertLevel;
    if      (cmd == "normal")   alertLevel = 0;
    else if (cmd == "warning")  alertLevel = 1;
    else if (cmd == "critical") alertLevel = 2;
    if (alertLevel != prev) {
      patternTimer = 0;
      patternStep  = 0;
    }
  }
}

// ─── Pattern runner (non-blocking) ───────────────────────────────────────────
void runPattern() {
  unsigned long now = millis();

  if (alertLevel == 0) {
    // NORMAL — solid green, silent
    applyNormal();

  } else if (alertLevel == 1) {
    // WARNING — slow blink yellow + two short beeps every 3 s
    // Steps: 0=LED on(1000ms) 1=LED off(800ms) 2=beep1(100ms) 3=gap(100ms) 4=beep2(100ms) 5=wait(900ms)
    unsigned long durations[] = {1000, 800, 100, 100, 100, 900};
    if (now - patternTimer >= durations[patternStep]) {
      patternTimer = now;
      patternStep  = (patternStep + 1) % 6;
    }
    allOff();
    if (patternStep == 0) { digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH); } // yellow
    if (patternStep == 2 || patternStep == 4) { digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH); digitalWrite(BUZZER, HIGH); }

  } else if (alertLevel == 2) {
    // CRITICAL — fast red strobe + continuous buzzer
    unsigned long durations[] = {200, 200};
    if (now - patternTimer >= durations[patternStep % 2]) {
      patternTimer = now;
      patternStep++;
    }
    allOff();
    if (patternStep % 2 == 0) { digitalWrite(RED, HIGH); digitalWrite(BUZZER, HIGH); }
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
void allOff() {
  digitalWrite(RED, LOW); digitalWrite(GREEN, LOW);
  digitalWrite(BLUE, LOW); digitalWrite(BUZZER, LOW);
}

void applyNormal() {
  digitalWrite(RED, LOW); digitalWrite(GREEN, HIGH);
  digitalWrite(BLUE, LOW); digitalWrite(BUZZER, LOW);
}