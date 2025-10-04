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
        options = uc.ChromeOptions()
        
        # Headless mod (Railway için zorunlu)
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        
        # Bot tespitini engelle
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Rastgele pencere boyutu
        width = random.randint(1200, 1600)
        height = random.randint(800, 1200)
        options.add_argument(f'--window-size={width},{height}')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Railway'de Chromium binary path
        options.binary_location = self.config.CHROME_BIN
        
        try:
            # Undetected ChromeDriver ile başlat - use_subprocess=False önemli!
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=self.config.CHROMEDRIVER_PATH,
                use_subprocess=False
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
        logger.info("�️ Cloudflare doğrulama süreci başlatılıyor...")
        logger.info(f"⏱️ Maksimum bekleme süresi: {timeout} saniye")
        
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            # Sayfanın yüklenmesini bekle
            initial_wait = random.uniform(3, 5)
            logger.info(f"⏳ İlk sayfa yükleme bekleniyor ({initial_wait:.1f} saniye)...")
            time.sleep(initial_wait)
            
            # Cloudflare challenge geçilene kadar bekle
            logger.info("🔍 Sayfa durumu kontrol ediliyor...")
            wait.until(lambda driver: driver.execute_script(
                "return document.readyState === 'complete' && document.body.innerText.length > 100"
            ))
            logger.info("✅ Sayfa tamamen yüklendi (readyState: complete)")
            
            # "Doğrulanıyor" yazısının kaybolmasını bekle
            max_wait = 30
            start_time = time.time()
            logger.info(f"🔄 Cloudflare challenge kontrolü başlıyor (max {max_wait} saniye)...")
            
            check_count = 0
            while time.time() - start_time < max_wait:
                check_count += 1
                elapsed = int(time.time() - start_time)
                
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                
                if check_count % 5 == 1:  # Her 5 kontrolde bir log
                    logger.info(f"⏱️ Cloudflare kontrol #{check_count} ({elapsed}/{max_wait} saniye)")
                
                if 'doğrulanıyor' not in page_text and 'verifying' not in page_text:
                    logger.info(f"✅ Cloudflare challenge geçildi! (toplam {elapsed} saniye)")
                    logger.info("🎉 Artık ana sayfaya erişim sağlandı!")
                    return True
                else:
                    if check_count <= 2:
                        logger.info("⏳ Cloudflare 'Doğrulanıyor' ekranı görünüyor, bekleniyor...")
                
                time.sleep(1)
            
            logger.warning(f"⏱️ Cloudflare timeout! {max_wait} saniye içinde geçilemedi")
            return False
            
        except Exception as e:
            logger.error(f"❌ Cloudflare hatası: {e}")
            return False
    
    def human_like_behavior(self):
        """İnsan benzeri davranış simülasyonu"""
        logger.info("🤖 İnsan benzeri davranış simülasyonu başlıyor...")
        
        # Rastgele mouse hareketleri
        logger.info("🖱️ Rastgele mouse hareketleri simüle ediliyor (5 hareket)...")
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
        logger.info("✅ Mouse hareketleri tamamlandı")
        
        # Rastgele scroll
        scroll_amount = random.randint(100, 300)
        scroll_delay = random.uniform(0.5, 1.5)
        logger.info(f"📜 Sayfa scroll ediliyor (aşağı: {scroll_amount}px)...")
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        logger.info(f"⏳ {scroll_delay:.1f} saniye bekleniyor...")
        time.sleep(scroll_delay)
        logger.info(f"📜 Sayfa yukarı scroll ediliyor (yukarı: {scroll_amount}px)...")
        self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
        logger.info("✅ Scroll hareketleri tamamlandı")
    
    def check_appointments(self):
        """Randevu müsaitliği kontrolü"""
        logger.info("📅 Randevu durumu kontrol ediliyor...")
        
        try:
            # Sayfanın tamamen yüklenmesini bekle
            logger.info("⏳ Sayfa yüklenmesi bekleniyor (3 saniye)...")
            time.sleep(3)
            
            logger.info("📄 Sayfa içeriği analiz ediliyor...")
            page_source = self.driver.page_source.lower()
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
            
            logger.info(f"📊 Sayfa uzunluğu: {len(page_text)} karakter")
            
            # Randevu yok mesajlarını kontrol et
            no_appointment_keywords = [
                'randevu mevcut değil',
                'no appointment available',
                'randevu bulunamadı',
                'müsait randevu yok'
            ]
            
            logger.info("🔍 'Randevu yok' mesajları aranıyor...")
            has_no_appointment = any(keyword in page_text for keyword in no_appointment_keywords)
            
            if has_no_appointment:
                logger.info("❌ Sayfada 'randevu yok' mesajı tespit edildi")
            else:
                logger.info("✅ 'Randevu yok' mesajı bulunamadı, randevu butonları aranıyor...")
            
            if not has_no_appointment:
                # Randevu butonlarını ara
                appointment_selectors = [
                    "//button[contains(text(), 'Randevu')]",
                    "//a[contains(text(), 'Randevu')]",
                    "//button[contains(@class, 'appointment')]",
                    "//*[contains(text(), 'Müsait')]",
                    "//button[@type='submit']"
                ]
                
                for idx, selector in enumerate(appointment_selectors, 1):
                    try:
                        logger.info(f"🔎 Selector {idx}/{len(appointment_selectors)} deneniyor: {selector[:50]}...")
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            logger.info(f"📍 {len(elements)} adet element bulundu")
                            if elements[0].is_displayed():
                                logger.info("🎉 RANDEVU BULUNDU! Görünür buton tespit edildi!")
                                return True
                            else:
                                logger.info("⚠️ Element bulundu ama görünür değil")
                    except Exception as e:
                        logger.debug(f"❌ Selector {idx} hatası: {e}")
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
            logger.info("🚀 Kontrol başlatılıyor...")
            logger.info("🔧 Chrome driver kuruluyor...")
            if not self.setup_driver():
                logger.error("❌ Driver başlatılamadı!")
                return False
            
            # Sayfayı aç
            logger.info(f"🌐 Hedef URL'ye gidiliyor: {self.config.APPOINTMENT_URL}")
            self.driver.get(self.config.APPOINTMENT_URL)
            logger.info("✅ Sayfa yükleme başlatıldı")
            
            # Cloudflare'i geç
            logger.info("🛡️ Cloudflare bypass işlemi başlıyor...")
            if not self.wait_for_cloudflare():
                logger.error("❌ Cloudflare geçilemedi!")
                return False
            logger.info("✅ Cloudflare başarıyla bypass edildi!")
            
            # İnsan benzeri davranış
            wait_time = random.uniform(2, 4)
            logger.info(f"🤖 İnsan benzeri davranış simülasyonu ({wait_time:.1f} saniye)...")
            time.sleep(wait_time)
            self.human_like_behavior()
            logger.info("✅ İnsan benzeri hareketler tamamlandı")
            
            # CAPTCHA kontrolü
            logger.info("🔐 CAPTCHA çözme modülü başlatılıyor...")
            from src.captcha_solver import CaptchaSolver
            solver = CaptchaSolver(self.config.MISTRAL_API_KEY)
            logger.info("🎯 CAPTCHA tespit ve çözüm süreci başlıyor...")
            
            if not solver.solve_captcha(self.driver):
                logger.error("❌ CAPTCHA çözülemedi!")
                return False
            logger.info("✅ CAPTCHA işlemi tamamlandı!")
            
            # Randevu kontrolü
            logger.info("🔍 Randevu kontrol aşamasına geçiliyor...")
            return self.check_appointments()
            
        except Exception as e:
            logger.error(f"❌ Genel hata: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔚 Browser kapatıldı")