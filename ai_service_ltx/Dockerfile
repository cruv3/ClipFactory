FROM nvcr.io/nvidia/pytorch:24.10-py3 

RUN apt-get update && apt-get install -y git ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

# Repo klonen (wird in /opt/LTX-2 abgelegt)
WORKDIR /opt
RUN git clone https://github.com/Lightricks/LTX-2.git

# Nur die Pakete, die wir für die API zwingend brauchen
RUN pip install fastapi uvicorn pydantic accelerate torchvision transformers diffusers safetensors imageio

WORKDIR /app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]