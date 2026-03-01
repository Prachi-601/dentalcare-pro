🦷 DentalCare Pro

A complete admin-based Dentist Appointment & Patient Management System built with Flask + SQLite.

🚀 Quick Start
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://localhost:5000

On first run, you’ll be redirected to the Register page to create your admin account.
There are no default credentials — you set your own secure password.

📌 Features

Admin Authentication System

Secure Registration (Strong Password Enforcement)

Patient Management (Add / Edit / Delete)

Appointment Scheduling (Today + Upcoming)

Payment Recording System

Earnings Dashboard

Real-time Password Strength Meter

Dark / Light Mode (Saved in localStorage)

Optional SMS Reminder Integration (Twilio)

📁 Project Structure
├── app.py
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/

SQLite database is auto-created on first run.

🔐 Password Requirements

Minimum 8 characters

At least one uppercase letter

At least one lowercase letter

At least one digit

At least one special character

💳 Payment System

Record payments directly from patient profile

Auto-updated remaining balance

Payment history log

Delete incorrect entries

📲 Optional SMS Reminder Setup
pip install twilio

Set environment variables:

TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
🌗 Dark / Light Mode

Click the 🌙 icon in the navbar.
Theme preference is stored locally.