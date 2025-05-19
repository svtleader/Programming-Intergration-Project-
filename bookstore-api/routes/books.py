from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Book, Edition, Author, Info, OrderDetail, Order
from utils.auth import admin_required
from sqlalchemy import or_, func, text, desc, distinct
from datetime import datetime, timedelta

books_bp = Blueprint('books', __name__)

@books_bp.route('/books', methods=['GET'])
def get_all_books():
    """
    Get all books with optional filtering
    Optimized to use database indexes
    """
    # Query parameters
    title = request.args.get('title')
    author_id = request.args.get('author_id')
    genre = request.args.get('genre')
    series_id = request.args.get('series_id')
    sort_by = request.args.get('sort_by', 'title')
    order = request.args.get('order', 'asc')
    
    # Base query
    query = Book.query
    
    # Apply filters optimized for indexes
    if title:
        # Use LOWER() to match the case-insensitive index idx_book_title_ci
        query = query.filter(func.lower(Book.Title).like(f'%{title.lower()}%'))
    
    if author_id:
        # Uses the idx_book_authid index
        query = query.filter(Book.AuthID == author_id)
    
    if genre:
        # Join with Info table for genre filtering
        query = query.join(Info, Book.BookID == Info.BookID)
        query = query.filter(Info.Genre.ilike(f'%{genre}%'))
    
    if series_id:
        # Join with Info table for series filtering
        query = query.outerjoin(Info, Book.BookID == Info.BookID)
        query = query.filter(Info.SeriesID == series_id)
    
    # Apply sorting optimized for indexes
    if sort_by == 'title':
        # Uses the idx_book_title_ci index
        if order.lower() == 'desc':
            query = query.order_by(desc(func.lower(Book.Title)))
        else:
            query = query.order_by(func.lower(Book.Title))
    elif sort_by == 'author':
        # Uses the idx_book_authid index in conjunction with author indexes
        query = query.join(Author, Book.AuthID == Author.AuthID)
        if order.lower() == 'desc':
            query = query.order_by(desc(Author.LastName), desc(Author.FirstName))
        else:
            query = query.order_by(Author.LastName, Author.FirstName)
    
    # Execute query
    books = query.all()
    
    return jsonify({
        "count": len(books),
        "books": [book.to_dict_extended() for book in books]
    }), 200

@books_bp.route('/books/bestsellers', methods=['GET'])
def get_bestselling_books():
    """
    Get books with the most orders
    Using joins and indexes for optimal performance
    """
    limit = request.args.get('limit', 10, type=int)
    days = request.args.get('days', 30, type=int)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query for bestsellers using OrderDetails and Edition to join to Book
    query = db.session.query(
        Book,
        func.sum(OrderDetail.Quantity).label('total_sold')
    ).join(
        Edition, Book.BookID == Edition.BookID
    ).join(
        OrderDetail, Edition.ISBN == OrderDetail.ISBN
    ).join(
        Order, OrderDetail.OrderID == Order.OrderID
    ).filter(
        Order.SaleDate.between(start_date, end_date)
    ).group_by(
        Book.BookID
    ).order_by(
        desc('total_sold')
    ).limit(limit)
    
    results = query.all()
    
    return jsonify({
        "count": len(results),
        "bestsellers": [{
            **book.to_dict_extended(),
            "total_sold": total_sold
        } for book, total_sold in results]
    }), 200

@books_bp.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    """
    Get a specific book by ID with sales data
    """
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({"message": "Book not found"}), 404
    
    # Get sales data for this book
    days = request.args.get('days', 30, type=int)
    include_sales = request.args.get('include_sales', 'true').lower() == 'true'
    
    if include_sales:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sales data
        sales_data = db.session.query(
            func.sum(OrderDetail.Quantity).label('total_sold')
        ).join(
            Order, OrderDetail.OrderID == Order.OrderID
        ).join(
            Edition, OrderDetail.ISBN == Edition.ISBN
        ).filter(
            Edition.BookID == book_id,
            Order.SaleDate.between(start_date, end_date)
        ).scalar() or 0
        
        return jsonify({
            "book": book.to_dict_extended(),
            "sales_data": {
                "days": days,
                "total_sold": sales_data
            }
        }), 200
    else:
        return jsonify({"book": book.to_dict_extended()}), 200

@books_bp.route('/books', methods=['POST'])
@jwt_required()
@admin_required
def create_book():
    """
    Create a new book (admin only)
    """
    data = request.get_json()
    
    # Check if required fields are provided
    if 'BookID' not in data or 'Title' not in data:
        return jsonify({"message": "BookID and Title are required"}), 400
    
    # Check if book already exists
    if Book.query.get(data['BookID']):
        return jsonify({"message": "Book with this ID already exists"}), 400
    
    # Create new book
    book = Book(
        BookID=data['BookID'],
        Title=data['Title'],
        AuthID=data.get('AuthID')
    )
    
    db.session.add(book)
    
    # Handle book info if provided
    if 'info' in data:
        info_data = data['info']
        info = Info(
            BookID=book.BookID,
            Genre=info_data.get('Genre'),
            SeriesID=info_data.get('SeriesID'),
            VolumeNumber=info_data.get('VolumeNumber'),
            StaffComment=info_data.get('StaffComment')
        )
        db.session.add(info)
    
    # Handle editions if provided
    if 'editions' in data and isinstance(data['editions'], list):
        for edition_data in data['editions']:
            if 'ISBN' in edition_data:
                edition = Edition(
                    ISBN=edition_data['ISBN'],
                    BookID=book.BookID,
                    Formatt=edition_data.get('Format'),
                    PubID=edition_data.get('PubID'),
                    PublicationDate=edition_data.get('PublicationDate'),
                    Pages=edition_data.get('Pages'),
                    PrintRunSizeK=edition_data.get('PrintRunSizeK'),
                    Price=edition_data.get('Price')
                )
                db.session.add(edition)
    
    db.session.commit()
    
    return jsonify({
        "message": "Book created successfully",
        "book": book.to_dict_extended()
    }), 201

