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

# Global variable to store RFID
rfid_tag = None

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# MQTT message handling
def on_message(client, userdata, message):
    global rfid_tag
    rfid_tag = message.payload.decode("utf-8")
    print(f"Received RFID: {rfid_tag}")

mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)
mqtt_client.subscribe(MQTT_TOPIC)
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
        rfid_tag = None  # Reset RFID tag to prevent multiple logins
        return jsonify(success=True), 200
    else:
        return jsonify(success=False), 403

@app.route("/dashboard")
def iot_dashboard():
    if "user_id" not in session:
        return redirect(url_for("authentication"))

    username = session.get("username")
    return render_template("main.html", username=username)


if __name__ == '__main__':
    try:
        app.run(host='172.20.10.3', port=5500, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()