# 🚀 Bright Data Unlocker API Entegrasyonu

## 📊 Önemli Değişiklik

**Selenium/SeleniumBase başarısız oldu!** 60 saniye boyunla Cloudflare geçilemedi.

Artık **Bright Data Unlocker API** kullanıyoruz - profesyonel Cloudflare bypass çözümü.

## ✅ Yeni Mimari

### Eski Yöntem (BAŞARISIZ):
```
Selenium → UC Mode → SeleniumBase → Cloudflare (60s timeout) ❌
```

### Yeni Yöntem (Bright Data):
```
HTTP Request → Bright Data Unlocker API → Clean HTML ✅
```

## 🔧 Kurulum

### 1. Bright Data API Key Al

1. **Bright Data hesabı aç:** https://brightdata.com
2. **Unlocker API** ürününü aktive et
3. **API Key** oluştur
4. **Billing** bilgilerini gir (sadece başarılı request'ler için ödeme)

### 2. Environment Variables

Railway Dashboard → Variables → Ekle:

```bash
BRIGHTDATA_API_KEY=your_api_key_here
MISTRAL_API_KEY=CNo9XqLhjxqcRnmFQD5HHe7wdSjM7JO6
```

### 3. Kod Değişikliği

`src/app.py` içinde import değişikliği:

```python
# ESKİ:
from src.checker import AppointmentChecker

# YENİ:
from src.checker_brightdata import AppointmentChecker
```

## 📊 Bright Data Avantajları

| Özellik | Selenium | Bright Data |
|---------|----------|-------------|
| Cloudflare Bypass | ❌ 60s timeout | ✅ %99.9 başarı |
| Proxy Rotation | ❌ Manuel | ✅ Otomatik |
| CAPTCHA Handling | ❌ Kısmi | ✅ Dahil |
| Maintenance | ❌ Sürekli update | ✅ Yönetilir |
| Headless Mode | ❌ Sorunlu | ✅ Sorunsuz |
| Hız | 🐢 90-120s | ⚡ 5-10s |
| Railway Uyumluluğu | ❌ Chrome sorunları | ✅ Sadece HTTP |

## 🎯 API Kullanımı

### Request:
```json
{
  "url": "https://it-tr-appointment.idata.com.tr/tr",
  "format": "html",
  "country": "tr",
  "render": true,
  "timeout": 60000
}
```

### Response:
```html
<!DOCTYPE html>
<html>
  <!-- Clean HTML, Cloudflare bypass edilmiş! -->
  <img class="imageCaptcha" src="data:image/png;base64,..." />
</html>
```

## 💰 Maliyet

- **Pricing:** Pay-per-use (başarılı request başına)
- **Free Trial:** İlk 100 request ücretsiz
- **Tahmin:** ~$0.01 - $0.05 per request
- **Aylık (her 60s):** ~43,200 request/ay × $0.03 = **~$1,296/ay**

**Alternatif:** Check interval'i artır → 5 dakika = $260/ay

## 🔄 Migration Checklist

- [x] ✅ Bright Data Unlocker API client oluşturuldu (`checker_brightdata.py`)
- [x] ✅ BeautifulSoup HTML parsing eklendi
- [x] ✅ CAPTCHA extraction metodu yazıldı
- [x] ✅ Mistral AI base64 CAPTCHA solver eklendi
- [x] ✅ Config'e BRIGHTDATA_API_KEY eklendi
- [x] ✅ Requirements.txt güncellendi (beautifulsoup4)
- [ ] ⏳ app.py import değişikliği (ESKİ checker → YENİ checker_brightdata)
- [ ] ⏳ Railway Variables ekleme (BRIGHTDATA_API_KEY)
- [ ] ⏳ Test deployment
- [ ] ⏳ Production monitoring

## 🚦 Test Adımları

### Lokal Test:
```bash
# .env dosyası oluştur
echo "BRIGHTDATA_API_KEY=your_key_here" >> .env
echo "MISTRAL_API_KEY=CNo9XqLhjxqcRnmFQD5HHe7wdSjM7JO6" >> .env

# Direkt test
python src/checker_brightdata.py

# Beklenen çıktı:
# 🌐 Bright Data Unlocker API ile sayfa getiriliyor...
# ✅ Sayfa başarıyla getirildi!
# ✅ Cloudflare başarıyla bypass edildi!
# 🔐 CAPTCHA bulundu, Mistral AI ile çözülüyor...
```

### Railway Test:
1. Commit ve push yap
2. Railway Variables ekle (BRIGHTDATA_API_KEY)
3. Deployment loglarını izle
4. Application logs'da "✅ Cloudflare başarıyla bypass edildi!" ara

## 📖 Dokümantasyon

- **Bright Data Unlocker API:** https://docs.brightdata.com/scraping-automation/web-unlocker/introduction
- **API Reference:** https://docs.brightdata.com/scraping-automation/web-unlocker/api-reference
- **Pricing:** https://brightdata.com/pricing/web-unlocker

## 🎯 Sonraki Adımlar

1. **Bright Data hesabı aç ve API key al**
2. **Railway Variables ekle** (BRIGHTDATA_API_KEY)
3. **app.py import değiştir** (checker → checker_brightdata)
4. **Commit + push** → Railway auto-deploy
5. **Logs izle** → "✅ Cloudflare başarıyla bypass edildi!" görmeli

---

**Not:** Selenium tamamen kaldırılabilir ama şimdilik opsiyonel bırakıyoruz (fallback için).
