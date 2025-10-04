"""
MySQL Database Setup for Railway
"""

CREATE_TABLES_SQL = """
-- Kontrol logları tablosu
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CAPTCHA geçmişi tablosu
CREATE TABLE IF NOT EXISTS captcha_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    captcha_image LONGTEXT,
    captcha_text VARCHAR(10),
    solved_correctly BOOLEAN,
    mistral_response_time INT,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sistem durumu tablosu
CREATE TABLE IF NOT EXISTS system_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    last_check_time DATETIME,
    monitoring_active BOOLEAN DEFAULT FALSE,
    total_checks INT DEFAULT 0,
    successful_checks INT DEFAULT 0,
    failed_checks INT DEFAULT 0,
    appointments_found INT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- İlk kayıt
INSERT INTO system_status (id, total_checks, successful_checks, failed_checks, appointments_found)
VALUES (1, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE id=id;
"""

# MySQL bağlantı ayarları (Railway environment variables'dan)
"""
Railway'de MySQL eklendikten sonra otomatik olarak şu environment variables eklenir:
- MYSQLHOST
- MYSQLPORT
- MYSQLDATABASE
- MYSQLUSER
- MYSQLPASSWORD

Bağlantı string'i:
mysql+pymysql://{MYSQLUSER}:{MYSQLPASSWORD}@{MYSQLHOST}:{MYSQLPORT}/{MYSQLDATABASE}
"""
