"""
Core API Blueprint for Soil Vision 360
REST API v1 endpoints for soil analysis
"""

import os
import uuid
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models.database import db, SoilReport,User
from utils.soil_analyzer import get_crop_growth_simulation
from models.soil_model import analyze_soil_image
import requests
import re

def clean_tamil(text):
    # remove only full english words, keep numbers & symbols
    return re.sub(r'\b[A-Za-z]{2,}\b', '', text)

def ask_huggingface(prompt, lang="en"):
    api_key = (
        current_app.config.get("HUGGINGFACE_API_KEY")
        or os.environ.get("HUGGINGFACE_API_KEY")
        or os.environ.get("HF_TOKEN")
    )
    api_key = api_key.strip() if api_key else ""
    if not api_key:
        logger.warning("Hugging Face request skipped: missing HUGGINGFACE_API_KEY or HF_TOKEN")
        return None

    try:
        base_url = current_app.config.get(
            "HUGGINGFACE_BASE_URL",
            "https://router.huggingface.co/v1",
        ).rstrip("/")
        model = current_app.config.get(
            "HUGGINGFACE_MODEL",
            "Qwen/Qwen2.5-7B-Instruct:fastest",
        ).strip()
        timeout = current_app.config.get("HUGGINGFACE_TIMEOUT", 30)
        system_prompt = (
            "You are SoilBot 360, a professional civil engineering and soil "
            "science assistant. Give concise practical answers. Reply in "
            f"{'Tamil' if lang == 'ta' else 'English'}."
        )

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 220,
                "stream": False,
            },
            timeout=timeout,
        )
        if not response.ok:
            logger.warning(
                "Hugging Face request failed with status %s: %s",
                response.status_code,
                response.text[:500],
            )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            logger.warning("Hugging Face response did not include choices: %s", data)
            return None

        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return content.strip()
        return choices[0].get("text")

    except Exception as e:
        logger.warning(f"Hugging Face request failed: {e}")
        return None

