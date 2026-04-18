// Device 3 — Actuator Node (Sunny)
// Receives alert level via Serial, drives buzzer + RGB LED.
// Placeholder — wire up to match actual pin assignments.

const int BUZZER    = 6;
const int LED_GREEN = 9;
const int LED_YELLOW = 10;
const int LED_RED   = 11;

String alertLevel = "normal";

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER,     OUTPUT);
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED,    OUTPUT);
}

void loop() {
  if (Serial.available()) {
    alertLevel = Serial.readStringUntil('\n');
    alertLevel.trim();
  }

  if (alertLevel == "normal") {
    digitalWrite(LED_GREEN,  HIGH);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    LOW);
    noTone(BUZZER);
  } else if (alertLevel == "warning") {
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_YELLOW, HIGH);
    digitalWrite(LED_RED,    LOW);
    tone(BUZZER, 1000, 200);
  } else if (alertLevel == "critical") {
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    HIGH);
    tone(BUZZER, 2000, 500);
  }

  delay(500);
}
