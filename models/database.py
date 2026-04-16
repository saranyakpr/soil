"""
Database models for Soil Vision 360
SQLAlchemy ORM models with proper relationships
"""

import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model with authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('user', 'admin', 'analyst'), default='user')
    api_key = db.Column(db.String(64), unique=True, index=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    # Relationships
    soil_reports = db.relationship('SoilReport', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        self.password_hash = f"{salt}:{pwd_hash}"
    
    def check_password(self, password):
        """Verify password"""
        if ':' not in self.password_hash:
            return False
        salt, pwd_hash = self.password_hash.split(':', 1)
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest() == pwd_hash
    
    def generate_api_key(self):
        """Generate unique API key"""
        self.api_key = secrets.token_hex(32)
        return self.api_key
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f"<User {self.email}>"


class SoilReport(db.Model):
    """Soil analysis report model"""
    __tablename__ = 'soil_reports'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    soil_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    soil_type = db.Column(db.String(50), nullable=False)
    soil_code = db.Column(db.String(10), nullable=False)
    
    # Color analysis
    avg_red = db.Column(db.Integer, default=0)
    avg_green = db.Column(db.Integer, default=0)
    avg_blue = db.Column(db.Integer, default=0)
    
    # Core scores
    water_retention = db.Column(db.Integer, default=0)
    crop_score = db.Column(db.Integer, default=0)
    construction_score = db.Column(db.Integer, default=0)
    heat_index = db.Column(db.Integer, default=0)
    
    # Advanced analytics
    land_potential_score = db.Column(db.Integer, default=0)
    agriculture_roi = db.Column(db.Float, default=0.0)
    construction_risk = db.Column(db.String(20), default='Low')
    flood_risk = db.Column(db.String(20), default='Low')
    
    # Metadata
    image_path = db.Column(db.String(255), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'soil_id': self.soil_id,
            'soil_type': self.soil_type,
            'soil_code': self.soil_code,
            'color': {'r': self.avg_red, 'g': self.avg_green, 'b': self.avg_blue},
            'water_retention': self.water_retention,
            'crop_score': self.crop_score,
            'construction_score': self.construction_score,
            'heat_index': self.heat_index,
            'land_potential_score': self.land_potential_score,
            'agriculture_roi': self.agriculture_roi,
            'construction_risk': self.construction_risk,
            'flood_risk': self.flood_risk,
            'image_path': self.image_path,
            'district': self.district,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat()
        }

class DistrictSoilData(db.Model):
    """Aggregated district soil data for map visualization"""
    __tablename__ = 'district_soil_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    district_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    dominant_soil_type = db.Column(db.String(50), nullable=True)
    black_count = db.Column(db.Integer, default=0)
    red_count = db.Column(db.Integer, default=0)
    yellow_count = db.Column(db.Integer, default=0)
    brown_count = db.Column(db.Integer, default=0)
    total_analyses = db.Column(db.Integer, default=0)
    avg_land_potential = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'district': self.district_name,
            'dominant_soil': self.dominant_soil_type,
            'counts': {
                'black': self.black_count,
                'red': self.red_count,
                'yellow': self.yellow_count,
                'brown': self.brown_count
            },
            'total': self.total_analyses,
            'avg_potential': self.avg_land_potential
        }

class ClimateRecord(db.Model):
    """Climate change impact records for trend analysis"""
    __tablename__ = 'climate_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    district = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    avg_rainfall_mm = db.Column(db.Float, default=0.0)
    avg_temp_celsius = db.Column(db.Float, default=0.0)
    drought_risk_index = db.Column(db.Float, default=0.0)
    flood_risk_index = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db(app):
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@soilvision360.com').first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@soilvision360.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            admin.generate_api_key()
            db.session.add(admin)
            db.session.commit()
        
       

