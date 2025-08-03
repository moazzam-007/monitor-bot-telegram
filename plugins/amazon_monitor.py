import asyncio
from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
from services.duplicate_detector import DuplicateDetector 
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API client
token_bot_api = TokenBotAPI()

# Initialize Duplicate Detector
duplicate_detector = DuplicateDetector(time_window_hours=24)

# DEBUG: Log configuration at startup
logger.info(f"🔧 DEBUG: Configured channels: {Config.CHANNELS}")
logger.info(f"🔧 DEBUG: Total channels: {len(Config.CHANNELS)}")
logger.info(f"🔧 DEBUG: API URL: {Config.TOKEN_BOT_API_URL}")

# Amazon URL patterns
AMAZON_PATTERNS = [
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/[^\s]*',
    r'https?://amzn\.to/[^\s]*',
    r'https?://a\.co/[^\s]*'
]

def extract_amazon_urls(text):
    """Extract all Amazon URLs from text"""
    if not text:
        return []
    urls = []
    for pattern in AMAZON_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    return list(set(urls))

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

    # Extract images - send file_id only if valid
    if message.photo:
        if hasattr(message.photo, 'file_id') and message.photo.file_id:
            data["images"].append({
                "file_id": message.photo.file_id,
                "file_size": getattr(message.photo, 'file_size', 0)
            })
    
    # Handle media groups (multiple images)
    # Pyrogram sends each photo in a media group as a separate message
    # So this block is not strictly necessary for basic functionality
    if message.media_group_id:
        pass

    return data

# Universal message handler - monitors ALL messages without filters
@Client.on_message()
async def universal_message_monitor(client, message):
    """Monitor ALL messages and filter for configured channels"""
    try:
        # Skip if no chat info
        if not hasattr(message, 'chat') or not message.chat:
            return
        
        channel_id = message.chat.id
        channel_title = getattr(message.chat, 'title', 'Unknown')

        # Check if the channel is in our configured list
        # Note: Config.CHANNELS will be a list of strings, so we must match the type
        # The fix is to ensure the channel IDs are properly formatted in .env file
        if str(channel_id) not in Config.CHANNELS:
            return
            
        logger.info(f"🎯 MESSAGE from CONFIGURED CHANNEL: {channel_title} ({channel_id})")

        # Extract text from any message type
        text_content = message.caption or message.text or ""
        
        if not text_content or len(text_content) < 10:
            return

        logger.info(f"📝 Text: {text_content[:100]}...")

        # Check for Amazon URLs
        amazon_urls = extract_amazon_urls(text_content)
        if not amazon_urls:
            return

        logger.info(f"🔍 Found {len(amazon_urls)} Amazon link(s) from {channel_title}: {amazon_urls}")

        # Process each URL
        for url in amazon_urls:
            # Check for duplicates before sending to API
            # Note: We pass the URL without query parameters for cleaner detection
            clean_url = url.split('?')[0].split('#')[0]
            if duplicate_detector.is_duplicate(clean_url):
                logger.info(f"🔄 SKIPPING: Duplicate URL {url} from {channel_title}")
                continue

            try:
                message_data = extract_message_data(message)
                payload = {
                    "url": url,
                    "original_text": message_data["text"],
                    "images": message_data["images"],
                    "channel_info": message_data["channel_info"]
                }
                
                logger.info(f"📤 Sending {url} to API from {channel_title}")

                # API call with retry logic
                response = await token_bot_api.process_amazon_link(payload)

                if response and response.get("status") == "success":
                    logger.info(f"✅ SUCCESS: {url} from {channel_title}")
                elif response and response.get("status") == "duplicate":
                    logger.info(f"🔄 DUPLICATE: {url} from {channel_title}")
                else:
                    logger.error(f"❌ FAILED: {url} from {channel_title} - {response}")

            except Exception as e:
                logger.error(f"❌ Error processing {url} from {channel_title}: {e}")

    except Exception as e:
        logger.error(f"❌ Universal monitor error: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
