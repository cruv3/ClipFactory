FROM nvcr.io/nvidia/pytorch:24.10-py3 

RUN apt-get update && apt-get install -y git ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip


WORKDIR /opt
RUN git clone https://github.com/Lightricks/LTX-2.git

WORKDIR /opt/LTX-2

RUN pip install .

RUN pip install fastapi uvicorn pydantic accelerate

WORKDIR /app

# Startbefehl für deine API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]