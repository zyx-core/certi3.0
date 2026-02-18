# Use a specific, stable slim version (Bookworm is Debian 12)
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# Added libgl1 and libglib2.0-0 which are common requirements for cv2/pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create the static directory for Flutter files (if it doesn't exist yet)
RUN mkdir -p app/static

# Expose the port (Render will use this if PORT is not set)
EXPOSE 8000

# Command to run the application using shell form to expand environment variables
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
