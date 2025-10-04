import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='appointments.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Veritabanı tablolarını oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    appointment_found BOOLEAN,
                    error TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Veritabanı hazır")
            
        except Exception as e:
            logger.error(f"❌ Veritabanı hatası: {e}")
    
    def log_check(self, status, appointment_found=False, error=None):
        """Kontrol kaydı ekle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO checks (status, appointment_found, error)
                VALUES (?, ?, ?)
            ''', (status, appointment_found, error))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Kayıt hatası: {e}")
    
    def get_recent_checks(self, limit=50):
        """Son kontrolleri getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM checks 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Sorgu hatası: {e}")
            return []