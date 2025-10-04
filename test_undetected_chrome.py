import os
import time
import json
import logging
import undetected_chromedriver as uc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeadlessDiagnostics:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.outdir = os.path.join(os.getcwd(), "headless_diagnostics")
        os.makedirs(self.outdir, exist_ok=True)

    def setup_headless(self, width=1280, height=720):
        try:
            logger.info("🔧 Headless setup starting...")
            options = uc.ChromeOptions()
            options.add_argument(f"--window-size={width},{height}")
            # NOT: --headless is intentionally used (we are diagnosing headless behavior)
            options.add_argument("--headless=new")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")

            # (KASITLI OLARAK HERHANGİ BİR 'ANTI-DETECTION' ARGÜMANI EKLENMİYOR)
            self.driver = uc.Chrome(options=options, version_main=140, headless=True)
            logger.info("✅ Headless browser started (diagnostic mode).")
            return True
        except Exception as e:
            logger.error(f"❌ Headless setup failed: {e}")
            return False

    def enable_console_and_network_logging(self):
        """CDP ile console mesajlarını ve basit network isteği özetini toplayalım."""
        try:
            # Console logları için event listener kur:
            self.driver.execute_cdp_cmd("Log.enable", {})
            # Network olayları için:
            self.driver.execute_cdp_cmd("Network.enable", {"maxTotalBufferSize": 10000000})
            # Basit: performans ve network için domain enable
            self.driver.execute_cdp_cmd("Performance.enable", {})
            logger.info("🔎 Console & Network logging enabled via CDP.")
        except Exception as e:
            logger.warning(f"⚠️  CDP enable failed: {e}")

    def gather_diagnostics(self, timeout=20):
        try:
            logger.info(f"🌐 Navigating to {self.url}")
            self.driver.get(self.url)

            # sayfanın yüklenmesi için bekle
            time.sleep(3)

            # sayfa kaynağı
            page_source = self.driver.page_source
            with open(os.path.join(self.outdir, "page_source.html"), "w", encoding="utf-8") as f:
                f.write(page_source)
            logger.info("📄 page_source.html saved")

            # başlık ve url
            meta = {
                "current_url": self.driver.current_url,
                "title": self.driver.title,
                "length_html": len(page_source)
            }
            with open(os.path.join(self.outdir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            logger.info("📝 meta.json saved")

            # ekran görüntüsü
            screenshot_path = os.path.join(self.outdir, "screenshot.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 screenshot saved: {screenshot_path}")

            # konsol loglarını al (Log.entryAdded yoksa boş dönebilir)
            try:
                logs = self.driver.execute_cdp_cmd("Log.getEntries", {})
                with open(os.path.join(self.outdir, "console_logs.json"), "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
                logger.info("🧾 console_logs.json saved")
            except Exception as e:
                logger.warning(f"⚠️ Console logs retrieval failed: {e}")

            # basit network isteği özetini al (son birkaç isteği topla)
            try:
                # Performance.getMetrics'den bazı metrikler alınabilir
                perf = self.driver.execute_cdp_cmd("Performance.getMetrics", {})
                with open(os.path.join(self.outdir, "performance.json"), "w", encoding="utf-8") as f:
                    json.dump(perf, f, indent=2, ensure_ascii=False)
                logger.info("📈 performance.json saved")
            except Exception as e:
                logger.warning(f"⚠️ Performance metrics failed: {e}")

            # Eğer daha detaylı HAR gerekiyorsa, buradan proxy/HAR kaydedici yönlendirmesi kullan
            # (örnek: BrowserMob Proxy veya mitmproxy ile entegre et)
            logger.info("✅ Diagnostics collection finished.")
            return True

        except Exception as e:
            logger.error(f"❌ Diagnostics failed: {e}")
            return False

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    url = "https://it-tr-appointment.idata.com.tr/tr"
    diag = HeadlessDiagnostics(url)
    if diag.setup_headless():
        diag.enable_console_and_network_logging()
        success = diag.gather_diagnostics()
        diag.close()
        if success:
            print("Diagnostics collected. Dosyaları 'headless_diagnostics' klasöründe kontrol et.")
        else:
            print("Diagnostics failed. Loglara bak.")
    else:
        print("Headless setup failed.")
