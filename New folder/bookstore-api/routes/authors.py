from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Author, Book
from utils.auth import admin_required
from sqlalchemy import func, text, or_

authors_bp = Blueprint('authors', __name__)

@authors_bp.route('/authors', methods=['GET'])
def get_all_authors():
    """
    Get all authors with optional filtering
    Optimized to use case-insensitive indexes
    """
    # Query parameters
    name = request.args.get('name')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    country = request.args.get('country')
    writing_hours = request.args.get('min_writing_hours', type=int)
    
    # Base query
    query = Author.query
    
    # Apply filters optimized for indexes
    if name:
        # Use LOWER() to match the case-insensitive indexes
        query = query.filter(or_(
            func.lower(Author.FirstName).like(f'%{name.lower()}%'),
            func.lower(Author.LastName).like(f'%{name.lower()}%')
        ))
    
    # Separate first_name and last_name filters for better index usage
    if first_name:
        query = query.filter(func.lower(Author.FirstName).like(f'%{first_name.lower()}%'))
    if last_name:
        query = query.filter(func.lower(Author.LastName).like(f'%{last_name.lower()}%'))
    
    if country:
        query = query.filter(Author.CountryOfResidence.ilike(f'%{country}%'))
    
    if writing_hours is not None:
        query = query.filter(Author.HrsWritingPerDay >= writing_hours)
    
    # Add sorting to improve cache hits
    query = query.order_by(Author.LastName, Author.FirstName)
    
    # Execute query
    authors = query.all()
    
    return jsonify({
        "count": len(authors),
        "authors": [author.to_dict() for author in authors]
    }), 200

@authors_bp.route('/authors/prolific', methods=['GET'])
def get_prolific_authors():
    """
    Get authors with the most books published
    """
    limit = request.args.get('limit', 10, type=int)
    
    # Use a subquery to count books per author
    query = db.session.query(
        Author,
        func.count(Book.BookID).label('book_count')
    ).join(
        Book, Author.AuthID == Book.AuthID
    ).group_by(
        Author.AuthID
    ).order_by(
        text('book_count DESC')
    ).limit(limit)
    
    results = query.all()
    
    return jsonify({
        "count": len(results),
        "authors": [{
            **author.to_dict(),
            "book_count": book_count
        } for author, book_count in results]
    }), 200

@authors_bp.route('/authors/<auth_id>', methods=['GET'])
def get_author(auth_id):
    """
    Get a specific author by ID
    """
    author = Author.query.get(auth_id)
    
    if not author:
        return jsonify({"message": "Author not found"}), 404
    
    # Include book count to optimize for common use case
    book_count = Book.query.filter_by(AuthID=auth_id).count()
    
    return jsonify({
        "author": author.to_dict(),
        "book_count": book_count,
        "books": [book.to_dict() for book in author.books]
    }), 200

@authors_bp.route('/authors', methods=['POST'])
@jwt_required()
@admin_required
def create_author():
    """
    Create a new author (admin only)
    """
    data = request.get_json()
    
    # Check if required fields are provided
    if 'AuthID' not in data or 'FirstName' not in data or 'LastName' not in data:
        return jsonify({"message": "AuthID, FirstName, and LastName are required"}), 400
    
    # Check if author already exists
    if Author.query.get(data['AuthID']):
        return jsonify({"message": "Author with this ID already exists"}), 400
    
    # Create new author
    author = Author(
        AuthID=data['AuthID'],
        FirstName=data['FirstName'],
        LastName=data['LastName'],
        Birthday=data.get('Birthday'),
        CountryOfResidence=data.get('CountryOfResidence'),
        HrsWritingPerDay=data.get('HrsWritingPerDay')
    )
    
    db.session.add(author)
    db.session.commit()
    
    return jsonify({
        "message": "Author created successfully",
        "author": author.to_dict()
    }), 201

@authors_bp.route('/authors/<auth_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_author(auth_id):
    """
    Update an author (admin only)
    """
    author = Author.query.get(auth_id)
    
    if not author:
        return jsonify({"message": "Author not found"}), 404
    
    data = request.get_json()
    
    # Update author attributes
    if 'FirstName' in data:
        author.FirstName = data['FirstName']
    if 'LastName' in data:
        author.LastName = data['LastName']
    if 'Birthday' in data:
        author.Birthday = data['Birthday']
    if 'CountryOfResidence' in data:
        author.CountryOfResidence = data['CountryOfResidence']
    if 'HrsWritingPerDay' in data:
        author.HrsWritingPerDay = data['HrsWritingPerDay']
    
    db.session.commit()
    
    return jsonify({
        "message": "Author updated successfully",
        "author": author.to_dict()
    }), 200

@authors_bp.route('/authors/<auth_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_author(auth_id):
    """
    Delete an author (admin only)
    """
    author = Author.query.get(auth_id)
    
    if not author:
        return jsonify({"message": "Author not found"}), 404
    
    # Check if author has any books
    if author.books:
        return jsonify({"message": "Cannot delete author with associated books"}), 400
    
    db.session.delete(author)
    db.session.commit()
    
    return jsonify({"message": "Author deleted successfully"}), 200

@authors_bp.route('/authors/search', methods=['GET'])
def search_authors():
    """
    Advanced search for authors optimized for indexes
    """
    query = request.args.get('q', '')
    country = request.args.get('country')
    min_books = request.args.get('min_books', type=int)
    
    if not query and not country and min_books is None:
        return jsonify({"message": "At least one search parameter is required"}), 400
    
    # Base query
    base_query = Author.query
    
    # Apply name search using indexed fields
    if query:
        base_query = base_query.filter(or_(
            func.lower(Author.FirstName).like(f'%{query.lower()}%'),
            func.lower(Author.LastName).like(f'%{query.lower()}%')
        ))
    
    # Apply country filter
    if country:
        base_query = base_query.filter(Author.CountryOfResidence.ilike(f'%{country}%'))
    
    # Apply minimum books filter if needed
    if min_books is not None:
        author_ids = db.session.query(
            Book.AuthID,
            func.count(Book.BookID).label('book_count')
        ).group_by(
            Book.AuthID
        ).having(
            func.count(Book.BookID) >= min_books
        ).all()
        
        # Extract author IDs that meet the criteria
        valid_auth_ids = [auth_id for auth_id, _ in author_ids]
        
        if valid_auth_ids:
            base_query = base_query.filter(Author.AuthID.in_(valid_auth_ids))
        else:
            # No authors meet the min_books criteria
            return jsonify({"count": 0, "authors": []}), 200
    
    # Execute query
    authors = base_query.order_by(Author.LastName, Author.FirstName).all()
    
    # If min_books was specified, include book count in response
    if min_books is not None:
        # Get book count for each author
        author_book_counts = {
            auth_id: count for auth_id, count in 
            db.session.query(
                Book.AuthID,
                func.count(Book.BookID).label('count')
            ).filter(
                Book.AuthID.in_([a.AuthID for a in authors])
            ).group_by(
                Book.AuthID
            ).all()
        }
        
        # Add book count to author data
        author_data = [
            {**author.to_dict(), "book_count": author_book_counts.get(author.AuthID, 0)}
            for author in authors
        ]
    else:
        author_data = [author.to_dict() for author in authors]
    
    return jsonify({
        "count": len(authors),
        "authors": author_data
    }), 200