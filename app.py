import os
import joblib
import firebase_admin
import smtplib
from email.message import EmailMessage
from twilio.rest import Client
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://machinemonitor-6d071-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# Load model and scaler
model = joblib.load('xgb_model.pkl')
scaler = joblib.load('scaler.pkl')

# Email and Twilio config
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
USER_PHONE = os.getenv("USER_PHONE")

# Firebase paths
sensor_ref = db.reference('sensor_data/latest')
maintenance_ref = db.reference('maintenance/last_updated')   # stores last maintenance date
fault_alerts_ref = db.reference('alerts')                   # per-fault alerts
maintenance_alert_ref = db.reference('maintenance/last_alert_sent')  # preventive maintenance alerts

features = ['Vibration', 'Temperature', 'Pressure', 'RMS_Vibration', 'Mean_Temp']
class_names = {0: "Normal", 1: "Bearing Fault", 2: "Overheating"}

@app.route('/')
def index():
    return render_template('index.html')

ALERT_INTERVAL = timedelta(minutes=10)  # Fault alerts every 10 mins

@app.route('/predict')
def predict():
    try:
        # get sensor data
        data = sensor_ref.get()
        input_data = [float(data[f]) for f in features]
        scaled_input = scaler.transform(pd.DataFrame([input_data], columns=features))
        probs = model.predict_proba(scaled_input)[0]

        pred_class = 0 if probs[0] >= 0.14 else np.argmax(probs)
        label = class_names[pred_class]

        if pred_class != 0:
            # get last alert time for this fault from Firebase
            alert_data = fault_alerts_ref.child(label).get()
            last_alert_sent_str = alert_data.get("last_alert_sent") if alert_data else None

            if last_alert_sent_str:
                last_alert_sent = datetime.strptime(last_alert_sent_str, "%Y-%m-%d %H:%M:%S")
            else:
                last_alert_sent = datetime.min  # very old date

            now = datetime.now()

            # check if 10 mins passed since last alert
            if now - last_alert_sent >= ALERT_INTERVAL:
                send_email_alert(label)
                send_sms_alert(label)
                make_voice_call()

                # update Firebase with new timestamp
                new_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                fault_alerts_ref.child(label).update({"last_alert_sent": new_time_str})

        return jsonify({
            "prediction": int(pred_class),
            "label": label,
            "probs": probs.tolist()
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/update_maintenance', methods=['POST'])
def update_maintenance():
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        maintenance_ref.set(current_time)
        return jsonify({"message": "Maintenance date updated successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})

def send_email_alert(pred_label):
    msg = EmailMessage()
    msg.set_content(f"Machine fault detected! Fault class: {pred_label}")
    msg['Subject'] = "Machine Fault Alert"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = "devikakg0206@gmail.com"

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASS)
        smtp.send_message(msg)

def send_sms_alert(pred_label):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        body=f"Machine fault detected! Fault class: {pred_label}",
        from_=TWILIO_PHONE,
        to=USER_PHONE
    )

def make_voice_call():
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.calls.create(
        twiml='<Response><Say>Machine fault detected! Immediate attention required.</Say></Response>',
        from_=TWILIO_PHONE,
        to=USER_PHONE
    )

def send_maintenance_email():
    msg = EmailMessage()
    msg.set_content("Reminder: Machine maintenance is overdue. Please perform maintenance.")
    msg['Subject'] = "Maintenance Due Alert"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = "devikakg0206@gmail.com"

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASS)
        smtp.send_message(msg)

def send_maintenance_sms():
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        body="Reminder: Machine maintenance is overdue. Please service the machine.",
        from_=TWILIO_PHONE,
        to=USER_PHONE
    )

@app.route('/maintenance_status')
def maintenance_status():
    try:
        last_maint = maintenance_ref.get()
        last_alert = maintenance_alert_ref.get()
        maintenance_due = False

        if last_maint:
            last_time = datetime.strptime(last_maint, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last_time > timedelta(days=3):
                maintenance_due = True
        else:
            maintenance_due = True

        if maintenance_due:
            alert_needed = True
            if last_alert:
                last_alert_time = datetime.strptime(last_alert, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_alert_time < timedelta(hours=3):
                    alert_needed = False

            if alert_needed:
                send_maintenance_email()
                send_maintenance_sms()
                maintenance_alert_ref.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return jsonify({"maintenance_due": maintenance_due})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
