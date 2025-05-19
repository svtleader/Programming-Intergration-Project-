from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Order, OrderDetail, Edition, Book
from utils.auth import admin_required
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, text

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    order_id = request.args.get('order_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    # New filters
    isbn = request.args.get('isbn')
    book_id = request.args.get('book_id')
    date_range_only = request.args.get('date_range_only', 'false').lower() == 'true'
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 5), 100)  # Minimum 5, maximum 100

    query = Order.query

    # Using fulltext index for OrderID search
    if order_id:
        # Use MySQL's MATCH AGAINST for fulltext search on OrderID
        # This will utilize the idx_orders_orderid_fulltext index
        query = query.filter(text("MATCH(OrderID) AGAINST(:order_id IN BOOLEAN MODE)").bindparams(order_id=f'*{order_id}*'))

    # Date range search using idx_orders_saledate or idx_orders_date_id
    if start_date and end_date and date_range_only:
        # When only filtering by date range, use idx_orders_saledate
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.SaleDate.between(start, end))
        except ValueError:
            return jsonify({"message": "Invalid date format. Expected YYYY-MM-DD"}), 422
    else:
        # Individual date filters that can be combined with other filters
        if start_date:
            try:
                if start_date.strip():
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    query = query.filter(Order.SaleDate >= start)
            except ValueError:
                return jsonify({"message": "Invalid start_date format. Expected YYYY-MM-DD"}), 422

        if end_date:
            try:
                if end_date.strip():
                    end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(Order.SaleDate <= end)
            except ValueError:
                return jsonify({"message": "Invalid end_date format. Expected YYYY-MM-DD"}), 422

    # ISBN filter using join and idx_orderdetails_isbn
    if isbn:
        query = query.join(OrderDetail, Order.OrderID == OrderDetail.OrderID).filter(OrderDetail.ISBN == isbn)

    # Book ID filter requiring joins through Edition table
    if book_id:
        query = query.join(OrderDetail, Order.OrderID == OrderDetail.OrderID) \
                    .join(Edition, OrderDetail.ISBN == Edition.ISBN) \
                    .filter(Edition.BookID == book_id)

    # Ensure results are distinct when using joins
    if isbn or book_id:
        query = query.distinct()

    # Apply sorting to utilize composite index
    query = query.order_by(Order.SaleDate, Order.OrderID)
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination - important to do this AFTER the counting
    query = query.offset((page - 1) * per_page).limit(per_page)

    orders = query.all()

    return jsonify({
        "count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,  # Ceiling division
        "orders": [order.to_dict() for order in orders]
    }), 200

@orders_bp.route('/orders/search', methods=['GET'])
@jwt_required()
def search_orders():
    """
    Advanced search endpoint that combines multiple filters
    and makes optimal use of database indexes with pagination
    """
    search_term = request.args.get('search', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    isbn = request.args.get('isbn')
    min_quantity = request.args.get('min_quantity', type=int)
    book_title = request.args.get('book_title')
    author_last_name = request.args.get('author_last_name')
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 5), 100)  # Minimum 5, maximum 100
    
    # Start with a base query joining orders and order details
    query = db.session.query(Order).distinct()
    
    # Apply search term to OrderID using fulltext index
    if search_term:
        query = query.filter(text("MATCH(Orders.OrderID) AGAINST(:term IN BOOLEAN MODE)").bindparams(term=f'*{search_term}*'))
    
    # Apply date range filters using date index
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.SaleDate >= start)
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Expected YYYY-MM-DD"}), 422

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.SaleDate <= end)
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Expected YYYY-MM-DD"}), 422
    
    # Join tables and apply additional filters
    if isbn or min_quantity or book_title or author_last_name:
        query = query.join(OrderDetail, Order.OrderID == OrderDetail.OrderID)
        
        if isbn:
            query = query.filter(OrderDetail.ISBN == isbn)
            
        if min_quantity:
            query = query.filter(OrderDetail.Quantity >= min_quantity)
            
        if book_title or author_last_name:
            query = query.join(Edition, OrderDetail.ISBN == Edition.ISBN)
            query = query.join(Book, Edition.BookID == Book.BookID)
            
            if book_title:
                # Use the idx_book_title_ci index for case-insensitive title search
                query = query.filter(func.lower(Book.Title).like(f'%{book_title.lower()}%'))
                
            if author_last_name:
                # Use the idx_book_authid index to join to Author and then use idx_author_lastname_ci
                from models import Author
                query = query.join(Author, Book.AuthID == Author.AuthID)
                query = query.filter(func.lower(Author.LastName).like(f'%{author_last_name.lower()}%'))
    
    # Get total count for pagination before applying limits
    total_count = query.count()
    
    # Apply sorting to utilize composite index
    query = query.order_by(Order.SaleDate, Order.OrderID)
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    orders = query.all()
    
    return jsonify({
        "count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,  # Ceiling division
        "orders": [order.to_dict() for order in orders]
    }), 200

