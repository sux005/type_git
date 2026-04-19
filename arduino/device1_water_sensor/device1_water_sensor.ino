// Device 1 — Water Sensor Node for Uno Q
// Reads analog water level, classifies alert, outputs JSON over Monitor.

#include <Arduino_RouterBridge.h>

const int WATER_PIN  = A0;
const int LED_GREEN  = 9;
const int LED_YELLOW = 10;
const int LED_RED    = 11;

// Thresholds — tune after seeing actual sensor range
const int THRESHOLD_WARNING  = 400;
const int THRESHOLD_CRITICAL = 700;

void setup() {
  Monitor.begin(115200);  // Use Monitor for Uno Q App Lab
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED,    OUTPUT);

  // Boot message
  Monitor.println("{\"status\":\"booted\"}");
}

void loop() {
  int raw = analogRead(WATER_PIN);
  float normalized = raw / 1023.0;
  String alert;

  if (raw < THRESHOLD_WARNING) {
    alert = "normal";
    digitalWrite(LED_GREEN,  HIGH);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    LOW);
  } else if (raw < THRESHOLD_CRITICAL) {
    alert = "warning";
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_YELLOW, HIGH);
    digitalWrite(LED_RED,    LOW);
  } else {
    alert = "critical";
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    HIGH);
  }

  Monitor.print("{\"device_id\":\"water_node\",\"value\":");
  Monitor.print(normalized, 3);
  Monitor.print(",\"alert_level\":\"");
  Monitor.print(alert);
  Monitor.println("\"}");

  delay(1000);
}
