#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <PubSubClient.h>

// WiFi and MQTT settings
const char* ssid = "Damiano";
const char* password = "DamianoM";
const char* mqtt_server = "172.20.10.3"; // RPI IP address

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Define pins for RFID
#define SS_PIN 5 // SDA Pin on RC522
#define RST_PIN 4 // RST Pin on RC522
MFRC522 rfid(SS_PIN, RST_PIN); // Create MFRC522 instance

void setup() {
  // Begin the WiFi connection
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  // Wait for the ESP32 to connect to WiFi
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Connect to MQTT broker
  client.setServer(mqtt_server, 1883);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect("ESP32Client")) {
      Serial.println("Connected to MQTT Broker");
    } else {
      Serial.print("Failed to connect to MQTT Broker. State=");
      Serial.println(client.state());
      delay(2000);
    }
  }

  // Initialize RFID reader
  SPI.begin();
  rfid.PCD_Init();
  Serial.println("Place your RFID card near the reader...");
}

void loop() {
  // Ensure the MQTT connection remains active
  if (!client.connected()) {
    while (!client.connected()) {
      Serial.println("Reconnecting to MQTT...");
      if (client.connect("ESP32Client")) {
        Serial.println("Reconnected to MQTT Broker");
      } else {
        Serial.print("Failed to reconnect. State=");
        Serial.println(client.state());
        delay(2000);
      }
    }
  }
  client.loop();

  // Look for new RFID cards
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Create the UID string
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    uid += String(rfid.uid.uidByte[i], HEX);
  }

  // Log the UID
  Serial.print("Card UID: ");
  Serial.println(uid);

  // Publish the UID to the MQTT topic
  if (client.publish("rfid/scan", uid.c_str())) {
    Serial.println("UID published to MQTT");
  } else {
    Serial.println("Failed to publish UID");
  }

  // Halt PICC and prepare for the next scan
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
