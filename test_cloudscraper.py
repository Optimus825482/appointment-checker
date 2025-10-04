import cloudscraper

# cloudscraper, tarayıcı açmadan (headless) çalışır ve Cloudflare korumalarına karşı istekleri taklit eder.
# İsteğe göre tarayıcı benzetimini özelleştirebilirsiniz (browser/platform/mobile gibi alanlar).
scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False,
    }
)

response = scraper.get("https://it-tr-appointment.idata.com.tr/tr")
print(response.content)