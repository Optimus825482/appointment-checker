from mistralai import Mistral
import logging

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Mistral(api_key=api_key) if api_key else None
        self.model = "pixtral-12b-2409"
    
    def solve_captcha_from_base64(self, base64_data):
        """Base64 CAPTCHA görselini Mistral ile çöz"""
        if not self.client:
            logger.error("Mistral API anahtari yok!")
            return None
        
        try:
            if not base64_data.startswith("data:image"):
                logger.error("Base64 data gecerli formatta degil!")
                return None
            
            logger.info("Base64 CAPTCHA verisi isleniyor...")
            logger.info(f"Mistral AI Vision API'ye gonderiliyor (model: {self.model})...")
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "This image contains a 6-digit numeric CAPTCHA code. Read ONLY the 6 numbers from left to right. Return ONLY the 6 digits, nothing else. No letters, no spaces, no explanations. Example format: 123456"
                        },
                        {
                            "type": "image_url",
                            "image_url": base64_data
                        }
                    ]
                }
            ]
            
            logger.info("Mistral AI yaniti bekleniyor...")
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            captcha_text = response.choices[0].message.content.strip().upper()
            logger.info(f"Mistral AI tarafindan tespit edilen CAPTCHA metni: '{captcha_text}'")
            
            return captcha_text
            
        except Exception as e:
            logger.error(f"CAPTCHA cozum hatasi: {e}")
            return None
