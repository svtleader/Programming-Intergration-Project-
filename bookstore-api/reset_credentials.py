import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USERNAME', 'root'),
    'password': os.getenv('DB_PASSWORD', 'ledung04gmailcom'),
    'database': os.getenv('DB_NAME', 'bookstore')
}

def hash_password(password):
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def reset_user_credentials():
    """Reset the admin and user credentials with proper bcrypt hashes."""
    try:
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Hash the passwords
        admin_hash = hash_password('admin123')
        user_hash = hash_password('user123')
        
        print(f"Generated admin hash: {admin_hash}")
        print(f"Generated user hash: {user_hash}")
        
        # Delete existing users
        cursor.execute("DELETE FROM users WHERE username IN ('admin', 'user')")
        
        # Insert admin user
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        """, ('admin', 'admin@example.com', admin_hash, 'admin'))
        
        # Insert regular user
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        """, ('user', 'user@example.com', user_hash, 'user'))
        
        # Commit the changes
        conn.commit()
        print("Users have been reset with new password hashes!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    reset_user_credentials()