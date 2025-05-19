from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Publisher
from utils.auth import admin_required

publishers_bp = Blueprint('publishers', __name__)

@publishers_bp.route('/publishers', methods=['GET'])
def get_all_publishers():
    """
    Get all publishers with optional filtering
    """
    # Query parameters
    name = request.args.get('name')
    country = request.args.get('country')
    
    # Base query
    query = Publisher.query
    
    # Apply filters
    if name:
        query = query.filter(Publisher.PublishingHouse.ilike(f'%{name}%'))
    if country:
        query = query.filter(Publisher.Country.ilike(f'%{country}%'))
    
    # Execute query
    publishers = query.all()
    
    return jsonify({
        "count": len(publishers),
        "publishers": [publisher.to_dict() for publisher in publishers]
    }), 200

@publishers_bp.route('/publishers/<pub_id>', methods=['GET'])
def get_publisher(pub_id):
    """
    Get a specific publisher by ID
    """
    publisher = Publisher.query.get(pub_id)
    
    if not publisher:
        return jsonify({"message": "Publisher not found"}), 404
    
    return jsonify({"publisher": publisher.to_dict()}), 200

@publishers_bp.route('/publishers', methods=['POST'])
@jwt_required()
@admin_required
def create_publisher():
    """
    Create a new publisher (admin only)
    """
    data = request.get_json()
    
    # Check if required fields are provided
    if 'PubID' not in data or 'PublishingHouse' not in data:
        return jsonify({"message": "PubID and PublishingHouse are required"}), 400
    
    # Check if publisher already exists
    if Publisher.query.get(data['PubID']):
        return jsonify({"message": "Publisher with this ID already exists"}), 400
    
    # Create new publisher
    publisher = Publisher(
        PubID=data['PubID'],
        PublishingHouse=data['PublishingHouse'],
        City=data.get('City'),
        State=data.get('State'),
        Country=data.get('Country'),
        YearEstablished=data.get('YearEstablished'),
        MarketingSpend=data.get('MarketingSpend')
    )
    
    db.session.add(publisher)
    db.session.commit()
    
    return jsonify({
        "message": "Publisher created successfully",
        "publisher": publisher.to_dict()
    }), 201

@publishers_bp.route('/publishers/<pub_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_publisher(pub_id):
    """
    Update a publisher (admin only)
    """
    publisher = Publisher.query.get(pub_id)
    
    if not publisher:
        return jsonify({"message": "Publisher not found"}), 404
    
    data = request.get_json()
    
    # Update publisher attributes
    if 'PublishingHouse' in data:
        publisher.PublishingHouse = data['PublishingHouse']
    if 'City' in data:
        publisher.City = data['City']
    if 'State' in data:
        publisher.State = data['State']
    if 'Country' in data:
        publisher.Country = data['Country']
    if 'YearEstablished' in data:
        publisher.YearEstablished = data['YearEstablished']
    if 'MarketingSpend' in data:
        publisher.MarketingSpend = data['MarketingSpend']
    
    db.session.commit()
    
    return jsonify({
        "message": "Publisher updated successfully",
        "publisher": publisher.to_dict()
    }), 200

@publishers_bp.route('/publishers/<pub_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_publisher(pub_id):
    """
    Delete a publisher (admin only)
    """
    publisher = Publisher.query.get(pub_id)
    
    if not publisher:
        return jsonify({"message": "Publisher not found"}), 404
    
    # Check if publisher has any editions
    if publisher.editions:
        return jsonify({"message": "Cannot delete publisher with associated editions"}), 400
    
    db.session.delete(publisher)
    db.session.commit()
    
    return jsonify({"message": "Publisher deleted successfully"}), 200