# Keep the rest of the original methods
@orders_bp.route('/orders/summary', methods=['GET'])
@jwt_required()
def get_orders_summary():
    """
    Get summary statistics for orders with optional date range filter
    Utilizes the idx_orders_saledate index
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(
        func.date_format(Order.SaleDate, '%Y-%m').label('month'),
        func.count().label('order_count'),
        func.sum(OrderDetail.Quantity).label('total_items')
    ).join(OrderDetail, Order.OrderID == OrderDetail.OrderID)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.SaleDate >= start)
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Expected YYYY-MM-DD"}), 422

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.SaleDate <= end)
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Expected YYYY-MM-DD"}), 422
    
    result = query.group_by(func.date_format(Order.SaleDate, '%Y-%m')).order_by(text('month')).all()
    
    return jsonify({
        "summary": [{"month": item.month, "order_count": item.order_count, "total_items": item.total_items} for item in result]
    }), 200

@orders_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"message": "Order not found"}), 404

    return jsonify({"order": order.to_dict()}), 200

@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json()

    if 'OrderID' not in data:
        return jsonify({"message": "OrderID is required"}), 400

    try:
        with db.session.begin_nested():
            order = Order(
                OrderID=data['OrderID'],
                SaleDate=data.get('SaleDate', datetime.now().strftime('%Y-%m-%d'))
            )
            db.session.add(order)

            if 'items' in data and isinstance(data['items'], list):
                order_details = []
                for i, item_data in enumerate(data['items']):
                    if 'ISBN' in item_data:
                        edition = Edition.query.get(item_data['ISBN'])
                        if not edition:
                            raise ValueError(f"ISBN {item_data['ISBN']} not found")

                        item_id = item_data.get('ItemID', f"{i+1}")
                        quantity = item_data.get('Quantity', 1)

                        order_details.append({
                            "OrderID": order.OrderID,
                            "ItemID": item_id,
                            "ISBN": item_data['ISBN'],
                            "Quantity": quantity
                        })

                if order_details:
                    db.session.bulk_insert_mappings(OrderDetail, order_details)

        db.session.commit()
        return jsonify({"message": "Order created successfully", "order": order.to_dict()}), 201

    except (SQLAlchemyError, ValueError) as e:
        db.session.rollback()
        return jsonify({"message": f"Error creating order: {str(e)}"}), 400

@orders_bp.route('/orders/<order_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_order(order_id):
    data = request.get_json()
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"message": "Order not found"}), 404

    if 'SaleDate' in data:
        order.SaleDate = data['SaleDate']

    items = data.get('items', [])
    isbns = [item.get('ISBN') for item in items if 'ISBN' in item]
    valid_editions = Edition.query.filter(Edition.ISBN.in_(isbns)).all()
    valid_isbn_set = {edition.ISBN for edition in valid_editions}

    invalid_isbns = [isbn for isbn in isbns if isbn not in valid_isbn_set]
    if invalid_isbns:
        return jsonify({"message": f"Invalid ISBNs: {', '.join(invalid_isbns)}"}), 400

    OrderDetail.query.filter_by(OrderID=order_id).delete()

    new_order_details = [
        OrderDetail(
            OrderID=order_id,
            ItemID=item.get('ItemID', str(index + 1)),
            ISBN=item['ISBN'],
            Quantity=item.get('Quantity', 1)
        )
        for index, item in enumerate(items) if item['ISBN'] in valid_isbn_set
    ]

    db.session.bulk_save_objects(new_order_details)
    db.session.commit()

    return jsonify({
        "message": "Order updated successfully",
        "order": order.to_dict()
    }), 200

@orders_bp.route('/orders/<order_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_order(order_id):
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"message": "Order not found"}), 404

    try:
        # Delete associated OrderDetails first
        OrderDetail.query.filter_by(OrderID=order_id).delete()

        # Delete the Order
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({"message": "Order deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting order: {str(e)}"}), 500

@orders_bp.route('/orders/by-isbn/<isbn>', methods=['GET'])
@jwt_required()
def get_orders_by_isbn(isbn):
    """
    Get all orders containing a specific ISBN
    Utilizes the idx_orderdetails_isbn index
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 5), 100)  # Minimum 5, maximum 100
    
    # Build query using the ISBN index
    query = Order.query.join(OrderDetail).filter(OrderDetail.ISBN == isbn)
    
    # Apply date filtering if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.SaleDate >= start)
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Expected YYYY-MM-DD"}), 422

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.SaleDate <= end)
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Expected YYYY-MM-DD"}), 422
    
    # Get total count for pagination
    total_count = query.count()
    
    # Sort by date to use composite index
    query = query.order_by(Order.SaleDate)
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    orders = query.all()
    
    return jsonify({
        "isbn": isbn,
        "count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
        "orders": [order.to_dict() for order in orders]
    }), 200

