from flask import Blueprint

def register_routes(app):
    """
    Register all API routes with Flask application
    """
    from .auth import auth_bp
    from .books import books_bp
    from .orders import orders_bp
    from .authors import authors_bp
    from .publishers import publishers_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix=app.config['API_PREFIX'])
    app.register_blueprint(books_bp, url_prefix=app.config['API_PREFIX'])
    app.register_blueprint(orders_bp, url_prefix=app.config['API_PREFIX'])
    app.register_blueprint(authors_bp, url_prefix=app.config['API_PREFIX'])
    app.register_blueprint(publishers_bp, url_prefix=app.config['API_PREFIX'])