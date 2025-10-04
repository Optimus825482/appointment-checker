# 🎯 Appointment Checker — Railway.app

İtalya vize randevu sistemini otomatik kontrol eden, Cloudflare bypass özellikli, Railway.app'te çalışabilen tam otomatik sistem.

## ✨ Özellikler

- 🤖 **Cloudflare Bypass**: Undetected ChromeDriver ile bot tespitinden kaçınma
- 🧠 **AI CAPTCHA Çözümü**: Mistral Pixtral 12B ile görsel CAPTCHA okuma
- 📊 **Web Dashboard**: Gerçek zamanlı durum izleme ve kontrol paneli
- 🔔 **Bildirim**: Telegram ve Email entegrasyonu
- 📈 **İstatistik**: Detaylı kontrol geçmişi ve analiz
- ☁️ **Railway Ready**: Tek tıkla deploy

## 🚀 Hızlı Başlangıç

### Lokal Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/YOUR_USERNAME/appointment-checker.git
cd appointment-checker

# Sanal ortam oluşturun
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# .env dosyası oluşturun
cp .env.example .env
# .env dosyasını düzenleyip API anahtarlarınızı ekleyin

# Uygulamayı çalıştırın
python src/app.py
```

Tarayıcıdan `http://localhost:5000` adresine gidin.

### Railway.app Deploy

1. **GitHub'a push edin:**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Railway.app'te:**
   - New Project → Deploy from GitHub
   - Repository'nizi seçin
   - Environment Variables ekleyin:
     - `MISTRAL_API_KEY`
     - `TELEGRAM_BOT_TOKEN` (opsiyonel)
     - `TELEGRAM_CHAT_ID` (opsiyonel)
   - Deploy!

3. **Railway otomatik domain verir:**
   - `your-app.up.railway.app`

## 🔧 Konfigürasyon

### Gerekli Environment Variables

```env
# Zorunlu
MISTRAL_API_KEY=your_mistral_api_key

# Opsiyonel Bildirimler
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@email.com

# Kontrol Ayarları
CHECK_INTERVAL=60
MAX_RETRIES=5
```

### Mistral API Anahtarı Alma

1. https://console.mistral.ai adresine gidin
2. API Keys bölümünden yeni anahtar oluşturun
3. `.env` dosyasına ekleyin

### Telegram Bot Oluşturma

1. Telegram'da @BotFather'ı bulun
2. `/newbot` komutuyla bot oluşturun
3. Token'ı kopyalayıp `.env` dosyasına ekleyin
4. Bot ile konuşarak chat ID'nizi öğrenin: https://api.telegram.org/botYOUR_TOKEN/getUpdates

## 📁 Proje Yapısı

```
appointment-checker/
├── src/
│   ├── app.py              # Flask API
│   ├── checker.py          # Randevu kontrol mantığı
│   ├── captcha_solver.py   # CAPTCHA çözümü
│   ├── notifier.py         # Bildirim sistemi
│   └── database.py         # SQLite veritabanı
├── templates/
│   └── index.html          # Web arayüzü
├── static/
│   ├── css/style.css       # Stiller
│   └── js/main.js          # Frontend JavaScript
├── config/
│   └── settings.py         # Ayarlar
├── requirements.txt        # Python paketleri
├── Procfile               # Railway deployment
├── railway.toml           # Railway config
├── nixpacks.toml          # Chromium kurulumu
└── README.md
```

## 🎮 Kullanım

1. **Web arayüzünü açın**
2. **Kontrol aralığını** ayarlayın (minimum 30 saniye)
3. **"İzlemeyi Başlat"** butonuna tıklayın
4. Sistem otomatik olarak:
   - Cloudflare'i geçer
   - CAPTCHA'yı çözer
   - Randevu kontrolü yapar
   - Bulduğunda bildirim gönderir

## 📊 API Endpoints

- `GET /` - Ana sayfa
- `POST /api/start` - İzlemeyi başlat
- `POST /api/stop` - İzlemeyi durdur
- `POST /api/check-now` - Anında kontrol
- `GET /api/status` - Mevcut durum
- `GET /api/history` - Kontrol geçmişi

## 🐛 Sorun Giderme

### Chrome/Chromedriver Hatası
Railway'de Chromium otomatik kurulur. Lokal'de sorun varsa:
```bash
# Ubuntu/Debian
sudo apt install chromium-browser chromium-chromedriver

# macOS
brew install chromium chromedriver

# Windows
# Chrome'u manuel indirin: https://www.google.com/chrome/
```

### CAPTCHA Çözülmüyor
- Mistral API anahtarınızı kontrol edin
- API limitinizi kontrol edin
- Log'larda hata mesajlarını inceleyin

### Railway'de Uygulama Başlamıyor
- Environment variables'ı kontrol edin
- Logs sekmesinden hataları inceleyin
- `railway logs` komutuyla detaylı log alın

## 📝 Lisans

Bu proje eğitim amaçlıdır. Kullanım sorumluluğu kullanıcıya aittir.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing`)
5. Pull Request açın

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

---

Made with ❤️ for educational purposes
```