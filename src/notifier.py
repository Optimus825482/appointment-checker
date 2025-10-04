import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        self.config = Config()
    
    def send_telegram(self, message):
        """Telegram bildirimi gönder"""
        if not self.config.TELEGRAM_BOT_TOKEN or not self.config.TELEGRAM_CHAT_ID:
            logger.warning("⚠️ Telegram ayarları eksik")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": self.config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram bildirimi gönderildi")
                return True
            else:
                logger.error(f"❌ Telegram hatası: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram gönderim hatası: {e}")
            return False
    
    def send_email(self, subject, body):
        """Email bildirimi gönder"""
        if not self.config.EMAIL_SENDER or not self.config.EMAIL_PASSWORD:
            logger.warning("⚠️ Email ayarları eksik")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_SENDER
            msg['To'] = self.config.EMAIL_RECEIVER
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ Email bildirimi gönderildi")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email gönderim hatası: {e}")
            return False
    
    def notify_appointment_found(self):
        """Randevu bulundu bildirimi"""
        message = "🎉 <b>RANDEVU AÇILDI!</b>\n\nhttps://it-tr-appointment.idata.com.tr/tr"
        
        self.send_telegram(message)
        self.send_email(
            "🎉 Randevu Açıldı!",
            f"<h2>Randevu müsait!</h2><p>Hemen başvurun: <a href='https://it-tr-appointment.idata.com.tr/tr'>Randevu Al</a></p>"
        )