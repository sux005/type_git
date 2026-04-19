#include <Arduino_RouterBridge.h>

const int WATER_PIN          = A0;
const int THRESHOLD_WARNING  = 400;
const int THRESHOLD_CRITICAL = 700;

void setup() {
  Monitor.begin(115200);
  Bridge.begin();
  Monitor.println("Uno Q bridge ready");
}

void loop() {
  int raw = analogRead(WATER_PIN);
  float normalized = raw / 1023.0;

  const char* alert;
  if (raw < THRESHOLD_WARNING)       alert = "normal";
  else if (raw < THRESHOLD_CRITICAL) alert = "warning";
  else                               alert = "critical";

  char payload[128];
  snprintf(payload, sizeof(payload),
    "{\"device_id\":\"water_node\",\"value\":%.3f,\"alert_level\":\"%s\"}",
    normalized, alert);

  Monitor.println(payload);
  Bridge.call("post_event", payload);

  delay(2000);
}
