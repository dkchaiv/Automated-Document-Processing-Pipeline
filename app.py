"""
Automated Document Processing Pipeline
Flask backend with Tesseract OCR for extracting structured data from documents.
Developed by V. Chaitanya | 22331A4764 | CIC — MVGR College of Engineering
"""

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime
import time
import threading
import requests

# ---------------------------------------------------------------------------
# Try to import OCR libraries — gracefully handle missing dependencies
# ---------------------------------------------------------------------------
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import pdf2image
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder='templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
POPPLER_PATH = os.path.join(BASE_DIR, 'poppler', 'Library', 'bin')

# Point pytesseract to the bundled executable
TESSERACT_PATH = os.path.join(BASE_DIR, 'Tesseract-OCR', 'tesseract.exe')
if OCR_AVAILABLE and os.path.isfile(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# ---------------------------------------------------------------------------
# Keep-Alive Logic
# ---------------------------------------------------------------------------
def keep_alive():
    while True:
        time.sleep(14 * 60)  # every 14 minutes
        try:
            requests.get("https://automated-document-processing-pipeline.onrender.com/health")
            print("Keep-alive ping sent")
        except:
            pass

# Start keep-alive thread when app launches
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_image(image) -> str:
    """Run Tesseract OCR on a PIL Image and return raw text."""
    if not OCR_AVAILABLE:
        raise Exception("pytesseract or Pillow is not installed. Install with: pip install pytesseract Pillow")
    try:
        # Optimization: Convert to grayscale. This significantly speeds up
        # OCR processing and often improves text recognition accuracy.
        image = image.convert('L')
        # Using default PSM, but grayscale reduces memory & processing time
        return pytesseract.image_to_string(image)
    except Exception as e:
        raise Exception(f"OCR error: {e}")


def convert_pdf_to_images(pdf_path: str) -> list:
    """Convert each page of a PDF to a PIL Image."""
    if not PDF_SUPPORT:
        raise Exception("pdf2image is not installed. Install with: pip install pdf2image")
    try:
        # Optimization: explicit dpi=200 and grayscale=True for ~40% faster PDF parsing
        poppler_kwargs = {'dpi': 200, 'grayscale': True}
        
        # Use bundled Poppler if available, otherwise fall back to system PATH
        if os.path.isdir(POPPLER_PATH):
            return pdf2image.convert_from_path(pdf_path, poppler_path=POPPLER_PATH, **poppler_kwargs)
        else:
            return pdf2image.convert_from_path(pdf_path, **poppler_kwargs)
    except Exception as e:
        raise Exception(f"PDF conversion error: {e}")


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

    lines = raw_text.split('\n')

    # 1. Name
    # Improved capture that limits length, handles punctuation, and strictly stops at newlines
    name_pattern = r'(?:Name|Bill\s*To|Customer|Client|From)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\.\,\'&]{2,40})(?:\n|$)'
    name_match = re.search(name_pattern, raw_text, re.IGNORECASE)
    if name_match:
        # Clean up any trailing space or double-spaces
        clean_name = re.sub(r'\s+', ' ', name_match.group(1).strip())
        extracted['name'] = clean_name
    else:
        # Robust Fallback: Search for a standalone line that resembles a typical personal or company name
        for line in lines:
            stripped = line.strip()
            # Avoid long sentences. Match Title Case words (e.g., "John Doe", "Acme Corp")
            if len(stripped) < 30 and re.match(r'^([A-Z][A-Za-z\.]+\s*){2,4}$', stripped):
                extracted['name'] = stripped
                break
            # Second fallback: ALL CAPS name (e.g. "JOHN DOE")
            elif len(stripped) < 30 and re.match(r'^([A-Z\.]+\s*){2,4}$', stripped) and len(stripped) > 4:
                extracted['name'] = stripped
                break

    # 2. Amount
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

    # 3. Date
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(\d{4}-\d{1,2}-\d{1,2})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
    ]
    for pat in date_patterns:
        date_match = re.search(pat, raw_text, re.IGNORECASE)
        if date_match:
            extracted['date'] = date_match.group(1)
            break

    # 4. Invoice / Document ID
    id_patterns = [
        r'((?:INV|BIL|REF)[\s\-]*[\d\-]+[A-Z0-9\-]*)',
        r'(?:Invoice|Bill|Ref|Reference|ID|Number)\s*[#:]\s*([A-Z0-9\-]+)',
    ]
    for pat in id_patterns:
        id_match = re.search(pat, raw_text, re.IGNORECASE)
        if id_match:
            extracted['invoice_id'] = id_match.group(1).strip()
            break

    return extracted


def validate_extraction(data: dict) -> dict:
    """Validate each extracted field and return a status dict."""
    validation = {}

    validation['name'] = 'valid' if data['name'] and len(data['name']) > 2 else 'invalid'

    validation['amount'] = 'valid' if data['amount'] and data['amount'] > 0 else 'invalid'

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

    validation['invoice_id'] = 'valid' if data['invoice_id'] and len(str(data['invoice_id'])) > 0 else 'invalid'

    return validation


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint — also reports dependency status."""
    return jsonify({
        'status': 'healthy',
        'ocr_available': OCR_AVAILABLE,
        'pdf_support': PDF_SUPPORT,
    }), 200


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

        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Convert to images
            if filename.lower().endswith('.pdf'):
                images = convert_pdf_to_images(filepath)
            else:
                if not OCR_AVAILABLE:
                    raise Exception("Pillow is not installed. Install with: pip install Pillow")
                images = [Image.open(filepath)]

            # OCR — extract text from every page / image
            all_text = ''
            for img in images:
                all_text += extract_text_from_image(img) + '\n'

            # Parse fields
            extracted_data = parse_document(all_text)

            # Validate
            validation = validate_extraction(extracted_data)

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

        finally:
            # Always clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Automated Document Processing Pipeline")
    print("  Developed by V. Chaitanya | 22331A4764")
    print("  CIC - MVGR College of Engineering")
    print("=" * 60)
    ocr_status = "[OK] Available" if OCR_AVAILABLE else "[X] Not installed"
    pdf_status = "[OK] Available" if PDF_SUPPORT else "[X] Not installed"
    print(f"  OCR (pytesseract): {ocr_status}")
    print(f"  PDF support:       {pdf_status}")
    print(f"  Server:            http://localhost:5001")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
