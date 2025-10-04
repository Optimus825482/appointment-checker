import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
    
    def wait_for_cloudflare(self, timeout=90):
        """
        Cloudflare bypass - captcha_bot.py'den alındı
        Cloudflare tarayıcı kontrolü/Turnstile geçene kadar bekle
        """
        logger.info("🛡️ Cloudflare bypass başlatılıyor...")
        logger.info(f"⏱️ Maksimum bekleme: {timeout} saniye")
        
        start = time.time()
        challenge_attempted = False
        check_count = 0
        
        while time.time() - start < timeout:
            check_count += 1
            elapsed = int(time.time() - start)
            
            try:
                ps = self.driver.page_source.lower()
                url = (self.driver.current_url or '').lower()
                title = (self.driver.title or "")
                
                # Cloudflare marker listesi (captcha_bot.py'den)
                markers = [
                    "cloudflare",
                    "checking your browser",
                    "just a moment",
                    "cf-challenge",
                    "turnstile",
                    "attention required"
                ]
                
                # Marker kontrolü
                if any(m in ps or m in url for m in markers):
                    if check_count % 5 == 1:  # Her 5 kontrolde bir log
                        logger.info(f"⏳ Cloudflare marker bulundu ({elapsed}s)")
                    
                    # İlk denemede challenge handler çalıştır
                    if not challenge_attempted:
                        logger.info("🔍 Cloudflare challenge handler çağrılıyor...")
                        solved = self.handle_cloudflare_challenge(timeout=20)
                        if solved:
                            logger.info("✅ Challenge çözüldü!")
                            challenge_attempted = True
                            time.sleep(1.5)
                            continue
                        challenge_attempted = True
                    
                    time.sleep(2)
                    continue
                
                # Marker yok = başarılı!
                logger.info(f"✅ Cloudflare başarıyla geçildi! ({elapsed} saniye)")
                logger.info(f"📄 Sayfa başlığı: {title}")
                logger.info(f"🔗 URL: {self.driver.current_url[:80]}...")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Kontrol sırasında hata: {e}")
                time.sleep(2)
        
        # Timeout
        logger.error(f"❌ Cloudflare timeout! ({timeout}s)")
        logger.error(f"📄 Son başlık: {self.driver.title}")
        return False
    
    def handle_cloudflare_challenge(self, timeout=25):
        """
        Cloudflare challenge iframe içinde checkbox/button arar ve tıklar
        captcha_bot.py'den alındı
        """
        if self.driver is None:
            return False
        
        drivers = self.driver
        deadline = time.time() + max(5, timeout)
        attempted_click = False
        
        while time.time() < deadline:
            try:
                frames = drivers.find_elements(By.CSS_SELECTOR, "iframe")
            except Exception:
                frames = []
            
            for frame in frames:
                try:
                    title = (frame.get_attribute("title") or "").lower()
                    src = (frame.get_attribute("src") or "").lower()
                    
                    # Cloudflare/Turnstile iframe'i mi?
                    if not any(keyword in (title + " " + src) for keyword in 
                              ("cloudflare", "challenge", "turnstile", "hcaptcha")):
                        continue
                    
                    # Iframe'e geç
                    drivers.switch_to.frame(frame)
                    
                    # Tıklanabilir elementler
                    selectors = [
                        "input[type='checkbox']",
                        "label[for]",
                        "div.cf-turnstile",
                        "button[type='submit']",
                        "div[role='button']",
                        "span.cb-lc"
                    ]
                    
                    for selector in selectors:
                        try:
                            elements = drivers.find_elements(By.CSS_SELECTOR, selector)
                        except Exception:
                            continue
                        
                        for element in elements:
                            try:
                                if not element.is_displayed():
                                    continue
                                
                                attempted_click = True
                                
                                # İnsan benzeri tıklama
                                try:
                                    element.click()
                                    logger.info("✅ Cloudflare öğesine tıklandı")
                                    drivers.switch_to.default_content()
                                    return True
                                except Exception:
                                    # JS fallback
                                    try:
                                        drivers.execute_script("arguments[0].click();", element)
                                        logger.info("✅ Cloudflare öğesine JS ile tıklandı")
                                        drivers.switch_to.default_content()
                                        return True
                                    except Exception:
                                        continue
                            except Exception:
                                continue
                    
                    drivers.switch_to.default_content()
                except Exception:
                    try:
                        drivers.switch_to.default_content()
                    except Exception:
                        pass
            
            time.sleep(1.5)
        
        try:
            drivers.switch_to.default_content()
        except Exception:
            pass
        
        if attempted_click:
            logger.warning("⚠️ Cloudflare tıklama denendi ama başarısız")
        else:
            logger.info("ℹ️ Cloudflare challenge elementi bulunamadı")
        
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
            
            # İlk yükleme bekleme
            try:
                logger.info("⏳ CAPTCHA elementi bekleniyor (12s)...")
                WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "imageCaptcha"))
                )
                logger.info("✅ CAPTCHA elementi bulundu!")
            except TimeoutException:
                logger.info("⏳ CAPTCHA yüklenene kadar ek bekleme...")
                time.sleep(random.uniform(0.42, 0.68))
            
            # Cloudflare'i geç - TAM captcha_bot.py metodolojisi!
            logger.info("🛡️ Cloudflare bypass işlemi başlıyor...")
            if not self.wait_for_cloudflare(timeout=90):
                logger.error("❌ Cloudflare geçilemedi!")
                return False
            logger.info("✅ Cloudflare başarıyla bypass edildi!")
            
            # Sayfa yönlendirmesi
            logger.info("⏳ Form sayfası yükleniyor...")
            time.sleep(3)
            
            # İnsan benzeri davranış
            wait_time = random.uniform(2, 4)
            logger.info(f"🤖 İnsan benzeri davranış simülasyonu ({wait_time:.1f} saniye)...")
            time.sleep(wait_time)
            self.human_like_behavior()
            logger.info("✅ İnsan benzeri hareketler tamamlandı")
            
            # CAPTCHA kontrolü
            logger.info("🔐 CAPTCHA çözme modülü başlatılıyor...")
            logger.info(f"📄 Şu anki sayfa URL'si: {self.driver.current_url}")
            logger.info(f"📄 Sayfa başlığı: {self.driver.title}")
            
            # Sayfayı aşağı scroll et (CAPTCHA görünür hale gelsin)
            logger.info("📜 Sayfa aşağı kaydırılıyor (CAPTCHA'nın görünür olması için)...")
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)
            
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
