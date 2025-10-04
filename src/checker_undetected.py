"""
Undetected ChromeDriver ile Cloudflare bypass
Bright Data'dan 4-6x daha hızlı ve ÜCRETSIZ!
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from dataclasses import dataclass
from typing import Optional
import os
import base64

logger = logging.getLogger(__name__)


@dataclass
class CheckerConfig:
    """Configuration for the appointment checker"""
    MISTRAL_API_KEY: str
    TARGET_URL: str = "https://it-tr-appointment.idata.com.tr/tr"
    # NOT: HEADLESS artık kullanılmıyor - Railway/Docker Xvfb (virtual display) kullanıyor


class UndetectedChecker:
    """Appointment checker using Undetected ChromeDriver"""
    
    def __init__(self, config: CheckerConfig):
        self.config = config
        self.driver = None
        
    def _get_chrome_options(self):
        """Chrome ayarlarını hazırla (captcha_bot.py yöntemi)"""
        # Chrome profil dizini (captcha_bot.py'deki gibi)
        chrome_profile = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(chrome_profile, exist_ok=True)
        
        # User agent (captcha_bot.py'deki gibi)
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        )
        
        # Undetected Chrome options
        options = uc.ChromeOptions()
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument(f"--window-size=1280,720")
        options.add_argument(f'--user-data-dir={chrome_profile}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Railway/Docker için (Xvfb kullanıyoruz - headless gerekmez!)
        # Sadece Docker environment için gerekli ayarlar
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')  # Docker'da GPU yok
        
        # NOT: --headless kullanmıyoruz! Xvfb virtual display sağlıyor
        # Bu sayede Cloudflare headless detection'ı atlatıyoruz
        
        return options
    
    def fetch_page(self, url: str, max_retries: int = 2) -> Optional[str]:
        """
        Sayfayı undetected Chrome ile getir
        
        Returns:
            HTML içeriği veya None (hata durumunda)
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 Attempt {attempt + 1}/{max_retries}: Starting Chrome...")
                start_time = time.time()
                
                # Chrome'u başlat (captcha_bot.py yöntemi)
                options = self._get_chrome_options()
                
                # Auto-detect Chrome version
                self.driver = uc.Chrome(
                    options=options,
                    version_main=140  # Auto-download matching driver
                )
                
                # WebDriver özelliğini gizle (captcha_bot.py'deki gibi)
                self.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                
                logger.info(f"🌐 Navigating to: {url}")
                self.driver.get(url)
                
                # Sayfanın yüklenmesini bekle
                logger.info("⏳ Waiting for page load...")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Cloudflare challenge'ı bekle (captcha_bot.py yöntemi)
                cloudflare_passed = self._wait_for_cloudflare(timeout=60)
                
                if not cloudflare_passed:
                    logger.error("❌ Cloudflare challenge failed")
                    self._close_browser()
                    
                    if attempt < max_retries - 1:
                        logger.info(f"🔄 Retrying... ({attempt + 2}/{max_retries})")
                        time.sleep(3)
                        continue
                    return None
                
                page_source = self.driver.page_source
                current_url = self.driver.current_url
                title = self.driver.title
                elapsed = time.time() - start_time
                
                logger.info(f"✅ Page fetched successfully!")
                logger.info(f"⏱️  Time: {elapsed:.2f} seconds")
                logger.info(f"📊 HTML Length: {len(page_source):,} chars")
                logger.info(f"📄 Page Title: {title}")
                
                self._close_browser()
                return page_source
                
            except Exception as e:
                logger.error(f"❌ Error fetching page: {e}")
                self._close_browser()
                
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(3)
                    continue
                
                return None
        
        return None
    
    def _wait_for_cloudflare(self, timeout=60):
        """
        Cloudflare challenge'ını bekle (captcha_bot.py yöntemi)
        
        Returns:
            True if Cloudflare passed, False if timeout
        """
        logger.info("⏳ Waiting for Cloudflare challenge to pass...")
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                ps = self.driver.page_source.lower()
                title = self.driver.title or ""
                
                # Cloudflare challenge markers
                markers = [
                    "cloudflare",
                    "checking your browser",
                    "just a moment",
                    "cf-challenge",
                    "turnstile",
                    "attention required",
                    "bir dakika lütfen"
                ]
                
                if any(m in ps for m in markers):
                    logger.info("🔄 Cloudflare challenge detected, waiting...")
                    time.sleep(3)
                    continue
                
                # Cloudflare geçildi!
                logger.info("✅ Cloudflare challenge passed!")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️  Error during Cloudflare wait: {e}")
                time.sleep(2)
        
        logger.error("❌ Cloudflare challenge timeout")
        return False
    
    def _close_browser(self):
        """Browser'ı güvenli şekilde kapat"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
    
    def check_appointments(self) -> dict:
        """
        Randevu kontrolü yap
        
        Returns:
            {
                'success': bool,
                'available': bool,
                'captcha_image': str (base64) or None,
                'html_length': int,
                'elapsed_time': float,
                'error': str or None
            }
        """
        start_time = time.time()
        result = {
            'success': False,
            'available': False,
            'captcha_image': None,
            'html_length': 0,
            'elapsed_time': 0,
            'error': None
        }
        
        try:
            logger.info("🔍 Starting appointment check...")
            
            # Sayfayı getir
            html = self.fetch_page(self.config.TARGET_URL)
            
            if not html:
                result['error'] = "Failed to fetch page"
                return result
            
            result['html_length'] = len(html)
            result['elapsed_time'] = time.time() - start_time
            
            # CAPTCHA kontrolü
            if 'captcha' in html.lower() or 'imageCaptcha' in html:
                logger.info("🔐 CAPTCHA detected!")
                
                # CAPTCHA'yı çöz (Mistral AI ile)
                # TODO: Implement CAPTCHA solving
                result['captcha_image'] = None  # Placeholder
            
            # Randevu kontrolü
            if "randevu" in html.lower() and "müsait" in html.lower():
                logger.info("🎉 Appointments available!")
                result['available'] = True
            else:
                logger.info("❌ No appointments available")
                result['available'] = False
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"❌ Check failed: {e}")
            result['error'] = str(e)
            result['elapsed_time'] = time.time() - start_time
            return result


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test config
    config = CheckerConfig(
        MISTRAL_API_KEY=os.getenv("MISTRAL_API_KEY", "")
        # NOT: Lokal testte görüntülü mod otomatik (DISPLAY yok ise)
        # Railway'de Xvfb virtual display sağlıyor
    )
    
    checker = UndetectedChecker(config)
    
    print("\n" + "="*60)
    print("🚀 Testing Undetected ChromeDriver Checker")
    print("="*60 + "\n")
    
    result = checker.check_appointments()
    
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    print(f"✅ Success: {result['success']}")
    print(f"📊 HTML Length: {result['html_length']:,} chars")
    print(f"⏱️  Time: {result['elapsed_time']:.2f} seconds")
    print(f"🎯 Available: {result['available']}")
    if result['error']:
        print(f"❌ Error: {result['error']}")
    print("="*60 + "\n")
