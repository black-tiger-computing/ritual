FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/backend/ /app/

# Create non-root user
RUN useradd -m -u 1000 ritual && chown -R ritual:ritual /app
USER ritual

# Environment defaults
ENV PORT=8765
ENV HOST=0.0.0.0

EXPOSE 8765

CMD ["python", "main.py", "--port", "8765"]