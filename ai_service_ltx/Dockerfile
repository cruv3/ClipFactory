FROM nvcr.io/nvidia/pytorch:26.02-py3

RUN apt-get update && apt-get install -y git ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

# Repo klonen
WORKDIR /opt
RUN git clone https://github.com/Lightricks/LTX-2.git

# HIER IST DIE ANTWORT: Saubere Installation via Pip!
RUN pip install /opt/LTX-2/packages/ltx-core
RUN pip install /opt/LTX-2/packages/ltx-pipelines

# API Abhängigkeiten
RUN pip install -r requirements.txt

WORKDIR /app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]