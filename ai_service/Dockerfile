FROM nvcr.io/nvidia/pytorch:24.01-py3

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy<2.0.0" && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic \
    transformers \
    accelerate \
    diffusers \
    bitsandbytes \
    sentencepiece \
    moviepy \
    kokoro \
    OmegaConf \
    vector_quantize_pytorch \
    scikit-learn \
    scipy

# 3. Den Service-Code kopieren
COPY . .

# Pfad für die Modelle (gemappt in docker-compose)
ENV HF_HOME=/models
ENV TORCH_HOME=/models

# Port für FastAPI
EXPOSE 8880

# Startbefehl für den High-End Service
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8880"]