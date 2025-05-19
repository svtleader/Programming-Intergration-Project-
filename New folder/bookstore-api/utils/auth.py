from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from models import User

def admin_required(fn):
    """
    Decorator function to check if the user has admin privileges
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        user = User.query.get(identity)
        
        if user and user.role == 'admin':
            return fn(*args, **kwargs)
        else:
            return jsonify({"message": "Admin privileges required"}), 403
    
    return wrapper

def get_current_user():
    """
    Helper function to get the current authenticated user
    """
    try:
        verify_jwt_in_request()
        identity = get_jwt_identity()
        user = User.query.get(identity)
        return user
    except:
        return None