from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import func
import re, os, secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
with app.app_context():
    db.create_all()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'
login_manager.login_message_category = 'warning'


# ═══════════════════════════════════════════════════
#   MODELS
# ═══════════════════════════════════════════════════

class Admin(UserMixin, db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash= db.Column(db.String(256), nullable=False)
    clinic_name  = db.Column(db.String(120), default='SmileCare Dental Clinic')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Patient(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    full_name     = db.Column(db.String(120), nullable=False)
    phone         = db.Column(db.String(20),  nullable=False)
    age           = db.Column(db.Integer)
    gender        = db.Column(db.String(10))
    address       = db.Column(db.Text)
    treatment_type= db.Column(db.String(100))
    total_cost    = db.Column(db.Float, default=0.0)
    amount_paid   = db.Column(db.Float, default=0.0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    appointments  = db.relationship('Appointment', backref='patient',  lazy=True, cascade='all, delete-orphan')
    payments      = db.relationship('PaymentLog',  backref='patient',  lazy=True, cascade='all, delete-orphan')

    @property
    def remaining_amount(self):
        return max(0.0, (self.total_cost or 0) - (self.amount_paid or 0))


class Appointment(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    patient_id          = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_date    = db.Column(db.Date,    nullable=False)
    appointment_time    = db.Column(db.Time,    nullable=False)
    work_to_be_done     = db.Column(db.Text)
    treatment_suggestion= db.Column(db.String(100))
    status              = db.Column(db.String(20), default='Scheduled')
    payment_collected   = db.Column(db.Float, default=0.0)
    notes               = db.Column(db.Text)
    reminder_sent       = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentLog(db.Model):
    """Tracks each individual payment made by a patient with date."""
    id          = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    patient_id  = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    payment_date= db.Column(db.Date,  nullable=False, default=date.today)
    note        = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


# ═══════════════════════════════════════════════════
#   PASSWORD VALIDATION HELPER
# ═══════════════════════════════════════════════════

def validate_password(pw):
    """Returns list of errors. Empty list = valid."""
    errors = []
    if len(pw) < 8:
        errors.append('At least 8 characters')
    if not re.search(r'[A-Z]', pw):
        errors.append('At least one uppercase letter')
    if not re.search(r'[a-z]', pw):
        errors.append('At least one lowercase letter')
    if not re.search(r'\d', pw):
        errors.append('At least one number')
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-]', pw):
        errors.append('At least one special character (!@#$%^&* etc.)')
    return errors


# ═══════════════════════════════════════════════════
#   AUTH ROUTES
# ═══════════════════════════════════════════════════

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    # If no admins exist yet, redirect to register
    if Admin.query.count() == 0:
        flash('No admin account found. Please register first.', 'info')
        return redirect(url_for('register'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {admin.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username    = request.form.get('username', '').strip()
        email       = request.form.get('email', '').strip().lower()
        clinic_name = request.form.get('clinic_name', '').strip()
        password    = request.form.get('password', '')
        confirm_pw  = request.form.get('confirm_password', '')

        # Validations
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if Admin.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if not email or '@' not in email:
            errors.append('Enter a valid email address.')
        if Admin.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if password != confirm_pw:
            errors.append('Passwords do not match.')
        pw_errors = validate_password(password)
        if pw_errors:
            errors.append('Password must contain: ' + ', '.join(pw_errors))

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html',
                username=username, email=email, clinic_name=clinic_name)

        admin = Admin(username=username, email=email,
                      clinic_name=clinic_name or 'SmileCare Dental Clinic')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', username='', email='', clinic_name='')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════
#   DASHBOARD
# ═══════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    first_of_month = today.replace(day=1)

    today_appointments = Appointment.query.filter_by(
    appointment_date=today,
    admin_id=current_user.id
    ).order_by(Appointment.appointment_time).all()

    upcoming_appointments = Appointment.query.filter(
    Appointment.appointment_date > today,
    Appointment.status == 'Scheduled',
    Appointment.admin_id == current_user.id
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(10).all()

    # Income = ALL payments recorded in PaymentLog (covers both manual + appointment payments)
    today_income = db.session.query(func.sum(PaymentLog.amount)).filter(
    PaymentLog.payment_date == today,
    PaymentLog.admin_id == current_user.id
    ).scalar() or 0

    monthly_income = db.session.query(func.sum(PaymentLog.amount)).filter(
    PaymentLog.payment_date >= first_of_month,
    PaymentLog.admin_id == current_user.id
    ).scalar() or 0

    pending_payments = db.session.query(
    func.sum(Patient.total_cost - Patient.amount_paid)
    ).filter(
        Patient.admin_id == current_user.id,
        (Patient.total_cost - Patient.amount_paid) > 0
    ).scalar() or 0

    total_patients = Patient.query.filter_by(
    admin_id=current_user.id
    ).count()

    recent_payments = PaymentLog.query.filter_by(
    admin_id=current_user.id
    ).order_by(
        PaymentLog.created_at.desc()
    ).limit(5).all()

    return render_template('dashboard.html',
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        today_income=today_income,
        monthly_income=monthly_income,
        pending_payments=pending_payments,
        total_patients=total_patients,
        recent_payments=recent_payments,
        today=today
    )


# ═══════════════════════════════════════════════════
#   PATIENT ROUTES
# ═══════════════════════════════════════════════════

@app.route('/patients')
@login_required
def patients():
    search = request.args.get('search', '').strip()
    query = Patient.query.filter_by(admin_id=current_user.id)
    if search:
        query = query.filter(
            (Patient.full_name.ilike(f'%{search}%')) |
            (Patient.phone.ilike(f'%{search}%'))
        )
    patients_list = query.order_by(Patient.full_name).all()
    return render_template('patients.html', patients=patients_list, search=search)


@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient = Patient(
            admin_id=current_user.id,
            full_name    = request.form['full_name'].strip(),
            phone        = request.form['phone'].strip(),
            age          = request.form.get('age') or None,
            gender       = request.form.get('gender'),
            address      = request.form.get('address', '').strip(),
            treatment_type = request.form.get('treatment_type', '').strip(),
            total_cost   = float(request.form.get('total_cost') or 0),
            amount_paid  = float(request.form.get('amount_paid') or 0),
        )
        db.session.add(patient)
        db.session.flush()  # get patient.id before commit

        # Log initial payment if any
        if patient.amount_paid > 0:
            log = PaymentLog(
            admin_id     = current_user.id,
            patient_id   = patient.id,
            amount       = patient.amount_paid,
            payment_date = date.today(),
            note         = 'Initial payment on registration'
            )
            db.session.add(log)

        db.session.commit()
        flash(f'Patient {patient.full_name} added successfully!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient.id))
    return render_template('patient_form.html', patient=None, action='Add')


@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    if request.method == 'POST':
        patient.full_name     = request.form['full_name'].strip()
        patient.phone         = request.form['phone'].strip()
        patient.age           = request.form.get('age') or None
        patient.gender        = request.form.get('gender')
        patient.address       = request.form.get('address', '').strip()
        patient.treatment_type= request.form.get('treatment_type', '').strip()
        patient.total_cost    = float(request.form.get('total_cost') or 0)
        # Don't touch amount_paid here — managed via PaymentLog
        db.session.commit()
        flash(f'Patient {patient.full_name} updated successfully!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient.id))
    return render_template('patient_form.html', patient=patient, action='Edit')


@app.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    name = patient.full_name
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient "{name}" and all records deleted.', 'info')
    return redirect(url_for('patients'))


@app.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.appointment_date.desc()).all()
    payments = PaymentLog.query.filter_by(patient_id=patient_id).order_by(
        PaymentLog.payment_date.desc(), PaymentLog.created_at.desc()).all()
    return render_template('patient_detail.html',
        patient=patient, appointments=appointments, payments=payments, today=date.today())


# ─── ADD PAYMENT TO PATIENT ──────────────────────────────────────────────────

@app.route('/patients/<int:patient_id>/add_payment', methods=['POST'])
@login_required
def add_payment(patient_id):
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    amount = float(request.form.get('amount') or 0)
    note   = request.form.get('note', '').strip()
    pay_date_str = request.form.get('payment_date', '')

    if amount <= 0:
        flash('Payment amount must be greater than zero.', 'danger')
        return redirect(url_for('patient_detail', patient_id=patient_id))

    try:
        pay_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date() if pay_date_str else date.today()
    except ValueError:
        pay_date = date.today()

    log = PaymentLog(
        admin_id     = current_user.id,
        patient_id   = patient.id,
        amount       = amount,
        payment_date = pay_date,
        note         = note or 'Manual payment'
    )
    db.session.add(log)
    patient.amount_paid += amount
    db.session.commit()
    flash(f'₹{amount:.2f} payment recorded for {patient.full_name}.', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))


@app.route('/patients/<int:patient_id>/delete_payment/<int:log_id>', methods=['POST'])
@login_required
def delete_payment(patient_id, log_id):
    log = PaymentLog.query.filter_by(
    id=log_id,
    admin_id=current_user.id
).first_or_404()
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    patient.amount_paid = max(0, patient.amount_paid - log.amount)
    db.session.delete(log)
    db.session.commit()
    flash(f'Payment of ₹{log.amount:.2f} removed.', 'info')
    return redirect(url_for('patient_detail', patient_id=patient_id))


# ═══════════════════════════════════════════════════
#   APPOINTMENT ROUTES
# ═══════════════════════════════════════════════════

@app.route('/appointments')
@login_required
def appointments():
    filter_date   = request.args.get('date', '')
    status_filter = request.args.get('status', '')
    today = date.today()

    today_appts = Appointment.query.filter_by(
    appointment_date=today,
    admin_id=current_user.id
    ).order_by(
        Appointment.appointment_time).all()

    upcoming_appts = Appointment.query.filter(
        Appointment.appointment_date > today,
        Appointment.status == 'Scheduled',
        Appointment.admin_id == current_user.id
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    # Filtered results
    query = Appointment.query.filter_by(admin_id=current_user.id)
    if filter_date:
        try:
            fd = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=fd)
        except ValueError:
            pass
    if status_filter:
        query = query.filter_by(status=status_filter)

    all_appts = query.order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time).all() \
        if (filter_date or status_filter) else []

    patients_list = Patient.query.filter_by(
    admin_id=current_user.id
    ).order_by(Patient.full_name).all()
    return render_template('appointments.html',
        today_appts=today_appts,
        upcoming_appts=upcoming_appts,
        all_appts=all_appts,
        patients=patients_list,
        filter_date=filter_date,
        status_filter=status_filter,
        today=today
    )


@app.route('/appointments/add', methods=['GET', 'POST'])
@login_required
def add_appointment():
    today = date.today()                          # ← FIX: always pass today
    patients_list = Patient.query.filter_by(
    admin_id=current_user.id
    ).order_by(Patient.full_name).all()

    if request.method == 'POST':
        treatment = request.form.get('treatment_suggestion', '')
        if treatment == 'Custom':
            treatment = request.form.get('custom_treatment', '').strip()

        payment = float(request.form.get('payment_collected') or 0)
        appt = Appointment(
            admin_id=current_user.id,
            patient_id          = int(request.form['patient_id']),
            appointment_date    = datetime.strptime(request.form['appointment_date'], '%Y-%m-%d').date(),
            appointment_time    = datetime.strptime(request.form['appointment_time'], '%H:%M').time(),
            work_to_be_done     = request.form.get('work_to_be_done', '').strip(),
            treatment_suggestion= treatment,
            status              = request.form.get('status', 'Scheduled'),
            payment_collected   = payment,
            notes               = request.form.get('notes', '').strip(),
        )
        db.session.add(appt)

        # Log payment if any was collected at appointment
        if payment > 0:
            patient = db.session.get(Patient, appt.patient_id)
            patient.amount_paid += payment
            log = PaymentLog(
                admin_id     = current_user.id,
                patient_id   = appt.patient_id,
                amount       = payment,
                payment_date = appt.appointment_date,
                note         = f'Payment at appointment ({treatment or appt.work_to_be_done or ""})'
            )
            db.session.add(log)

        db.session.commit()
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('appointments'))

    return render_template('appointment_form.html',
        appointment=None, patients=patients_list, action='Add', today=today)


@app.route('/appointments/<int:appt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(appt_id):
    appt = Appointment.query.filter_by(
    id=appt_id,
    admin_id=current_user.id
    ).first_or_404()
    today = date.today()                          # ← FIX: always pass today
    patients_list = Patient.query.order_by(Patient.full_name).all()

    if request.method == 'POST':
        treatment = request.form.get('treatment_suggestion', '')
        if treatment == 'Custom':
            treatment = request.form.get('custom_treatment', '').strip()

        old_payment = appt.payment_collected
        new_payment = float(request.form.get('payment_collected') or 0)

        appt.patient_id          = int(request.form['patient_id'])
        appt.appointment_date    = datetime.strptime(request.form['appointment_date'], '%Y-%m-%d').date()
        appt.appointment_time    = datetime.strptime(request.form['appointment_time'], '%H:%M').time()
        appt.work_to_be_done     = request.form.get('work_to_be_done', '').strip()
        appt.treatment_suggestion= treatment
        appt.status              = request.form.get('status', 'Scheduled')
        appt.payment_collected   = new_payment
        appt.notes               = request.form.get('notes', '').strip()

        diff = new_payment - old_payment
        if diff != 0:
            patient = db.session.get(Patient, appt.patient_id)
            patient.amount_paid = max(0, patient.amount_paid + diff)

        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments'))

    return render_template('appointment_form.html',
        appointment=appt, patients=patients_list, action='Edit', today=today)


@app.route('/appointments/<int:appt_id>/delete', methods=['POST'])
@login_required
def delete_appointment(appt_id):
    appt = Appointment.query.filter_by(
    id=appt_id,
    admin_id=current_user.id
    ).first_or_404()
    db.session.delete(appt)
    db.session.commit()
    flash('Appointment deleted.', 'info')
    return redirect(url_for('appointments'))


@app.route('/appointments/<int:appt_id>/status', methods=['POST'])
@login_required
def update_status(appt_id):
    appt = Appointment.query.filter_by(
    id=appt_id,
    admin_id=current_user.id
).first_or_404()
    appt.status = request.form.get('status', appt.status)
    db.session.commit()
    return redirect(url_for('appointments'))


# ═══════════════════════════════════════════════════
#   API
# ═══════════════════════════════════════════════════

@app.route('/api/patient/<int:patient_id>')
@login_required
def api_patient(patient_id):
    patient = Patient.query.filter_by(
    id=patient_id,
    admin_id=current_user.id
    ).first_or_404()
    return jsonify({'phone': patient.phone, 'name': patient.full_name,
                    'remaining': patient.remaining_amount})


@app.route('/api/send_reminder/<int:appt_id>', methods=['POST'])
@login_required
def send_reminder(appt_id):
    appt = Appointment.query.filter_by(
    id=appt_id,
    admin_id=current_user.id
).first_or_404()
    result = _send_sms_reminder(appt)
    if result['success']:
        appt.reminder_sent = True
        db.session.commit()
        return jsonify({'success': True, 'message': f'Reminder sent to {appt.patient.phone}'})
    return jsonify({'success': False, 'message': result['message']}), 400


def _send_sms_reminder(appointment):
    sid    = os.environ.get('TWILIO_ACCOUNT_SID')
    token  = os.environ.get('TWILIO_AUTH_TOKEN')
    from_n = os.environ.get('TWILIO_PHONE_NUMBER')
    if not all([sid, token, from_n]):
        return {'success': False, 'message': 'Twilio credentials not configured.'}
    try:
        from twilio.rest import Client
        admin = current_user
        clinic = admin.clinic_name if admin else 'Dental Clinic'
        body = (f"Hello {appointment.patient.full_name}, reminder from {clinic}. "
                f"Appointment on {appointment.appointment_date.strftime('%B %d, %Y')} "
                f"at {appointment.appointment_time.strftime('%I:%M %p')}. "
                f"Treatment: {appointment.treatment_suggestion or appointment.work_to_be_done}.")
        Client(sid, token).messages.create(body=body, from_=from_n, to=appointment.patient.phone)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}


# ═══════════════════════════════════════════════════
#   EARNINGS
# ═══════════════════════════════════════════════════

@app.route('/earnings')
@login_required
def earnings():
    today = date.today()
    first_of_month = today.replace(day=1)

    daily_data = db.session.query(
        PaymentLog.payment_date,
        func.sum(PaymentLog.amount).label('total')
    ).filter(
    PaymentLog.payment_date >= first_of_month,
    PaymentLog.admin_id == current_user.id
    ).group_by(PaymentLog.payment_date).order_by(PaymentLog.payment_date).all()

    today_income = db.session.query(func.sum(PaymentLog.amount)).filter(
        PaymentLog.payment_date == today,PaymentLog.admin_id == current_user.id).scalar() or 0

    monthly_income = db.session.query(func.sum(PaymentLog.amount)).filter(
    PaymentLog.payment_date >= first_of_month,
    PaymentLog.admin_id == current_user.id
    ).scalar() or 0

    pending_payments = db.session.query(
        func.sum(Patient.total_cost - Patient.amount_paid)
    ).filter(Patient.admin_id == current_user.id,(Patient.total_cost - Patient.amount_paid) > 0).scalar() or 0

    patients_with_pending = Patient.query.filter(Patient.total_cost > Patient.amount_paid,Patient.admin_id == current_user.id).all()

    # Payment log for current month
    monthly_payment_logs = PaymentLog.query.filter(
    PaymentLog.payment_date >= first_of_month,
    PaymentLog.admin_id == current_user.id
    ).order_by(PaymentLog.payment_date.desc()).all()

    return render_template('earnings.html',
        today_income=today_income,
        monthly_income=monthly_income,
        pending_payments=pending_payments,
        daily_data=daily_data,
        patients_with_pending=patients_with_pending,
        monthly_payment_logs=monthly_payment_logs,
        today=today
    )


# ═══════════════════════════════════════════════════
#   DB INIT — no default admin, require registration
# ═══════════════════════════════════════════════════

def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Database ready. Visit http://localhost:5000 to register your admin account.")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)