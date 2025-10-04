let isMonitoring = false;
let statusInterval = null;
let statsInterval = null;

let detailedLogsInterval = null;

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Uygulama başlatıldı');
    loadStatus();
    loadHistory();
    startStatusPolling();
    startDetailedLogsPolling(); // Detaylı log polling başlat
});

// İzlemeyi başlat
async function startMonitoring() {
    const interval = document.getElementById('intervalInput').value;
    
    if (interval < 30) {
        showToast('Kontrol aralığı en az 30 saniye olmalıdır!', 'error');
        return;
    }
    
    try {
        addLog('İzleme başlatılıyor...', 'info');
        
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ interval: parseInt(interval) })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isMonitoring = true;
            updateUIState(true);
            addLog(`✅ İzleme başlatıldı (${interval}s aralıklarla)`, 'success');
            showToast('İzleme başlatıldı!', 'success');
            
            // Durum güncellemelerini başlat
            if (!statusInterval) {
                startStatusPolling();
            }
        } else {
            addLog(`❌ Başlatma hatası: ${data.error}`, 'error');
            showToast(data.error, 'error');
        }
    } catch (error) {
        addLog(`❌ Bağlantı hatası: ${error.message}`, 'error');
        showToast('Sunucuya bağlanılamadı!', 'error');
    }
}

// İzlemeyi durdur
async function stopMonitoring() {
    try {
        addLog('İzleme durduruluyor...', 'info');
        
        const response = await fetch('/api/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isMonitoring = false;
            updateUIState(false);
            addLog('⏹️ İzleme durduruldu', 'warning');
            showToast('İzleme durduruldu', 'warning');
        } else {
            addLog(`❌ Durdurma hatası: ${data.error}`, 'error');
            showToast(data.error, 'error');
        }
    } catch (error) {
        addLog(`❌ Bağlantı hatası: ${error.message}`, 'error');
        showToast('Sunucuya bağlanılamadı!', 'error');
    }
}

// Anında kontrol
async function checkNow() {
    try {
        addLog('⚡ Anında kontrol yapılıyor...', 'info');
        document.getElementById('checkNowBtn').disabled = true;
        
        const response = await fetch('/api/check-now', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(`✅ Kontrol tamamlandı: ${data.result}`, 'success');
            showToast('Kontrol tamamlandı!', 'success');
            loadHistory();
        } else {
            addLog(`❌ Kontrol hatası: ${data.error}`, 'error');
            showToast(data.error, 'error');
        }
    } catch (error) {
        addLog(`❌ Bağlantı hatası: ${error.message}`, 'error');
        showToast('Sunucuya bağlanılamadı!', 'error');
    } finally {
        setTimeout(() => {
            document.getElementById('checkNowBtn').disabled = false;
        }, 2000);
    }
}

// Durum güncelleme polling
function startStatusPolling() {
    statusInterval = setInterval(loadStatus, 1000); // 1 saniyede bir (HIZLI!)
    statsInterval = setInterval(loadHistory, 5000); // 5 saniyede bir
}

// Detaylı log polling (gerçek zamanlı backend logları)
function startDetailedLogsPolling() {
    detailedLogsInterval = setInterval(loadDetailedLogs, 500); // 0.5 saniyede bir (ÇOK HIZLI!)
    loadDetailedLogs(); // İlk yüklemeyi hemen yap
}

// Backend'den detaylı logları yükle
async function loadDetailedLogs() {
    try {
        const response = await fetch('/api/logs/recent');
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
            const logContainer = document.getElementById('logContainer');
            
            // Mevcut logları sakla
            const currentLogs = Array.from(logContainer.children);
            const currentCount = currentLogs.length;
            
            // Yeni logları ekle (en yeni önce)
            data.logs.reverse().forEach(log => {
                const logEntry = document.createElement('div');
                const typeClass = log.level === 'ERROR' ? 'error' : 
                                 log.level === 'WARNING' ? 'warning' : 
                                 log.level === 'SUCCESS' ? 'success' : 'info';
                
                logEntry.className = `log-entry ${typeClass}`;
                logEntry.innerHTML = `
                    <span class="log-time">${log.timestamp}</span>
                    <span class="log-message">${log.message}</span>
                `;
                
                // Yeni logu en üste ekle
                if (currentCount === 0 || logEntry.textContent !== currentLogs[0].textContent) {
                    logContainer.insertBefore(logEntry, logContainer.firstChild);
                }
            });
            
            // En fazla 100 log tut
            while (logContainer.children.length > 100) {
                logContainer.removeChild(logContainer.lastChild);
            }
        }
        
    } catch (error) {
        console.error('Detaylı log yükleme hatası:', error);
    }
}

