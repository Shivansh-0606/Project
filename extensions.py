from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create the database object
db = SQLAlchemy()

# Create the login manager object
login_manager = LoginManager()
# Tell login manager where to send users who are not logged in
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'