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

app = Flask(__name__)
app.secret_key = "IoT_2024"  # Simple key for local testing

# MQTT settings
MQTT_BROKER = "172.20.10.3"
MQTT_TOPIC = "rfid/scan"
mqtt_client = mqtt.Client()

#GPIO setupd
LEDpin = 2 #example
GPIO.setmode(GPIO.BCM)
GPIO.setup(LEDpin, GPIO.OUT)

#Email setup
sender_email = "stromika78@gmail.com"
app_password= "uekhmtqwuotoghbx"
receiver_email = "nsumanyim@gmail.com" 
SMTP_PORT = 587
topic = "sensor/light"

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

            if current_light_intensity > 400000:
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

@app.route("/dashboard")
def iot_dashboard():
    if "user_id" not in session:
        return redirect(url_for("authentication"))

    led_status = "ON" if GPIO.input(LEDpin) == GPIO.HIGH else "OFF"
    username = session.get("username")
    user_id = session.get("user_id")
    light_threshold = session.get("light_threshold")
    temperature_threshold = session.get("temperature_threshold")

    return render_template("main.html", username=username, user_id=user_id, light_threshold=light_threshold, temp_threshold=temperature_threshold, light_intensity=current_light_intensity, led_status=led_status)


if __name__ == '__main__':
    try:
        app.run(host='172.20.10.3', port=5500, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()