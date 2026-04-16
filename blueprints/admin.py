"""Admin Blueprint for Soil Vision 360"""
from flask import Blueprint, jsonify, request, session
from models.database import db, User, SoilReport

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify({'success': True, 'data': [u.to_dict() for u in users]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/reports/recent', methods=['GET'])
def get_recent_reports():
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        reports = SoilReport.query.order_by(SoilReport.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [r.to_dict() for r in reports]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500