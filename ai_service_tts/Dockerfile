FROM nvcr.io/nvidia/pytorch:26.02-py3

# 1. System-Abhängigkeiten (espeak-ng ist Pflicht für Kokoro!)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    espeak-ng \
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

# Startbefehl (mit --reload, damit du Code ohne Rebuild ändern kannst)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800", "--reload"]