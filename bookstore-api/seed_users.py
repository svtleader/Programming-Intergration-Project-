import os
import sys
from flask import Flask
from config import Config
from models import db
from models.user import User

# Ensure the correct path is added to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

def seed_users():
    """
    Seed the database with initial admin and user accounts.
    """
    with app.app_context():
        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', email='admin@example.com', password='admin123', role='admin')
            db.session.add(admin_user)

        # Create regular user
        regular_user = User.query.filter_by(username='user').first()
        if not regular_user:
            regular_user = User(username='user', email='user@example.com', password='user123')
            db.session.add(regular_user)

        db.session.commit()
        print("Users seeded successfully.")

if __name__ == "__main__":
    seed_users()
