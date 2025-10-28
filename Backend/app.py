from flask import Flask, render_template, redirect, url_for, flash, request
from extensions import db, login_manager
from models import User, Doctor, Patient, Appointment, Treatment, Department, load_user
from forms import LoginForm, RegistrationForm
from flask_login import login_user, logout_user, login_required, current_user
import os

# --- APP CONFIGURATION ---

app = Flask(__name__)

# Set a secret key for session management and form security
app.config['SECRET_KEY'] = 'your_super_secret_key_here_change_this' 

# Configure the SQLite database
# Gets the absolute path of the current file's directory
basedir = os.path.abspath(os.path.dirname(__file__)) 
# Sets the database URI to a file named 'hospital.db' in the project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hospital.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZE EXTENSIONS ---

# Connect the database to the Flask app
db.init_app(app)

# Connect the login manager to the Flask app
login_manager.init_app(app)
# This is the function Flask-Login will call to get a user from a session ID
login_manager.user_loader(load_user)
# This is the view function name for the login page
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info' # For styling flash messages

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, send them away
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect')) 

    form = RegistrationForm()
    if form.validate_on_submit():
        # Form is valid, create the new user
        
        # 1. Create the base User
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            role='patient' # All registrations are for patients
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        # We must commit here so the new_user gets an 'id'
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user. Email may already exist. {e}', 'danger')
            return render_template('register.html', title='Register', form=form)

        # 2. Create the associated Patient profile
        new_patient = Patient(
            user_id=new_user.id
            # You can add more fields here if needed, e.g., from the form
        )
        db.session.add(new_patient)
        db.session.commit()

        # 3. Log the new user in
        login_user(new_user)
        
        flash('Your account has been created! You are now logged in.', 'success')
        return redirect(url_for('dashboard_redirect')) # Send to their new dashboard

    # If form is not valid (or GET request), show the page
    # Your friend will create 'register.html'
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))

    form = LoginForm()
    if form.validate_on_submit():
        # Find the user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            
            # This is the 'next' page logic. If a user was trying
            # to access a 'login_required' page, they get sent there
            # after logging in.
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard_redirect'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    # Your friend will create 'login.html'
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
@login_required # You can't logout if you aren't logged in
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# --- CORE APP ROUTES ---

@app.route('/')
def index():
    # This will be the main landing page
    # Your friend will create 'index.html'
    return render_template('index.html') 


@app.route('/dashboard')
@login_required
def dashboard_redirect():
    """
    This is a "dummy" route. It just figures out
    which real dashboard to send the user to.
    """
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif current_user.role == 'patient':
        return redirect(url_for('patient_dashboard'))
    else:
        # Just in case, send to index
        flash('Your user role is not defined.', 'danger')
        logout_user()
        return redirect(url_for('index'))

# --- (YOUR ADMIN, DOCTOR, PATIENT ROUTES WILL GO HERE) ---

# We'll create these "dummy" dashboards next
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # A quick check to make sure they are an admin
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard_redirect'))
        
    # Your friend will create 'admin/dashboard.html'
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard_redirect'))

    # Your friend will create 'doctor/dashboard.html'
    return render_template('doctor/dashboard.html', title='Doctor Dashboard')

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard_redirect'))

    # Your friend will create 'patient/dashboard.html'
    return render_template('patient/dashboard.html', title='Patient Dashboard')


# --- RUN SCRIPT ---

if __name__ == '__main__':
    app.run(debug=True)