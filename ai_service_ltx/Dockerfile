FROM nvcr.io/nvidia/pytorch:24.10-py3

# 1. System-Abhängigkeiten (FFmpeg ist hier der Star)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Pip updaten und Liste installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Code kopieren
COPY . .

ENV HF_HOME=/models
EXPOSE 8800

# Startbefehl mit Auto-Reload
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800", "--reload"]