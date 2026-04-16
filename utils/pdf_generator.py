"""
PDF Report Generator for Soil Vision 360
Creates professional soil analysis reports using ReportLab
"""

import os
import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas


# Color palette
SOIL_COLORS = {
    'Black Soil': colors.HexColor('#1a1a2e'),
    'Red Soil': colors.HexColor('#8b1a1a'),
    'Yellow Soil': colors.HexColor('#b8860b'),
    'Brown/Alluvial Soil': colors.HexColor('#6b4423'),
}

ACCENT_COLOR = colors.HexColor('#00ff88')
BG_COLOR = colors.HexColor('#0d1117')
TEXT_COLOR = colors.HexColor('#e8e8e8')
CARD_BG = colors.HexColor('#1e2a3a')


def generate_qr_code(url, size=100):
    """Generate QR code image and return path"""
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def create_score_bar_drawing(label, score, color):
    """Create a visual score bar"""
    d = Drawing(400, 25)
    
    # Background bar
    d.add(Rect(0, 5, 300, 15, fillColor=colors.HexColor('#2a2a2a'), strokeColor=None))
    
    # Score bar
    fill_width = (score / 100) * 300
    d.add(Rect(0, 5, fill_width, 15, fillColor=color, strokeColor=None))
    
    # Label
    d.add(String(0, -5, label, fontSize=8, fillColor=colors.black))
    
    # Score text
    d.add(String(310, 5, f"{score}%", fontSize=9, fillColor=colors.black, fontName='Helvetica-Bold'))
    
    return d


