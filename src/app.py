from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from src.checker_brightdata import AppointmentChecker  # Bright Data Unlocker API kullanıyor!
from src.notifier import Notifier
from src.database import Database
from src.mysql_db import MySQLDatabase
from config.settings import Config
import logging
import time
from pathlib import Path
from collections import deque
from datetime import datetime

# Memory'de tutulacak log buffer'ı
log_buffer = deque(maxlen=100)  # Son 100 log mesajı

class MemoryLogHandler(logging.Handler):
    """Logları memory'de tutan handler"""
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': self.format(record)
        }
        log_buffer.append(log_entry)

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Memory handler ekle
memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter('%(message)s'))

# Tüm logger'lara memory handler ekle
logging.getLogger('src.checker').addHandler(memory_handler)
logging.getLogger('src.captcha_solver').addHandler(memory_handler)
logging.getLogger('src.app').addHandler(memory_handler)

logger = logging.getLogger(__name__)

# Proje root dizinini bul
BASE_DIR = Path(__file__).resolve().parent.parent

# Flask app'i root dizinindeki templates ve static ile oluştur
app = Flask(__name__,
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))
CORS(app)
app.config.from_object(Config)

# Global nesneler
checker = AppointmentChecker()
notifier = Notifier()
db = Database()
mysql_db = MySQLDatabase()  # MySQL database handler
scheduler = BackgroundScheduler()

# Durum değişkenleri
monitoring_active = False
last_check_time = None
last_check_status = "Henüz kontrol yapılmadı"
last_captcha_image = None  # Son CAPTCHA görseli (base64)
last_captcha_text = None   # Son çözülen CAPTCHA metni

