FROM python:3.11-slim

# Install Tesseract OCR + Poppler at OS level — guaranteed to persist at runtime
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Expose port (Render uses 10000 by default for Docker)
EXPOSE 10000

# Start the app with Gunicorn
CMD ["gunicorn", "app:app", "--workers", "2", "--bind", "0.0.0.0:10000"]
