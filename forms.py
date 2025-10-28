# File: /project_folder/forms.py
# (Replaces your entire old forms.py file)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.fields import DateField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User, Department
from datetime import date

# ... (RegistrationForm, LoginForm, AddDoctorForm, UpdateDoctorForm, BookingForm, TreatmentForm are all here... no changes) ...

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddDoctorForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Doctor')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class UpdateDoctorForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Doctor')

    def __init__(self, original_email, *args, **kwargs):
        super(UpdateDoctorForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already in use by another user.')

class BookingForm(FlaskForm):
    date = DateField('Appointment Date', validators=[DataRequired()], format='%Y-%m-%d')
    time = TimeField('Appointment Time', validators=[DataRequired()], format='%H:%M')
    submit = SubmitField('Book Appointment')

    def validate_date(self, date_field):
        if date_field.data < date.today():
            raise ValidationError("You cannot book an appointment in the past.")

class TreatmentForm(FlaskForm):
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    prescription = TextAreaField('Prescription')
    notes = TextAreaField('Notes')
    submit = SubmitField('Mark as Completed')

# --- THIS CLASS IS NEW ---
class UpdateAvailabilityForm(FlaskForm):
    """Form for doctors to update their weekly availability."""
    monday = StringField('Monday', default='Not Available')
    tuesday = StringField('Tuesday', default='Not Available')
    wednesday = StringField('Wednesday', default='Not Available')
    thursday = StringField('Thursday', default='Not Available')
    friday = StringField('Friday', default='Not Available')
    saturday = StringField('Saturday', default='Not Available')
    sunday = StringField('Sunday', default='Not Available')
    submit = SubmitField('Update Availability')