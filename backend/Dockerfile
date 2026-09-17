# Production Dockerfile for AutoViva FastAPI Backend
FROM python:3.11-slim

# Prevent Python from writing pyc files to disc & buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

WORKDIR /app

# Install system dependencies (Poppler, fitz, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements
COPY requirements.txt .

# Install PyTorch CPU and Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformers BAAI/bge-small-en-v1.5 model during Docker build
# This ensures zero cold-start delay for embeddings in production
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Copy application source code
COPY . .

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
