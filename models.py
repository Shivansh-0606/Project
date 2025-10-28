# File: /project_folder/models.py
# (Replaces your entire old models.py file)

from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import json  # <-- ADD THIS IMPORT

# This is the 'loader' function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Only load active users
    user = User.query.get(int(user_id))
    if user and user.is_active:
        return user
    return None

# --- USER MODELS ---

class User(db.Model, UserMixin):
    # ... (No changes to the User model) ...
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False) 
    is_active = db.Column(db.Boolean, default=True, nullable=False) 

    doctor_profile = db.relationship('Doctor', back_populates='user', uselist=False)
    patient_profile = db.relationship('Patient', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Department(db.Model):
    # ... (No changes to the Department model) ...
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    doctors = db.relationship('Doctor', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'


class Doctor(db.Model):
    __tablename__ = 'doctor'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', back_populates='doctor_profile')
    
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    department = db.relationship('Department', back_populates='doctors')
    
    # This is the raw JSON text, e.g., '{"monday": "9-5", "tuesday": "1-4"}'
    availability = db.Column(db.Text, nullable=True) 

    appointments = db.relationship('Appointment', back_populates='doctor')
    
    @property
    def name(self):
        return self.user.name

    # --- THIS IS NEW ---
    @property
    def availability_data(self):
        """
        Helper property to parse the JSON 'availability' text 
        into a Python dictionary for easier use in templates.
        """
        if not self.availability:
            # Return a default dict for the 7 days
            return {
                'Monday': 'Not set', 'Tuesday': 'Not set', 'Wednesday': 'Not set',
                'Thursday': 'Not set', 'Friday': 'Not set', 'Saturday': 'Not set', 'Sunday': 'Not set'
            }
        try:
            return json.loads(self.availability)
        except json.JSONDecodeError:
            # Return a default if the JSON is somehow corrupted
            return {'Error': 'Could not read availability.'}

    def __repr__(self):
        return f'<Doctor {self.user.name}>'


class Patient(db.Model):
    # ... (No changes to the Patient model) ...
    __tablename__ = 'patient'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', back_populates='patient_profile')
    
    contact_phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True) 
    
    appointments = db.relationship('Appointment', back_populates='patient')

    @property
    def name(self):
        return self.user.name

    def __repr__(self):
        return f'<Patient {self.user.name}>'

# --- TRANSACTION MODELS ---

class Appointment(db.Model):
    # ... (No changes to the Appointment model) ...
    __tablename__ = 'appointment'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked') 
    
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False)

    def __repr__(self):
        return f'<Appointment {self.id} on {self.appointment_date}>'


class Treatment(db.Model):
    # ... (No changes to the Treatment model) ...
    __tablename__ = 'treatment'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), unique=True, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    appointment = db.relationship('Appointment', back_populates='treatment')

    def __repr__(self):
        return f'<Treatment for Appt {self.appointment_id}>'