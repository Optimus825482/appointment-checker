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
        captcha_selectors = [
            "//img[contains(@alt, 'captcha')]",
            "//img[contains(@id, 'captcha')]",
            "//div[contains(@class, 'captcha')]",
            "//iframe[contains(@src, 'recaptcha')]",
            "//iframe[contains(@src, 'hcaptcha')]"
        ]
        
        for selector in captcha_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    logger.info(f"🎯 CAPTCHA tespit edildi: {selector}")
                    return elements[0]
            except Exception:
                continue
        
        logger.info("✅ CAPTCHA bulunamadı")
        return None
    
    def solve_image_captcha(self, driver, captcha_element):
        """Görsel CAPTCHA'yı Mistral ile çöz"""
        if not self.client:
            logger.error("❌ Mistral API anahtarı yok!")
            return False
        
        try:
            # Ekran görüntüsü al
            screenshot = captcha_element.screenshot_as_png
            image_base64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Mistral'a gönder
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bu CAPTCHA görüntüsündeki metni oku. Sadece karakterleri ver, başka açıklama yapma."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{image_base64}"
                        }
                    ]
                }
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            captcha_text = response.choices[0].message.content.strip()
            logger.info(f"🔤 Tespit edilen CAPTCHA: {captcha_text}")
            
            # Input alanına yaz
            input_field = driver.find_element(By.XPATH, 
                "//input[@type='text' and (contains(@name, 'captcha') or contains(@id, 'captcha') or contains(@placeholder, 'captcha'))]")
            
            input_field.clear()
            time.sleep(0.5)
            input_field.send_keys(captcha_text)
            
            # Submit
            submit_btn = driver.find_element(By.XPATH,
                "//button[@type='submit'] | //input[@type='submit']")
            submit_btn.click()
            
            time.sleep(2)
            
            # Hata kontrolü
            errors = driver.find_elements(By.XPATH,
                "//*[contains(text(), 'yanlış') or contains(text(), 'hatalı') or contains(text(), 'geçersiz')]")
            
            if errors:
                logger.warning("⚠️ CAPTCHA yanlış")
                return False
            
            logger.info("✅ CAPTCHA başarıyla çözüldü!")
            return True
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA çözüm hatası: {e}")
            return False
    
    def solve_captcha(self, driver, max_retries=3):
        """Ana CAPTCHA çözüm fonksiyonu"""
        for attempt in range(max_retries):
            logger.info(f"🔄 CAPTCHA çözme denemesi {attempt + 1}/{max_retries}")
            
            captcha_element = self.detect_captcha(driver)
            
            if not captcha_element:
                return True  # CAPTCHA yok
            
            if self.solve_image_captcha(driver, captcha_element):
                return True
            
            time.sleep(2)
        
        return False