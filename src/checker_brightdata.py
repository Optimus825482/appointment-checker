"""
Bright Data Unlocker API ile Cloudflare Bypass
Bu modül Selenium yerine Bright Data'nın profesyonel Unlocker API'sini kullanır
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentChecker:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        
    def fetch_with_brightdata(self, url, max_retries=2):
        """
        Bright Data Unlocker API ile sayfa getir
        
        Args:
            url: Hedef URL
            max_retries: Maksimum deneme sayısı
            
        Returns:
            tuple: (success: bool, html: str, status_code: int)
        """
        logger.info(f"🌐 Bright Data Unlocker API ile sayfa getiriliyor: {url}")
        
        # API Key kontrolü
        api_key = self.config.BRIGHTDATA_API_KEY
        if not api_key:
            logger.error("❌ BRIGHTDATA_API_KEY bulunamadı!")
            return False, "", 0
        
        logger.info(f"🔑 API Key (ilk 10 karakter): {api_key[:10]}...")
        
        # Bright Data Web Unlocker API endpoint
        api_url = "https://api.brightdata.com/request"
        
        # API Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Request payload (Bright Data format)
        payload = {
            "zone": "web_unlocker1",  # Zone name (default for Web Unlocker)
            "url": url,
            "format": "raw",  # Raw HTML response
            "country": "tr"   # Turkey proxy (TESTED: WORKS!)
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Deneme {attempt}/{max_retries}...")
                
                response = self.session.post(
                    api_url,
                    json=payload,
                    headers=headers,
                    timeout=45  # 45 saniye (test sonuçlarına göre optimize edildi - max 44.74s görüldü)
                )
                
                # Debug logging
                logger.info(f"📡 Response Status: {response.status_code}")
                logger.info(f"📡 Response Headers: {dict(response.headers)}")
                logger.info(f"📡 Response Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                logger.info(f"📡 Response Length: {len(response.content)} bytes")
                logger.info(f"📡 Response Text Length: {len(response.text)} chars")
                
                if len(response.text) > 0:
                    logger.info(f"📡 Response Preview (first 500 chars): {response.text[:500]}")
                
                if response.status_code == 200:
                    if len(response.text) == 0:
                        # Navigation timeout kontrolü
                        brd_error = response.headers.get('x-brd-error', '')
                        if 'navigation timeout' in brd_error.lower():
                            logger.warning(f"⚠️ Navigation timeout! Deneme {attempt}/{max_retries}")
                            if attempt < max_retries:
                                logger.info(f"🔄 {attempt * 3}s bekleyip tekrar denenecek...")
                                time.sleep(attempt * 3)
                                continue
                        
                        logger.error("❌ Response boş! API yanıt veriyor ama içerik yok")
                        logger.error(f"💡 Full Response: {response.content}")
                        logger.error(f"💡 Request Payload: {payload}")
                        return False, "", response.status_code
                    
                    logger.info(f"✅ Sayfa başarıyla getirildi! (Status: {response.status_code})")
                    logger.info(f"📊 Response boyutu: {len(response.text)} karakter")
                    return True, response.text, response.status_code
                    
                elif response.status_code == 401:
                    logger.error("❌ Bright Data API Key geçersiz!")
                    logger.error("💡 BRIGHTDATA_API_KEY environment variable'ı kontrol edin")
                    return False, "", response.status_code
                    
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limit aşıldı, {attempt * 5}s bekleniyor...")
                    time.sleep(attempt * 5)
                    continue
                    
                else:
                    logger.warning(f"⚠️ Beklenmeyen status code: {response.status_code}")
                    logger.warning(f"   Response: {response.text[:200]}")
                    
                    if attempt < max_retries:
                        logger.info(f"🔄 {attempt * 3}s sonra tekrar denenecek...")
                        time.sleep(attempt * 3)
                        continue
                        
            except requests.exceptions.Timeout:
                logger.error(f"❌ Timeout hatası! (Deneme {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request hatası: {e}")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Beklenmeyen hata: {e}")
                if attempt < max_retries:
                    time.sleep(attempt * 3)
                    continue
        
        logger.error(f"❌ {max_retries} denemeden sonra başarısız!")
        return False, "", 0
    
    def extract_captcha_from_html(self, html):
        """
        HTML'den CAPTCHA görselini çıkar
        
        Args:
            html: Sayfa HTML içeriği
            
        Returns:
            str: CAPTCHA base64 data URL veya None
        """
        try:
            # Use lxml parser for better performance
            soup = BeautifulSoup(html, 'lxml')
            
            logger.info("🔍 CAPTCHA görseli aranıyor...")
            logger.info(f"📊 HTML boyutu: {len(html)} karakter")
            
            # CAPTCHA görseli ara
            captcha_img = soup.find('img', class_='imageCaptcha')
            
            if captcha_img:
                logger.info("✅ img.imageCaptcha elementi bulundu!")
                src = captcha_img.get('src', '')
                logger.info(f"📡 src attribute: {src[:100]}...")
                
                if src and src.startswith('data:image'):
                    logger.info("✅ CAPTCHA görseli HTML'de bulundu!")
                    logger.info(f"📊 Base64 boyutu: {len(src)} karakter")
                    return src
                else:
                    logger.warning(f"⚠️ src attribute geçersiz: {src[:50]}")
            else:
                logger.warning("⚠️ img.imageCaptcha elementi bulunamadı")
                
                # Debug: Tüm img elementlerini listele
                all_imgs = soup.find_all('img')
                logger.info(f"📊 Toplam img elementi: {len(all_imgs)}")
                for idx, img in enumerate(all_imgs[:5]):  # İlk 5'i göster
                    logger.info(f"   img[{idx}]: class={img.get('class', [])} src={str(img.get('src', ''))[:50]}...")
                    
            logger.warning("⚠️ CAPTCHA görseli HTML'de bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"❌ CAPTCHA extraction hatası: {e}")
            return None
    
    def submit_captcha(self, captcha_text):
        """
        CAPTCHA kodunu POST et ve form sayfasını al
        
        Args:
            captcha_text: Mistral AI tarafından çözülen CAPTCHA metni
            
        Returns:
            tuple: (success: bool, html: str)
        """
        try:
            target_url = "https://it-tr-appointment.idata.com.tr/tr"
            api_url = "https://api.brightdata.com/request"
            
            logger.info(f"📤 CAPTCHA POST ediliyor: {captcha_text}")
            logger.info(f"🎯 Hedef URL: {target_url}")
            
            # Form data hazırla
            payload = {
                "zone": "web_unlocker1",
                "url": target_url,
                "format": "raw",
                "country": "tr",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": target_url,
                    "Origin": "https://it-tr-appointment.idata.com.tr"
                },
                "body": f"mailConfirmCode={captcha_text}"
            }
            
            headers = {
                "Authorization": f"Bearer {self.config.BRIGHTDATA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            logger.info("🔄 POST isteği gönderiliyor...")
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=45  # 45 saniye timeout (test sonuçlarına göre optimize edildi)
            )
            
            logger.info(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                html = response.text
                logger.info(f"📊 Form sayfası boyutu: {len(html)} karakter")
                
                # HTML'i küçük harfe çevir (performans için sadece bir kez)
                html_lower = html.lower()
                
                # Form sayfası kontrolü (geliştirilmiş)
                form_indicators = [
                    "appointment-form",
                    "başvuru bilgileri",
                    "ikametgah şehri",
                    "idata ofisi seçiniz",
                    "gidiş amacı",
                    "hizmet türü"
                ]
                
                error_indicators = [
                    "yanlış",
                    "hatalı",
                    "geçersiz",
                    "invalid",
                    "incorrect",
                    "wrong"
                ]
                
                # Form sayfası mı?
                if any(indicator in html_lower for indicator in form_indicators):
                    logger.info("✅ Form sayfasına yönlendirme başarılı!")
                    logger.info("📋 Başvuru formu sayfası tespit edildi")
                    return True, html
                
                # Hata sayfası mı?
                if any(error in html_lower for error in error_indicators):
                    logger.warning("⚠️ CAPTCHA kodu yanlış girildi!")
                    return False, None
                
                # Belirsiz ama HTML var
                logger.info("ℹ️ Sayfa içeriği belirsiz, HTML döndürülüyor")
                logger.info(f"📄 HTML Preview: {html[:200]}...")
                return True, html
            else:
                logger.error(f"❌ POST başarısız: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ CAPTCHA POST hatası: {e}")
            return False, None
    
    def fill_appointment_form(self, form_html):
        """
        Form sayfasını doldur ve randevu kontrolü yap
        
        İzmir seçenekleri:
        - Şehir: İzmir
        - Ofis: İzmir Ofisi
        - Gidiş Amacı: Turistik
        - Hizmet Türü: Standart
        - Kişi Sayısı: 1
        
        Args:
            form_html: Form sayfasının HTML içeriği
            
        Returns:
            tuple: (success: bool, result_html: str or None)
        """
        try:
            logger.info("📝 Form doldurma başlatılıyor...")
            
            # Form sayfasındaki select option'ları parse et
            soup = BeautifulSoup(form_html, 'html.parser')
            
            # 1. Şehir seçimi için option değerlerini al (dinamik bekleme ile)
            izmir_option = None
            max_retries = 3  # Maksimum 3 deneme
            
            for attempt in range(1, max_retries + 1):
                logger.info(f"🏙️ Şehir seçenekleri kontrol ediliyor (Deneme {attempt}/{max_retries})...")
                
                # HTML'i yeniden parse et (her denemede)
                soup = BeautifulSoup(form_html, 'html.parser')
                city_select = soup.find('select', {'id': 'city_id'})
                
                if city_select:
                    options = city_select.find_all('option')
                    logger.info(f"📊 {len(options)} şehir seçeneği bulundu")
                    
                    # İzmir'i ara
                    for option in options:
                        option_text = option.get_text().strip().lower()
                        if 'izmir' in option_text and option.get('value'):
                            izmir_option = option.get('value')
                            logger.info(f"✅ İzmir bulundu: value={izmir_option}, text={option.get_text().strip()}")
                            break
                    
                    if izmir_option:
                        break  # İzmir bulundu, döngüden çık
                    else:
                        logger.warning(f"⚠️ İzmir bulunamadı, 2 saniye bekleniyor...")
                        if attempt < max_retries:
                            time.sleep(2)
                            # Sayfayı yeniden getir
                            logger.info("🔄 Sayfa yeniden getiriliyor...")
                            _, form_html, _ = self.fetch_with_brightdata(self.config.APPOINTMENT_URL)
                else:
                    logger.warning(f"⚠️ city_id select elementi bulunamadı, 2 saniye bekleniyor...")
                    if attempt < max_retries:
                        time.sleep(2)
                        # Sayfayı yeniden getir
                        _, form_html, _ = self.fetch_with_brightdata(self.config.APPOINTMENT_URL)
            
            if not izmir_option:
                logger.error("❌ İzmir seçeneği bulunamadı (3 deneme sonrası)!")
                logger.info("📋 Bulunan seçenekler:")
                if city_select:
                    for opt in city_select.find_all('option'):
                        logger.info(f"   - value={opt.get('value')}, text={opt.get_text().strip()}")
                return False, None
            
            # 2. İlk POST: Şehir seçimi (İzmir)
            logger.info("📤 POST 1/4: Şehir seçimi (İzmir)...")
            city_payload = {
                "zone": "web_unlocker1",
                "url": self.config.APPOINTMENT_URL,
                "format": "raw",
                "country": "tr",
                "method": "POST",
                "body": f"city_id={izmir_option}"
            }
            
            api_url = "https://api.brightdata.com/request"
            headers = {
                "Authorization": f"Bearer {self.config.BRIGHTDATA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(api_url, json=city_payload, headers=headers, timeout=45)
            
            if response.status_code != 200:
                logger.error(f"❌ Şehir seçimi başarısız: {response.status_code}")
                return False, None
            
            logger.info("✅ İzmir seçildi, ofis seçenekleri yükleniyor...")
            time.sleep(3)  # Server'ın ofis seçeneklerini yüklemesini bekle
            
            # 3. İkinci GET: Ofis seçeneklerini al (dinamik bekleme ile)
            izmir_office = None
            
            for attempt in range(1, max_retries + 1):
                logger.info(f"🏢 Ofis seçenekleri kontrol ediliyor (Deneme {attempt}/{max_retries})...")
                
                office_soup = BeautifulSoup(response.text, 'html.parser')
                office_select = office_soup.find('select', {'id': 'office_id'})
                
                if office_select:
                    options = office_select.find_all('option')
                    logger.info(f"📊 {len(options)} ofis seçeneği bulundu")
                    
                    # İzmir Ofisi'ni ara
                    for option in options:
                        option_text = option.get_text().strip().lower()
                        if 'izmir' in option_text and option.get('value'):
                            izmir_office = option.get('value')
                            logger.info(f"✅ İzmir Ofisi bulundu: value={izmir_office}, text={option.get_text().strip()}")
                            break
                    
                    if izmir_office:
                        break  # İzmir Ofisi bulundu
                    else:
                        logger.warning(f"⚠️ İzmir Ofisi bulunamadı, 2 saniye bekleniyor...")
                        if attempt < max_retries:
                            time.sleep(2)
                else:
                    logger.warning(f"⚠️ office_id select elementi bulunamadı, 2 saniye bekleniyor...")
                    if attempt < max_retries:
                        time.sleep(2)
            
            if not izmir_office:
                logger.error("❌ İzmir Ofisi bulunamadı (3 deneme sonrası)!")
                logger.info("📋 Bulunan ofis seçenekleri:")
                if office_select:
                    for opt in office_select.find_all('option'):
                        logger.info(f"   - value={opt.get('value')}, text={opt.get_text().strip()}")
                return False, None
            
            # 4. İkinci POST: Ofis seçimi
            logger.info("📤 POST 2/4: Ofis seçimi (İzmir Ofisi)...")
            office_payload = {
                "zone": "web_unlocker1",
                "url": self.config.APPOINTMENT_URL,
                "format": "raw",
                "country": "tr",
                "method": "POST",
                "body": f"city_id={izmir_option}&office_id={izmir_office}"
            }
            
            response = requests.post(api_url, json=office_payload, headers=headers, timeout=45)
            
            if response.status_code != 200:
                logger.error(f"❌ Ofis seçimi başarısız: {response.status_code}")
                return False, None
            
            logger.info("✅ İzmir Ofisi seçildi, vize tipleri yükleniyor...")
            time.sleep(2)
            
            # 5. Üçüncü GET: Vize tipi ve hizmet türü seçeneklerini al
            visa_soup = BeautifulSoup(response.text, 'html.parser')
            
            # Gidiş amacı (purpose)
            purpose_select = visa_soup.find('select', {'id': 'visa_purpose_id'})
            tourist_purpose = None
            
            if purpose_select:
                logger.info("🎯 Gidiş amacı bulundu, Turistik aranıyor...")
                options = purpose_select.find_all('option')
                for option in options:
                    if 'turist' in option.get_text().lower():
                        tourist_purpose = option.get('value')
                        logger.info(f"✅ Turistik bulundu: value={tourist_purpose}")
                        break
            
            # Hizmet türü (service type)
            service_select = visa_soup.find('select', {'id': 'service_type_id'})
            standard_service = None
            
            if service_select:
                logger.info("🛠️ Hizmet türü bulundu, Standart aranıyor...")
                options = service_select.find_all('option')
                for option in options:
                    if 'standart' in option.get_text().lower() or 'standard' in option.get_text().lower():
                        standard_service = option.get('value')
                        logger.info(f"✅ Standart bulundu: value={standard_service}")
                        break
            
            if not tourist_purpose or not standard_service:
                logger.warning("⚠️ Vize tipi veya hizmet türü bulunamadı!")
                return False, None
            
            # 6. Üçüncü POST: Vize tipi ve hizmet türü seçimi
            logger.info("📤 POST 3/4: Turistik + Standart seçimi...")
            visa_payload = {
                "zone": "web_unlocker1",
                "url": self.config.APPOINTMENT_URL,
                "format": "raw",
                "country": "tr",
                "method": "POST",
                "body": f"city_id={izmir_option}&office_id={izmir_office}&visa_purpose_id={tourist_purpose}&service_type_id={standard_service}"
            }
            
            response = requests.post(api_url, json=visa_payload, headers=headers, timeout=45)
            
            if response.status_code != 200:
                logger.error(f"❌ Vize tipi seçimi başarısız: {response.status_code}")
                return False, None
            
            logger.info("✅ Turistik + Standart seçildi, kişi sayısı ayarlanıyor...")
            time.sleep(2)
            
            # 7. Dördüncü POST: Kişi sayısı (1 kişi)
            logger.info("📤 POST 4/4: Kişi sayısı (1 kişi)...")
            count_payload = {
                "zone": "web_unlocker1",
                "url": self.config.APPOINTMENT_URL,
                "format": "raw",
                "country": "tr",
                "method": "POST",
                "body": f"city_id={izmir_option}&office_id={izmir_office}&visa_purpose_id={tourist_purpose}&service_type_id={standard_service}&applicant_count=1"
            }
            
            response = requests.post(api_url, json=count_payload, headers=headers, timeout=45)
            
            if response.status_code != 200:
                logger.error(f"❌ Kişi sayısı ayarı başarısız: {response.status_code}")
                return False, None
            
            logger.info("✅ Form doldurma tamamlandı!")
            logger.info("📊 Son sayfa HTML boyutu: {} karakter".format(len(response.text)))
            
            return True, response.text
            
        except Exception as e:
            logger.error(f"❌ Form doldurma hatası: {e}")
            return False, None
    
    def check_appointment_availability(self, html):
        """
        HTML'den randevu durumunu kontrol et
        
        Args:
            html: Sayfa HTML içeriği
            
        Returns:
            tuple: (available: bool, message: str)
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text().lower()
            
            logger.info("🔍 Randevu durumu kontrol ediliyor...")
            
            # Form sayfasında mıyız? (CAPTCHA geçildiyse)
            if "appointment-form" in html or "BAŞVURU BİLGİLERİ" in html:
                logger.info("📋 Form sayfasında - Randevu seçenekleri aranıyor...")
                
                # "Uygun randevu yok" alert div
                no_appointment_alert = soup.find('div', class_='alert-danger')
                if no_appointment_alert and "Uygun randevu tarihi bulunmamaktadır" in no_appointment_alert.get_text():
                    logger.info("😔 'Uygun randevu tarihi bulunmamaktadır' mesajı bulundu")
                    return False, "😔 Randevu yok"
                
                # "İLERİ" butonu var mı? (Randevu varsa görünür)
                ileri_button = soup.find('a', id='btnAppCountNext')
                if ileri_button and hasattr(ileri_button, 'get'):
                    style = str(ileri_button.get('style', ''))
                    if 'display: none' not in style:
                        logger.info("✅ 'İLERİ' butonu aktif - RANDEVU VAR!")
                        return True, "🎉 RANDEVU VAR!"
                
                logger.info("ℹ️ Form sayfası yüklendi ama randevu durumu belirsiz")
                return False, "ℹ️ Form sayfası - durum belirsiz"
            
            # İlk sayfa (CAPTCHA sayfası)
            # "Randevu yok" mesajları
            no_appointment_keywords = [
                "no appointment",
                "randevu yok",
                "müsait randevu yok",
                "no available appointment"
            ]
            
            for keyword in no_appointment_keywords:
                if keyword in text:
                    logger.info(f"😔 '{keyword}' mesajı bulundu - Randevu yok")
                    return False, "😔 Randevu yok"
            
            # Randevu butonları ara (ilk sayfada)
            appointment_count = text.count('randevu') + text.count('appointment')
            if appointment_count > 0:
                logger.info(f"🎉 Randevu referansları bulundu! ({appointment_count} adet)")
                return True, f"🎉 RANDEVU VAR! ({appointment_count} referans)"
            
            logger.info("ℹ️ Net bir sonuç bulunamadı, daha fazla analiz gerekli")
            return False, "ℹ️ Belirsiz durum"
            
        except Exception as e:
            logger.error(f"❌ HTML analiz hatası: {e}")
            return False, f"❌ Hata: {e}"
    
    def run_check(self, progress_callback=None):
        """
        Ana kontrol döngüsü - Bright Data Unlocker API ile
        
        Args:
            progress_callback: Progress güncellemesi için callback fonksiyonu
        
        Returns:
            dict: {
                'status': str,  # Sonuç mesajı
                'captcha_image': str or None,  # Base64 CAPTCHA görseli
                'captcha_text': str or None    # Çözülen CAPTCHA metni
            }
        """
        result = {
            'status': "Kontrol başlatılıyor...",
            'captcha_image': None,
            'captcha_text': None
        }
        
        def update_progress(step, message):
            """Progress callback helper"""
            if progress_callback:
                progress_callback(step, message)
        
        try:
            logger.info("🚀 Kontrol başlatılıyor...")
            logger.info("🌐 Bright Data Unlocker API kullanılıyor (Selenium YOK!)")
            
            # 1. Sayfa getir (Cloudflare bypass dahil!)
            update_progress(1, "URL'ye bağlanılıyor...")
            success, html, status_code = self.fetch_with_brightdata(self.config.APPOINTMENT_URL)
            
            if not success:
                logger.error("❌ Sayfa getirilemedi!")
                result['status'] = "❌ Bağlantı hatası"
                return result
            
            # 2. Cloudflare kontrolü
            update_progress(2, "Cloudflare kontrolü...")
            if "cloudflare" in html.lower() or "attention required" in html.lower():
                logger.error("❌ Bright Data bile Cloudflare'ı geçemedi!")
                logger.error("💡 Bu çok nadir bir durum, API key'i kontrol edin")
                result['status'] = "❌ Cloudflare bypass başarısız"
                return result
            
            logger.info("✅ Cloudflare başarıyla bypass edildi!")
            logger.info(f"📄 HTML boyutu: {len(html)} karakter")
            
            # 3. CAPTCHA var mı kontrol et
            update_progress(3, "CAPTCHA algılanıyor...")
            captcha_data = self.extract_captcha_from_html(html)
            
            if captcha_data:
                logger.info("🔐 CAPTCHA bulundu, Mistral AI ile çözülüyor...")
                
                # CAPTCHA görselini kaydet
                result['captcha_image'] = captcha_data
                
                from src.captcha_solver import CaptchaSolver
                solver = CaptchaSolver(self.config.MISTRAL_API_KEY)
                
                # CAPTCHA'yı çöz
                update_progress(3, "CAPTCHA çözülüyor (Mistral AI)...")
                captcha_text = solver.solve_captcha_from_base64(captcha_data)
                
                if captcha_text:
                    logger.info(f"✅ CAPTCHA çözüldü: {captcha_text}")
                    
                    # CAPTCHA metnini kaydet
                    result['captcha_text'] = captcha_text
                    
                    # CAPTCHA kodunu POST et
                    update_progress(4, "CAPTCHA gönderiliyor...")
                    logger.info("📤 CAPTCHA kodu POST ediliyor...")
                    success, form_html = self.submit_captcha(captcha_text)
                    
                    if success and form_html:
                        logger.info("✅ CAPTCHA POST başarılı, form sayfası alındı!")
                        html = form_html  # Yeni HTML'i kullan
                        
                        # Form doldurma adımı ekle
                        update_progress(5, "Form doldurma (İzmir/Turistik/Standart/1 kişi)...")
                        logger.info("📝 Form doldurma başlatılıyor...")
                        form_success, final_html = self.fill_appointment_form(form_html)
                        
                        if form_success and final_html:
                            logger.info("✅ Form başarıyla dolduruldu!")
                            html = final_html  # Son HTML'i kullan
                        else:
                            logger.warning("⚠️ Form doldurulamadı, mevcut HTML kullanılacak")
                    else:
                        logger.warning("⚠️ CAPTCHA POST başarısız, ilk sayfadaki HTML kullanılacak")
                else:
                    logger.warning("⚠️ CAPTCHA çözülemedi!")
            else:
                logger.info("ℹ️ CAPTCHA bulunamadı veya gerekli değil")
            
            # 4. Randevu durumunu kontrol et
            update_progress(6, "Randevu durumu kontrol ediliyor...")
            available, message = self.check_appointment_availability(html)
            
            # 5. Sonuç analizi
            update_progress(7, "Sonuç analiz ediliyor...")
            
            logger.info(f"📊 Sonuç: {message}")
            result['status'] = message
            return result
            
        except Exception as e:
            logger.error(f"❌ Kritik hata: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result['status'] = f"❌ Hata: {e}"
            return result
        
        finally:
            logger.info("🔚 Kontrol tamamlandı")
    
    def cleanup(self):
        """Temizlik işlemleri"""
        logger.info("🧹 Temizlik yapılıyor...")
        self.session.close()
        logger.info("✅ Session kapatıldı")

def main():
    """Test için"""
    checker = AppointmentChecker()
    result = checker.run_check()
    print(f"\n{'='*60}")
    print(f"SONUÇ: {result}")
    print(f"{'='*60}\n")
    checker.cleanup()

if __name__ == "__main__":
    main()
