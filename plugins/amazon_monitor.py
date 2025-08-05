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
    
    # === YEH LOGIC THEEK KI GAYI HAI ===
    # Ab yeh single photo ko bhi safely handle karega
    if message.photo:
        # Direct access to file_id is safer than using an index,
        # as message.photo is not always a list.
        if hasattr(message.photo, 'file_id') and message.photo.file_id:
            data["images"].append({
                "file_id": message.photo.file_id,
                "file_size": getattr(message.photo, 'file_size', 0)
            })
    # ====================================
    
    # Handle media groups (multiple images)
    if message.media_group_id:
        # For media groups, we would need to fetch all media in the group
        # This is a simplified version - in production you might want to handle this more thoroughly
        pass
    
    return data

# Create a filter for the configured channels
# This correctly converts string IDs from config to integers
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))

@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    """Monitor messages from configured channels"""
    try:
        channel_id = message.chat.id
        channel_title = getattr(message.chat, 'title', 'Unknown')
        
        # DEBUG: Log all messages from configured channels
        logger.info(f"🔍 DEBUG: Received message from {channel_title} ({channel_id})")
        
        # Extract text from any message type
        text_content = message.caption or message.text or ""
        
        # DEBUG: Log message content
        logger.info(f"🔍 DEBUG: Message content: {text_content[:100]}...")
        
        if not text_content or len(text_content) < 10:
            logger.info(f"🔍 DEBUG: Skipping message - too short or no text")
            return
            
        # Check for Amazon URLs
        amazon_urls = extract_amazon_urls(text_content)
        logger.info(f"🔍 DEBUG: Found URLs: {amazon_urls}")
        
        if not amazon_urls:
            logger.info(f"🔍 DEBUG: No Amazon URLs found in message")
            return
            
        logger.info(f"🔍 Found {len(amazon_urls)} Amazon link(s) from {channel_title}: {amazon_urls}")
        
        # Process each URL
        for url in amazon_urls:
            logger.info(f"🔍 DEBUG: Processing URL: {url}")
            
            # Clean the URL for duplicate checking
            clean_url_str = clean_url(url)
            logger.info(f"🔍 DEBUG: Cleaned URL: {clean_url_str}")
            
            # Check for duplicates before sending to API
            if duplicate_detector.is_duplicate(clean_url_str):
                logger.info(f"🔍 DEBUG: Skipping duplicate URL: {url}")
                continue
                
            try:
                # This function will now work correctly for photo messages
                message_data = extract_message_data(message)
                
                # Extract product context for better logging
                context = extract_product_context(text_content, url)
                logger.info(f"🔍 DEBUG: Context: {context[:100]}...")
                
                payload = {
                    "url": url,
                    "original_text": message_data["text"],
                    "images": message_data["images"],
                    "channel_info": message_data["channel_info"]
                }
                
                logger.info(f"🔍 DEBUG: Sending payload to API: {payload}")
                
                # API call with retry logic
                response = await token_bot_api.process_amazon_link(payload)
                logger.info(f"🔍 DEBUG: API response: {response}")
                
                if response and response.get("status") == "success":
                    logger.info(f"✅ SUCCESS: {url} from {channel_title}")
                elif response and response.get("status") == "duplicate":
                    logger.info(f"🔄 DUPLICATE: {url} from {channel_title}")
                else:
                    logger.error(f"❌ FAILED: {url} from {channel_title} - {response}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {url} from {channel_title}: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                
    except Exception as e:
        logger.error(f"❌ Monitor error: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
