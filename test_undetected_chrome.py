import time
import sys
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


URL = "https://it-tr-appointment.idata.com.tr/tr"
OUTPUT_HTML = Path(__file__).parent / "aa.html"


def main():
    # Chrome options (headless + stealth)
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--lang=tr-TR,tr")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

    # Başlat (version_main=140 for Chrome 140)
    driver = uc.Chrome(options=options, version_main=140)
    driver.set_page_load_timeout(90)

    try:
        driver.get(URL)

        # Cloudflare bekletmesi için birkaç deneme (başarı garantisi yok)
        # Hedef: sayfa başlığı "Just a moment..." değilse veya önemli bir element görünürse devam etmek
        for _ in range(6):  # ~30-45 sn arası bekleme olasılığı
            title = driver.title or ""
            if "Just a moment" not in title:
                break
            time.sleep(5)

        # Bazı temel elementleri bekleme (başlık, dil seçimi, buton vs.)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#confirmationbtn, select.language, meta[name='csrf-token']"))
            )
        except Exception:
            # Element bulunamazsa yine de HTML'yi yazalım; Cloudflare sayfası olabilir
            pass

        html = driver.page_source
        OUTPUT_HTML.write_text(html, encoding="utf-8")
        print(f"[OK] HTML kaydedildi: {OUTPUT_HTML}")

    except Exception as e:
        print(f"[HATA] {e}")
        sys.exit(1)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
