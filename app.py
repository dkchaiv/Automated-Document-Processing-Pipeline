"""
Automated Document Processing Pipeline
Flask backend with Tesseract OCR for extracting structured data from documents.
Developed by V. Chaitanya | 22331A4764 | CIC — MVGR College of Engineering
"""

from flask import Flask, request, jsonify, send_from_directory, make_response, render_template
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import Image
import pdf2image
import re
from datetime import datetime
import json
import time
import gzip
from io import BytesIO

app = Flask(__name__, static_folder='static', template_folder='templates')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_pdf_to_images(pdf_path: str) -> list:
    """Convert each page of a PDF to a PIL Image."""
    try:
        return pdf2image.convert_from_path(pdf_path)
    except Exception as e:
        raise Exception(f"PDF conversion error: {e}")


def extract_text_from_image(image: Image.Image) -> str:
    """Run Tesseract OCR on a PIL Image and return raw text."""
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        raise Exception(f"OCR error: {e}")


def parse_document(raw_text: str) -> dict:
    """
    Parse OCR text and extract specific fields using regex patterns.
    Returns a dict with keys: name, amount, date, invoice_id.
    """
    extracted = {
        'name': None,
        'amount': None,
        'date': None,
        'invoice_id': None,
    }

    text = ' '.join(raw_text.split())
    lines = raw_text.split('\n')

    # ── 1. Name ──────────────────────────────────────────────────────────
    name_pattern = r'(?:Name|Bill\s*To|Customer|Client|From)[\s:]*([A-Z][a-zA-Z\s\.]+?)(?:\n|$)'
    name_match = re.search(name_pattern, raw_text, re.IGNORECASE)
    if name_match:
        extracted['name'] = name_match.group(1).strip()
    else:
        for line in lines:
            stripped = line.strip()
            if re.match(r'^[A-Z][a-zA-Z\s\.]+$', stripped) and len(stripped) > 3:
                extracted['name'] = stripped
                break

    # ── 2. Amount ────────────────────────────────────────────────────────
    amount_pattern = r'\$\s*(\d+[,.]?\d*(?:\.\d{2})?)'
    amount_matches = re.findall(amount_pattern, raw_text)
    if amount_matches:
        amounts = [float(a.replace(',', '')) for a in amount_matches]
        extracted['amount'] = max(amounts)

    if not extracted['amount']:
        total_pattern = r'(?:Total|Amount|Price|Due)[\s:]*\$?\s*(\d+[,.]?\d*(?:\.\d{2})?)'
        total_match = re.search(total_pattern, raw_text, re.IGNORECASE)
        if total_match:
            extracted['amount'] = float(total_match.group(1).replace(',', ''))

    # ── 3. Date ──────────────────────────────────────────────────────────
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',                                         # MM/DD/YYYY
        r'(\d{1,2}-\d{1,2}-\d{4})',                                         # MM-DD-YYYY
        r'(\d{4}-\d{1,2}-\d{1,2})',                                         # YYYY-MM-DD
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DD MMM YYYY
    ]
    for pat in date_patterns:
        date_match = re.search(pat, raw_text, re.IGNORECASE)
        if date_match:
            extracted['date'] = date_match.group(1)
            break

    # ── 4. Invoice / Document ID ─────────────────────────────────────────
    id_patterns = [
        (r'((?:INV|BIL|REF)[\s\-]*[\d\-]+[A-Z0-9\-]*)', True),   # INV-2024-001 style
        (r'(?:Invoice|Bill|Ref|Reference|ID|Number)\s*[#:]\s*([A-Z0-9\-]+)', True),
    ]
    for pat, _ in id_patterns:
        id_match = re.search(pat, raw_text, re.IGNORECASE)
        if id_match:
            extracted['invoice_id'] = id_match.group(1).strip()
            break

    return extracted


def validate_extraction(data: dict) -> dict:
    """Validate each extracted field and return a status dict."""
    validation = {}

    # Name
    if data['name'] and len(data['name']) > 2:
        validation['name'] = 'valid'
    else:
        validation['name'] = 'invalid'

    # Amount
    if data['amount'] and data['amount'] > 0:
        validation['amount'] = 'valid'
    else:
        validation['amount'] = 'invalid'

    # Date
    if data['date']:
        date_valid = False
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d %B %Y', '%d %b %Y'):
            try:
                datetime.strptime(data['date'], fmt)
                date_valid = True
                break
            except ValueError:
                continue
        validation['date'] = 'valid' if date_valid else 'warning'
    else:
        validation['date'] = 'invalid'

    # Invoice ID
    if data['invoice_id'] and len(str(data['invoice_id'])) > 0:
        validation['invoice_id'] = 'valid'
    else:
        validation['invoice_id'] = 'invalid'

    return validation


# ---------------------------------------------------------------------------
# Middleware — add headers to every response
# ---------------------------------------------------------------------------

@app.after_request
def add_headers(response):
    """Add performance, developer, and caching headers."""
    response.headers['X-Developer'] = 'V. Chaitanya | 22331A4764 | CIC - MVGR College of Engineering'
    response.headers['X-Powered-By'] = 'Flask + Tesseract OCR'

    # Cache static assets aggressively
    if request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.ico', '.woff2')):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif request.path == '/':
        response.headers['Cache-Control'] = 'public, max-age=300'

    # Gzip compression for text responses (skip streaming / direct-passthrough)
    if (
        not response.direct_passthrough
        and response.content_type
        and ('text' in response.content_type or 'json' in response.content_type)
        and 'gzip' in request.headers.get('Accept-Encoding', '')
        and response.content_length
        and response.content_length > 500
    ):
        data = response.get_data()
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as f:
            f.write(data)
        response.set_data(buf.getvalue())
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(response.get_data())

    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('templates', 'index.html')


@app.route('/styles.css')
def serve_css():
    """Serve the extracted CSS file from templates folder."""
    return send_from_directory('templates', 'styles.css')


@app.route('/Scripts.js')
def serve_js():
    """Serve the extracted JS file from templates folder."""
    return send_from_directory('templates', 'Scripts.js')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload, run OCR pipeline, return structured JSON."""
    start_time = time.time()

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Allowed: PDF, JPG, JPEG, PNG'}), 400

        # Save uploaded file (secure filename to prevent path traversal)
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Convert to images
        images = []
        if filename.lower().endswith('.pdf'):
            images = convert_pdf_to_images(filepath)
        else:
            images = [Image.open(filepath)]

        # OCR — extract text from every page / image
        all_text = ''
        for img in images:
            all_text += extract_text_from_image(img) + '\n'

        # Parse fields
        extracted_data = parse_document(all_text)

        # Validate
        validation = validate_extraction(extracted_data)

        # Clean up the uploaded file
        os.remove(filepath)

        processing_time = round(time.time() - start_time, 2)

        response = {
            'status': 'success',
            'data': {
                'name': extracted_data['name'] or 'Not found',
                'amount': f"${extracted_data['amount']:.2f}" if extracted_data['amount'] else 'Not found',
                'date': extracted_data['date'] or 'Not found',
                'invoice_id': extracted_data['invoice_id'] or 'Not found',
            },
            'validation': validation,
            'raw_text': all_text[:500],
            'processing_time': f"{processing_time}s",
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
