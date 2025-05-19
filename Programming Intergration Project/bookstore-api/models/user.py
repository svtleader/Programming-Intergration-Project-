from . import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def __init__(self, username, email, password, role='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        self.password_hash = hashed.decode('utf-8')
        
    def check_password(self, password):
        password_bytes = password.encode('utf-8')
        stored_hash = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash)
        
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
