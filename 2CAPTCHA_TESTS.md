# 2Captcha Test Dosyaları

Bu dizinde 2Captcha servisini test etmek için hazırlanmış dosyalar bulunur.

## 📦 Gerekli Paket

```bash
pip install 2captcha-python
```

## 🔑 API Key Kurulumu

`.env` dosyasına ekleyin:

```env
APIKEY_2CAPTCHA=2cf3168177d616e92b996208721c272c
```

## 📝 Test Dosyaları

### 1. `test_2captcha_turnstile.py`

**Amaç**: 2Captcha servisinin temel Cloudflare Turnstile çözme fonksiyonunu test eder.

**Kullanım**:
```bash
python test_2captcha_turnstile.py
```

**Çıktı**:
- ✅ Turnstile token (15-40 saniye içinde)
- 📝 Sonuç `2captcha_result.txt` dosyasına kaydedilir
- 💰 Maliyet: ~$0.002-0.003 per solve

**Örnek Çıktı**:
```
✅ BAŞARILI!
⏱️  Süre: 15.39 saniye
🎯 Sonuç Kodu: XXXX.DUMMY.TOKEN.XXXX
```

---

### 2. `test_2captcha_idata.py`

**Amaç**: iDATA randevu sitesinde Cloudflare Turnstile'ı bypass edip form doldurma testi yapar.

**Kullanım**:
```bash
python test_2captcha_idata.py
```

**Süreç**:
1. 🌐 Chrome başlatılır (undetected-chromedriver)
2. 🔍 Cloudflare Turnstile iframe'i aranır
3. 🚀 2Captcha ile Turnstile çözülür
4. 💉 Token sayfaya inject edilir
5. ✅ Form elementleri kontrol edilir (İzmir seçimi)
6. 📝 Sonuç HTML kaydedilir

**Çıktı Dosyaları**:
- `idata_after_turnstile.html` - Turnstile bypass sonrası sayfa
- `idata_no_turnstile.html` - Turnstile bulunamazsa sayfa

**Özellikler**:
- ✅ Visible Chrome (Cloudflare detection bypass)
- ✅ Otomatik İzmir şehir seçimi
- ✅ Otomatik İzmir Ofisi seçimi
- ✅ CAPTCHA görsel kontrolü

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: Sadece Turnstile Test
Eğer sadece 2Captcha'nın çalışıp çalışmadığını test etmek istiyorsanız:
```bash
python test_2captcha_turnstile.py
```

### Senaryo 2: iDATA Entegrasyonu Test
Gerçek iDATA sitesiyle entegrasyon testi için:
```bash
python test_2captcha_idata.py
```

---

## 💡 Notlar

### API Maliyeti
- Cloudflare Turnstile: **$0.002-0.003 per solve**
- İşlem süresi: **15-40 saniye**
- Başarı oranı: **%95+**

### Hata Durumları

#### "API Key geçersiz"
```bash
❌ Hata: ERROR_WRONG_USER_KEY
```
**Çözüm**: `.env` dosyasındaki `APIKEY_2CAPTCHA` değerini kontrol edin.

#### "Bakiye yetersiz"
```bash
❌ Hata: ERROR_ZERO_BALANCE
```
**Çözüm**: 2Captcha hesabınıza bakiye ekleyin: https://2captcha.com

#### "Chrome crash"
```bash
❌ Hata: invalid session id
```
**Çözüm**: Chrome sürümünü kontrol edin (`version_main=140` parametresi)

---

## 📚 Dokümantasyon

- 2Captcha API Docs: https://2captcha.com/2captcha-api
- 2Captcha Python SDK: https://github.com/2captcha/2captcha-python
- Cloudflare Turnstile: https://developers.cloudflare.com/turnstile/

---

## 🔄 Entegrasyon Önerisi

Bu test dosyaları başarılı olduğunda, `checker_brightdata.py` dosyasına **2Captcha entegrasyonu eklenebilir**:

```python
# Bright Data API ile Cloudflare bypass başarısız olursa
# Fallback olarak 2Captcha kullan
if cloudflare_detected:
    from twocaptcha import TwoCaptcha
    solver = TwoCaptcha(os.getenv('APIKEY_2CAPTCHA'))
    
    result = solver.turnstile(
        sitekey='...',
        url=IDATA_URL
    )
    
    # Token'ı POST et
    ...
```

---

## ✅ Test Sonuçları

### test_2captcha_turnstile.py
- ✅ **ÇALIŞIYOR** (15.39s)
- Token: `XXXX.DUMMY.TOKEN.XXXX`
- CAPTCHA ID: `80803292584`

### test_2captcha_idata.py
- ⏳ **TEST DEVAM EDİYOR**
- Chrome başlatma: ✅
- URL açılıyor: ✅
- Turnstile detection: 🔄

---

## 🎉 Sonuç

2Captcha servisi **başarıyla çalışıyor**! iDATA entegrasyonu için:

1. ✅ Turnstile çözme fonksiyonu hazır
2. ⏳ iDATA sitesi entegrasyonu test ediliyor
3. 🔄 Bright Data + 2Captcha **hybrid yaklaşım** önerilir
