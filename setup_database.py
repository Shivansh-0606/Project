from app import app, db # Import the app and database
from models import User, Department # Import User model to create admin user
from werkzeug.security import generate_password_hash
import os

# --- SETTINGS ---
ADMIN_EMAIL = 'admin@hospital.com'
ADMIN_PASSWORD = 'admin123'
# --- END SETTINGS ---

def create_initial_data():
    """Creates the database tables and a default admin user."""
    
    # SQLAlchemy needs the app context to work properly
    with app.app_context():
        
        print("Creating database tables...")
        # This creates all tables defined in models.py
        db.create_all()
        print("Tables created.")

        # --- Create Admin User ---
        # Check if the admin user already exists
        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            print(f"Creating default admin user: {ADMIN_EMAIL}")
            
            admin_user = User(
                email=ADMIN_EMAIL,
                name="Admin User",
                role="admin"
            )
            # Use the set_password method from the model
            admin_user.set_password(ADMIN_PASSWORD) 
            
            db.session.add(admin_user)
        else:
            print("Admin user already exists.")

        # --- Create Sample Departments ---
        if not Department.query.first():
            print("Creating sample departments...")
            depts = [
                Department(name="Cardiology", description="Heart and blood vessel issues."),
                Department(name="Neurology", description="Nervous system disorders."),
                Department(name="Pediatrics", description="Medical care for infants, children, and adolescents."),
                Department(name="Orthopedics", description="Musculoskeletal system issues.")
            ]
            db.session.bulk_save_objects(depts)
        else:
            print("Departments already exist.")

        # Commit all the changes to the database
        try:
            db.session.commit()
            print("Admin user and departments successfully added.")
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {e}")
        
        print("Database setup complete.")

# This makes the script runnable directly
if __name__ == '__main__':
    # Check for existing database file to avoid overwriting
    if os.path.exists('hospital.db'):
        print('Database file "hospital.db" already exists.')
    
    create_initial_data()