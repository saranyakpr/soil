"""Authentication Blueprint for Soil Vision 360"""

import hashlib
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models.database import db, User
from flask import render_template

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')


@auth_bp.route('/register-page')
def register_page():
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if email exists
        try:
            existing = User.query.filter_by(email=email).first()
            if existing:
                return jsonify({'error': 'Email already registered'}), 409
            
            user = User(name=name, email=email, role='user', is_active=True)
            user.set_password(password)
            user.generate_api_key()
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user': user.to_dict(),
                'api_key': user.api_key
            }), 201
        
        except Exception as db_error:
            db.session.rollback()
            return jsonify({'error': f'Registration failed: {str(db_error)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        try:
            user = User.query.filter_by(email=email, is_active=True).first()
            
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session
            session['user_id'] = user.id
            session['user_role'] = user.role
            session.permanent = True
            
            response = jsonify({
                 'success': True,
                 'message': 'Login successful',
                 'user': user.to_dict(),
                 'api_key': user.api_key
})

            response.set_cookie(
             "soilvision_session",
              str(user.id),
             httponly=True,
             samesite="Lax"
)
        
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user.to_dict(),
                'api_key': user.api_key
            }), 200
        
        except Exception as db_error:
            return jsonify({'error': f'Login failed: {str(db_error)}'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'success': True, 'user': user.to_dict()}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500