def generate_soil_report(analysis_data, image_path=None, output_path=None, base_url='http://localhost:5000'):
    """
    Generate a professional PDF soil analysis report
    
    Args:
        analysis_data: dict with soil analysis results
        image_path: optional path to soil image
        output_path: where to save PDF
        base_url: base URL for QR code
    
    Returns:
        bytes: PDF content
    """
    if output_path is None:
        output_path = f"/tmp/soil_report_{analysis_data.get('soil_id', 'report')}.pdf"
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    soil_type = analysis_data.get('soil_type', 'Unknown')
    soil_color = SOIL_COLORS.get(soil_type, colors.HexColor('#4a4a4a'))
    soil_id = analysis_data.get('soil_id', 'N/A')
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=6,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#555555'),
        spaceAfter=4,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=soil_color,
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        borderPad=4
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=16
    )
    
    # Build content
    story = []
    
    # ── HEADER ──────────────────────────────────────────────────────────────
    # Logo/title banner
    header_data = [[
        Paragraph('<b>SOIL VISION 360</b>', ParagraphStyle(
            'HeaderTitle',
            fontSize=22,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        )),
        Paragraph(f'Report ID: <b>{soil_id}</b><br/>Date: {datetime.now().strftime("%B %d, %Y")}',
                  ParagraphStyle('HeaderRight', fontSize=9, textColor=colors.HexColor('#cccccc'), alignment=TA_RIGHT))
    ]]
    
    header_table = Table(header_data, colWidths=[12*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0d1117')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))
    
    # Soil type banner
    soil_banner_data = [[
        Paragraph(f'<b>ANALYSIS RESULT: {soil_type.upper()}</b>',
                  ParagraphStyle('Banner', fontSize=16, textColor=colors.white,
                                 fontName='Helvetica-Bold', alignment=TA_CENTER))
    ]]
    soil_banner = Table(soil_banner_data, colWidths=[17*cm])
    soil_banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), soil_color),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(soil_banner)
    story.append(Spacer(1, 15))
    
    # ── SOIL IMAGE + QR CODE ────────────────────────────────────────────────
    img_qr_data = []
    
    # Soil image
    if image_path and os.path.exists(image_path):
        try:
            img = RLImage(image_path, width=7*cm, height=7*cm)
            img_cell = [img, Paragraph('<i>Analyzed Soil Sample</i>',
                                       ParagraphStyle('Caption', fontSize=8, alignment=TA_CENTER,
                                                      textColor=colors.grey))]
        except Exception:
            img_cell = [Paragraph('Image not available', body_style)]
    else:
        img_cell = [Paragraph('<b>Soil Sample Image</b><br/>Not Available',
                               ParagraphStyle('NoImg', fontSize=10, alignment=TA_CENTER,
                                              textColor=colors.grey))]
    
    # QR Code
    report_url = f"{base_url}/reports/view/{soil_id}"
    try:
        qr_buf = generate_qr_code(report_url)
        qr_img = RLImage(qr_buf, width=4*cm, height=4*cm)
        qr_cell = [qr_img,
                   Paragraph(f'<i>Scan to view<br/>online report</i>',
                              ParagraphStyle('QRCaption', fontSize=8, alignment=TA_CENTER,
                                             textColor=colors.grey))]
    except Exception:
        qr_cell = [Paragraph(f'QR: {report_url}', body_style)]
    
    img_qr_table = Table(
        [[img_cell[0], qr_cell[0]]],
        colWidths=[9*cm, 8*cm]
    )
    img_qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(img_qr_table)
    story.append(Spacer(1, 8))
    
    # Description
    desc = analysis_data.get('description', '')
    story.append(Paragraph(f'<b>Soil Description:</b> {desc}', body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dddddd'), spaceAfter=10))
    
    # ── CORE SCORES TABLE ───────────────────────────────────────────────────
    story.append(Paragraph('Core Analysis Scores', heading_style))
    
    scores = [
        ['Metric', 'Score', 'Rating'],
        ['Water Retention', f"{analysis_data.get('water_retention', 0)}%",
         _get_rating(analysis_data.get('water_retention', 0))],
        ['Crop Compatibility', f"{analysis_data.get('crop_score', 0)}%",
         _get_rating(analysis_data.get('crop_score', 0))],
        ['Construction Stability', f"{analysis_data.get('construction_score', 0)}%",
         _get_rating(analysis_data.get('construction_score', 0))],
        ['Heat Absorption Index', f"{analysis_data.get('heat_index', 0)}%",
         _get_rating(analysis_data.get('heat_index', 0))],
        ['Land Potential Score', f"{analysis_data.get('land_potential_score', 0)}%",
         _get_rating(analysis_data.get('land_potential_score', 0))],
    ]
    
    scores_table = Table(scores, colWidths=[7*cm, 4*cm, 6*cm])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), soil_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f8f8'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 15))
    
    # ── ADVANCED ANALYTICS ──────────────────────────────────────────────────
    story.append(Paragraph('Advanced Risk Analytics', heading_style))
    
    adv_data = [
        ['Indicator', 'Value', 'Status'],
        ['Agriculture ROI', f"{analysis_data.get('agriculture_roi', 0)}%", ''],
        ['Construction Risk', analysis_data.get('construction_risk', 'N/A'), ''],
        ['Flood Risk Level', analysis_data.get('flood_risk', 'N/A'), ''],
        ['pH Range', analysis_data.get('ph_range', 'N/A'), ''],
        ['Soil Texture', analysis_data.get('texture', 'N/A'), ''],
    ]
    
    adv_table = Table(adv_data, colWidths=[7*cm, 5*cm, 5*cm])
    adv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f4f8'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
    ]))
    story.append(adv_table)
    story.append(Spacer(1, 15))
    
    # ── CROP RECOMMENDATIONS ────────────────────────────────────────────────
    crop_data = analysis_data.get('crop_recommendations', {})
    if crop_data:
        story.append(Paragraph('Crop Recommendations', heading_style))
        
        primary_crops = ', '.join(crop_data.get('primary', []))
        secondary_crops = ', '.join(crop_data.get('secondary', []))
        avoid_crops = ', '.join(crop_data.get('avoid', []))
        
        crop_info = [
            ['Category', 'Details'],
            ['Primary Crops', primary_crops],
            ['Secondary Crops', secondary_crops],
            ['Crops to Avoid', avoid_crops],
            ['Best Season', crop_data.get('season', 'N/A')],
            ['Irrigation Need', crop_data.get('irrigation', 'N/A')],
            ['Fertilizer Guide', crop_data.get('fertilizer', 'N/A')],
        ]
        
        crop_table = Table(crop_info, colWidths=[5*cm, 12*cm])
        crop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0fff4'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        story.append(crop_table)
        story.append(Spacer(1, 15))
    
    # ── CONSTRUCTION ADVICE ─────────────────────────────────────────────────
    const_advice = analysis_data.get('construction_advice', {})
    if const_advice:
        story.append(Paragraph('Construction Analysis', heading_style))
        
        const_color = colors.HexColor('#27ae60') if analysis_data.get('construction_score', 0) >= 50 else colors.HexColor('#e74c3c')
        
        precautions_text = ' | '.join(const_advice.get('precautions', []))
        
        const_info = [
            ['Parameter', 'Details'],
            ['Suitability', const_advice.get('suitability', 'N/A')],
            ['Foundation Type', const_advice.get('foundation', 'N/A')],
            ['Cost Factor', f"{const_advice.get('estimated_cost_factor', 1.0)}x baseline"],
            ['Precautions', precautions_text],
            ['Expert Recommendation', const_advice.get('recommendation', 'N/A')],
        ]
        
        const_table = Table(const_info, colWidths=[5*cm, 12*cm])
        const_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), const_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f8f8'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        story.append(const_table)
        story.append(Spacer(1, 15))
    
    # ── NUTRIENTS ───────────────────────────────────────────────────────────
    nutrients = analysis_data.get('nutrients', {})
    if nutrients:
        story.append(Paragraph('Nutrient Profile', heading_style))
        
        nutrient_data = [
            ['Nutrient', 'Level', 'Score'],
            ['Nitrogen (N)', _get_rating(nutrients.get('nitrogen', 0)), f"{nutrients.get('nitrogen', 0)}%"],
            ['Phosphorus (P)', _get_rating(nutrients.get('phosphorus', 0)), f"{nutrients.get('phosphorus', 0)}%"],
            ['Potassium (K)', _get_rating(nutrients.get('potassium', 0)), f"{nutrients.get('potassium', 0)}%"],
            ['Organic Matter', _get_rating(nutrients.get('organic_matter', 0)), f"{nutrients.get('organic_matter', 0)}%"],
        ]
        
        nut_table = Table(nutrient_data, colWidths=[6*cm, 6*cm, 5*cm])
        nut_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#faf5ff'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (0, -1), 12),
        ]))
        story.append(nut_table)
        story.append(Spacer(1, 15))
    
    # ── FOOTER ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=2, color=soil_color, spaceAfter=8))
    
    footer_data = [[
        Paragraph(
            f'<b>Soil Vision 360</b> | Professional Soil Intelligence Platform<br/>'
            f'Report ID: {soil_id} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}<br/>'
            f'<i>This report is generated by AI analysis and should be verified by a certified soil scientist for critical decisions.</i>',
            ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER, leading=12)
        )
    ]]
    
    footer_table = Table(footer_data, colWidths=[17*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(footer_table)
    
    # Build PDF
    doc.build(story)
    
    with open(output_path, 'rb') as f:
        return f.read()


def _get_rating(score):
    """Convert numeric score to rating text"""
    if score >= 80:
        return 'Excellent'
    elif score >= 65:
        return 'Good'
    elif score >= 45:
        return 'Moderate'
    elif score >= 25:
        return 'Poor'
    else:
        return 'Very Poor'