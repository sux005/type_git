#include <Arduino_RouterBridge.h>
#include <Modulino.h>
#include <DHT.h>

#define DHT_PIN  2
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);
ModulinoDistance distance;
ModulinoThermo   thermo;
ModulinoMovement movement;

const int WATER_PIN = A0;

void setup() {
  Monitor.begin(115200);
  Bridge.begin();
  Modulino.begin();
  dht.begin();

  distance.begin();
  thermo.begin();
  movement.begin();

  Monitor.println("Uno Q ready");
}

void loop() {
  // Water depth (analog)
  int rawWater = analogRead(WATER_PIN);
  float waterDepth = rawWater / 1023.0;

  // DHT11
  float humidity    = dht.readHumidity();
  float tempDHT     = dht.readTemperature();

  // Modulinos
  float distanceCm  = distance.available() ? distance.get() : -1;
  float tempThermo  = thermo.getTemperature();
  float humidThermo = thermo.getHumidity();

  movement.update();
  float ax = movement.getX();
  float ay = movement.getY();
  float az = movement.getZ();
  float vibration = sqrt(ax*ax + ay*ay + az*az);

  // Run KNN inference
  const char* alert = classify(waterDepth, humidity, distanceCm, vibration);

  char payload[256];
  snprintf(payload, sizeof(payload),
    "{\"device_id\":\"water_node\",\"alert_level\":\"%s\","
    "\"water_depth\":%.3f,\"humidity\":%.1f,\"temp\":%.1f,"
    "\"distance\":%.1f,\"vibration\":%.3f}",
    alert, waterDepth, humidity, tempDHT, distanceCm, vibration);

  Monitor.println(payload);
  Bridge.call("post_event", payload);

  delay(100);
}

const char* classify(float water, float humidity, float dist, float vibration) {
  // Training data: {water, humidity, dist, vibration, label}
  // 0=normal, 1=warning, 2=critical
  // Tune these after collecting real readings
  static const float train[][5] = {
    // {water_depth, humidity, distance, vibration, label}  0=normal 1=warning 2=critical
    // Normal — dry, calm, room conditions
    {0.00, 57, 20, 1.00, 0},
    {0.10, 57, 20, 1.00, 0},
    {0.20, 57, 20, 1.00, 0},
    {0.10, 65, 20, 1.05, 0},
    // Warning — moderate water OR rising humidity+vibration (storm approaching)
    {0.30, 57, 20, 1.00, 1},
    {0.40, 57, 20, 1.00, 1},
    {0.50, 57, 19, 1.00, 1},
    {0.05, 75, 20, 1.15, 1},
    {0.10, 80, 20, 1.20, 1},
    {0.20, 75, 20, 1.10, 1},
    // Critical — high water OR extreme humidity+vibration (active flood/storm)
    {0.60, 57, 19, 1.00, 2},
    {0.68, 57, 19, 1.00, 2},
    {0.71, 57, 18, 1.00, 2},
    {0.10, 90, 20, 1.30, 2},
    {0.20, 85, 20, 1.25, 2},
    {0.40, 82, 19, 1.20, 2},
  };
  const int N = sizeof(train) / sizeof(train[0]);
  const int K = 3;

  // KNN
  float bestDist[K];
  int   bestLabel[K];
  for (int i = 0; i < K; i++) { bestDist[i] = 1e9; bestLabel[i] = 0; }

  for (int i = 0; i < N; i++) {
    float d = 0;
    float diffs[4] = {
      water    - train[i][0],
      humidity - train[i][1],
      dist     - train[i][2],
      vibration- train[i][3]
    };
    // normalize each feature roughly
    float scales[4] = {1.0, 30.0, 100.0, 0.3};
    for (int f = 0; f < 4; f++) d += (diffs[f]/scales[f]) * (diffs[f]/scales[f]);

    for (int j = 0; j < K; j++) {
      if (d < bestDist[j]) {
        for (int m = K-1; m > j; m--) { bestDist[m]=bestDist[m-1]; bestLabel[m]=bestLabel[m-1]; }
        bestDist[j] = d; bestLabel[j] = (int)train[i][4];
        break;
      }
    }
  }

  int votes[3] = {0, 0, 0};
  for (int i = 0; i < K; i++) votes[bestLabel[i]]++;

  if (votes[2] >= votes[1] && votes[2] >= votes[0]) return "critical";
  if (votes[1] >= votes[0]) return "warning";
  return "normal";
}
