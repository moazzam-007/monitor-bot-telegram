import aiohttp
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class TokenBotAPI:
    def __init__(self):
        self.api_url = Config.TOKEN_BOT_API_URL
        self.timeout = aiohttp.ClientTimeout(total=Config.API_TIMEOUT)
        
    async def process_amazon_link(self, payload, max_retries=3, delay=5):
        """Send Amazon link to Token Bot for processing with retry logic"""
        if not self.api_url:
            logger.error("❌ TOKEN_BOT_API_URL not configured")
            return None
            
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 DEBUG: Attempting API call to {self.api_url} (Attempt {attempt + 1})")
                logger.info(f"🔍 DEBUG: Payload: {payload}")
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        logger.info(f"🔍 DEBUG: API Response status: {response.status}")
                        
                        # === YEH LINE BADLI GAYI HAI ===
                        # Ab yeh 200 (OK) aur 202 (Accepted) dono ko success manega
                        if response.status in [200, 202]: 
                            result = await response.json()
                            logger.info(f"🔍 DEBUG: API Response: {result}")
                            return result
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ API Error: {response.status} - {error_text}")
                            
            except (aiohttp.ClientTimeout, aiohttp.ClientError) as e:
                logger.error(f"⏰ API Timeout/Connection Error: {e} (Attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"❌ API Communication Error: {e} (Attempt {attempt + 1})")
                
            if attempt < max_retries - 1:
                logger.warning(f"🔄 Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                
        logger.error(f"❌ All {max_retries} attempts failed")
        return None
