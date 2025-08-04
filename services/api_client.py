import aiohttp
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class TokenBotAPI:
    def __init__(self):
        self.api_url = Config.TOKEN_BOT_API_URL
        # Aiohttp timeout should be an object, not just an integer
        self.timeout = aiohttp.ClientTimeout(total=Config.API_TIMEOUT)
        
    async def process_amazon_link(self, payload, max_retries=3, delay=5):
        """Send Amazon link to Token Bot for processing with retry logic"""
        if not self.api_url:
            logger.error("❌ TOKEN_BOT_API_URL not configured")
            return None
            
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"📡 API Response: {result.get('status', 'unknown')} (Attempt {attempt + 1})")
                            return result
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ API Error: {response.status} - {error_text} (Attempt {attempt + 1})")
                            
            except (aiohttp.ClientTimeout, aiohttp.ClientError) as e:
                logger.error(f"⏰ API Timeout/Connection Error: {e} (Attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"❌ API Communication Error: {e} (Attempt {attempt + 1})")
                
            if attempt < max_retries - 1:
                logger.warning(f"🔄 Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                
        return None # Return None after all retries fail
    
    async def health_check(self):
        """Check if Token Bot API is alive"""
        if not self.api_url:
            return False
        
        try:
            health_url = self.api_url.replace('/api/process', '/health')
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(
                    health_url
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
