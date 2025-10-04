FROM python:3.11-slim

# Chrome ve bağımlılıkları kur
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Start script'i kopyala ve executable yap
COPY start.sh .
RUN chmod +x start.sh

# Chrome binary konumu
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Başlatma
ENTRYPOINT ["./start.sh"]