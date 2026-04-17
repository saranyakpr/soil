"""
Soil Vision 360 - Main Application Entry Point
Production-grade Flask application with Blueprint architecture
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models.database import db, init_db
from flask import redirect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def create_app(config_name='development'):

    app = Flask(__name__)

    # SECRET KEY
    app.secret_key = "soilvision360_secret_key"

    # SESSION SETTINGS
    app.config['SESSION_COOKIE_NAME'] = "soilvision_session"
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_PERMANENT'] = True

    # Load configuration
    app.config.from_object(config[config_name])
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    # Initialize extensions
    CORS(app, supports_credentials=True, origins=["http://localhost:5000"])
    db.init_app(app)
    
    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.api import api_bp
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.reports import reports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'message': str(e)}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'message': str(e)}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500
    
    @app.route("/auth/google")
    def google_login():
        return redirect("https://accounts.google.com/o/oauth2/auth")

    @app.route("/auth/github")
    def github_login():
        return redirect("https://github.com/login/oauth/authorize")
    
    # Initialize database tables
    with app.app_context():
        try:
            init_db(app)
        except Exception as e:
            logger.warning(f"Database init warning: {e}")
    
    logger.info("Soil Vision 360 application initialized successfully")
    return app

env = os.environ.get('FLASK_ENV') or (
    'production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'development'
)
app = create_app(env)
logger.info("Runtime PORT environment value: %s", os.environ.get('PORT', 'not set'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(env == 'development'),
        use_reloader=False
    )
