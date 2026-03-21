FROM nvcr.io/nvidia/pytorch:24.01-py3

# 1. System-Pakete
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN uv pip install --system \
    "numpy<2.0.0" \
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
    scipy \
    soundfile

# 3. Code kopieren
COPY . .

ENV HF_HOME=/models
EXPOSE 8800

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]