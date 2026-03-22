# 📄 Automated Document Processing Pipeline

> An intelligent, OCR-powered pipeline that extracts structured data from invoices, forms, and receipts — **100% free, no paid APIs required.**

**Developed by V Chaitanya Sai | 22331A4764 | CIC — MVGR College of Engineering**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-black?logo=flask)](https://flask.palletsprojects.com)
[![Tesseract](https://img.shields.io/badge/OCR-Tesseract-green)](https://github.com/tesseract-ocr/tesseract)


---
![Demo Screenshot](./screenshots/rdme1.png)

## 🔍 What Is This?

This project is a full-stack web application that:

- **Accepts** PDF or image files (invoices, forms, receipts)
- **Extracts** raw text using Tesseract OCR
- **Parses** structured fields — Name, Amount, Date, Invoice ID — using regex
- **Validates** the extracted data and returns a clean JSON response
- **Displays** results live in the browser with field-level validation status

**Real-World Example:**

```
INPUT:  invoice.pdf
   ↓
OCR:    "INVOICE\nInvoice #: INV-2024-001\nDate: 03/18/2024\nBill To: Kusuma Kumar\nTotal: $1,500.00"
   ↓
PARSE:  Name → "Kusuma Kumar"  |  Amount → $1500.00  |  Date → 03/18/2024  |  ID → INV-2024-001
   ↓
OUTPUT: { "status": "success", "data": { ... }, "validation": { ... } }
```

---

## 🚀 Live Demo

> **Deployed URL:** `https://automated-document-processing-pipeline.onrender.com`

---
## Inputs
![Demo Screenshot](./screenshots/rdme2.png)
## Outputs
![Demo Screenshot](./screenshots/rdme3.png)

## 🏗️ Complete System Architecture
 
```
┌──────────────────────────────────────────────────────────┐
│                  USER INTERFACE (Frontend)                │
│                                                          │
│   ┌────────────────────────────────────────────────┐    │
│   │  File Upload Form                              │    │
│   │  ├─ Drag & Drop area                           │    │
│   │  ├─ File input button (PDF / JPG / PNG)        │    │
│   │  └─ Submit button                              │    │
│   │                                                │    │
│   │  Results Panel                                 │    │
│   │  ├─ Extracted fields table                     │    │
│   │  ├─ Validation badges (valid / invalid)        │    │
│   │  └─ Download JSON button                       │    │
│   └────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────┘
                           │  POST /upload  (multipart/form-data)
                           ▼
┌──────────────────────────────────────────────────────────┐
│               BACKEND SERVER (Flask + Python)            │
│                                                          │
│   STAGE 1 ── FILE HANDLER                               │
│              ├─ Receive & validate file format           │
│              ├─ Enforce 10 MB size limit                 │
│              └─ Save to temp folder                      │
│                         ▼                                │
│   STAGE 2 ── PDF / IMAGE CONVERTER                      │
│              ├─ PDF  → pdf2image + Poppler               │
│              ├─ Image → Pillow (used directly)           │
│              └─ Grayscale conversion for performance     │
│                         ▼                                │
│   STAGE 3 ── OCR ENGINE (Tesseract)                     │
│              ├─ Run pytesseract on each page/image       │
│              ├─ Grayscale at dpi=200 (~40% faster)       │
│              └─ Concatenate text from all pages          │
│                         ▼                                │
│   STAGE 4 ── TEXT PARSER (Regex)                        │
│              ├─ Name   → "Bill To / Customer / Name:" patterns
│              ├─ Amount → "$" + largest numeric value     │
│              ├─ Date   → MM/DD/YYYY, YYYY-MM-DD, etc.   │
│              └─ ID     → INV-*, BIL-*, REF-* patterns   │
│                         ▼                                │
│   STAGE 5 ── VALIDATION ENGINE                          │
│              ├─ name   → length > 2                      │
│              ├─ amount → positive float                  │
│              ├─ date   → parseable against known formats │
│              └─ id     → non-empty alphanumeric          │
│                         ▼                                │
│   STAGE 6 ── JSON BUILDER                               │
│              ├─ Structure data + validation dict         │
│              ├─ Include raw_text preview (500 chars)     │
│              ├─ Add processing_time                      │
│              └─ Clean up temp file                       │
└──────────────────────────┬───────────────────────────────┘
                           │  JSON Response
                           ▼
┌──────────────────────────────────────────────────────────┐
│  {                                                       │
│    "status": "success",                                  │
│    "data": {                                             │
│      "name":       "Kusuma Kumar",                       │
│      "amount":     "$1500.00",                           │
│      "date":       "03/18/2024",                         │
│      "invoice_id": "INV-2024-001"                        │
│    },                                                    │
│    "validation": {                                       │
│      "name": "valid",  "amount": "valid",                │
│      "date": "valid",  "invoice_id": "valid"             │
│    },                                                    │
│    "raw_text": "...",                                    │
│    "processing_time": "1.23s"                            │
│  }                                                       │
└──────────────────────────────────────────────────────────┘
```
 
---
 
## 📁 Project Structure
 
```
Automated-Document-Processing-Pipeline/
│
├── app.py                  # Flask backend — all pipeline logic
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── templates/
│   └── index.html          # Frontend UI
│
├── static/
│   ├── style.css           # Styles
│   └── script.js           # Frontend JS (upload + display)
│
├── Tesseract-OCR/          # Bundled Tesseract binary (Windows)
│   └── tesseract.exe
│
└── poppler/                # Bundled Poppler for PDF support (Windows)
    └── Library/bin/
```
 
---
 
## 🧰 Technology Stack
 
| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5 + CSS3 + JS | Upload form, result display |
| Backend | Python 3.9+ / Flask 3.1.3 | REST API, pipeline orchestration |
| OCR Engine | Tesseract (pytesseract 0.3.13) | Text extraction from images |
| PDF Support | pdf2image 1.17.0 + Poppler | Convert PDF pages to images |
| Image Processing | Pillow 12.1.1 | Image loading and grayscale conversion |
| Pattern Matching | Python `re` (built-in) | Field extraction via regex |
| Deployment | Railway / Render | Free cloud hosting |
 
**Why free?** Alternatives like AWS Textract ($1.50/page) or Google Vision ($1.50/1000 req) cost money. This stack is entirely open-source.
 
---
 
## ⚙️ Local Setup
 
### Prerequisites
 
- Python 3.9+
- pip
- Tesseract OCR installed on your system
 
### Step 1 — Install Tesseract
 
```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr
 
# macOS
brew install tesseract
 
# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Default install path: C:\Program Files\Tesseract-OCR\tesseract.exe
```
 
### Step 2 — Install Poppler (PDF support)
 
```bash
# Ubuntu / Debian
sudo apt-get install poppler-utils
 
# macOS
brew install poppler
 
# Windows
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Extract and place in project root as poppler/Library/bin/
```
 
### Step 3 — Clone & Install Dependencies
 
```bash
git clone https://github.com/dkchaiv/Automated-Document-Processing-Pipeline.git
cd Automated-Document-Processing-Pipeline
 
pip install -r requirements.txt
```
 
### Step 4 — Run the Server
 
```bash
python app.py
```
 
Server starts at **http://localhost:5001**
 
### Step 5 — Health Check
 
```bash
curl http://localhost:5001/health
```
 
Expected response:
```json
{ "status": "healthy", "ocr_available": true, "pdf_support": true }
```
 
---
 
## 🌐 Deployment
 
### Deploy to Railway (Recommended — Free)
 
```bash
# 1. Install Railway CLI
npm install -g @railway/cli
 
# 2. Login
railway login
 
# 3. Initialise project
railway init
 
# 4. Deploy
railway deploy
 
# 5. Get your live URL
railway open
```
 
Your app will be live at a URL like: `https://your-app.up.railway.app`
 
> ⚠️ **Note:** Tesseract must be available in the deployment environment. For Railway/Render, add a build command or Dockerfile that installs `tesseract-ocr` and `poppler-utils`.
 
### Deploy to Render (Alternative — Free)
 
1. Push your repo to GitHub.
2. Go to [render.com](https://render.com) → New Web Service → Connect GitHub repo.
3. Set **Build Command:** `apt-get install -y tesseract-ocr poppler-utils && pip install -r requirements.txt`
4. Set **Start Command:** `python app.py`
5. Deploy — live URL is provided automatically.
 
---
 
## 📡 API Reference
 
### `GET /health`
 
Returns server and dependency status.
 
**Response:**
```json
{ "status": "healthy", "ocr_available": true, "pdf_support": true }
```
 
---
 
### `POST /upload`
 
Upload a document for processing.
 
**Request:** `multipart/form-data` with field `file` (PDF / JPG / JPEG / PNG, max 10 MB)
 
**Success Response `200`:**
```json
{
  "status": "success",
  "data": {
    "name": "Kusuma Kumar",
    "amount": "$1500.00",
    "date": "03/18/2024",
    "invoice_id": "INV-2024-001"
  },
  "validation": {
    "name": "valid",
    "amount": "valid",
    "date": "valid",
    "invoice_id": "valid"
  },
  "raw_text": "INVOICE\nInvoice #: INV-2024-001...",
  "processing_time": "1.23s"
}
```
 
**Error Response `400 / 500`:**
```json
{ "error": "Invalid file format. Allowed: PDF, JPG, JPEG, PNG" }
```
 
---
 
## 🔄 Sample Execution Flows
 
### Invoice PDF
 
```
INPUT: invoice.pdf
  ↓
OCR TEXT:
  "INVOICE
   Invoice #: INV-2024-001
   Date: 03/18/2024
   Bill To: Kusuma Kumar
   Total Amount: $1,500.00"
  ↓
PARSED:
  name       → "Kusuma Kumar"
  amount     → 1500.00
  date       → "03/18/2024"
  invoice_id → "INV-2024-001"
  ↓
VALIDATION: all fields → "valid"
```
 
### Application Form (JPG)
 
```
INPUT: form.jpg
  ↓
OCR TEXT:
  "APPLICATION FORM
   Name: John Smith
   Amount Requested: $5000
   Date of Application: 2024-03-15
   Ref Number: REF-123456"
  ↓
PARSED:
  name       → "John Smith"
  amount     → 5000.00
  date       → "2024-03-15"
  invoice_id → "REF-123456"
  ↓
VALIDATION: all fields → "valid"
```
 
---
 
## ✅ Features
 
| Phase | Feature | Status |
|---|---|---|
| Phase 1 | File upload (PDF / Image) | ✅ |
| Phase 1 | OCR processing | ✅ |
| Phase 1 | Field extraction (Name, Amount, Date, ID) | ✅ |
| Phase 1 | JSON output | ✅ |
| Phase 1 | Simple UI | ✅ |
| Phase 2 | Input validation | ✅ |
| Phase 2 | Error handling | ✅ |
| Phase 2 | Improved regex patterns | ✅ |
| Phase 2 | Download JSON | ✅ |
| Phase 3 | Drag-and-drop upload | ✅ |
| Phase 3 | Confidence scores / processing time | ✅ |
 
---
 
## 🐛 Troubleshooting
 
| Issue | Fix |
|---|---|
| `Tesseract not found` | Install via `apt-get` / `brew` / Windows installer |
| `pytesseract module not found` | `pip install pytesseract` |
| `PDF conversion fails` | Install poppler — `apt-get install poppler-utils` or `brew install poppler` |
| `File too large` | In `app.py` change `MAX_FILE_SIZE = 50 * 1024 * 1024` |
| OCR gives poor results | Ensure document image is clear and at least 150 DPI |
 
---
 
## 🗺️ Roadmap
 
- [ ] Language detection for multilingual documents
- [ ] Batch processing for multiple files
- [ ] Confidence scores per extracted field
- [ ] Database (SQLite) for storing extraction history
- [ ] Queue system for large-volume processing
- [ ] OCR result preview / highlight overlay
- [ ] REST API for third-party integration
- [ ] Mobile app wrapper
 
---
 
## 💰 Cost
 
| Item | Cost |
|---|---|
| All libraries (Flask, Tesseract, Pillow, pdf2image) | **Free** |
| Railway / Render hosting (free tier) | **Free** |
| Domain (`.railway.app` / `.onrender.com`) | **Free** |
| **Total** | **$0** |
 
---
 

 
## 👨‍💻 Author
 
**V. Chaitanya**  
Roll No: 22331A4764  
CIC — MVGR College of Engineering
 
---
 
> *Built with ❤️ using Python, Flask, and Tesseract OCR.*
