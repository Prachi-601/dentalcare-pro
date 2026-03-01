# 🦷 DentalCare Pro

A complete admin-based Dentist Appointment & Patient Management System built with Flask + SQLite.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://localhost:5000
```

On first run, you'll be redirected to the **Register** page to create your admin account.
No default credentials — you set your own secure password.

---

## 📁 Project Structure

```
dental_app/
├── app.py                    ← All Flask routes & models
├── requirements.txt
├── dental.db                 ← SQLite DB (auto-created)
├── static/
│   ├── css/style.css         ← Full styles + dark/light mode
│   └── js/main.js            ← Theme toggle + utilities
└── templates/
    ├── base.html             ← Navbar + layout
    ├── login.html            ← Login page
    ├── register.html         ← Register with password strength meter
    ├── dashboard.html        ← Dashboard with stats
    ├── patients.html         ← Patient list + search
    ├── patient_form.html     ← Add/Edit patient
    ├── patient_detail.html   ← Patient profile + Add Payment section
    ├── appointments.html     ← Today + upcoming + filter
    ├── appointment_form.html ← Add/Edit appointment (today bug fixed)
    └── earnings.html         ← Earnings + payment log
```

---

## ✅ What's Fixed / New

| Issue | Fix |
|-------|-----|
| `today is undefined` in new appointment | Passes `today` in every GET route |
| No default admin | First visit → Register page, set your own password |
| Weak auth | Strong password enforced: 8+ chars, uppercase, lowercase, digit, special char |
| Register page | Full registration with real-time password strength meter |
| No quick payment | **Add Payment** section directly on patient profile page |
| Payment history | Every payment saved with date, note, timestamp |
| Delete payment | Can remove incorrect payment entries |

---

## 💳 Adding Payments (New Feature)

1. Go to any patient's profile page
2. Scroll to **"Record New Payment"** section
3. Enter amount + date + optional note → **Save Payment**
4. Full payment history shown below with delete option
5. Remaining balance auto-updates

---

## 🔐 Password Requirements

When registering, your password must have:
- ✅ At least 8 characters
- ✅ One uppercase letter (A-Z)
- ✅ One lowercase letter (a-z)
- ✅ One number (0-9)
- ✅ One special character (!@#$%^&* etc.)

A real-time strength meter guides you as you type.

---

## 📲 SMS Reminders (Twilio)

```bash
pip install twilio
export TWILIO_ACCOUNT_SID="ACxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_token"
export TWILIO_PHONE_NUMBER="+1XXXXXXXXXX"
```

---

## 🌗 Dark / Light Mode

Click the 🌙 moon icon in the navbar. Preference is saved in `localStorage`.
