# file: plugins/amazon_monitor.py (FINAL NORMALIZED VERSION)
import asyncio
from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
from services.duplicate_detector import DuplicateDetector
import re
import logging

# --- Initializations ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
token_bot_api = TokenBotAPI()
duplicate_detector = DuplicateDetector(time_window_hours=48)
last_message_ids = {}

# --- Helper Functions ---
def get_url_unique_id(url):
    """URL ka ek unique identifier nikalta hai (ASIN ya cleaned URL)."""
    try:
        if 'amazon' in url or 'amzn.to' in url or 'a.co' in url:
            # ASIN nikalne ki koshish karein
            match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
            if match:
                return f"asin_{match.group(1)}"
        
        # Agar ASIN na mile, ya non-Amazon link ho, to use saaf karein
        return url.split('?')[0].rstrip('/')
    except:
        return url # Failsafe

def extract_message_data(message): # (Ismein koi change nahi)
    #...
    return data

def is_amazon_url(url): # (Ismein koi change nahi)
    #...
    return False

# --- Core Logic Function ---
async def process_message_logic(client, message):
    try:
        channel_id = message.chat.id
        if message.id <= last_message_ids.get(channel_id, 0):
            return
        
        last_message_ids[channel_id] = message.id
        
        text_content = message.caption or message.text or ""
        if not text_content: return
        
        all_urls = list(set(re.findall(r'https?://[^\s]+', text_content, re.IGNORECASE)))
        if not all_urls: return

        # --- NAYI AUR BEHTAR DUPLICATE & ROUTING LOGIC ---
        
        amazon_links_in_message = [url for url in all_urls if is_amazon_url(url)]
        non_amazon_links_in_message = [url for url in all_urls if not is_amazon_url(url)]

        # Case 1: Agar message mein non-Amazon links hain
        if non_amazon_links_in_message:
            unique_id = get_url_unique_id(text_content) # Poore text par check
            if not duplicate_detector.is_duplicate(unique_id):
                logger.info(f"✅ Forwarding non-Amazon msg {message.id} to EarnKaro.")
                await client.forward_messages(chat_id=Config.EARNKARO_BOT_USERNAME, from_chat_id=channel_id, message_ids=message.id)
                duplicate_detector.mark_as_processed(unique_id) # Process mark karein
            return

        # Case 2: Agar message mein SIRF Amazon ke links hain
        elif amazon_links_in_message:
            for url in amazon_links_in_message:
                unique_id = get_url_unique_id(url)
                if duplicate_detector.is_duplicate(unique_id):
                    logger.info(f"🔄 Skipping duplicate Amazon URL: {url}")
                    continue
                
                logger.info(f"✅ Processing Amazon link: {url}")
                message_data = extract_message_data(message)
                payload = {"url": url, "original_text": message_data["text"], "images": message_data["images"], "channel_info": message_data["channel_info"]}
                await token_bot_api.process_amazon_link(payload)
                duplicate_detector.mark_as_processed(unique_id) # Process mark karein

    except Exception as e:
        logger.error(f"❌ Error in process_message_logic for message {message.id}: {e}", exc_info=True)

# (Real-time Handler aur Poller mein koi change nahi hai)
# ...
