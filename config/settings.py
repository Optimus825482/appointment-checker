import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Mistral AI
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
    
    # Bright Data Unlocker API
    BRIGHTDATA_API_KEY = os.getenv('BRIGHTDATA_API_KEY')
    
    # Randevu URL
    APPOINTMENT_URL = 'https://it-tr-appointment.idata.com.tr/tr'
    
    # Kontrol Ayarları
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 1500))  # saniye (25 dakika)
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 5))
    CLOUDFLARE_TIMEOUT = int(os.getenv('CLOUDFLARE_TIMEOUT', 30))
    
    # Chrome Ayarları
    CHROME_BIN = os.getenv('CHROME_BIN', '/usr/bin/chromium-browser')
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    # Bildirim Ayarları
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    EMAIL_SENDER = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')