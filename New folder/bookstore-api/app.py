from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enhanced CORS configuration 
    cors = CORS(app, 
        resources={r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }}
    )

    db.init_app(app)

    # Add a test route to verify API is accessible
    @app.route('/api/v1/test', methods=['GET'])
    def test_route():
        return jsonify({"message": "API is working!"}), 200

    # Initialize extensions

    jwt = JWTManager(app)

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.books import books_bp
    from routes.authors import authors_bp
    from routes.orders import orders_bp
    from routes.publishers import publishers_bp

    # Register blueprints with the API prefix from Config
    app.register_blueprint(auth_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(books_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(authors_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(orders_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(publishers_bp, url_prefix=Config.API_PREFIX)

    # Add error handler for debugging
    @app.errorhandler(Exception)
    def handle_error(e):
        print(f"Error: {str(e)}")

        # CORS or credential-related issues
        if hasattr(e, "code") and e.code == 403:
            return jsonify({"message": "Forbidden: CORS or credential error"}), 403
        
        return jsonify({"message": f"Server error: {str(e)}"}), 500

    if __name__ == "__main__":
        # Print all registered routes for debugging
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule} - {rule.methods}")
        print()
        
        # Run the app
        app.run(host="0.0.0.0", port=5000, debug=True)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)