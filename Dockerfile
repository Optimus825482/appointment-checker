FROM python:3.11-slim

# Çalışma dizini
WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Port ayarı
ENV PORT=5000

EXPOSE 5000

# Gunicorn ile başlat
# Bright Data Unlocker API kullanıyoruz - Chrome/Selenium gerekmez!
CMD ["gunicorn", "src.app:app", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "1", "--log-level", "info"]