# Bright Data API Performans Optimizasyonu 🚀

## Mevcut Durum 📊

**Pipeline Breakdown:**
- GET request: ~30s (60s timeout)
- CAPTCHA çözme: ~0.5s (Mistral AI)
- CAPTCHA POST: ~20s (90s timeout)
- City POST: ~10s
- Office POST: ~10s
- Visa/Service POST: ~10s
- Person POST: ~10s
- Dynamic waits: ~6s (3 retry × 2s)
- **TOPLAM: ~90-100s**

---

## Optimizasyon Stratejileri 💡

### 1️⃣ Timeout Optimizasyonu ⏱️

**Mevcut:**
```python
response = requests.post(
    api_url,
    json=payload,
    headers=headers,
    timeout=60  # GET için
)

response = requests.post(
    api_url,
    json=payload,
    headers=headers,
    timeout=90  # POST için
)
```

**Önerilen:**
```python
# Önce test_brightdata_performance.py ile optimal timeout'u belirle
# Örnek: 45s yeterli olabilir

response = requests.post(
    api_url,
    json=payload,
    headers=headers,
    timeout=45  # Her ikisi için de 45s
)
```

**Kazanç:**
- Başarısız durumda daha hızlı timeout
- Hata mesajı 60s yerine 45s'de alınır
- Risk: Düşük timeout → daha fazla timeout hatası

**Tavsiye:** `test_brightdata_performance.py` ile timeout sensitivity testi yap!

---

### 2️⃣ Parallel Requests 🔀

**Mevcut:**
```python
# SIRA İLE (Sequential)
city_response = submit_form(city_data)      # 10s
office_response = submit_form(office_data)  # 10s
visa_response = submit_form(visa_data)      # 10s
person_response = submit_form(person_data)  # 10s
# TOPLAM: 40s
```

**Önerilen:**
```python
import concurrent.futures

# PARALEL (Parallel)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    # İlk 2 POST'u paralel yap
    future_city = executor.submit(submit_form, city_data)
    future_office = executor.submit(submit_form, office_data)
    
    city_response = future_city.result()  # 10s
    office_response = future_office.result()  # 10s (paralel → toplam 10s)
    
    # Son 2 POST'u paralel yap
    future_visa = executor.submit(submit_form, visa_data)
    future_person = executor.submit(submit_form, person_data)
    
    visa_response = future_visa.result()
    person_response = future_person.result()

# TOPLAM: ~20s (40s'den 20s'ye düştü!)
```

**Kazanç:**
- 40s → 20s (**20s kazanç!**)
- Risk: Bazı form POSTları sıra bağımlı olabilir (örn. city seçilmeden office seçilemez)

