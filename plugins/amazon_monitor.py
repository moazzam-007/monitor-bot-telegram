import asyncio
from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
from services.duplicate_detector import DuplicateDetector 
import re
import logging
from utils.helpers import clean_url, extract_product_context

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

# Amazon URL patterns - enhanced to catch more variations
AMAZON_PATTERNS = [
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/[^\s]*',
    r'https?://amzn\.to/[^\s]*',
    r'https?://a\.co/[^\s]*',
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/dp/[A-Z0-9]{10}[^\s]*',
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/gp/product/[A-Z0-9]{10}[^\s]*'
]

def extract_amazon_urls(text):
    """Extract all Amazon URLs from text"""
    if not text:
        return []
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
    
    # Extract images - enhanced to handle multiple images better
    if message.photo:
        # Get the highest resolution photo
        photo = message.photo[-1]  # The last photo is the highest resolution
        if hasattr(photo, 'file_id') and photo.file_id:
            data["images"].append({
                "file_id": photo.file_id,
                "file_size": getattr(photo, 'file_size', 0)
            })
    
    # Handle media groups (multiple images)
    if message.media_group_id:
        # For media groups, we would need to fetch all media in the group
        # This is a simplified version - in production you might want to handle this more thoroughly
        pass
    
    return data

# Create a filter for the configured channels
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))

@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    """Monitor messages from configured channels"""
    try:
        channel_id = message.chat.id
        channel_title = getattr(message.chat, 'title', 'Unknown')
        
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
            # Clean the URL for duplicate checking
            clean_url_str = clean_url(url)
            
            # Check for duplicates before sending to API
            if duplicate_detector.is_duplicate(clean_url_str):
                logger.info(f"🔄 SKIPPING: Duplicate URL {url} from {channel_title}")
                continue
                
            try:
                message_data = extract_message_data(message)
                
                # Extract product context for better logging
                context = extract_product_context(text_content, url)
                logger.info(f"📋 Context: {context[:100]}...")
                
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
        logger.error(f"❌ Monitor error: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
