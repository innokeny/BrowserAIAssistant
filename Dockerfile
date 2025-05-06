FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for models if it doesn't exist
RUN mkdir -p models/silero models/whisper

# Download models
RUN python scripts/download_models.py

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "infrastructure.web.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 