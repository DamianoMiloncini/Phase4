//The Arduino code is handling the reading the light intensity data from the sensor and publishing it to the MQTT broker
#include <WiFi.h>
#include <PubSubClient.h>

//Wifi and MQTT settings (just like the lab)
const char* ssid = "Damiano";
const char* password = "DamianoM";
const char* mqtt_server = "172.20.10.3"; //RPI ip address

//MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

//light sensor (verify the Analog pin bs with ESP32)
const int lightSensorPin = 34; //for example
int lightIntensity = 0;

//Setting up the ESP32 and the MQTT server
void setup() {
    //Begin the wifi connection
    Serial.begin(115200);
    WiFi.begin(ssid,password);

    //Wait for the ESP32 to connect to the wifi
    while (WiFi.status() != WL_CONNECTED){
        delay(1000);
         Serial.println(WiFi.status());
        Serial.println("Connecting to Wifi ...");
    }
     Serial.println("Connected to Wifi");


     //Connect to MQTT broker
     client.setServer(mqtt_server,1883);
     while(!client.connected()){
        Serial.println("Connecting to MQTT ...");
        if(client.connect("ESP32Client")) {
        Serial.println("Connected to MQTT Broker");
        }
        else {
             Serial.println("Failed to connect to MQTT Broker");
        }
     }
}

void loop() {
    lightIntensity = analogRead(lightSensorPin);
    Serial.print("Light Intensity: ");
    Serial.println(lightIntensity);

    //publish the light intensity to the MQTT topic
    String payload = String(lightIntensity);
    client.publish("sensor/light", payload.c_str());
    delay(2000);
}
