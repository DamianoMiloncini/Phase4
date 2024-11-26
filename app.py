# This code will handle subscribing to the MQTT broker and handle the data 
# import the python library the teacher gave us
from flask import Flask, render_template, jsonify, session
import smtplib
import paho.mqtt.client as mqtt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import RPi.GPIO as GPIO
import threading
import sqlite3
import Freenove_DHT as DHT
import time

app = Flask(__name__)
app.secret_key = "IoT_2024"  # Simple key for local testing

# MQTT settings
MQTT_BROKER = "172.20.10.3"
MQTT_TOPIC = "rfid/scan"
mqtt_client = mqtt.Client()

#GPIO setupd
LEDpin = 16 #example
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LEDpin, GPIO.OUT)

#Email setup
sender_email = "stromika78@gmail.com"
app_password= "uekhmtqwuotoghbx"
receiver_email = "nsumanyim@gmail.com" 
SMTP_PORT = 587
topic = "sensor/light"

# GPIO and DHT setup
GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BOARD)
DHTPin = 33
Motor1 = 11
Motor2 = 13
Motor3 = 15

GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(Motor2, GPIO.OUT)
GPIO.setup(Motor3, GPIO.OUT)

# Initialize flag and lock for fan
alert_sent = False
alert_lock = threading.Lock()
current_temp = None
current_humidity = None
dht_lock = threading.Lock()  # Lock for thread safety

# Global variables for data
rfid_tag = None
current_light_intensity = 0

def send_email(sender_email, sender_password, receiver_email, subject, body):
    try:
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject #tbh this could be hardcoded
        message.attach(MIMEText(body, 'plain')) #tbh this could be hardcoded (the body i mean)

        with smtplib.SMTP('smtp.gmail.com', 587) as server: #!!dont change the smtp.gmail.com its required!!
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print("Email was sent successfully")
    except Exception as e:
        print("Failed to send the email",e)

