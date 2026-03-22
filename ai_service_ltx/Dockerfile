# 1. Wir nutzen das moderne Basis-Image für vollen PyTorch 2.x & Flash Attention Support
FROM nvcr.io/nvidia/pytorch:24.10-py3 

# 2. System-Abhängigkeiten (Git für den Download, ffmpeg für Videoverarbeitung)
RUN apt-get update && apt-get install -y git ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# 3. Offizielles LTX-2 Repo in ein Verzeichnis laden, das nicht vom Volume überschrieben wird
WORKDIR /opt
RUN git clone https://github.com/Lightricks/LTX-2.git

# 4. Die nativen LTX-Packages installieren
WORKDIR /opt/LTX-2
RUN pip install -e ./ltx-core
RUN pip install -e ./ltx-pipelines

# 5. Deine API-Abhängigkeiten installieren (falls du noch andere hast, hier ergänzen)
RUN pip install -r requirements.txt

# 6. Arbeitsverzeichnis zurück auf deinen Mount-Ordner setzen
WORKDIR /app

# Startbefehl für deine API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8800"]