"""
Bright Data Web Unlocker - Alternative Implementation
Test both API modes: Direct API vs Proxy Mode
"""

import requests
import time
import logging
from config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrightDataTester:
    def __init__(self):
        self.config = Config()
    
    def test_api_mode_v1(self):
        """Test Method 1: Direct API with zone"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Direct API Mode (zone-based)")
        logger.info("="*60)
        
        url = "https://api.brightdata.com/request"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.BRIGHTDATA_API_KEY}"
        }
        payload = {
            "zone": "web_unlocker1",
            "url": "https://it-tr-appointment.idata.com.tr/tr",
            "format": "raw",
            "country": "tr"
        }
        
        try:
            logger.info(f"📡 Endpoint: {url}")
            logger.info(f"📡 Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=90)
            
            logger.info(f"✅ Status: {response.status_code}")
            logger.info(f"📊 Length: {len(response.text)} chars")
            logger.info(f"📊 Headers: {dict(response.headers)}")
            
            if len(response.text) > 0:
                logger.info(f"📄 Preview: {response.text[:300]}")
            else:
                logger.error(f"❌ Empty response!")
                logger.error(f"💡 Raw content: {response.content}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def test_api_mode_v2(self):
        """Test Method 2: Simplified payload"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Simplified API Mode")
        logger.info("="*60)
        
        url = "https://api.brightdata.com/request"
        headers = {
            "Authorization": f"Bearer {self.config.BRIGHTDATA_API_KEY}"
        }
        payload = {
            "url": "https://it-tr-appointment.idata.com.tr/tr"
        }
        
        try:
            logger.info(f"📡 Endpoint: {url}")
            logger.info(f"📡 Payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=90)
            
            logger.info(f"✅ Status: {response.status_code}")
            logger.info(f"📊 Length: {len(response.text)} chars")
            
            if len(response.text) > 0:
                logger.info(f"📄 Preview: {response.text[:300]}")
            else:
                logger.error(f"❌ Empty response!")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def test_proxy_mode(self):
        """Test Method 3: Proxy Mode (recommended by Bright Data)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Proxy Mode")
        logger.info("="*60)
        
        # Bright Data Proxy format: 
        # http://username:password@proxy-host:port
        # Username format: customer-CUSTOMER_ID-zone-ZONE_NAME
        
        # Example proxy (you need to replace with your actual credentials)
        proxy_host = "brd.superproxy.io"
        proxy_port = "22225"
        
        # This is just a template - actual credentials needed
        logger.info("⚠️ Proxy mode requires specific zone credentials")
        logger.info("💡 Check Bright Data Dashboard → Zone → Access Parameters")
        logger.info(f"📡 Proxy format: customer-XXX-zone-ZONE@{proxy_host}:{proxy_port}")
    
    def test_all(self):
        """Run all tests"""
        logger.info("🚀 Starting Bright Data API Tests...")
        logger.info(f"🔑 API Key: {self.config.BRIGHTDATA_API_KEY[:20]}...")
        
        self.test_api_mode_v1()
        time.sleep(2)
        
        self.test_api_mode_v2()
        time.sleep(2)
        
        self.test_proxy_mode()
        
        logger.info("\n" + "="*60)
        logger.info("✅ Tests completed!")
        logger.info("="*60)

if __name__ == "__main__":
    tester = BrightDataTester()
    tester.test_all()
