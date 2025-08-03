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

    # Extract images
    if message.photo:
        data["images"].append({
            "file_id": message.photo.file_id,
            "file_size": message.photo.file_size
        })

    return data

# Main handler for ALL channels and ALL message types
@Client.on_message(filters.chat(Config.CHANNELS))
async def universal_monitor(client, message):
    """Universal handler for ALL configured channels"""
    try:
        channel_title = getattr(message.chat, 'title', 'Unknown')
        channel_id = message.chat.id

        logger.info(f"🎯 MESSAGE RECEIVED from {channel_title} ({channel_id})")

        # Extract text from any message type (including forwarded)
        text_content = ""
        if message.text:
            text_content = message.text
        elif message.caption:
            text_content = message.caption
        else:
            # Skip non-text messages
            return

        if not text_content or len(text_content) < 10:
            return

        logger.info(f"📝 Text: {text_content[:100]}...")

        # Check for Amazon URLs
        amazon_urls = extract_amazon_urls(text_content)
        if not amazon_urls:
            return

        logger.info(f"🔍 Found {len(amazon_urls)} Amazon link(s) from {channel_title}: {amazon_urls}")

        # Extract message data
        message_data = extract_message_data(message)

        # Process each URL
        for url in amazon_urls:
            try:
                payload = {
                    "url": url,
                    "original_text": message_data["text"],
                    "images": message_data["images"],
                    "channel_info": message_data["channel_info"]
                }

                logger.info(f"📤 Sending {url} to API from {channel_title}")

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

# Simple test handler to log all channel activity
@Client.on_message(filters.all)
async def channel_activity_log(client, message):
    """Log activity from all channels"""
    if message.chat.id in Config.CHANNELS:
        channel_title = getattr(message.chat, 'title', 'Unknown')
        logger.info(f"📊 ACTIVITY: {channel_title} ({message.chat.id}) - Message type: {message.media or 'text'}")