**Tavsiye:** 
- City → Office: Sıralı (office city'ye bağlı)
- Visa → Person: Paralel olabilir (birbirinden bağımsız)

---

### 3️⃣ Retry Strategy Optimizasyonu 🔄

**Mevcut:**
```python
def fetch_with_brightdata(self, url, max_retries=2):
    for attempt in range(max_retries):
        try:
            response = self.session.post(...)
            if response.status_code == 200:
                return response
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
```

**Önerilen:**
```python
def fetch_with_brightdata(self, url, max_retries=1):  # 2 → 1
    for attempt in range(max_retries):
        try:
            response = self.session.post(...)
            if response.status_code == 200:
                return response
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)  # 5s → 3s
                continue
```

**Kazanç:**
- Başarısız durumda: 2 retry × 30s = 60s → 1 retry × 30s = 30s (**30s kazanç**)
- Risk: Daha az retry → daha fazla başarısızlık riski

**Tavsiye:** Bright Data API başarı oranı yüksekse (>95%) max_retries=1 yeterli!

---

### 4️⃣ Response Caching 💾

**Mevcut:**
```python
# Her çalıştırmada aynı city/office seçeneklerini yeniden çek
city_response = submit_form({"city_id": 35})  # 10s
office_response = submit_form({"office_id": 123})  # 10s
```

**Önerilen:**
```python
import functools
import time

# Cache decorator
def cache_response(ttl=3600):  # 1 saat cache
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{args}_{kwargs}"
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if time.time() - cached_time < ttl:
                    logger.info(f"✅ Cache HIT: {func.__name__}")
                    return cached_result
            
            result = func(*args, **kwargs)
            cache[cache_key] = (time.time(), result)
            return result
        return wrapper
    return decorator

# Kullanım:
@cache_response(ttl=1800)  # 30 dakika cache
def get_city_options(self):
    response = self.fetch_with_brightdata(...)
    return response

@cache_response(ttl=1800)
def get_office_options(self, city_id):
    response = self.submit_form({"city_id": city_id})
    return response
```

**Kazanç:**
- Tekrarlı isteklerde: ~10-20s kazanç
- İlk çalıştırmada: Kazanç yok (cache doldurma)
- Risk: Cache stale olabilir (eski veri)

**Tavsiye:** 
- Scheduler mode için çok faydalı (her 1500s'de aynı form)
- Cache TTL = 30 dakika (form seçenekleri nadiren değişir)

---

### 5️⃣ Connection Pooling ✅

**Mevcut:**
```python
self.session = requests.Session()  # ✅ Zaten kullanılıyor!
```

**Durum:**
- ✅ requests.Session() kullanılıyor
- ✅ Keep-alive connections aktif
- ✅ Connection reuse mevcut

**Kazanç:**
- Zaten optimize edilmiş ✅

---

### 6️⃣ Dynamic Wait Optimizasyonu ⏳

**Mevcut:**
```python
for attempt in range(1, 3 + 1):
    city_select = soup.find('select', {'id': 'city_id'})
    if izmir_option:
        break
    if attempt < 3:
        time.sleep(2)  # 2s sabit bekleme
```

**Önerilen:**
```python
for attempt in range(1, 3 + 1):
    city_select = soup.find('select', {'id': 'city_id'})
    if izmir_option:
        break
    if attempt < 3:
        # Exponential backoff: 0.5s → 1s → 2s
        wait_time = 0.5 * (2 ** attempt)
        time.sleep(wait_time)
```

**Kazanç:**
- İlk denemede bulursa: 0s wait (2s'den 0s'ye)
- 2. denemede bulursa: 1s wait (2s'den 1s'ye)
- 3. denemede bulursa: 3s wait (4s'den 3s'ye)
- **Ortalama: ~4s → ~2s (2s kazanç)**

---

### 7️⃣ Bright Data API Parametreleri 🎛️

**Mevcut:**
```python
payload = {
    "url": url,
    "format": "raw"
}
```

**Önerilen:**
```python
payload = {
    "url": url,
    "format": "raw",
    "country": "tr",  # Türkiye proxy kullan (daha hızlı)
    "render_js": False  # JavaScript render'a gerek yoksa devre dışı bırak
}
```

**Kazanç:**
- Türkiye proxy: ~5-10s kazanç (daha yakın sunucu)
- JS render devre dışı: ~2-5s kazanç (gereksiz JS yürütme yok)

**Risk:**
- `render_js: False` → Dinamik içerik yüklenemeyebilir (AJAX)
- Önce test et!

---

### 8️⃣ Error Handling Optimizasyonu ⚠️

**Mevcut:**
```python
try:
    response = self.session.post(...)
    if response.status_code == 200:
        return response
    else:
        logger.error(f"❌ Status: {response.status_code}")
        return None
except Exception as e:
    logger.error(f"❌ Error: {e}")
    return None
```

**Önerilen:**
```python
try:
    response = self.session.post(...)
    if response.status_code == 200:
        return response
    elif response.status_code in [429, 503]:
        # Rate limit veya server busy → retry
        logger.warning(f"⚠️  Status: {response.status_code}, retrying...")
        time.sleep(5)
        return None  # Retry loop'a dön
    else:
        # Diğer hatalar → hemen fail
        logger.error(f"❌ Status: {response.status_code}, aborting...")
        raise Exception(f"HTTP {response.status_code}")
except requests.exceptions.Timeout:
    logger.error(f"❌ Timeout after {timeout}s")
    raise  # Timeout'ta hemen fail
except Exception as e:
    logger.error(f"❌ Error: {e}")
    raise
```

**Kazanç:**
- Gereksiz retry'ları önler
- Timeout durumunda hemen fail (gereksiz beklemeler yok)

---

## Tahmini Toplam Kazanç 📈

| Optimizasyon | Kazanç | Risk |
|--------------|--------|------|
| Parallel Requests | **20s** | Orta |
| Timeout (45s) | 15s (hata durumunda) | Düşük |
| Retry (max=1) | 30s (hata durumunda) | Orta |
| Dynamic Wait | **2s** | Düşük |
| Response Caching | 10-20s (tekrar çalıştırmada) | Düşük |
| Bright Data params | **5-10s** | Orta |
| **TOPLAM** | **37-52s** | - |

**Optimum senaryo:**
- Mevcut: ~90-100s
- Optimize: **~45-60s** ✅
- **Kazanç: %40-50 daha hızlı!**

---

## Test ve Uygulama Planı 📋

### Adım 1: Baseline Ölçümü
```bash
python test_brightdata_performance.py
```
→ Mevcut performansı kaydet

### Adım 2: Timeout Optimizasyonu
1. `test_brightdata_performance.py` → Optimal timeout bul
2. `src/checker_brightdata.py` → Timeout'u güncelle
3. Test et → Başarı oranını kontrol et

### Adım 3: Parallel Requests
1. `concurrent.futures` ile paralel POST'ları implement et
2. Test et → Sıra bağımlılığını kontrol et
3. Kazancı ölç

### Adım 4: Bright Data Params
1. `country: "tr"` parametresini ekle
2. Test et → Response time'ı karşılaştır
3. `render_js: False` test et → Dinamik içerik kontrolü

### Adım 5: Dynamic Wait Optimization
1. Exponential backoff ekle
2. Test et → Hala doğru seçenekleri bulduğunu kontrol et

### Adım 6: Final Test
```bash
python test_brightdata_performance.py
```
→ Optimize edilmiş performansı ölç

---

## Önerilen İlk Uygulama 🎯

**En yüksek ROI (Return on Investment):**

1. **Parallel Requests** → 20s kazanç, orta risk
2. **Bright Data params (country: "tr")** → 5-10s kazanç, düşük risk
3. **Dynamic Wait Optimization** → 2s kazanç, düşük risk

**Toplam: ~27-32s kazanç, düşük-orta risk**

---

## Sorular ve Cevaplar ❓

**Q: Parallel requests güvenli mi?**
A: City → Office sıralı kalmalı (bağımlı), Visa → Person paralel olabilir.

**Q: Timeout 45s'ye düşürülürse ne olur?**
A: `test_brightdata_performance.py` ile test et! Başarı oranı %95+ ise sorun yok.

**Q: Caching Railway'de çalışır mı?**
A: Evet, ancak container restart'ta cache sıfırlanır. Redis kullanılabilir (daha kalıcı).

**Q: render_js: False yaparsam dinamik içerik yüklenir mi?**
A: Belki yüklenmez. Önce test et! AJAX-loaded selectler etkilenebilir.

---

## İletişim 📧

Sorular için: GitHub Issues veya maintainer ile iletişime geçin.