@books_bp.route('/books/<book_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_book(book_id):
    """
    Update a book (admin only)
    """
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({"message": "Book not found"}), 404
    
    data = request.get_json()
    
    # Update book attributes
    if 'Title' in data:
        book.Title = data['Title']
    if 'AuthID' in data:
        book.AuthID = data['AuthID']
    
    # Update book info if provided
    if 'info' in data:
        info_data = data['info']
        info = Info.query.get(book_id)
        
        if info:
            if 'Genre' in info_data:
                info.Genre = info_data['Genre']
            if 'SeriesID' in info_data:
                info.SeriesID = info_data['SeriesID']
            if 'VolumeNumber' in info_data:
                info.VolumeNumber = info_data['VolumeNumber']
            if 'StaffComment' in info_data:
                info.StaffComment = info_data['StaffComment']
        else:
            # Create new info if it doesn't exist
            info = Info(
                BookID=book.BookID,
                Genre=info_data.get('Genre'),
                SeriesID=info_data.get('SeriesID'),
                VolumeNumber=info_data.get('VolumeNumber'),
                StaffComment=info_data.get('StaffComment')
            )
            db.session.add(info)
    
    db.session.commit()
    
    return jsonify({
        "message": "Book updated successfully",
        "book": book.to_dict_extended()
    }), 200

@books_bp.route('/books/<book_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_book(book_id):
    """
    Delete a book (admin only)
    """
    book = Book.query.get(book_id)
    
    if not book:
        return jsonify({"message": "Book not found"}), 404
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({"message": "Book deleted successfully"}), 200

@books_bp.route('/books/search', methods=['GET'])
def search_books():
    """
    Search books by title, author name, or genre
    Optimized to use indexes
    """
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({"message": "Search query must be at least 2 characters"}), 400
    
    # Create a union query for better performance
    # Search by title using idx_book_title_ci
    title_query = db.session.query(Book.BookID).filter(
        func.lower(Book.Title).like(f'%{query.lower()}%')
    )
    
    # Search by author name using author indexes
    author_query = db.session.query(Book.BookID).join(Author).filter(
        or_(
            func.lower(Author.FirstName).like(f'%{query.lower()}%'),
            func.lower(Author.LastName).like(f'%{query.lower()}%')
        )
    )
    
    # Search by genre
    genre_query = db.session.query(Book.BookID).join(Info).filter(
        Info.Genre.ilike(f'%{query}%')
    )
    
    # Combine the queries using UNION
    combined_query = title_query.union(author_query, genre_query)
    
    # Get all BookIDs from the combined query
    book_ids = [book_id for (book_id,) in combined_query.all()]
    
    # Finally, get the complete book objects
    books = Book.query.filter(Book.BookID.in_(book_ids)).all()
    
    return jsonify({
        "count": len(books),
        "books": [book.to_dict_extended() for book in books]
    }), 200

@books_bp.route('/editions/<isbn>', methods=['GET'])
def get_edition(isbn):
    """
    Get a specific edition by ISBN
    Uses the idx_edition_isbn index
    """
    edition = Edition.query.get(isbn)
    
    if not edition:
        return jsonify({"message": "Edition not found"}), 404
    
    return jsonify({
        "edition": edition.to_dict(),
        "book": edition.book.to_dict() if edition.book else None
    }), 200

@books_bp.route('/books/series/<series_id>', methods=['GET'])
def get_series_books(series_id):
    """
    Get all books in a series, sorted by volume number
    Uses the idx_info_seriesid index
    """
    books = Book.query.join(Info).filter(
        Info.SeriesID == series_id
    ).order_by(
        Info.VolumeNumber
    ).all()
    
    if not books:
        return jsonify({
            "count": 0,
            "series_id": series_id,
            "books": []
        }), 200
    
    return jsonify({
        "count": len(books),
        "series_id": series_id,
        "books": [book.to_dict_extended() for book in books]
    }), 200

@books_bp.route('/editions', methods=['GET'])
def get_editions():
    """
    Get editions with filtering capabilities
    Using Edition table indexes
    """
    book_id = request.args.get('book_id')
    format = request.args.get('format')
    publisher_id = request.args.get('publisher_id')
    max_price = request.args.get('max_price', type=float)
    
    query = Edition.query
    
    # Apply filters using indexes where available
    if book_id:
        # Uses idx_edition_bookid
        query = query.filter(Edition.BookID == book_id)
    
    if format:
        query = query.filter(Edition.Formatt.ilike(f'%{format}%'))
    
    if publisher_id:
        query = query.filter(Edition.PubID == publisher_id)
    
    if max_price is not None:
        query = query.filter(Edition.Price <= max_price)
    
    editions = query.all()
    
    return jsonify({
        "count": len(editions),
        "editions": [edition.to_dict() for edition in editions]
    }), 200