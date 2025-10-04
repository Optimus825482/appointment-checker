FROM python:3.11-slim

# Chrome ve dependencies kurulumu
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    xvfb \
    x11vnc \
    fluxbox \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Xvfb başlatma scripti oluştur
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
exec "$@"' > /usr/local/bin/xvfb-run.sh && \
    chmod +x /usr/local/bin/xvfb-run.sh

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Chrome profil dizini oluştur
RUN mkdir -p /app/chrome_profile && chmod 777 /app/chrome_profile

# Port ve Display ayarları
ENV PORT=5000
ENV DISPLAY=:99

EXPOSE 5000

# Xvfb ile başlat (Virtual Display - headless gerekmez!)
CMD ["/usr/local/bin/xvfb-run.sh", "gunicorn", "src.app:app", "--bind", "0.0.0.0:5000", "--timeout", "180", "--workers", "1", "--log-level", "info"]