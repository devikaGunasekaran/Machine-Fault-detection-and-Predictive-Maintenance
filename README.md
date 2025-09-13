# 🛠️ Machine Fault Detection & Predictive Maintenance  

## 📌 Overview  
This project is a **Smart Automation System** for real-time **machine fault detection** and **predictive maintenance**.  
It combines **Machine Learning (XGBoost)**, and **automation alerts** to prevent unexpected breakdowns.  

The system continuously monitors key machine parameters like **Vibration, Temperature, Pressure, RMS Vibration, and Mean Temperature**, then predicts the machine’s health status:  
- ✅ Normal Operation  
- ⚠️ Bearing Fault  
- 🔥 Overheating  

If a fault or maintenance issue is detected, the system automatically sends:  
- 📩 **Email alerts**  
- 📱 **SMS alerts**  
- ☎️ **Voice calls** (via Twilio)  

A **dashboard frontend** allows users to view the current status and update maintenance logs.  


## 🚀 Features  
- 🔍 **Real-time fault detection** using ML model (XGBoost).  
- 🔔 **Automatic alerts** via Email, SMS, and Voice Calls.  
- 🖥️ **Web dashboard** to display machine status and maintenance info.  
- 🔄 **Firebase Realtime Database** integration for storing sensor and maintenance data.  
- ⏰ **Predictive maintenance alerts** every 3 hours if service is overdue.  


## 🏗️ Tech Stack  
### **Backend**  
- Python (Flask)  
- XGBoost (Machine Learning)  
- Firebase Realtime Database  
- Twilio API (SMS & Voice)  
- SMTP (Email alerts)  

### **Frontend**  
- HTML, CSS, JavaScript  
- Animated dashboard UI  


## ⚙️ How It Works  
1. Sensor data is pushed into **Firebase** (latest readings).  
2. Flask backend fetches the latest data, applies **scaling** and feeds it into the trained **XGBoost model**.  
3. The model predicts the machine status (Normal, Bearing Fault, Overheating).  
4. If a fault is detected → **Alerts are triggered** (Email, SMS, Call).  
5. Maintenance check:  
   - If no update is recorded for **3+ days**, a **maintenance alert** is sent every 3 hours until resolved.  
6. Frontend dashboard updates automatically, showing prediction and maintenance status.  