def scheduled_check():
    """Zamanlanmış kontrol"""
    global last_check_time, last_check_status, last_captcha_image, last_captcha_text, monitoring_active
    
    try:
        logger.info("⏰ Zamanlanmış kontrol başladı")
        start_time = time.time()
        last_check_time = start_time
        last_check_status = "Kontrol ediliyor..."
        
        result = checker.run_check()
        response_time = int((time.time() - start_time) * 1000)  # milisaniye
        
        # CAPTCHA bilgilerini kaydet
        if isinstance(result, dict):
            last_check_status = result.get('status', 'Bilinmeyen durum')
            last_captcha_image = result.get('captcha_image')
            last_captcha_text = result.get('captcha_text')
            
            # Randevu kontrolü
            appointment_found = "RANDEVU VAR" in last_check_status
            
            # MySQL'e kaydet
            mysql_db.log_check(
                status="success",
                message=last_check_status,
                captcha_text=last_captcha_text,
                appointment_found=appointment_found,
                response_time=response_time
            )
            
            # SQLite'a da kaydet (backward compatibility)
            db.log_check("success", appointment_found=appointment_found)
            
            if appointment_found:
                notifier.notify_appointment_found()
                # Randevu bulununca izlemeyi durdur
                monitoring_active = False
                scheduler.pause()
        else:
            # Eski format (string)
            last_check_status = str(result)
            appointment_found = bool(result)
            
            # MySQL'e kaydet
            mysql_db.log_check(
                status="success",
                message=last_check_status,
                appointment_found=appointment_found,
                response_time=response_time
            )
            
            db.log_check("success", appointment_found=appointment_found)
            
            if appointment_found:
                notifier.notify_appointment_found()
                monitoring_active = False
                scheduler.pause()
        
        logger.info(f"✅ Kontrol tamamlandı: {last_check_status} ({response_time}ms)")
        
    except Exception as e:
        last_check_status = f"❌ Hata: {str(e)}"
        
        # MySQL'e hata kaydet
        mysql_db.log_check(
            status="error",
            error=str(e),
            response_time=int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
        )
        
        db.log_check("error", error=str(e))
        logger.error(f"❌ Kontrol hatası: {e}")

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/logs')
def logs():
    """Log sayfası"""
    return render_template('logs.html')

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """İzlemeyi başlat"""
    global monitoring_active
    
    if monitoring_active:
        return jsonify({'error': 'Zaten çalışıyor'}), 400
    
    try:
        interval = request.json.get('interval', Config.CHECK_INTERVAL) if request.json else Config.CHECK_INTERVAL
        
        # Scheduler zaten çalışıyor mu kontrol et
        if not scheduler.running:
            logger.info("🔄 Scheduler başlatılıyor...")
            scheduler.start()
        
        # Mevcut job'u kaldır (varsa)
        try:
            scheduler.remove_job('appointment_check')
            logger.info("♻️ Eski job kaldırıldı")
        except Exception:
            pass  # Job yoksa sorun yok
        
        # Yeni job ekle
        scheduler.add_job(
            scheduled_check,
            'interval',
            seconds=interval,
            id='appointment_check',
            replace_existing=True
        )
        
        # İlk kontrolü hemen yap
        scheduled_check()
        
        monitoring_active = True
        
        logger.info(f"✅ İzleme başlatıldı (interval: {interval}s)")
        return jsonify({
            'status': 'started',
            'interval': interval,
            'message': 'İzleme başlatıldı'
        })
        
    except Exception as e:
        logger.error(f"❌ Başlatma hatası: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """İzlemeyi durdur"""
    global monitoring_active
    
    try:
        scheduler.pause()
        monitoring_active = False
        
        logger.info("⏹️ İzleme durduruldu")
        return jsonify({
            'status': 'stopped',
            'message': 'İzleme durduruldu'
        })
        
    except Exception as e:
        logger.error(f"❌ Durdurma hatası: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Mevcut durumu getir"""
    return jsonify({
        'monitoring_active': monitoring_active,
        'last_check_time': last_check_time,
        'last_check_status': last_check_status,
        'check_interval': Config.CHECK_INTERVAL,
        'captcha_image': last_captcha_image,
        'captcha_text': last_captcha_text
    })

@app.route('/api/history')
def get_history():
    """Kontrol geçmişini getir (MySQL'den)"""
    try:
        # MySQL'den logları getir
        mysql_logs = mysql_db.get_recent_logs(limit=50)
        
        history = []
        for log in mysql_logs:
            history.append({
                'id': log.get('id'),
                'timestamp': log.get('timestamp').isoformat() if log.get('timestamp') else None,
                'status': log.get('status'),
                'message': log.get('message'),
                'captcha_text': log.get('captcha_text'),
                'appointment_found': bool(log.get('appointment_found')),
                'error': log.get('error'),
                'response_time': log.get('response_time')
            })
        
        return jsonify(history)
        
    except Exception as e:
        # MySQL hatası varsa SQLite'a fallback
        logger.warning(f"⚠️ MySQL hata, SQLite kullanılıyor: {e}")
        checks = db.get_recent_checks(limit=50)
        
        history = []
        for check in checks:
            history.append({
                'id': check[0],
                'timestamp': check[1],
                'status': check[2],
                'appointment_found': bool(check[3]),
                'error': check[4]
            })
        
        return jsonify(history)

@app.route('/api/stats')
def get_stats():
    """MySQL istatistiklerini getir"""
    try:
        stats = mysql_db.get_stats()
        return jsonify({
            'total_checks': stats.get('total_checks', 0),
            'successful_checks': stats.get('successful_checks', 0),
            'failed_checks': stats.get('failed_checks', 0),
            'appointments_found': stats.get('appointments_found', 0),
            'success_rate': round(
                (stats.get('successful_checks', 0) / stats.get('total_checks', 1)) * 100, 2
            ) if stats.get('total_checks', 0) > 0 else 0,
            'last_check_time': stats.get('last_check_time').isoformat() if stats.get('last_check_time') is not None else None,
            'monitoring_active': stats.get('monitoring_active', False)
        })
    except Exception as e:
        logger.error(f"❌ Stats hatası: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/recent')
def get_recent_logs():
    """Son logları getir (gerçek zamanlı detaylı loglar)"""
    try:
        # Memory buffer'daki logları JSON olarak döndür
        return jsonify({
            'logs': list(log_buffer),
            'count': len(log_buffer)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Log buffer'ını temizle"""
    try:
        log_buffer.clear()
        return jsonify({'status': 'cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-now', methods=['POST'])
def check_now():
    """Anında kontrol yap"""
    try:
        scheduled_check()
        return jsonify({
            'status': 'completed',
            'result': last_check_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Uygulama başladığında otomatik izlemeyi başlat (Railway için)
def auto_start_monitoring():
    """Railway deployment sonrası otomatik başlat"""
    global monitoring_active
    
    if not monitoring_active:
        try:
            logger.info("🤖 Otomatik izleme başlatılıyor (Railway auto-start)...")
            
            if not scheduler.running:
                scheduler.start()
            
            # Job ekle
            scheduler.add_job(
                scheduled_check,
                'interval',
                seconds=Config.CHECK_INTERVAL,
                id='appointment_check',
                replace_existing=True
            )
            
            monitoring_active = True
            logger.info(f"✅ Otomatik izleme başladı (interval: {Config.CHECK_INTERVAL}s)")
            
            # İlk kontrolü hemen yap
            scheduled_check()
            
        except Exception as e:
            logger.error(f"❌ Otomatik başlatma hatası: {e}")

# Otomatik başlatmayı çağır (Gunicorn başladığında)
auto_start_monitoring()

if __name__ == '__main__':
    port = Config.PORT
    logger.info(f"🚀 Uygulama başlatılıyor (port: {port})")
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)