soil_layers = {

 "Red Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Red Sandy Soil"},
  {"depth_start":0.5,"depth_end":2,"layer":"Sandy Clay"},
  {"depth_start":2,"depth_end":4,"layer":"Laterite Layer"},
  {"depth_start":4,"depth_end":10,"layer":"Rock"}
 ],

 "Black Soil":[
  {"depth_start":0,"depth_end":0.4,"layer":"Black Clay"},
  {"depth_start":0.4,"depth_end":1.5,"layer":"Dense Clay"},
  {"depth_start":1.5,"depth_end":4,"layer":"Hard Clay"},
  {"depth_start":4,"depth_end":10,"layer":"Basalt Rock"}
 ],

 "Alluvial Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Topsoil"},
  {"depth_start":0.5,"depth_end":2,"layer":"Silty Clay"},
  {"depth_start":2,"depth_end":5,"layer":"Sand"},
  {"depth_start":5,"depth_end":10,"layer":"Rock"}
 ],

 "Clay Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Soft Clay"},
  {"depth_start":0.5,"depth_end":2,"layer":"Sticky Clay"},
  {"depth_start":2,"depth_end":5,"layer":"Dense Clay"},
  {"depth_start":5,"depth_end":10,"layer":"Rock"}
 ],

 "Cinder Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Volcanic Ash"},
  {"depth_start":0.5,"depth_end":2,"layer":"Porous Cinder"},
  {"depth_start":2,"depth_end":5,"layer":"Lava Rock"},
  {"depth_start":5,"depth_end":10,"layer":"Bedrock"}
 ],

 "Laterite Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Laterite Topsoil"},
  {"depth_start":0.5,"depth_end":2,"layer":"Iron Rich Laterite"},
  {"depth_start":2,"depth_end":5,"layer":"Hard Laterite"},
  {"depth_start":5,"depth_end":10,"layer":"Rock"}
 ],

 "Peat Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Organic Peat"},
  {"depth_start":0.5,"depth_end":2,"layer":"Wet Peat"},
  {"depth_start":2,"depth_end":5,"layer":"Dark Organic Soil"},
  {"depth_start":5,"depth_end":10,"layer":"Clay Base"}
 ],

 "Yellow Soil":[
  {"depth_start":0,"depth_end":0.5,"layer":"Yellow Sandy Soil"},
  {"depth_start":0.5,"depth_end":2,"layer":"Yellow Clay"},
  {"depth_start":2,"depth_end":5,"layer":"Weathered Rock"},
  {"depth_start":5,"depth_end":10,"layer":"Bedrock"}
 ]
}

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def get_optional_db():
    """Try to use database, return None if unavailable"""
    try:
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# SOIL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/analyze', methods=['POST'])
def analyze_soil():
    """
    Analyze uploaded soil image
    Returns complete soil analysis with all scores
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        # Save uploaded file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Get optional metadata
        user_id = request.form.get('user_id')
        lang = request.form.get("lang", "en")
        
        # Analyze soil
        analysis = analyze_soil_image(filepath)
        # 🔥 FIX: normalize construction data
        ca = analysis.get("construction_advice", {})

        analysis["construction"] = {
         "foundation": ca.get("foundation_type", "foundation_reinforced_raft"),
         "suitability": ca.get("suitability", "construction_moderate"),
         "cost_factor": ca.get("estimated_cost_factor", 1)
        }

        soil_type = analysis.get("soil_type")
        confidence = analysis.get("confidence", 0)

        analysis["model_prediction"] = soil_type
        analysis["confidence"] = confidence
        soil_type = analysis.get("soil_type","").strip().title()

        soil_mapping = {
          "Clay": "Clay Soil",
          "Alluvial": "Alluvial Soil",
          "Red": "Red Soil",
          "Black": "Black Soil",
          "Cinder": "Cinder Soil",
          "Laterite": "Laterite Soil",
          "Peat": "Peat Soil",
          "Yellow": "Yellow Soil"
        }

        soil_type = soil_mapping.get(soil_type, soil_type)

        analysis['soil_type'] = soil_type
        analysis['layers'] = soil_layers.get(soil_type, [])

        from utils.translator import translate_analysis

        analysis = translate_analysis(analysis, lang)

        print("Detected soil:", soil_type)
        print("Layers:", analysis['layers'])

        analysis['image_path'] = f"/static/uploads/{filename}"
        analysis['image_filename'] = filename
        
    
        
        # Store in database (graceful fallback if DB unavailable)
        db_available = get_optional_db()
        if db_available:
            try:
                report = SoilReport(
                    soil_id=analysis['soil_id'],
                    soil_type=analysis['soil_type'],
                    soil_code=analysis['soil_code'],
                    avg_red=analysis['avg_rgb']['r'],
                    avg_green=analysis['avg_rgb']['g'],
                    avg_blue=analysis['avg_rgb']['b'],
                    water_retention=analysis['water_retention'],
                    crop_score=analysis['crop_score'],
                    construction_score=analysis['construction_score'],
                    heat_index=analysis['heat_index'],
                    land_potential_score=analysis['land_potential_score'],
                    agriculture_roi=analysis['agriculture_roi'],
                    construction_risk=analysis['construction_risk'],
                    flood_risk=analysis['flood_risk'],
                    image_path=analysis['image_path'],
                    user_id=int(user_id) if user_id else None
                )
                db.session.add(report)
                
                db.session.commit()
                analysis['db_id'] = report.id
                
            except Exception as e:
                logger.warning(f"DB write failed (non-fatal): {e}")
                db.session.rollback()
        
        logger.info(f"Soil analysis complete: {analysis['soil_id']} - {analysis['soil_type']}")
        return jsonify({'success': True, 'data': analysis}), 200
    
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({'error': 'Analysis failed', 'message': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/reports', methods=['GET'])
def get_reports():
    """Get paginated soil reports"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        soil_type_filter = request.args.get('soil_type')
        
        db_available = get_optional_db()
        if not db_available:
            return jsonify({'error': 'Database unavailable'}), 503
        
        query = SoilReport.query.order_by(SoilReport.created_at.desc())
        
        if soil_type_filter:
            query = query.filter(SoilReport.soil_type.ilike(f'%{soil_type_filter}%'))
        
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/reports/<string:soil_id>', methods=['GET'])
def get_report(soil_id):
    """Get specific report by soil ID"""
    try:
        db_available = get_optional_db()
        if not db_available:
            return jsonify({'error': 'Database unavailable'}), 503
        
        report = SoilReport.query.filter_by(soil_id=soil_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({'success': True, 'data': report.to_dict()}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CROP SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/simulate/crop', methods=['POST'])
def simulate_crop():
    """Simulate crop growth based on soil scores"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        crop_name = data.get('crop', 'Wheat')
        crop_score = int(data.get('crop_score', 70))
        water_retention = int(data.get('water_retention', 70))
        
        simulation = get_crop_growth_simulation(crop_name, crop_score, water_retention)
        return jsonify({'success': True, 'data': simulation}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Admin dashboard statistics"""
    try:
        db_available = get_optional_db()
        
        if db_available:
            total_analyses = SoilReport.query.count()
            total_users = User.query.count()
            
            # Soil type distribution
            from sqlalchemy import func
            distribution = db.session.query(
                SoilReport.soil_type,
                func.count(SoilReport.id).label('count')
            ).group_by(SoilReport.soil_type).all()
            
            soil_dist = {row[0]: row[1] for row in distribution}
            
            # Average scores
            avg_data = db.session.query(
                func.avg(SoilReport.water_retention),
                func.avg(SoilReport.crop_score),
                func.avg(SoilReport.construction_score),
                func.avg(SoilReport.heat_index),
                func.avg(SoilReport.land_potential_score)
            ).first()
            
            stats = {
                'total_analyses': total_analyses,
                'total_users': total_users,
                'soil_distribution': soil_dist,
                'averages': {
                    'water_retention': round(avg_data[0] or 0, 1),
                    'crop_score': round(avg_data[1] or 0, 1),
                    'construction_score': round(avg_data[2] or 0, 1),
                    'heat_index': round(avg_data[3] or 0, 1),
                    'land_potential': round(avg_data[4] or 0, 1)
                }
            }
        else:
            # Demo stats
            stats = {
                'total_analyses': 1248,
                'total_users': 342,
                'soil_distribution': {
                    'Black Soil': 387,
                    'Red Soil': 412,
                    'Clay Soil': 218,
                    'Alluvial Soil': 231,
                    'Cinder Soil': 150,
                    'Laterite Soil': 120,
                    'Peat Soil': 90,
                    'Yellow Soil': 170
                },
                'averages': {
                    'water_retention': 64.2,
                    'crop_score': 71.5,
                    'construction_score': 59.8,
                    'heat_index': 72.3,
                    'land_potential': 65.4
                }
            }
        
        return jsonify({'success': True, 'data': stats}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT
# ─────────────────────────────────────────────────────────────────────────────
@api_bp.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    message = data.get('message', '')
    soil_type = data.get('soil_type', 'Unknown')
    construction_score = data.get('construction_score', 50)
    crop_score = data.get('crop_score', 50)
    lang = data.get("lang", "en")

    # 1. முதலில் உங்கள் Rules (விதிமுறைகள்) மூலம் பதில் தேடவும்
    rule_reply = _generate_chatbot_response(message, soil_type, construction_score, crop_score)
    if rule_reply:
        return jsonify({"success": True, "response": rule_reply})

    # 2. If rules do not answer it, ask Hugging Face.
    prompt = f"""
    Act as a professional Civil Engineer and Soil Expert.
    User Question: {message}
    Context: The soil type is {soil_type}.
    Instruction: Give a direct, technical, and helpful answer in 2 lines.
    Language: {'Tamil' if lang=='ta' else 'English'}.
    Do NOT use poetic or mysterious language.
    """

    ai_reply = ask_huggingface(prompt, lang)

    if not ai_reply:
        return jsonify({
            "success": True,
            "response": _generate_fallback_chatbot_response(
                soil_type,
                construction_score,
                crop_score,
                lang,
            )
        })

    # தமிழ் என்றால் மட்டும் தேவையில்லாத ஆங்கிலத்தை நீக்கவும்
    if lang == "ta":
        # clean_tamil(ai_reply) - இதைத் தற்காலிகமாக தவிர்க்கவும், அதுதான் அர்த்தத்தை மாற்றுகிறது
        pass 

    return jsonify({
        "success": True, 
        "response": ai_reply.strip()
    })


@api_bp.route('/chatbot/debug', methods=['GET'])
def chatbot_debug():
    api_key = (
        current_app.config.get("HUGGINGFACE_API_KEY")
        or os.environ.get("HUGGINGFACE_API_KEY")
        or os.environ.get("HF_TOKEN")
        or ""
    ).strip()

    return jsonify({
        "success": True,
        "provider": "huggingface",
        "has_api_key": bool(api_key),
        "api_key_prefix": api_key[:3] if api_key else "",
        "base_url": current_app.config.get("HUGGINGFACE_BASE_URL"),
        "model": current_app.config.get("HUGGINGFACE_MODEL"),
        "timeout": current_app.config.get("HUGGINGFACE_TIMEOUT"),
    })


def _generate_fallback_chatbot_response(soil_type, construction_score, crop_score, lang):
    has_soil = bool(soil_type and soil_type.strip())
    has_scores = (
        construction_score not in (None, "", 50) or
        crop_score not in (None, "", 50)
    )

    if lang == "ta":
        if has_soil and has_scores:
            return (
                f"AI service is temporarily unavailable. {soil_type} currently has "
                f"construction score {construction_score}% and crop score {crop_score}%. "
                "Please update the API key and try again."
            )

        if has_soil:
            return (
                f"AI service is temporarily unavailable for {soil_type}. "
                "Please update the API key and try again."
            )

        return "AI service is temporarily unavailable. Please update the API key and try again."

    if has_soil and has_scores:
        return (
            f"AI service is temporarily unavailable. {soil_type} currently has "
            f"a construction score of {construction_score}% and a crop score of {crop_score}%. "
            "Please update the API key and try again."
        )

    if has_soil:
        return (
            f"AI service is temporarily unavailable for {soil_type}. "
            "Please update the API key and try again."
        )

    return "AI service is temporarily unavailable. Please update the API key and try again."


def _generate_chatbot_response(message, soil_type, construction_score, crop_score):
    """எளிமையான கேள்விகளுக்கு உடனடி பதில் அளிக்கும் ரூல்ஸ்"""
    msg = message.lower()
    
    # கட்டுமானப் பணி குறித்த கேள்வி
    if "build" in msg or "construction" in msg or "கட்டடம்" in msg:
        if construction_score > 60:
            return f"Yes, {soil_type} is generally good for construction with a score of {construction_score}%."
        else:
            return f"Caution: {soil_type} has a low construction score ({construction_score}%). Consult an engineer."

    # விவசாயம் குறித்த கேள்வி
    if "crop" in msg or "plant" in msg or "விவசாயம்" in msg:
        if crop_score > 60:
            return f"{soil_type} is fertile ({crop_score}%) and suitable for most crops recommended in your report."
        else:
            return f"{soil_type} needs soil treatment as the crop score is only {crop_score}%."

    return None
