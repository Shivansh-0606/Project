from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from functools import wraps
from extensions import db, login_manager
from models import User, Doctor, Patient, Appointment, Treatment, Department, load_user
from flask_wtf.csrf import CSRFProtect
from flask_login import login_user, logout_user, login_required, current_user
import os
from dotenv import load_dotenv
import json
from datetime import date
import datetime  # Added for the context processor
from sqlalchemy import or_

load_dotenv()

# --- APP CONFIGURATION ---
app = Flask(__name__)
# We use the hardcoded key for now to ensure it works.
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') 
app.config['SECRET_KEY'] = 'f8e3a2c5d1b74a0e9f8d7c6b5a4f3e2d' # Hardcoded fix
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hospital.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZE EXTENSIONS ---
db.init_app(app)
login_manager.init_app(app)
login_manager.user_loader(load_user)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)

# --- IMPORT FORMS (AFTER CONFIG) ---
from forms import (
    LoginForm, RegistrationForm, AddDoctorForm,
    UpdateDoctorForm, BookingForm, TreatmentForm, UpdateAvailabilityForm
)

# --- HELPER DECORATORS ---
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('This page is for admins only.', 'danger')
            return redirect(url_for('dashboard_redirect'))
        return f(*args, **kwargs)
    return decorated_function

