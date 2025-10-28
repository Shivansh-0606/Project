Hospital Management System - Flask Starter

This is a starter project for a Hospital Management System based on your wireframes. It uses Flask for the backend, SQLAlchemy for the database (with SQLite), and Jinja2 with Tailwind CSS for the frontend.

Project Structure

/
|-- app.py             # Main Flask application, routes, and models
|-- requirements.txt   # Python dependencies
|-- hospital.db        # SQLite database file (will be created)
|-- templates/
|   |-- base.html          # Base template with Tailwind
|   |-- login.html         # Login page
|   |-- register.html      # Patient registration page
|   |-- admin_dashboard.html # Admin dashboard
|   |-- doctor_dashboard.html# Doctor dashboard
|   |-- patient_dashboard.html# Patient dashboard
|-- README.md          # This file


Setup Instructions

Create a virtual environment:

python -m venv venv


Activate the virtual environment:

macOS/Linux: source venv/bin/activate

Windows: venv\Scripts\activate

Install the required packages:

pip install -r requirements.txt


Running the Application

Set the Flask app environment variables:

macOS/Linux:

export FLASK_APP=app.py
export FLASK_DEBUG=1


Windows:

set FLASK_APP=app.py
set FLASK_DEBUG=1


Run the Flask app:

flask run


The application will be running at http://127.0.0.1:5000.

First-Time Setup (IMPORTANT)

Before you can log in, you need to create the database and a default admin user.

Make sure the app is running (flask run).

Open your web browser and go to this URL:
http://127.0.0.1:5000/init_db

This will create the hospital.db file in your project folder and add a default admin user.

You can now log in with the following credentials:

Username: admin

Password: password123

Next Steps

This starter kit provides the basic structure, authentication, and dashboard layouts with mock data. Your next steps would be to:

Implement Full CRUD: Wire up the "Add Doctor", "Update Schedule", "Delete Patient" buttons to database logic in app.py.

Build Booking Flow: Create the pages for "View Department Details" and "Doctor's Availability" to allow patients to book appointments.

Dynamic Data: Replace all the mock_ data in the dashboard routes with real database queries (e.g., doctors = Doctor.query.all()).

Refine Relationships: Expand on the database models to connect everything fully (e.g., linking appointments to history).

Let me know if you have any questions as you start building it out!