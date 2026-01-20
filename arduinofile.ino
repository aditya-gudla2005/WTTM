#include <ESP8266WiFi.h>

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
}

void loop() {
  int n = WiFi.scanNetworks();
  for (int i = 0; i < n; i++) {
    Serial.print(WiFi.SSID(i));
    Serial.print(",");
    Serial.print(WiFi.RSSI(i));
    Serial.print(",");
    Serial.println(WiFi.channel(i));
    delay(10);
  }
  Serial.println("END");
  delay(3000);
}
