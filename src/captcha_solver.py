from mistralai.client import MistralClient
from selenium.webdriver.common.by import By
import base64
import time
import logging

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = MistralClient(api_key=api_key) if api_key else None
        self.model = "pixtral-12b-2409"
    
    def detect_captcha(self, driver):
        """CAPTCHA varlığını tespit et"""
        logger.info("🔍 CAPTCHA aranıyor...")
        captcha_selectors = [
            ("CLASS_NAME", "imageCaptcha"),  # Ana CAPTCHA selector
            ("XPATH", "//img[contains(@alt, 'CAPTCHA')]"),
            ("XPATH", "//img[contains(@class, 'imageCaptcha')]"),
            ("XPATH", "//img[contains(@src, 'data:image/png;base64')]"),
            ("XPATH", "//iframe[contains(@src, 'recaptcha')]"),
            ("XPATH", "//iframe[contains(@src, 'hcaptcha')]")
        ]
        
        for idx, (method, selector) in enumerate(captcha_selectors, 1):
            try:
                logger.info(f"🔎 CAPTCHA selector {idx}/{len(captcha_selectors)} kontrol ediliyor ({method}: {selector[:50]}...)...")
                
                if method == "CLASS_NAME":
                    elements = driver.find_elements(By.CLASS_NAME, selector)
                else:
                    elements = driver.find_elements(By.XPATH, selector)
                    
                if elements:
                    logger.info(f"🎯 CAPTCHA tespit edildi! Method: {method}, Selector: {selector}")
                    logger.info(f"📊 {len(elements)} adet CAPTCHA elementi bulundu")
                    logger.info(f"📍 Element tag: {elements[0].tag_name}, src başlangıcı: {elements[0].get_attribute('src')[:80] if elements[0].get_attribute('src') else 'N/A'}...")
                    return elements[0]
                else:
                    logger.debug(f"❌ Bu selector'da CAPTCHA yok: {method} - {selector[:50]}...")
            except Exception as e:
                logger.debug(f"⚠️ Selector {idx} hatası: {e}")
                continue
        
        logger.info("✅ Sayfada CAPTCHA bulunamadı (CAPTCHA yok veya zaten geçildi)")
        return None
    
    def solve_image_captcha(self, driver, captcha_element):
        """Görsel CAPTCHA'yı Mistral ile çöz"""
        if not self.client:
            logger.error("❌ Mistral API anahtarı yok!")
            return False
        
        try:
            # Base64 src'yi direkt al (ekran görüntüsü değil)
            logger.info("📸 CAPTCHA base64 verisi alınıyor (src attribute)...")
            src = captcha_element.get_attribute("src")
            
            if not src or not src.startswith("data:image"):
                logger.error("❌ CAPTCHA src attribute'u geçerli base64 formatında değil!")
                return False
            
            # data:image/png;base64,XXXXX formatından base64 kısmını çıkar
            logger.info("✅ CAPTCHA src formatı doğrulandı")
            image_base64 = src.split(",", 1)[1]
            image_size = len(image_base64)
            logger.info(f"✅ Base64 verisi çıkarıldı ({image_size} karakter)")
            
            # Arşiv için kaydet (debugging)
            try:
                import os
                os.makedirs("captcha_images", exist_ok=True)
                timestamp = int(time.time() * 1000) % 1000000
                captcha_path = f"captcha_images/captcha_{timestamp:06d}.png"
                
                # Base64'ü decode et ve kaydet
                image_data = base64.b64decode(image_base64)
                with open(captcha_path, 'wb') as f:
                    f.write(image_data)
                logger.info(f"💾 CAPTCHA arşivlendi: {captcha_path}")
            except Exception as e:
                logger.warning(f"⚠️ CAPTCHA arşivleme hatası (kritik değil): {e}")
            
            # Mistral'a gönder
            logger.info(f"🤖 Mistral AI Vision API'ye gönderiliyor (model: {self.model})...")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bu CAPTCHA görüntüsündeki 6 karakterli metni oku. Sadece büyük harflerle karakterleri ver, başka açıklama yapma."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{image_base64}"
                        }
                    ]
                }
            ]
            
            logger.info("⏳ Mistral AI yanıtı bekleniyor...")
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            captcha_text = response.choices[0].message.content.strip().upper()
            logger.info(f"🔤 Mistral AI tarafından tespit edilen CAPTCHA metni: '{captcha_text}'")
            
            # Input alanına yaz (id: mailConfirmCodeControl)
            logger.info("🔍 CAPTCHA input alanı aranıyor (id: mailConfirmCodeControl)...")
            input_field = driver.find_element(By.ID, "mailConfirmCodeControl")
            
            logger.info("✅ Input alanı bulundu (#mailConfirmCodeControl), eski değer temizleniyor...")
            input_field.clear()
            time.sleep(0.3)
            
            logger.info(f"⌨️ CAPTCHA metni giriliyor: '{captcha_text}'")
            input_field.send_keys(captcha_text)
            logger.info("✅ Metin başarıyla girildi")
            time.sleep(0.5)
            
            # Submit (id: confirmationbtn)
            logger.info("🔍 'RANDEVU AL' butonu aranıyor (id: confirmationbtn)...")
            submit_btn = driver.find_element(By.ID, "confirmationbtn")
            logger.info("✅ 'RANDEVU AL' butonu bulundu, tıklanıyor...")
            submit_btn.click()
            logger.info("✅ Form gönderildi, yanıt bekleniyor (3 saniye)...")
            
            time.sleep(3)
            
            # Hata kontrolü - SweetAlert2 modalını kontrol et
            logger.info("🔍 CAPTCHA doğruluğu kontrol ediliyor (SweetAlert2 modal)...")
            
            # Hata modalını ara
            try:
                error_modal = driver.find_element(By.CLASS_NAME, "swal2-modal")
                error_text = error_modal.text.lower()
                
                if "yanlış" in error_text or "hata" in error_text:
                    logger.warning(f"⚠️ CAPTCHA yanlış girildi! Modal mesajı: {error_text[:100]}...")
                    
                    # "Tamam" butonuna bas
                    logger.info("🖱️ Hata modalındaki 'Tamam' butonuna basılıyor...")
                    ok_button = driver.find_element(By.CLASS_NAME, "swal2-confirm")
                    ok_button.click()
                    logger.info("✅ Modal kapatıldı, tekrar denenecek")
                    time.sleep(1)
                    
                    return False
                    
            except Exception as e:
                logger.info("✅ Hata modalı bulunamadı (CAPTCHA muhtemelen doğru)")
            
            logger.info("✅ CAPTCHA başarıyla çözüldü ve doğrulandı!")
            return True
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA çözüm hatası: {e}")
            return False
    
    def solve_captcha_from_base64(self, base64_data):
        """
        Base64 CAPTCHA görselini Mistral ile çöz (Bright Data için)
        
        Args:
            base64_data: data:image/png;base64,XXXXX formatında base64 string
            
        Returns:
            str: CAPTCHA metni veya None
        """
        if not self.client:
            logger.error("❌ Mistral API anahtarı yok!")
            return None
        
        try:
            # data:image/png;base64,XXXXX formatını kontrol et
            if not base64_data.startswith("data:image"):
                logger.error("❌ Base64 data geçerli formatta değil!")
                return None
            
            logger.info("📸 Base64 CAPTCHA verisi işleniyor...")
            
            # Mistral'a gönder
            logger.info(f"🤖 Mistral AI Vision API'ye gönderiliyor (model: {self.model})...")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bu CAPTCHA görüntüsündeki 6 karakterli metni oku. Sadece büyük harflerle karakterleri ver, başka açıklama yapma."
                        },
                        {
                            "type": "image_url",
                            "image_url": base64_data
                        }
                    ]
                }
            ]
            
            logger.info("⏳ Mistral AI yanıtı bekleniyor...")
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            captcha_text = response.choices[0].message.content.strip().upper()
            logger.info(f"🔤 Mistral AI tarafından tespit edilen CAPTCHA metni: '{captcha_text}'")
            
            return captcha_text
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA çözüm hatası: {e}")
            return None
    
    def solve_captcha(self, driver, max_retries=3):
        """Ana CAPTCHA çözüm fonksiyonu"""
        logger.info(f"🎯 CAPTCHA çözüm süreci başlatıldı (maksimum {max_retries} deneme hakkı)")
        
        for attempt in range(max_retries):
            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"🔄 CAPTCHA Çözme Denemesi: {attempt + 1}/{max_retries}")
            logger.info(f"{'='*60}")
            
            captcha_element = self.detect_captcha(driver)
            
            if not captcha_element:
                logger.info("✅ Sayfada CAPTCHA yok, bir sonraki adıma geçiliyor")
                return True  # CAPTCHA yok
            
            logger.info("🚀 CAPTCHA çözme işlemi başlıyor...")
            if self.solve_image_captcha(driver, captcha_element):
                logger.info("🎉 CAPTCHA başarıyla çözüldü!")
                return True
            
            if attempt < max_retries - 1:
                logger.warning(f"❌ Deneme {attempt + 1} başarısız, 2 saniye sonra tekrar denenecek...")
                time.sleep(2)
            else:
                logger.error(f"❌ Tüm denemeler tükendi ({max_retries}/{max_retries})")
        
        logger.error("💥 CAPTCHA çözülemedi! Maksimum deneme sayısına ulaşıldı")
        return False