# Method for receiving email and checking response
def receive_email(email_address, app_password, num_emails=5):
    imap_server = "imap.gmail.com"
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(email_address, app_password)
    imap.select('INBOX')
    _, message_numbers = imap.search(None, 'ALL')
    email_ids = message_numbers[0].split()[-num_emails:]
    for email_id in reversed(email_ids):
        _, msg_data = imap.fetch(email_id, '(RFC822 FLAGS)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_body = response_part[1]
                email_message = email.message_from_bytes(email_body)
                flags = response_part[0].decode().split(' ')
                if '\\Seen' not in flags and email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                content = part.get_payload(decode=True).decode('utf-8')
                                if "YES" in content.strip().upper():
                                    return True
                            except UnicodeDecodeError:
                                return False
    imap.close()
    imap.logout()
    return False

# Background function to handle temperature alerts
def monitor_temperature():
    global alert_sent
    dht = DHT.DHT(DHTPin)

    while True:
        readValue = dht.readDHT11()
        if readValue == dht.DHTLIB_OK:
            current_temp = dht.temperature
            with alert_lock:
                if current_temp > 20 and not alert_sent:
                    # Send email if the temperature is too high and no alert has been sent
                    send_email(
                        sender_email,
                        app_password,
                        receiver_email,
                        "Temperature Alert",
                        f"The current temperature is {current_temp}°C. Reply with 'YES' to turn on the fan."
                    )
                    alert_sent = True
                    print('Email sent for temperature alert.')

                    # Wait and check for the user’s response
                    time.sleep(40)
                    if receive_email(sender_email, app_password, num_emails=1):
                        print('Turning fan on.')
                        GPIO.output(Motor1, GPIO.HIGH)
                        GPIO.output(Motor2, GPIO.LOW)
                        GPIO.output(Motor3, GPIO.HIGH)
                        time.sleep(15)
                        GPIO.output(Motor1, GPIO.LOW)
                    else:
                        print('No response or fan off.')

                elif current_temp <= 20:
                    # Reset alert if temperature drops below threshold
                    alert_sent = False
        time.sleep(10)  # Interval to check temperature

# Start the background thread
threading.Thread(target=monitor_temperature, daemon=True).start()

#the defined functions from the paho library
def on_connect(client,userdata,flags,rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe(topic)
    else:
        print("Failed to connect to the MQTT broker")

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def on_message(client, userdata, msg):
    global rfid_tag, current_light_intensity

    #light_threshold = session.get("light_threshold")

    if msg.topic == "rfid/scan":
        # Handle RFID tag
        rfid_tag = msg.payload.decode("utf-8")
        print(f"Received RFID: {rfid_tag}")
        send_email(
                    sender_email,
                    app_password,
                    receiver_email,
                    "RFID scanned",
                    notification_message,
                )
        print("The LED has been turned on and the email was sent")
    
    elif msg.topic == "sensor/light":
        # Handle light intensity
        try:
            current_light_intensity = int(msg.payload.decode())
            print(f"Received light intensity: {current_light_intensity}")

            if current_light_intensity > 40000:
                GPIO.output(LEDpin, GPIO.HIGH)
                current_time = datetime.now().strftime("%H:%M")
                notification_message = f"The light is ON at {current_time}"
                send_email(
                    sender_email,
                    app_password,
                    receiver_email,
                    "Light Notification",
                    notification_message,
                )
                print("The LED has been turned on and the email was sent")
            else:
                GPIO.output(LEDpin, GPIO.LOW)
                print("LED is turned off")
        except ValueError:
            print("Invalid data received for light intensity")

# Initialize MQTT client
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)

# Subscribe to both topics
mqtt_client.subscribe("rfid/scan")
mqtt_client.subscribe("sensor/light")
mqtt_client.loop_start()

@app.route("/")
def authentication():
    return render_template("authentication.html")

@app.route("/check_rfid")
def check_rfid():
    global rfid_tag

    if rfid_tag is None:
        return jsonify(success=False), 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE rfid_id = ?", (rfid_tag,))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["temperature_threshold"] = user["temperature_threshold"]
        session["light_threshold"] = user["light_threshold"]
        rfid_tag = None  # Reset RFID tag to prevent multiple logins
        return jsonify(success=True), 200
    else:
        return jsonify(success=False), 403

# This method is used to get the constatly updating informatio and catch in javascript using the app route
@app.route('/check_light', methods=['GET'])
def get_status():
    led_status = "ON" if GPIO.input(LEDpin) == GPIO.HIGH else "OFF"
    return jsonify({"light_intensity": current_light_intensity, "led_status": led_status})

@app.route('/devices')
def devices():
    try:
        with open('devices.json', 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500

@app.route("/dashboard")
def iot_dashboard():
    if "user_id" not in session:
        return redirect(url_for("authentication"))

    # DHT
    dht = DHT.DHT(DHTPin)
    readValue = dht.readDHT11()
    current_temp = None
    current_humidity = None

    if readValue == dht.DHTLIB_OK:
        current_temp = dht.temperature
        current_humidity = dht.humidity
        print(current_temp)

    if current_temp is None or current_humidity is None:
        current_temp = "Error reading temperature"
        current_humidity = "Error reading humidity"


    led_status = "ON" if GPIO.input(LEDpin) == GPIO.HIGH else "OFF"
    username = session.get("username")
    user_id = session.get("user_id")
    light_threshold = session.get("light_threshold")
    temperature_threshold = session.get("temperature_threshold")
    return render_template("main.html", username=username, user_id=user_id, light_threshold=light_threshold, temp_threshold=temperature_threshold, light_intensity=current_light_intensity, led_status=led_status, temperature=current_temp, humidity=current_humidity)

@app.route('/sensor_data')
def sensor_data():
    dht = DHT.DHT(DHTPin)
    readValue = dht.readDHT11()
    current_temp = None
    current_humidity = None

    if readValue == dht.DHTLIB_OK:
        current_temp = dht.temperature
        current_humidity = dht.humidity

    return jsonify({'temperature': current_temp, 'humidity': current_humidity})

@app.route('/fan_status')
def fan_status():
    fan_is_on = GPIO.input(Motor1) == GPIO.HIGH
    return jsonify({'status': 'ON' if fan_is_on else 'OFF'})

if __name__ == '__main__':
    try:
        app.run(host='172.20.10.3', port=5500, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()