"""
Test: captcha_bot.py'deki ÇALIŞAN Cloudflare bypass yöntemini test et
"""

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaptchaBotMethodTester:
    """captcha_bot.py'deki yöntemi test et"""
    
    def __init__(self):
        self.driver = None
        self.url = "https://it-tr-appointment.idata.com.tr/tr"
        self.initial_window_width = 1280
        self.initial_window_height = 720
        
    def setup_driver(self, headless=True):
        """captcha_bot.py'deki setup_driver() metodunu headless olarak kullanan tam versiyon"""
        try:
            mode = "HEADLESS" if headless else "VISIBLE"
            logger.info(f"🚀 Setting up Chrome ({mode}) with captcha_bot method...")
            
            # Chrome profilini hazırla (headless için de user-data-dir kullanılabilir)
            chrome_profile = os.path.join(os.getcwd(), "chrome_profile_test")
            os.makedirs(chrome_profile, exist_ok=True)
            
            # User agent (gerçek tarayıcı gibi göster)
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            )
            
            # Undetected Chrome options
            uc_options = uc.ChromeOptions()
            uc_options.add_argument(f'user-agent={user_agent}')
            uc_options.add_argument(f"--window-size={self.initial_window_width},{self.initial_window_height}")
            uc_options.add_argument(f'--user-data-dir={chrome_profile}')
            uc_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Headless için gerekli argümanlar
            if headless:
                uc_options.add_argument("--headless=new")        # yeni headless modu
                uc_options.add_argument("--disable-gpu")         # GPU ile ilgili sorunları önlemek için
                uc_options.add_argument("--no-sandbox")          # bazı linux ortamlarda gerekli
                uc_options.add_argument("--disable-dev-shm-usage")
                uc_options.add_argument("--disable-features=NetworkService,NetworkServiceInProcess")
            
            # Chrome'u başlat (version_main=140 for Chrome 140)
            self.driver = uc.Chrome(
                options=uc_options,
                version_main=140,
                headless=headless
            )
            
            # WebDriver özelliğini gizle (CDP ile daha güvenilir)
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                logger.info("✅ WebDriver masking applied via CDP")
            except Exception as e:
                logger.warning(f"⚠️  CDP method failed: {e}, trying fallback...")
                # fallback
                try:
                    self.driver.execute_script(
                        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                    )
                    logger.info("✅ WebDriver masking applied via execute_script")
                except Exception as e2:
                    logger.error(f"❌ Both masking methods failed: {e2}")
            
            logger.info(f"✅ Chrome started in {mode} mode with captcha_bot method!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def wait_for_cloudflare(self, timeout=60):
        """captcha_bot.py'deki wait_for_cloudflare() metodunu kullan"""
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
                logger.warning(f"⚠️  Error during wait: {e}")
                time.sleep(2)
        
        logger.error("❌ Cloudflare challenge timeout")
        return False
    
    def test_full_flow(self):
        """Tam akışı test et: setup → navigate → wait → analyze"""
        try:
            logger.info("\n" + "="*60)
            logger.info("TEST: captcha_bot.py Method (FULL FLOW)")
            logger.info("="*60)
            
            start_time = time.time()
            
            # 1. Chrome'u başlat
            if not self.setup_driver():
                logger.error("❌ Driver setup failed")
                return False
            
            # 2. Siteye git
            logger.info(f"🌐 Navigating to: {self.url}")
            self.driver.get(self.url)
            
            # 3. Cloudflare'i bekle
            cloudflare_passed = self.wait_for_cloudflare(timeout=60)
            
            if not cloudflare_passed:
                logger.error("❌ Could not bypass Cloudflare")
                return False
            
            # 4. Sonuçları analiz et
            elapsed = time.time() - start_time
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            title = self.driver.title
            
            logger.info("\n" + "="*60)
            logger.info("📊 RESULTS")
            logger.info("="*60)
            logger.info(f"✅ Success: True")
            logger.info(f"⏱️  Time: {elapsed:.2f} seconds")
            logger.info(f"📊 HTML Length: {len(page_source):,} chars")
            logger.info(f"🔗 Current URL: {current_url}")
            logger.info(f"📄 Page Title: {title}")
            
            # CAPTCHA kontrolü
            if 'captcha' in page_source.lower() or 'imageCaptcha' in page_source:
                logger.info("🔐 CAPTCHA found in page!")
            else:
                logger.warning("⚠️  CAPTCHA not found!")
            
            # HTML preview
            preview = page_source[:500]
            logger.info(f"\n📄 HTML Preview:\n{preview}...")
            
            # Başarı kriteri: 40,000+ karakter
            if len(page_source) > 40000:
                logger.info("\n🎉 SUCCESS! Full page loaded (40K+ chars)")
                logger.info("✅ Cloudflare bypassed successfully!")
                logger.info(f"⏱️  Speed: {elapsed:.2f}s (vs Bright Data 60s)")
                logger.info("💰 Cost: FREE (vs $64.80/month)")
                return True
            else:
                logger.warning(f"\n⚠️  Page too short ({len(page_source):,} chars)")
                logger.warning("Expected 40,000+ chars for full page")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        finally:
            if self.driver:
                logger.info("\n🧹 Closing browser...")
                try:
                    self.driver.quit()
                except:
                    pass


if __name__ == "__main__":
    import sys
    
    # Komut satırından mode alabilmek için
    headless_mode = True  # Varsayılan HEADLESS
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['visible', 'v', 'false', '0']:
            headless_mode = False
    
    mode_str = "HEADLESS" if headless_mode else "VISIBLE"
    
    print("\n" + "="*60)
    print(f"🧪 Testing captcha_bot.py's Cloudflare Bypass ({mode_str})")
    print("="*60)
    print(f"💡 Mode: {mode_str}")
    print(f"🎯 Testing Railway-compatible headless configuration")
    print("="*60 + "\n")
    
    # Test 1: Seçilen mod ile test
    print(f"\n{'='*60}")
    print(f"TEST 1: {mode_str} Mode")
    print(f"{'='*60}\n")
    
    tester1 = CaptchaBotMethodTester()
    
    # setup_driver metodunu güncellenmiş parametre ile çağır
    class HeadlessTester(CaptchaBotMethodTester):
        def test_full_flow(self):
            try:
                logger.info("\n" + "="*60)
                logger.info(f"TEST: captcha_bot.py Method ({mode_str} MODE)")
                logger.info("="*60)
                
                start_time = time.time()
                
                # 1. Chrome'u başlat (headless parametresi ile)
                if not self.setup_driver(headless=headless_mode):
                    logger.error("❌ Driver setup failed")
                    return False
                
                # 2. Siteye git
                logger.info(f"🌐 Navigating to: {self.url}")
                self.driver.get(self.url)
                
                # 3. Cloudflare'i bekle
                cloudflare_passed = self.wait_for_cloudflare(timeout=60)
                
                if not cloudflare_passed:
                    logger.error("❌ Could not bypass Cloudflare")
                    return False
                
                # 4. Sonuçları analiz et
                elapsed = time.time() - start_time
                page_source = self.driver.page_source
                current_url = self.driver.current_url
                title = self.driver.title
                
                logger.info("\n" + "="*60)
                logger.info("📊 RESULTS")
                logger.info("="*60)
                logger.info(f"✅ Success: True")
                logger.info(f"⏱️  Time: {elapsed:.2f} seconds")
                logger.info(f"📊 HTML Length: {len(page_source):,} chars")
                logger.info(f"🔗 Current URL: {current_url}")
                logger.info(f"📄 Page Title: {title}")
                
                # CAPTCHA kontrolü
                if 'captcha' in page_source.lower() or 'imageCaptcha' in page_source:
                    logger.info("🔐 CAPTCHA found in page!")
                else:
                    logger.warning("⚠️  CAPTCHA not found!")
                
                # HTML preview
                preview = page_source[:500]
                logger.info(f"\n📄 HTML Preview:\n{preview}...")
                
                # Başarı kriteri: 40,000+ karakter
                if len(page_source) > 40000:
                    logger.info("\n🎉 SUCCESS! Full page loaded (40K+ chars)")
                    logger.info("✅ Cloudflare bypassed successfully!")
                    logger.info(f"⏱️  Speed: {elapsed:.2f}s (vs Bright Data 60s)")
                    logger.info("💰 Cost: FREE (vs $64.80/month)")
                    return True
                else:
                    logger.warning(f"\n⚠️  Page too short ({len(page_source):,} chars)")
                    logger.warning("Expected 40,000+ chars for full page")
                    logger.warning("⚠️  Cloudflare may still be active!")
                    return False
                
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
            
            finally:
                if self.driver:
                    logger.info("\n🧹 Closing browser...")
                    try:
                        self.driver.quit()
                    except:
                        pass
    
    tester = HeadlessTester()
    success = tester.test_full_flow()
    
    print("\n" + "="*60)
    print(f"📊 FINAL RESULTS ({mode_str} MODE)")
    print("="*60)
    if success:
        print("✅ TEST PASSED!")
        print(f"🎯 captcha_bot.py method works in {mode_str} mode!")
        print("💡 Ready for Railway deployment!")
    else:
        print("❌ TEST FAILED!")
        print(f"⚠️  {mode_str} mode needs investigation")
        if headless_mode:
            print("\n💡 TIP: Try visible mode to debug:")
            print("   python test_captcha_bot_method.py visible")
    print("="*60 + "\n")