// Mevcut durumu yükle
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Durum göstergesini güncelle
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        if (data.monitoring_active) {
            statusDot.className = 'status-dot active';
            statusText.textContent = 'İzleme aktif';
            isMonitoring = true;
        } else {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Sistem hazır';
            isMonitoring = false;
        }
        
        // Son kontrol bilgilerini güncelle
        if (data.last_check_time) {
            const lastCheckDate = new Date(data.last_check_time * 1000);
            document.getElementById('lastCheck').textContent = lastCheckDate.toLocaleString('tr-TR');
        }
        
        document.getElementById('lastResult').textContent = data.last_check_status;
        document.getElementById('checkInterval').textContent = data.check_interval;
        
        // CAPTCHA görselini göster (otomatik güncelleme)
        const captchaCard = document.getElementById('captchaCard');
        const captchaImage = document.getElementById('captchaImage');
        const captchaText = document.getElementById('captchaText');
        
        if (data.captcha_image) {
            // CAPTCHA varsa kartı göster
            if (captchaCard.style.display === 'none') {
                captchaCard.style.display = 'block';
                captchaCard.style.animation = 'fadeIn 0.3s ease-in';
            }
            
            // Görsel değiştiyse güncelle (smooth transition)
            if (captchaImage.src !== data.captcha_image) {
                captchaImage.style.opacity = '0.3';
                setTimeout(() => {
                    captchaImage.src = data.captcha_image;
                    captchaImage.style.opacity = '1';
                }, 150);
            }
            
            // Metin değiştiyse güncelle (smooth transition)
            if (captchaText.textContent !== (data.captcha_text || '-')) {
                captchaText.style.transform = 'scale(1.2)';
                captchaText.style.color = '#28a745';
                captchaText.textContent = data.captcha_text || '-';
                setTimeout(() => {
                    captchaText.style.transform = 'scale(1)';
                    captchaText.style.color = '#007bff';
                }, 300);
            }
        } else {
            captchaCard.style.display = 'none';
        }
        
        updateUIState(data.monitoring_active);
        
    } catch (error) {
        console.error('Durum yükleme hatası:', error);
    }
}

// Kontrol geçmişini yükle
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        const historyContainer = document.getElementById('historyContainer');
        
        if (data.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted">Henüz kontrol yapılmadı...</p>';
            return;
        }
        
        // İstatistikleri hesapla
        const totalChecks = data.length;
        const successfulChecks = data.filter(c => c.status === 'success').length;
        const failedChecks = data.filter(c => c.error).length;
        const appointmentsFound = data.filter(c => c.appointment_found).length;
        
        document.getElementById('totalChecks').textContent = totalChecks;
        document.getElementById('successfulChecks').textContent = successfulChecks;
        document.getElementById('failedChecks').textContent = failedChecks;
        document.getElementById('appointmentsFound').textContent = appointmentsFound;
        
        // Geçmişi göster
        historyContainer.innerHTML = data.slice(0, 10).map(check => {
            const date = new Date(check.timestamp);
            const statusClass = check.error ? 'error' : 'success';
            const badgeClass = check.error ? 'badge-error' : 'badge-success';
            const statusText = check.appointment_found ? '🎉 Randevu bulundu!' : 
                             check.error ? `❌ ${check.error}` : '✅ Başarılı';
            
            return `
                <div class="history-item ${statusClass}">
                    <div class="history-info">
                        <div class="history-time">${date.toLocaleString('tr-TR')}</div>
                        <div class="history-status">${statusText}</div>
                    </div>
                    <div class="history-badge ${badgeClass}">
                        ${check.appointment_found ? 'Randevu' : check.error ? 'Hata' : 'Kontrol'}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Geçmiş yükleme hatası:', error);
    }
}

// Geçmişi yenile
function refreshHistory() {
    addLog('🔄 Geçmiş yenileniyor...', 'info');
    loadHistory();
    showToast('Geçmiş yenilendi', 'success');
}

// UI durumunu güncelle
function updateUIState(monitoring) {
    document.getElementById('startBtn').disabled = monitoring;
    document.getElementById('stopBtn').disabled = !monitoring;
    document.getElementById('intervalInput').disabled = monitoring;
}

// Log ekle
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const time = new Date().toLocaleTimeString('tr-TR');
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${message}</span>
    `;
    
    logContainer.insertBefore(logEntry, logContainer.firstChild);
    
    // En fazla 50 log tut
    while (logContainer.children.length > 50) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Logları temizle
function clearLogs() {
    const logContainer = document.getElementById('logContainer');
    logContainer.innerHTML = `
        <div class="log-entry info">
            <span class="log-time">${new Date().toLocaleTimeString('tr-TR')}</span>
            <span class="log-message">Loglar temizlendi</span>
        </div>
    `;
    showToast('Loglar temizlendi', 'success');
}

// Toast bildirimi göster
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.style.borderLeftColor = 
        type === 'success' ? 'var(--primary-color)' :
        type === 'error' ? 'var(--danger-color)' :
        type === 'warning' ? 'var(--warning-color)' :
        'var(--info-color)';
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Sayfa kapatılırken polling'i durdur
window.addEventListener('beforeunload', () => {
    if (statusInterval) clearInterval(statusInterval);
    if (statsInterval) clearInterval(statsInterval);
    if (detailedLogsInterval) clearInterval(detailedLogsInterval);
});