@orders_bp.route('/orders/books-sold/<book_id>', methods=['GET'])
@jwt_required()
def get_books_sold(book_id):
    """
    Get sales information for a specific book across all its editions
    Using indexes on Edition.BookID and OrderDetails.ISBN
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # First get all ISBNs for this book
    editions = Edition.query.filter_by(BookID=book_id).all()
    if not editions:
        return jsonify({"message": "No editions found for this book ID"}), 404
    
    # Get the book details
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404
    
    # Build a query using these ISBNs
    isbn_list = [edition.ISBN for edition in editions]
    
    # Query for order count and total quantity
    query = db.session.query(
        OrderDetail.ISBN,
        func.count(Order.OrderID).label('order_count'),
        func.sum(OrderDetail.Quantity).label('total_quantity')
    ).join(
        Order, OrderDetail.OrderID == Order.OrderID
    ).filter(
        OrderDetail.ISBN.in_(isbn_list)
    )
    
    # Apply date filtering if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.SaleDate >= start)
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Expected YYYY-MM-DD"}), 422

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Order.SaleDate <= end)
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Expected YYYY-MM-DD"}), 422
    
    # Group and get results
    results = query.group_by(OrderDetail.ISBN).all()
    
    # Format the results
    editions_data = {
        edition.ISBN: {
            "format": edition.Formatt,
            "price": float(edition.Price),
            "publication_date": edition.PublicationDate.strftime('%Y-%m-%d') if edition.PublicationDate else None
        } for edition in editions
    }
    
    sales_data = {}
    for isbn, order_count, total_quantity in results:
        sales_data[isbn] = {
            "order_count": order_count,
            "total_quantity": total_quantity,
            **editions_data.get(isbn, {})
        }
    
    # Add editions with no sales
    for isbn in isbn_list:
        if isbn not in sales_data:
            sales_data[isbn] = {
                "order_count": 0,
                "total_quantity": 0,
                **editions_data.get(isbn, {})
            }
    
    return jsonify({
        "book_id": book_id,
        "title": book.Title,
        "sales_by_edition": sales_data,
        "total_editions": len(isbn_list),
        "total_orders": sum(data["order_count"] for data in sales_data.values()),
        "total_books_sold": sum(data["total_quantity"] for data in sales_data.values())
    }), 200