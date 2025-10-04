import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import random
import logging
from config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentChecker:
    def __init__(self):
        self.driver = None
        self.config = Config()
        
    def setup_driver(self):
        """Railway için optimize edilmiş driver ayarları"""
        options = Options()
        
        # Headless mod (Railway için zorunlu)
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        
        # Bot tespitini engelle
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Rastgele pencere boyutu
        width = random.randint(1200, 1600)
        height = random.randint(800, 1200)
        options.add_argument(f'--window-size={width},{height}')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Railway'de Chromium binary path
        options.binary_location = self.config.CHROME_BIN
        
        try:
            # Undetected ChromeDriver ile başlat
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=self.config.CHROMEDRIVER_PATH,
                version_main=120
            )
            
            # Bot tespitini engelleme scriptleri
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['tr-TR', 'tr', 'en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
            
            logger.info("✅ Chrome driver başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logger.error(f"❌ Driver başlatma hatası: {e}")
            return False
    
    def wait_for_cloudflare(self, timeout=30):
        """Cloudflare doğrulamasını bekle"""
        logger.info("🔄 Cloudflare doğrulaması bekleniyor...")
        
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            # Sayfanın yüklenmesini bekle
            time.sleep(random.uniform(3, 5))
            
            # Cloudflare challenge geçilene kadar bekle
            wait.until(lambda driver: driver.execute_script(
                "return document.readyState === 'complete' && document.body.innerText.length > 100"
            ))
            
            # "Doğrulanıyor" yazısının kaybolmasını bekle
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                
                if 'doğrulanıyor' not in page_text and 'verifying' not in page_text:
                    logger.info("✅ Cloudflare başarıyla geçildi!")
                    return True
                
                time.sleep(1)
            
            logger.warning("⏱️ Cloudflare timeout!")
            return False
            
        except Exception as e:
            logger.error(f"❌ Cloudflare hatası: {e}")
            return False
    
    def human_like_behavior(self):
        """İnsan benzeri davranış simülasyonu"""
        # Rastgele mouse hareketleri
        self.driver.execute_script("""
            function randomMove() {
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                const event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': x,
                    'clientY': y
                });
                document.dispatchEvent(event);
            }
            for(let i = 0; i < 5; i++) {
                setTimeout(randomMove, i * 200);
            }
        """)
        
        # Rastgele scroll
        scroll_amount = random.randint(100, 300)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.5, 1.5))
        self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
    
    def check_appointments(self):
        """Randevu müsaitliği kontrolü"""
        logger.info("📅 Randevu durumu kontrol ediliyor...")
        
        try:
            # Sayfanın tamamen yüklenmesini bekle
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            # Randevu yok mesajlarını kontrol et
            no_appointment_keywords = [
                'randevu mevcut değil',
                'no appointment available',
                'randevu bulunamadı',
                'müsait randevu yok'
            ]
            
            has_no_appointment = any(keyword in page_text for keyword in no_appointment_keywords)
            
            if not has_no_appointment:
                # Randevu butonlarını ara
                appointment_selectors = [
                    "//button[contains(text(), 'Randevu')]",
                    "//a[contains(text(), 'Randevu')]",
                    "//button[contains(@class, 'appointment')]",
                    "//*[contains(text(), 'Müsait')]",
                    "//button[@type='submit']"
                ]
                
                for selector in appointment_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements and elements[0].is_displayed():
                            logger.info("🎉 RANDEVU BULUNDU!")
                            return True
                    except:
                        continue
            
            logger.info("😔 Henüz randevu yok...")
            return False
            
        except Exception as e:
            logger.error(f"❌ Randevu kontrolü hatası: {e}")
            return False
    
    def run_check(self):
        """Tam kontrol döngüsü"""
        try:
            # Driver'ı başlat
            if not self.setup_driver():
                return False
            
            # Sayfayı aç
            logger.info(f"🌐 {self.config.APPOINTMENT_URL} açılıyor...")
            self.driver.get(self.config.APPOINTMENT_URL)
            
            # Cloudflare'i geç
            if not self.wait_for_cloudflare():
                logger.error("❌ Cloudflare geçilemedi!")
                return False
            
            # İnsan benzeri davranış
            time.sleep(random.uniform(2, 4))
            self.human_like_behavior()
            
            # CAPTCHA kontrolü
            from captcha_solver import CaptchaSolver
            solver = CaptchaSolver(self.config.MISTRAL_API_KEY)
            
            if not solver.solve_captcha(self.driver):
                logger.error("❌ CAPTCHA çözülemedi!")
                return False
            
            # Randevu kontrolü
            return self.check_appointments()
            
        except Exception as e:
            logger.error(f"❌ Genel hata: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔚 Browser kapatıldı")