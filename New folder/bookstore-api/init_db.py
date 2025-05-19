import os
import sys
from flask import Flask
from config import Config
from models import db

# Ensure the correct path is added to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

def init_db():
    """
    Create all tables in the database.
    """
    with app.app_context():
        db.create_all()
        print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
