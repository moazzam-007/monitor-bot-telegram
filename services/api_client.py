import aiohttp
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class TokenBotAPI:
    def __init__(self):
        self.api_url = Config.TOKEN_BOT_API_URL
        self.timeout = Config.API_TIMEOUT
        
    async def process_amazon_link(self, payload):
        """Send Amazon link to Token Bot for processing"""
        try:
            if not self.api_url:
                logger.error("❌ TOKEN_BOT_API_URL not configured")
                return None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,  # ✅ Fixed - direct URL
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📡 API Response: {result.get('status', 'unknown')}")
                        return result
                    else:
                        logger.error(f"❌ API Error: {response.status}")
                        return None
                        
        except aiohttp.ClientTimeout:
            logger.error(f"⏰ API Timeout after {self.timeout} seconds")
            return None
            
        except Exception as e:
            logger.error(f"❌ API Communication Error: {e}")
            return None
    
    async def health_check(self):
        """Check if Token Bot API is alive"""
        try:
            if not self.api_url:
                return False
                
            # Convert /api/process to /health
            health_url = self.api_url.replace('/api/process', '/health')
                
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_url,  # ✅ Fixed
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
