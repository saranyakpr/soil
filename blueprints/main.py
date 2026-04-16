"""Main blueprint - serves the frontend"""
from flask import Blueprint, render_template, send_from_directory
import os

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/admin')
def admin_page():
    return render_template('admin.html')

@main_bp.route('/analyze')
def analyze_page():
    return render_template('analyze.html')

@main_bp.route('/health')
def health():
    return {'status': 'healthy', 'service': 'Soil Vision 360'}, 200