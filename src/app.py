from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from src.checker import AppointmentChecker
from src.notifier import Notifier
from src.database import Database
from config.settings import Config
import logging
import time
from pathlib import Path

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
scheduler = BackgroundScheduler()

# Durum değişkenleri
monitoring_active = False
last_check_time = None
last_check_status = "Henüz kontrol yapılmadı"

def scheduled_check():
    """Zamanlanmış kontrol"""
    global last_check_time, last_check_status
    
    try:
        logger.info("⏰ Zamanlanmış kontrol başladı")
        last_check_time = time.time()
        last_check_status = "Kontrol ediliyor..."
        
        result = checker.run_check()
        
        if result:
            last_check_status = "🎉 RANDEVU BULUNDU!"
            notifier.notify_appointment_found()
            db.log_check("success", appointment_found=True)
            
            # Randevu bulununca izlemeyi durdur
            global monitoring_active
            monitoring_active = False
            scheduler.pause()
            
        else:
            last_check_status = "😔 Randevu yok"
            db.log_check("success", appointment_found=False)
        
        logger.info(f"✅ Kontrol tamamlandı: {last_check_status}")
        
    except Exception as e:
        last_check_status = f"❌ Hata: {str(e)}"
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
        interval = request.json.get('interval', Config.CHECK_INTERVAL)
        
        # İlk kontrolü hemen yap
        scheduled_check()
        
        # Scheduler'ı başlat
        scheduler.add_job(
            scheduled_check,
            'interval',
            seconds=interval,
            id='appointment_check'
        )
        
        if not scheduler.running:
            scheduler.start()
        else:
            scheduler.resume()
        
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
        'check_interval': Config.CHECK_INTERVAL
    })

@app.route('/api/history')
def get_history():
    """Kontrol geçmişini getir"""
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

if __name__ == '__main__':
    port = Config.PORT
    logger.info(f"🚀 Uygulama başlatılıyor (port: {port})")
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)