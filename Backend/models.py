from extensions import db
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

login_manager = LoginManager()

# This is the 'loader' function for Flask-Login
@login_manager.user_loader

def load_user(user_id):
    return User.query.get(int(user_id))

# --- USER MODELS ---

# This User model handles login and roles for EVERYONE
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # Role will be 'admin', 'doctor', or 'patient'
    role = db.Column(db.String(50), nullable=False) 

    # One-to-One relationship to Doctor (if role is 'doctor')
    doctor_profile = db.relationship('Doctor', back_populates='user', uselist=False)
    # One-to-One relationship to Patient (if role is 'patient')
    patient_profile = db.relationship('Patient', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Department(db.Model):
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # One-to-Many relationship: One department has many doctors
    doctors = db.relationship('Doctor', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'

class Doctor(db.Model):
    __tablename__ = 'doctor'
    
    id = db.Column(db.Integer, primary_key=True)
    # This links to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # This sets up the 'user' attribute to get User info (email, name)
    user = db.relationship('User', back_populates='doctor_profile')
    
    # This links to the Department table
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    department = db.relationship('Department', back_populates='doctors')
    
    # Doctor-specific field
    availability = db.Column(db.Text, nullable=True) # e.g., "Mon 9-5, Tue 1-5" or JSON

    # One-to-Many relationship: One doctor has many appointments
    appointments = db.relationship('Appointment', back_populates='doctor')
    
    # Helper property to get the doctor's name from the User model
    @property
    def name(self):
        return self.user.name

    def __repr__(self):
        return f'<Doctor {self.user.name}>'

class Patient(db.Model):
    __tablename__ = 'patient'
    
    id = db.Column(db.Integer, primary_key=True)
    # This links to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # This sets up the 'user' attribute to get User info (email, name)
    user = db.relationship('User', back_populates='patient_profile')
    
    # Patient-specific fields
    contact_phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True) # Date of Birth
    
    # One-to-Many relationship: One patient has many appointments
    appointments = db.relationship('Appointment', back_populates='patient')

    # Helper property to get the patient's name from the User model
    @property
    def name(self):
        return self.user.name

    def __repr__(self):
        return f'<Patient {self.user.name}>'

# --- TRANSACTION MODELS ---

class Appointment(db.Model):
    __tablename__ = 'appointment'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked') # Booked, Completed, Cancelled
    
    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    
    # One-to-One relationship to Treatment
    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False)

    def __repr__(self):
        return f'<Appointment {self.id} on {self.appointment_date}>'

class Treatment(db.Model):
    __tablename__ = 'treatment'
    
    id = db.Column(db.Integer, primary_key=True)
    # One-to-One link to Appointment
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), unique=True, nullable=False)
    
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationship
    appointment = db.relationship('Appointment', back_populates='treatment')

    def __repr__(self):
        return f'<Treatment for Appt {self.appointment_id}>'