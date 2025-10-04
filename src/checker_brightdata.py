"""
Bright Data Unlocker API ile Cloudflare Bypass
Bu modül Selenium yerine Bright Data'nın profesyonel Unlocker API'sini kullanır
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentChecker:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        
    def fetch_with_brightdata(self, url, max_retries=3):
        """
        Bright Data Unlocker API ile sayfa getir
        
        Args:
            url: Hedef URL
            max_retries: Maksimum deneme sayısı
            
        Returns:
            tuple: (success: bool, html: str, status_code: int)
        """
        logger.info(f"🌐 Bright Data Unlocker API ile sayfa getiriliyor: {url}")
        
        # Bright Data Unlocker API endpoint
        api_url = "https://api.brightdata.com/unlocker/v1/fetch"
        
        # API Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.BRIGHTDATA_API_KEY}"
        }
        
        # Request payload
        payload = {
            "url": url,
            "format": "html",  # HTML formatında dön
            "country": "tr",   # Türkiye proxy kullan
            "render": True,    # JavaScript render et
            "wait_for_selector": "body",  # Body yüklenene kadar bekle
            "timeout": 60000   # 60 saniye timeout
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Deneme {attempt}/{max_retries}...")
                
                response = self.session.post(
                    api_url,
                    json=payload,
                    headers=headers,
                    timeout=90  # API timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Sayfa başarıyla getirildi! (Status: {response.status_code})")
                    logger.info(f"📊 Response boyutu: {len(response.text)} karakter")
                    return True, response.text, response.status_code
                    
                elif response.status_code == 401:
                    logger.error("❌ Bright Data API Key geçersiz!")
                    logger.error("💡 BRIGHTDATA_API_KEY environment variable'ı kontrol edin")
                    return False, "", response.status_code
                    
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limit aşıldı, {attempt * 5}s bekleniyor...")
                    time.sleep(attempt * 5)
                    continue
                    
                else:
                    logger.warning(f"⚠️ Beklenmeyen status code: {response.status_code}")
                    logger.warning(f"   Response: {response.text[:200]}")
                    
                    if attempt < max_retries:
                        logger.info(f"🔄 {attempt * 3}s sonra tekrar denenecek...")
                        time.sleep(attempt * 3)
                        continue
                        
            except requests.exceptions.Timeout:
                logger.error(f"❌ Timeout hatası! (Deneme {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request hatası: {e}")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Beklenmeyen hata: {e}")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
        
        logger.error(f"❌ {max_retries} denemeden sonra başarısız!")
        return False, "", 0
    
    def extract_captcha_from_html(self, html):
        """
        HTML'den CAPTCHA görselini çıkar
        
        Args:
            html: Sayfa HTML içeriği
            
        Returns:
            str: CAPTCHA base64 data URL veya None
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # CAPTCHA görseli ara
            captcha_img = soup.find('img', class_='imageCaptcha')
            
            if captcha_img and captcha_img.get('src'):
                src = captcha_img['src']
                if src.startswith('data:image'):
                    logger.info("✅ CAPTCHA görseli HTML'de bulundu!")
                    return src
                    
            logger.warning("⚠️ CAPTCHA görseli HTML'de bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA extraction hatası: {e}")
            return None
    
    def check_appointment_availability(self, html):
        """
        HTML'den randevu durumunu kontrol et
        
        Args:
            html: Sayfa HTML içeriği
            
        Returns:
            tuple: (available: bool, message: str)
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text().lower()
            
            logger.info("🔍 Randevu durumu kontrol ediliyor...")
            
            # "Randevu yok" mesajları
            no_appointment_keywords = [
                "no appointment",
                "randevu yok",
                "müsait randevu yok",
                "no available appointment"
            ]
            
            for keyword in no_appointment_keywords:
                if keyword in text:
                    logger.info(f"😔 '{keyword}' mesajı bulundu - Randevu yok")
                    return False, "😔 Randevu yok"
            
            # Randevu butonları ara
            appointment_buttons = soup.find_all(['button', 'a'], 
                text=lambda t: t and any(word in t.lower() for word in ['randevu', 'appointment', 'müsait']))
            
            if appointment_buttons:
                logger.info(f"🎉 Randevu butonu bulundu! ({len(appointment_buttons)} adet)")
                return True, f"🎉 RANDEVU VAR! ({len(appointment_buttons)} müsait slot)"
            
            # Form submit butonu
            submit_button = soup.find('button', type='submit')
            if submit_button:
                logger.info("✅ Submit butonu bulundu - Form doldurulabilir")
                return True, "✅ Form doldurulabilir (submit butonu mevcut)"
            
            logger.info("ℹ️ Net bir sonuç bulunamadı, daha fazla analiz gerekli")
            return False, "ℹ️ Belirsiz durum"
            
        except Exception as e:
            logger.error(f"❌ HTML analiz hatası: {e}")
            return False, f"❌ Hata: {e}"
    
    def run_check(self):
        """
        Ana kontrol döngüsü - Bright Data Unlocker API ile
        """
        try:
            logger.info("🚀 Kontrol başlatılıyor...")
            logger.info("🌐 Bright Data Unlocker API kullanılıyor (Selenium YOK!)")
            
            # 1. Sayfa getir (Cloudflare bypass dahil!)
            success, html, status_code = self.fetch_with_brightdata(self.config.APPOINTMENT_URL)
            
            if not success:
                logger.error("❌ Sayfa getirilemedi!")
                return "❌ Bağlantı hatası"
            
            # 2. Cloudflare kontrolü
            if "cloudflare" in html.lower() or "attention required" in html.lower():
                logger.error("❌ Bright Data bile Cloudflare'ı geçemedi!")
                logger.error("💡 Bu çok nadir bir durum, API key'i kontrol edin")
                return "❌ Cloudflare bypass başarısız"
            
            logger.info("✅ Cloudflare başarıyla bypass edildi!")
            logger.info(f"📄 HTML boyutu: {len(html)} karakter")
            
            # 3. CAPTCHA var mı kontrol et
            captcha_data = self.extract_captcha_from_html(html)
            
            if captcha_data:
                logger.info("🔐 CAPTCHA bulundu, Mistral AI ile çözülüyor...")
                
                from src.captcha_solver import CaptchaSolver
                solver = CaptchaSolver(self.config.MISTRAL_API_KEY)
                
                # CAPTCHA'yı çöz
                captcha_text = solver.solve_captcha_from_base64(captcha_data)
                
                if captcha_text:
                    logger.info(f"✅ CAPTCHA çözüldü: {captcha_text}")
                    # TODO: Form submission için CAPTCHA'yı kullan
                    # Şimdilik sadece göster
                else:
                    logger.warning("⚠️ CAPTCHA çözülemedi!")
            else:
                logger.info("ℹ️ CAPTCHA bulunamadı veya gerekli değil")
            
            # 4. Randevu durumunu kontrol et
            available, message = self.check_appointment_availability(html)
            
            logger.info(f"📊 Sonuç: {message}")
            return message
            
        except Exception as e:
            logger.error(f"❌ Kritik hata: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Hata: {e}"
        
        finally:
            logger.info("🔚 Kontrol tamamlandı")
    
    def cleanup(self):
        """Temizlik işlemleri"""
        logger.info("🧹 Temizlik yapılıyor...")
        self.session.close()
        logger.info("✅ Session kapatıldı")

def main():
    """Test için"""
    checker = AppointmentChecker()
    result = checker.run_check()
    print(f"\n{'='*60}")
    print(f"SONUÇ: {result}")
    print(f"{'='*60}\n")
    checker.cleanup()

if __name__ == "__main__":
    main()
