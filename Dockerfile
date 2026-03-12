FROM mcr.microsoft.com/playwright/python:v1.58.2-noble

# 1. ImageMagick und Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# 2. Die Security Policy von ImageMagick fixen (Wichtig für Text-Rendering auf Linux)
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@\*"/g' /etc/ImageMagick-6/policy.xml; \
    fi && \
    if [ -f /etc/ImageMagick-7/policy.xml ]; then \
        sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@\*"/g' /etc/ImageMagick-7/policy.xml; \
    fi

WORKDIR /app

# 3. Requirements installieren (Caching nutzen)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Den Rest kopieren (inkl. deiner neuen Secrets)
COPY . .

ENV PYTHONPATH=/app
# Damit MoviePy auf Linux nicht nach 'magick.exe' sucht
ENV IMAGEMAGICK_BINARY=/usr/bin/convert 

CMD ["python", "scripts/main.py"]