def patient_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'patient':
            flash('This page is for patients only.', 'danger')
            return redirect(url_for('dashboard_redirect'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'doctor':
            flash('This page is for doctors only.', 'danger')
            return redirect(url_for('dashboard_redirect'))
        return f(*args, **kwargs)
    return decorated_function

# --- INJECT CONTEXT ---
@app.context_processor
def inject_current_year():
    """Injects the current year into all templates."""
    return {'current_year': datetime.date.today().year}

# --- AUTHENTICATION ROUTES ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(email=form.email.data, name=form.name.data, role='patient')
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user. Email may already exist. {e}', 'danger')
            return render_template('register.html', title='Register', form=form)
        new_patient = Patient(user_id=new_user.id)
        db.session.add(new_patient)
        db.session.commit()
        login_user(new_user)
        flash('Your account has been created! You are now logged in.', 'success')
        return redirect(url_for('dashboard_redirect'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard_redirect'))
        elif user and not user.is_active:
            flash('This account has been deactivated. Please contact an admin.', 'danger')
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- CORE APP ROUTES ---
@app.route('/')
def index():
    # Added title here
    return render_template('index.html', title='Welcome')

@app.route('/dashboard')
@login_required
def dashboard_redirect():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif current_user.role == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        flash('Your user role is not defined.', 'danger')
        logout_user()
        return redirect(url_for('index'))

# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    doctor_count = Doctor.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    # Path uses admin/ subfolder
    return render_template('admin/dashboard.html', title='Admin Dashboard',
                           doctor_count=doctor_count, patient_count=patient_count,
                           appointment_count=appointment_count)
@app.route('/admin/manage_doctors')
@admin_required
def admin_manage_doctors():
    """READ: Display all doctor profiles, with search."""
    q = request.args.get('q') # Get search query from URL
    
    if q:
        # If there is a search, filter by name OR department name
        query = Doctor.query.join(User).join(Department).filter(
            or_(
                User.name.ilike(f'%{q}%'),
                Department.name.ilike(f'%{q}%')
            )
        )
    else:
        # If no search, get all doctors
        query = Doctor.query
        
    doctors = query.all()
    
    # Path uses admin/ subfolder
    return render_template('admin/manage_doctors.html',
                           title='Manage Doctors',
                           doctors=doctors,
                           search_query=q) # Pass the query back

@app.route('/admin/add_doctor', methods=['GET', 'POST'])
@admin_required
def admin_add_doctor():
    form = AddDoctorForm()
    form.department.choices = [(dept.id, dept.name) for dept in Department.query.order_by(Department.name).all()]
    if form.validate_on_submit():
        new_user = User(email=form.email.data, name=form.name.data, role='doctor')
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {e}', 'danger')
            return render_template('admin/add_doctor.html', title='Add Doctor', form=form)
        new_doctor = Doctor(user_id=new_user.id, department_id=form.department.data)
        db.session.add(new_doctor)
        db.session.commit()
        flash(f'Doctor {form.name.data} has been added.', 'success')
        return redirect(url_for('admin_manage_doctors'))
    # Path uses admin/ subfolder
    return render_template('admin/add_doctor.html', title='Add Doctor', form=form)

@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = UpdateDoctorForm(original_email=doctor.user.email)
    form.department.choices = [(dept.id, dept.name) for dept in Department.query.order_by(Department.name).all()]
    if form.validate_on_submit():
        doctor.user.name = form.name.data
        doctor.user.email = form.email.data
        doctor.department_id = form.department.data
        db.session.commit()
        flash('Doctor profile has been updated.', 'success')
        return redirect(url_for('admin_manage_doctors'))
    elif request.method == 'GET':
        form.name.data = doctor.user.name
        form.email.data = doctor.user.email
        form.department.data = doctor.department_id
    # Path uses admin/ subfolder
    return render_template('admin/edit_doctor.html', title='Edit Doctor', form=form, doctor=doctor)

@app.route('/admin/deactivate_doctor/<int:user_id>', methods=['POST'])
@admin_required
def admin_deactivate_doctor(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'doctor':
        flash('This user is not a doctor.', 'danger')
        return redirect(url_for('admin_manage_doctors'))
    user.is_active = False
    db.session.commit()
    flash(f'Doctor {user.name} has been deactivated.', 'success')
    return redirect(url_for('admin_manage_doctors'))

@app.route('/admin/activate_doctor/<int:user_id>', methods=['POST'])
@admin_required
def admin_activate_doctor(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'doctor':
        flash('This user is not a doctor.', 'danger')
        return redirect(url_for('admin_manage_doctors'))
    user.is_active = True
    db.session.commit()
    flash(f'Doctor {user.name} has been reactivated.', 'success')
    return redirect(url_for('admin_manage_doctors'))

@app.route('/admin/manage_patients')
@admin_required
def admin_manage_patients():
    """READ: Display all patient profiles, with search."""
    q = request.args.get('q')
    
    if q:
        # Search by name, email, or contact phone
        query = Patient.query.join(User).filter(
            or_(
                User.name.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%'),
                Patient.contact_phone.ilike(f'%{q}%')
            )
        )
    else:
        query = Patient.query
        
    patients = query.all()
    
    # Path uses admin/ subfolder
    return render_template('admin/manage_patients.html',
                           title='Manage Patients',
                           patients=patients,
                           search_query=q)

# --- DOCTOR ROUTES ---
@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    doctor = current_user.doctor_profile
    if not doctor:
        flash('Could not find your doctor profile.', 'danger')
        return redirect(url_for('logout'))
    today = date.today()
    todays_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id, Appointment.appointment_date == today, Appointment.status == 'Booked'
    ).join(Patient).join(User).order_by(Appointment.appointment_time).all()
    upcoming_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id, Appointment.appointment_date > today, Appointment.status == 'Booked'
    ).join(Patient).join(User).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    completed_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id, Appointment.status == 'Completed'
    ).join(Patient).join(User).order_by(Appointment.appointment_date.desc()).all()
    form = TreatmentForm()
    # Path uses doctor/ subfolder
    return render_template('doctor/dashboard.html', title='Doctor Dashboard',
                           todays_appts=todays_appts, upcoming_appts=upcoming_appts,
                           completed_appts=completed_appts, form=form)

@app.route('/doctor/complete_appointment/<int:appointment_id>', methods=['POST'])
@doctor_required
def complete_appointment(appointment_id):
    form = TreatmentForm()
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.doctor_profile.id:
        flash('You do not have permission to modify this appointment.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    if form.validate_on_submit():
        appointment.status = 'Completed'
        new_treatment = Treatment(
            appointment_id=appointment.id, diagnosis=form.diagnosis.data,
            prescription=form.prescription.data, notes=form.notes.data
        )
        db.session.add(new_treatment)
        db.session.commit()
        flash('Appointment marked as complete and treatment notes saved.', 'success')
    else:
        flash('Could not complete appointment. Diagnosis is required.', 'danger')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/cancel_appointment/<int:appointment_id>', methods=['POST'])
@doctor_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.doctor_profile.id:
        flash('You do not have permission to modify this appointment.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    if appointment.status == 'Booked':
        appointment.status = 'Cancelled'
        db.session.commit()
        flash('Appointment has been cancelled.', 'success')
    else:
        flash('This appointment cannot be cancelled.', 'warning')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/patient_history/<int:patient_id>')
@doctor_required
def doctor_patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    completed_appts = Appointment.query.filter_by(
        patient_id=patient.id, status='Completed'
    ).join(Treatment).order_by(Appointment.appointment_date.desc()).all()
    # Path uses doctor/ subfolder
    return render_template('doctor/patient_history.html',
                           title=f"History for {patient.user.name}",
                           patient=patient, appointments=completed_appts)

@app.route('/doctor/availability', methods=['GET', 'POST'])
@doctor_required
def doctor_manage_availability():
    """Allow doctor to update their weekly availability."""
    doctor = current_user.doctor_profile
    form = UpdateAvailabilityForm()

    if form.validate_on_submit():
        # User is submitting the form
        availability_dict = {
            'Monday': form.monday.data,
            'Tuesday': form.tuesday.data,
            'Wednesday': form.wednesday.data,
            'Thursday': form.thursday.data,
            'Friday': form.friday.data,
            'Saturday': form.saturday.data,
            'Sunday': form.sunday.data
        }
        # Convert dict to JSON string and save
        doctor.availability = json.dumps(availability_dict)
        db.session.commit()
        flash('Your availability has been updated.', 'success')
        return redirect(url_for('doctor_dashboard'))
    
    elif request.method == 'GET':
        # User is loading the page, pre-fill with saved data
        data = doctor.availability_data
        form.monday.data = data.get('Monday', 'Not Available')
        form.tuesday.data = data.get('Tuesday', 'Not Available')
        form.wednesday.data = data.get('Wednesday', 'Not Available')
        form.thursday.data = data.get('Thursday', 'Not Available')
        form.friday.data = data.get('Friday', 'Not Available')
        form.saturday.data = data.get('Saturday', 'Not Available')
        form.sunday.data = data.get('Sunday', 'Not Available')

    # Path uses doctor/ subfolder
    return render_template('doctor/manage_availability.html',
                           title='Manage Availability',
                           form=form)

# --- PATIENT ROUTES ---
@app.route('/patient/dashboard')
@patient_required
def patient_dashboard():
    departments = Department.query.order_by(Department.name).all()
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    upcoming_appointments = []
    past_appointments = []
    if patient:
        all_appts = Appointment.query.filter_by(patient_id=patient.id)\
                                 .join(Doctor).join(User).order_by(Appointment.appointment_date.desc()).all()
        today = date.today()
        for appt in all_appts:
            if appt.appointment_date >= today:
                upcoming_appointments.append(appt)
            else:
                past_appointments.append(appt)
    # Path uses patient/ subfolder
    return render_template('patient/dashboard.html', title='Patient Dashboard',
                           departments=departments, upcoming_appts=upcoming_appointments,
                           past_appts=past_appointments)

@app.route('/patient/view_doctors')
@patient_required
def patient_view_doctors():
    """Show doctors, filtered by department AND/OR search query."""
    dept_id = request.args.get('dept_id', type=int)
    q = request.args.get('q')
    
    # Start with active doctors
    query = Doctor.query.join(User).filter(User.is_active == True)
    
    if dept_id:
        # Filter by department
        query = query.filter(Doctor.department_id == dept_id)
    
    if q:
        # Filter by search query (name or department)
        query = query.join(Department).filter(
            or_(
                User.name.ilike(f'%{q}%'),
                Department.name.ilike(f'%{q}%')
            )
        )
        
    doctors = query.all()
    
    # Path uses patient/ subfolder
    return render_template('patient/view_doctors.html',
                           title='View Doctors',
                           doctors=doctors,
                           search_query=q)

@app.route('/patient/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@patient_required
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = BookingForm()
    if form.validate_on_submit():
        date = form.date.data
        time = form.time.data
        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor.id, appointment_date=date,
            appointment_time=time, status='Booked'
        ).first()
        if existing_appointment:
            flash('This time slot is already taken by another patient. Please choose another time.', 'danger')
            return render_template('patient/book_appointment.html',
                                   title='Book Appointment', form=form, doctor=doctor)
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if not patient:
            flash('Error: Could not find your patient profile.', 'danger')
            return redirect(url_for('patient_dashboard'))
        new_appointment = Appointment(
            patient_id=patient.id, doctor_id=doctor.id,
            appointment_date=date, appointment_time=time, status='Booked'
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash(f'Appointment booked with Dr. {doctor.user.name} on {date} at {time}.', 'success')
        return redirect(url_for('patient_dashboard'))
    # Path uses patient/ subfolder
    return render_template('patient/book_appointment.html',
                           title='Book Appointment', form=form, doctor=doctor)

@app.route('/patient/view_treatment/<int:appointment_id>')
@patient_required
def patient_view_treatment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient.user_id != current_user.id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('patient_dashboard'))
    if not appointment.treatment:
        flash('Treatment details are not yet available for this appointment.', 'info')
        return redirect(url_for('patient_dashboard'))
    # Path uses patient/ subfolder
    return render_template('patient/view_treatment.html',
                           title='View Treatment', appointment=appointment)

# --- API ENDPOINTS (FULL CRUD) ---

@app.route('/api/doctors', methods=['GET', 'POST'])
@login_required # Require ALL API access to be by a logged-in user
def api_doctors():
    
    # --- METHOD 1: GET (Read All) ---
    if request.method == 'GET':
        doctors = Doctor.query.join(User).filter(User.is_active == True).all()
        doctor_list = []
        for doc in doctors:
            doctor_list.append({
                'id': doc.id,
                'name': doc.user.name,
                'email': doc.user.email,
                'department': doc.department.name
            })
        return jsonify(doctors=doctor_list)

    # --- METHOD 2: POST (Create) ---
    if request.method == 'POST':
        # Only admins can create doctors
        if current_user.role != 'admin':
            return jsonify(error='Forbidden. Admin access required.'), 403
            
        data = request.get_json()
        
        # Basic validation
        if not data or not 'email' in data or not 'password' in data or not 'name' in data or not 'department_id' in data:
            return jsonify(error='Missing required fields: email, password, name, department_id'), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify(error='Email already exists'), 409 # 409 = Conflict
            
        try:
            # 1. Create User
            new_user = User(
                email=data['email'],
                name=data['name'],
                role='doctor'
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit() # Commit to get the user ID
            
            # 2. Create Doctor
            new_doctor = Doctor(
                user_id=new_user.id,
                department_id=data['department_id']
            )
            db.session.add(new_doctor)
            db.session.commit()
            
            # Return the new doctor's data
            return jsonify(message='Doctor created successfully', doctor={
                'id': new_doctor.id,
                'name': new_user.name,
                'email': new_user.email
            }), 201 # 201 = Created
            
        except Exception as e:
            db.session.rollback()
            return jsonify(error=f'Database error: {str(e)}'), 500


@app.route('/api/doctors/<int:doctor_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required # Require ALL API access to be by a logged-in user
def api_single_doctor(doctor_id):
    
    doctor = Doctor.query.get_or_404(doctor_id)

    # --- METHOD 3: GET (Read One) ---
    if request.method == 'GET':
        if not doctor.user.is_active:
            return jsonify({'error': 'Doctor not found or is inactive.'}), 404
            
        return jsonify(doctor={
            'id': doctor.id,
            'name': doctor.user.name,
            'email': doctor.user.email,
            'department': doctor.department.name,
            'availability': doctor.availability_data
        })

    # --- METHOD 4: PUT (Update) ---
    if request.method == 'PUT':
        if current_user.role != 'admin':
            return jsonify(error='Forbidden. Admin access required.'), 403
        
        data = request.get_json()
        
        # Update user fields
        if 'name' in data:
            doctor.user.name = data['name']
        if 'email' in data:
            # Check if new email is taken by SOMEONE ELSE
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != doctor.user.id:
                return jsonify(error='Email already in use by another user.'), 409
            doctor.user.email = data['email']
        
        # Update doctor fields
        if 'department_id' in data:
            doctor.department_id = data['department_id']
        
        db.session.commit()
        return jsonify(message='Doctor updated successfully', doctor={
            'id': doctor.id,
            'name': doctor.user.name
        })

    # --- METHOD 5: DELETE (Delete) ---
    if request.method == 'DELETE':
        if current_user.role != 'admin':
            return jsonify(error='Forbidden. Admin access required.'), 403
        
        # We use our safe "deactivate" logic
        doctor.user.is_active = False
        db.session.commit()
        
        # 204 = No Content (success, but nothing to return)
        return '', 204
        
# --- RUN SCRIPT ---

if __name__ == '__main__':
    app.run(debug=True)