# plugins/amazon_monitor.py (Updated with Poller Logic)
import asyncio
from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
from services.duplicate_detector import DuplicateDetector
import re
import logging
from utils.helpers import clean_url, extract_product_context

# --- Initializations (No Change) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
token_bot_api = TokenBotAPI()
duplicate_detector = DuplicateDetector(time_window_hours=24)
logger.info(f"🔧 DEBUG: Configured channels: {Config.CHANNELS}")
logger.info(f"🔧 DEBUG: Total channels: {len(Config.CHANNELS)}")
logger.info(f"🔧 DEBUG: API URL: {Config.TOKEN_BOT_API_URL}")
AMAZON_PATTERNS = [
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/[^\s]*',
    r'https?://amzn\.to/[^\s]*',
    r'https?://a\.co/[^\s]*',
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/dp/[A-Z0-9]{10}[^\s]*',
    r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/gp/product/[A-Z0-9]{10}[^\s]*'
]

# --- Helper Functions (No Change) ---
def extract_amazon_urls(text):
    if not text: return []
    urls = []
    for pattern in AMAZON_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    return list(set(urls))

def extract_message_data(message):
    data = {
        "text": message.caption or message.text or "", "images": [],
        "channel_info": { "channel_id": message.chat.id, "message_id": message.id, "channel_title": getattr(message.chat, 'title', 'Unknown')}
    }
    if message.photo:
        if hasattr(message.photo, 'file_id') and message.photo.file_id:
            data["images"].append({"file_id": message.photo.file_id, "file_size": getattr(message.photo, 'file_size', 0)})
    if message.media_group_id: pass
    return data

# === LOGIC KO ALAG FUNCTION MEIN NIKALA GAYA HAI ===
async def process_message_logic(client, message):
    """Is function mein message ko process karne ki asal logic hai, taake isay dobara istemal kiya ja sake."""
    try:
        channel_title = getattr(message.chat, 'title', 'Unknown')
        text_content = message.caption or message.text or ""

        if not text_content or len(text_content) < 10:
            return # Chote ya khali messages ko ignore karein
        
        amazon_urls = extract_amazon_urls(text_content)
        if not amazon_urls:
            return # Bina Amazon URL wale messages ko ignore karein
        
        logger.info(f"✅ Link Found in {channel_title}. Processing...")
        
        for url in amazon_urls:
            clean_url_str = clean_url(url)
            # Duplicate detector yahan sab se ahem hai, taake poller baar baar ek hi link na bheje
            if duplicate_detector.is_duplicate(clean_url_str):
                logger.info(f"🔄 Skipping duplicate URL from polling/event: {url}")
                continue
            
            message_data = extract_message_data(message)
            payload = {
                "url": url, "original_text": message_data["text"],
                "images": message_data["images"], "channel_info": message_data["channel_info"]
            }
            await token_bot_api.process_amazon_link(payload)

    except Exception as e:
        logger.error(f"❌ Error in process_message_logic for message {message.id}: {e}", exc_info=True)


# === PURANA HANDLER AB SIRF LOGIC FUNCTION KO CALL KAREGA ===
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))
@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    """Yeh handler real-time updates ke liye hai (aapke test channels ke liye)."""
    logger.info(f"🔥 Real-time update received from {getattr(message.chat, 'title', 'Unknown')}")
    await process_message_logic(client, message)


# === YEH NAYI ACTIVE POLLING LOGIC HAI ===
async def periodic_checker(client: Client):
    """Har 60 seconds mein sabhi channels ke aakhri 10 messages check karta hai."""
    logger.info("✅ Active Polling service started in background.")
    while True:
        try:
            logger.info("... Polling all channels for new messages ...")
            channel_ids = list(map(int, Config.CHANNELS))
            for channel_id in channel_ids:
                # Channel ke aakhri 10 messages nikalein
                async for message in client.get_chat_history(chat_id=channel_id, limit=10):
                    # In messages ko bhi usi logic se process karein
                    await process_message_logic(client, message)
                await asyncio.sleep(2) # Har channel ke baad 2 second ka gap taake Telegram block na kare
            
            logger.info("... Polling cycle complete. Waiting for 60 seconds ...")
            await asyncio.sleep(60) # Agle check ke liye 60 second intezar karein

        except Exception as e:
            logger.error(f"❌ Error in periodic_checker loop: {e}", exc_info=True)
            await asyncio.sleep(60) # Error aane par bhi 60 second baad dobara try karein
