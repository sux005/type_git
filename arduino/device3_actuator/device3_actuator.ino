// Device 3 — Actuator Node (Sunny)
// Phase 2: Actuator Intelligence Layer
// Pins: RED=9, GREEN=10, BLUE=11, BUZZER=6, BUTTON=2

const int RED    = 9;
const int GREEN  = 10;
const int BLUE   = 11;
const int BUZZER = 6;
const int BUTTON = 2;

int alertLevel = 0;
bool lastButtonState = HIGH;
unsigned long lastDebounce = 0;
unsigned long patternTimer  = 0;
int patternStep = 0;

bool autoDemo = false;
unsigned long autoDemoTimer = 0;
unsigned long buttonHoldStart = 0;
bool holdTracking = false;

void setup() {
  Serial.begin(9600);
  pinMode(RED,    OUTPUT);
  pinMode(GREEN,  OUTPUT);
  pinMode(BLUE,   OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  startupSequence();
  startPattern();
}

void loop() {
  handleButton();
  handleAutoDemo();
  handleSerial();
  runPattern();
}

// ─── State change helper (resets pattern cleanly) ────────────────────────────
void setLevel(int level) {
  if (level == alertLevel) return;
  alertLevel = level;
  startPattern();
}

void startPattern() {
  patternStep  = 0;
  patternTimer = millis(); // must be current time, NOT 0
  allOff();
}

// ─── Startup: quick LED/buzzer self-test confirms wiring ─────────────────────
void startupSequence() {
  // Green flash
  digitalWrite(GREEN, HIGH); delay(300); digitalWrite(GREEN, LOW); delay(100);
  // Yellow flash
  digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH); delay(300);
  allOff(); delay(100);
  // Red + beep
  digitalWrite(RED, HIGH); digitalWrite(BUZZER, HIGH); delay(200);
  allOff(); delay(100);
  digitalWrite(BUZZER, HIGH); delay(200);
  allOff(); delay(300);
}

// ─── Button: short press = cycle state, long press (2s) = toggle auto-demo ───
void handleButton() {
  bool current = digitalRead(BUTTON);
  unsigned long now = millis();

  // Detect press start
  if (current == LOW && lastButtonState == HIGH) {
    buttonHoldStart = now;
    holdTracking    = true;
  }

  // Detect long-hold (2s) → toggle auto-demo
  if (holdTracking && current == LOW && now - buttonHoldStart >= 2000) {
    holdTracking = false;
    lastDebounce = now;
    autoDemo = !autoDemo;
    if (autoDemo) {
      autoDemoTimer = now; // start cycling immediately on next step
      setLevel(0);         // reset to normal when entering auto-demo
    }
  }

  // Detect short press release → cycle state (only if not a long press)
  if (current == HIGH && lastButtonState == LOW && holdTracking) {
    holdTracking = false;
    if (now - lastDebounce > 200) {
      lastDebounce = now;
      autoDemo = false;    // manual press cancels auto-demo
      setLevel((alertLevel + 1) % 3);
    }
  }

  lastButtonState = current;
}

// ─── Auto-demo: advance state every 4 seconds ────────────────────────────────
void handleAutoDemo() {
  if (!autoDemo) return;
  if (millis() - autoDemoTimer >= 4000) {
    autoDemoTimer = millis();
    setLevel((alertLevel + 1) % 3);
  }
}

// ─── Serial: receive "normal" / "warning" / "critical" from bridge ───────────
void handleSerial() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if      (cmd == "normal")   setLevel(0);
  else if (cmd == "warning")  setLevel(1);
  else if (cmd == "critical") setLevel(2);
}

// ─── Pattern runner (non-blocking) ───────────────────────────────────────────
//  NORMAL   — solid green, silent          → clearly "all good"
//  WARNING  — slow yellow blink + pip-pip  → "pay attention"
//  CRITICAL — fast red strobe + buzzer     → "emergency"

void runPattern() {
  unsigned long now = millis();

  switch (alertLevel) {

    case 0: // NORMAL — solid green
      digitalWrite(GREEN, HIGH);
      digitalWrite(RED,    LOW);
      digitalWrite(BLUE,   LOW);
      digitalWrite(BUZZER, LOW);
      break;

    case 1: { // WARNING — yellow blink + double-beep
      static const unsigned long W[] = {900, 100, 120, 100, 680};
      if (now - patternTimer >= W[patternStep]) {
        patternTimer = now;
        patternStep  = (patternStep + 1) % 5;
      }
      allOff();
      switch (patternStep) {
        case 0: // yellow LED steady
          digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH); break;
        case 1: // first beep (yellow + buzz)
          digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH);
          digitalWrite(BUZZER, HIGH); break;
        case 2: // silent gap between beeps
          break;
        case 3: // second beep (yellow + buzz)
          digitalWrite(RED, HIGH); digitalWrite(GREEN, HIGH);
          digitalWrite(BUZZER, HIGH); break;
        case 4: // dark pause before repeat
          break;
      }
      break;
    }

    case 2: { // CRITICAL — fast red strobe + pulsing buzzer
      static const unsigned long C[] = {200, 150};
      if (now - patternTimer >= C[patternStep % 2]) {
        patternTimer = now;
        patternStep++;
      }
      allOff();
      if (patternStep % 2 == 0) {
        digitalWrite(RED,    HIGH);
        digitalWrite(BUZZER, HIGH);
      }
      break;
    }
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
void allOff() {
  digitalWrite(RED,    LOW);
  digitalWrite(GREEN,  LOW);
  digitalWrite(BLUE,   LOW);
  digitalWrite(BUZZER, LOW);
}
