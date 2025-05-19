from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from utils.auth import admin_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login user and return access token
    """
    data = request.get_json()
    
    # Check if credentials are provided
    if 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password are required"}), 400
    
    # Find user by username
    user = User.query.filter_by(username=data['username']).first()
    
    # Check if user exists and password is correct
    if not user or not user.check_password(data['password']):
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Create access token with user.id converted to string
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200

@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user's information
    """
    current_user_id = get_jwt_identity()
    # Convert string ID back to integer if your database expects integer IDs
    user_id = int(current_user_id) if current_user_id.isdigit() else current_user_id
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    return jsonify({"user": user.to_dict()}), 200

@auth_bp.route('/auth/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    Get all users (admin only)
    """
    users = User.query.all()
    return jsonify({"users": [user.to_dict() for user in users]}), 200