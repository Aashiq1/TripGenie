FROM python:3.11-slim

# Environment settings for reliable logs and fewer .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies required by some Python packages (e.g., cryptography, bcrypt, pandas/numpy)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libssl-dev \
       libffi-dev \
       gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


