from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API client
token_bot_api = TokenBotAPI()

# DEBUG: Log configuration at startup
logger.info(f"🔧 DEBUG: Configured channels: {Config.CHANNELS}")
logger.info(f"🔧 DEBUG: Channel types: {[type(ch) for ch in Config.CHANNELS]}")
logger.info(f"🔧 DEBUG: API URL: {Config.TOKEN_BOT_API_URL}")
logger.info(f"🔧 DEBUG: Debug mode: {Config.DEBUG_MODE}")

# Amazon URL patterns
AMAZON_PATTERNS = [
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/[^\s]*',
    r'https?://amzn\.to/[^\s]*',
    r'https?://a\.co/[^\s]*'
]

def extract_amazon_urls(text):
    """Extract all Amazon URLs from text"""
    urls = []
    for pattern in AMAZON_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    return list(set(urls))  # Remove duplicates

def extract_message_data(message):
    """Extract all relevant data from message"""
    data = {
        "text": message.caption or message.text or "",
        "images": [],
        "channel_info": {
            "channel_id": message.chat.id,
            "message_id": message.id,
            "channel_title": getattr(message.chat, 'title', 'Unknown')
        }
    }
    
    # Extract images
    if message.photo:
        data["images"].append({
            "file_id": message.photo.file_id,
            "file_size": message.photo.file_size
        })
    
    # Extract media group (multiple images)
    if hasattr(message, 'media_group_id') and message.media_group_id:
        # This will be handled by pyrogram's collect_related_messages
        pass
    
    return data

@Client.on_message(filters.chat(Config.CHANNELS) & filters.text)
async def monitor_amazon_links(client, message):
    """Main monitoring function - FIXED VERSION"""
    try:
        logger.info(f"🎯 MAIN HANDLER TRIGGERED! From {getattr(message.chat, 'title', 'Unknown')} ({message.chat.id})")
        
        # Extract text content
        text_content = message.text or ""
        logger.info(f"📝 Message text: {text_content[:100]}...")
        
        # Check for Amazon URLs
        amazon_urls = extract_amazon_urls(text_content)
        if not amazon_urls:
            logger.info("❌ No Amazon links found")
            return  # No Amazon links found
            
        logger.info(f"🔍 Found {len(amazon_urls)} Amazon link(s): {amazon_urls}")
        
        # Extract message data
        message_data = extract_message_data(message)
        
        # Process each Amazon URL
        for url in amazon_urls:
            try:
                # Prepare API payload
                payload = {
                    "url": url,
                    "original_text": message_data["text"],
                    "images": message_data["images"],
                    "channel_info": message_data["channel_info"]
                }
                
                # Send to Token Bot API
                logger.info(f"📤 Sending to Token Bot API: {Config.TOKEN_BOT_API_URL}")
                logger.info(f"📤 URL: {url[:50]}...")
                
                response = await token_bot_api.process_amazon_link(payload)
                logger.info(f"📥 API Response: {response}")
                
                if response and response.get("status") == "success":
                    logger.info(f"✅ Successfully processed: {url}")
                elif response and response.get("status") == "duplicate":
                    logger.info(f"🔄 Duplicate link skipped: {url}")
                else:
                    logger.error(f"❌ Failed to process: {url}")
                    logger.error(f"❌ Response: {response}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing URL {url}: {str(e)}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                
    except Exception as e:
        logger.error(f"❌ Monitor function error: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")

# Simple test handler to verify filters work
@Client.on_message(filters.chat(Config.CHANNELS))
async def test_channel_filter(client, message):
    """Test if channel filter is working"""
    logger.info(f"✅ CHANNEL FILTER WORKS! Message from: {message.chat.id}")
