from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create database object
db = SQLAlchemy()

# Create  login manager object
login_manager = LoginManager()
# Tell Flask-Login where to redirect for login
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'