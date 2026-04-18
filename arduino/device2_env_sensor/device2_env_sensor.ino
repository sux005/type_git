// Device 2 — Environmental Sensor Node
// Reads a photoresistor (light/ambient intensity) as a proxy for
// wave intensity / environmental disturbance.
// Outputs alert level JSON over Serial for the bridge to forward.

const int SENSOR_PIN = A1;
const int LED_GREEN  = 9;
const int LED_YELLOW = 10;
const int LED_RED    = 11;

// Thresholds — tune after seeing actual sensor range on Serial Monitor
const int THRESHOLD_WARNING  = 400;
const int THRESHOLD_CRITICAL = 700;

void setup() {
  Serial.begin(9600);
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED,    OUTPUT);
}

void loop() {
  int raw = analogRead(SENSOR_PIN);
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

  Serial.print("{\"device_id\":\"env_node\",\"value\":");
  Serial.print(normalized, 3);
  Serial.print(",\"alert_level\":\"");
  Serial.print(alert);
  Serial.println("\"}");

  delay(1000);
}
