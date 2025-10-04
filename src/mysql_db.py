"""
MySQL Database Handler for Railway
Persistent log storage with fast queries
"""

import os
import logging
from datetime import datetime
import mysql.connector
from mysql.connector import Error, pooling

logger = logging.getLogger(__name__)

class MySQLDatabase:
    def __init__(self):
        """MySQL database bağlantısı"""
        self.connection_pool = None
        self.setup_connection_pool()
        self.create_tables()
    
    def setup_connection_pool(self):
        """Connection pool oluştur"""
        try:
            # Railway MySQL environment variables
            config = {
                'host': os.getenv('MYSQLHOST', 'localhost'),
                'port': int(os.getenv('MYSQLPORT', 3306)),
                'database': os.getenv('MYSQLDATABASE', 'railway'),
                'user': os.getenv('MYSQLUSER', 'root'),
                'password': os.getenv('MYSQLPASSWORD', ''),
                'pool_name': 'appointment_pool',
                'pool_size': 5,
                'pool_reset_session': True,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
            
            self.connection_pool = pooling.MySQLConnectionPool(**config)
            logger.info("✅ MySQL connection pool oluşturuldu")
            
        except Error as e:
            logger.error(f"❌ MySQL pool oluşturma hatası: {e}")
            self.connection_pool = None
    
    def get_connection(self):
        """Pool'dan bağlantı al"""
        if self.connection_pool:
            try:
                return self.connection_pool.get_connection()
            except Error as e:
                logger.error(f"❌ MySQL bağlantı hatası: {e}")
                return None
        return None
    
    def create_tables(self):
        """Tabloları oluştur"""
        if not self.connection_pool:
            logger.warning("⚠️ MySQL yok, SQLite kullanılacak")
            return
        
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # Kontrol logları tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS check_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) NOT NULL,
                    message TEXT,
                    captcha_text VARCHAR(10),
                    appointment_found BOOLEAN DEFAULT FALSE,
                    error TEXT,
                    response_time INT,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_status (status),
                    INDEX idx_appointment (appointment_found)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # CAPTCHA geçmişi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS captcha_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    captcha_text VARCHAR(10),
                    solved_correctly BOOLEAN,
                    mistral_response_time INT,
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Sistem durumu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INT PRIMARY KEY DEFAULT 1,
                    last_check_time DATETIME,
                    monitoring_active BOOLEAN DEFAULT FALSE,
                    total_checks INT DEFAULT 0,
                    successful_checks INT DEFAULT 0,
                    failed_checks INT DEFAULT 0,
                    appointments_found INT DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # İlk kayıt
            cursor.execute("""
                INSERT IGNORE INTO system_status (id, total_checks)
                VALUES (1, 0)
            """)
            
            connection.commit()
            logger.info("✅ MySQL tabloları hazır")
            
        except Error as e:
            logger.error(f"❌ Tablo oluşturma hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def log_check(self, status, message=None, captcha_text=None, 
                  appointment_found=False, error=None, response_time=None):
        """Kontrol logla"""
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO check_logs 
                (status, message, captcha_text, appointment_found, error, response_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (status, message, captcha_text, appointment_found, error, response_time))
            
            # İstatistikleri güncelle
            if status == "success":
                if appointment_found:
                    cursor.execute("""
                        UPDATE system_status 
                        SET total_checks = total_checks + 1,
                            successful_checks = successful_checks + 1,
                            appointments_found = appointments_found + 1,
                            last_check_time = NOW()
                        WHERE id = 1
                    """)
                else:
                    cursor.execute("""
                        UPDATE system_status 
                        SET total_checks = total_checks + 1,
                            successful_checks = successful_checks + 1,
                            last_check_time = NOW()
                        WHERE id = 1
                    """)
            else:
                cursor.execute("""
                    UPDATE system_status 
                    SET total_checks = total_checks + 1,
                        failed_checks = failed_checks + 1,
                        last_check_time = NOW()
                    WHERE id = 1
                """)
            
            connection.commit()
            
        except Error as e:
            logger.error(f"❌ Log kaydetme hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def log_captcha(self, captcha_text, solved_correctly, response_time=None):
        """CAPTCHA logla"""
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO captcha_history 
                (captcha_text, solved_correctly, mistral_response_time)
                VALUES (%s, %s, %s)
            """, (captcha_text, solved_correctly, response_time))
            
            connection.commit()
            
        except Error as e:
            logger.error(f"❌ CAPTCHA log hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_recent_logs(self, limit=50):
        """Son logları getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM check_logs 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            
            return cursor.fetchall()
            
        except Error as e:
            logger.error(f"❌ Log okuma hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_stats(self):
        """İstatistikleri getir"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM system_status WHERE id = 1")
            stats = cursor.fetchone()
            
            return stats or {}
            
        except Error as e:
            logger.error(f"❌ İstatistik okuma hatası: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
