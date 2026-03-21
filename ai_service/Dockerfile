FROM nvcr.io/nvidia/pytorch:24.01-py3

# 1. System-Pakete
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. DER DEFINITIVE TORCH-BLOCKER:
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy<2.0.0" && \
    pip install --no-cache-dir fastapi uvicorn python-multipart pydantic moviepy kokoro OmegaConf vector_quantize_pytorch scikit-learn scipy && \
    pip install --no-cache-dir --no-deps transformers accelerate diffusers bitsandbytes sentencepiece

# 3. Code kopieren
COPY . .

ENV HF_HOME=/models
EXPOSE 8800

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]