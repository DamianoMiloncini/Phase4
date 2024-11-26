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

// RFID setup
#define SS_PIN 5 // SDA Pin on RC522
#define RST_PIN 4 // RST Pin on RC522
MFRC522 rfid(SS_PIN, RST_PIN); // Create MFRC522 instance

// Light sensor setup
const int lightSensorPin = 34; // Analog pin for light sensor
const int ledPin = 2;          // GPIO pin on ESP32 for the light sensor's LED
int lightIntensity = 0;

// Function to connect to WiFi
void connectWiFi() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

// Function to connect to MQTT
void connectMQTT() {
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
}

void setup() {
  // Start serial communication
  Serial.begin(115200);

  // Initialize WiFi and MQTT connections
  connectWiFi();
  connectMQTT();

  // Initialize RFID
  SPI.begin();
  rfid.PCD_Init();
  Serial.println("RFID reader initialized. Place your card near the reader...");

  // Initialize light sensor LED
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // Ensure MQTT connection is active
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();

  // --- RFID Logic ---
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      uid += String(rfid.uid.uidByte[i], HEX);
    }
    Serial.print("RFID UID: ");
    Serial.println(uid);

    // Publish RFID data
    if (client.publish("rfid/scan", uid.c_str())) {
      Serial.println("RFID UID published to MQTT");
    } else {
      Serial.println("Failed to publish RFID UID");
    }

    // Halt RFID processing
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // --- Light Sensor Logic ---
  lightIntensity = analogRead(lightSensorPin);
  Serial.print("Light Intensity: ");
  Serial.println(lightIntensity);

  // Control LED based on light intensity (optional logic)
  if (lightIntensity < 500) {
    digitalWrite(ledPin, HIGH); // Turn on LED if intensity is low
  } else {
    digitalWrite(ledPin, LOW);  // Turn off LED if intensity is high
  }

  // Publish light intensity data
  String payload = String(lightIntensity);
  if (client.publish("sensor/light", payload.c_str())) {
    Serial.println("Light intensity published to MQTT");
  } else {
    Serial.println("Failed to publish light intensity");
  }

  // Add a small delay to prevent overloading the loop
  delay(2000);
}
