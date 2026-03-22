FROM nvcr.io/nvidia/pytorch:24.01-py3

WORKDIR /app

# 1. Pip updaten und Liste installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Code kopieren
COPY . .

ENV HF_HOME=/models
EXPOSE 8800

# Startbefehl mit Auto-Reload
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800", "--reload"]