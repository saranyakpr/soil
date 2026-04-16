"""Reports Blueprint - PDF generation and report viewing"""

import os
import io
import logging
from flask import Blueprint, request, jsonify, send_file, current_app, render_template
from models.database import db, SoilReport

reports_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)


@reports_bp.route('/generate', methods=['POST'])
def generate_pdf():
    """Generate PDF report for a soil analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Analysis data required'}), 400
        
        soil_id = data.get('soil_id', 'DEMO')
        analysis_data = data.get('analysis', data)
        image_path = data.get('image_path')
        
        # Resolve absolute image path
        abs_image_path = None
        if image_path:
            if image_path.startswith('/static/'):
                abs_image_path = os.path.join(
                    os.path.dirname(current_app.root_path),
                    'static',
                    image_path.replace('/static/', '')
                )
            elif os.path.exists(image_path):
                abs_image_path = image_path
        
        # Generate output path
        reports_folder = current_app.config.get('REPORTS_FOLDER', '/tmp')
        os.makedirs(reports_folder, exist_ok=True)
        output_path = os.path.join(reports_folder, f"soil_report_{soil_id}.pdf")
        
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        
        try:
            from utils.pdf_generator import generate_soil_report
            pdf_bytes = generate_soil_report(
                analysis_data=analysis_data,
                image_path=abs_image_path,
                output_path=output_path,
                base_url=base_url
            )
            
            return send_file(
                io.BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"Soil_Vision_360_Report_{soil_id}.pdf",
                mimetype='application/pdf'
            )
        
        except ImportError as imp_err:
            logger.warning(f"PDF generation libraries not available: {imp_err}")
            # Generate simple text-based report as fallback
            return _generate_simple_report(analysis_data, soil_id)
    
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500


def _generate_simple_report(analysis, soil_id):
    """Generate a simple HTML-based report as fallback"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Soil Report {soil_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #1a1a2e; }}
        .score {{ display: inline-block; padding: 5px 15px; background: #e8f5e9; border-radius: 4px; margin: 5px; }}
    </style>
    </head>
    <body>
    <h1>Soil Vision 360 - Analysis Report</h1>
    <p><b>Soil ID:</b> {soil_id}</p>
    <p><b>Soil Type:</b> {analysis.get('soil_type', 'N/A')}</p>
    <p><b>Water Retention:</b> <span class="score">{analysis.get('water_retention', 0)}%</span></p>
    <p><b>Crop Compatibility:</b> <span class="score">{analysis.get('crop_score', 0)}%</span></p>
    <p><b>Construction Score:</b> <span class="score">{analysis.get('construction_score', 0)}%</span></p>
    <p><b>Heat Index:</b> <span class="score">{analysis.get('heat_index', 0)}%</span></p>
    <p><b>Land Potential:</b> <span class="score">{analysis.get('land_potential_score', 0)}%</span></p>
    </body>
    </html>
    """
    return send_file(
        io.BytesIO(html.encode()),
        as_attachment=True,
        download_name=f"Soil_Report_{soil_id}.html",
        mimetype='text/html'
    )


@reports_bp.route('/view/<string:soil_id>', methods=['GET'])
def view_report(soil_id):
    """View a report by soil ID — returns HTML page or JSON based on Accept header"""
    try:
        # If browser request, serve the report HTML page
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            from flask import render_template
            return render_template('report.html')
        
        # API request — return JSON
        report = SoilReport.query.filter_by(soil_id=soil_id).first()
        if not report:
            return jsonify({'error': 'Report not found', 'soil_id': soil_id}), 404
        return jsonify({'success': True, 'data': report.to_dict()}), 200
    except Exception as e:
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            from flask import render_template
            return render_template('report.html')
        return jsonify({'success': True, 'data': {'soil_id': soil_id, 'note': 'Demo mode'}}), 200


@reports_bp.route('/report/<string:soil_id>', methods=['GET'])
def report_page(soil_id):
    """Serve the full report HTML page"""
    from flask import render_template
    return render_template('report.html')