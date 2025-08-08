# plugins/amazon_monitor.py (FINAL & COMPLETE)
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
last_message_ids = {} # "Starting Point" Memory

# --- Helper Functions ---
def clean_url(url):
    return url.split('?')[0]

def extract_message_data(message):
    data = {
        "text": message.caption or message.text or "", "images": [],
        "channel_info": {"channel_id": message.chat.id, "message_id": message.id, "channel_title": getattr(message.chat, 'title', 'Unknown')}
    }
    if message.photo:
        if hasattr(message.photo, 'file_id') and message.photo.file_id:
            data["images"].append({"file_id": message.photo.file_id, "file_size": getattr(message.photo, 'file_size', 0)})
    return data

def is_amazon_url(url):
    amazon_patterns = [r'https?://(?:www\.)?amazon\.', r'https?://amzn\.to', r'https?://a\.co']
    for pattern in amazon_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False

# --- Core Logic Function (Updated with all fixes) ---
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

        # --- SMART ROUTING & DUPLICATE CHECK LOGIC ---
        
        amazon_links_in_message = [url for url in all_urls if is_amazon_url(url)]
        non_amazon_links_in_message = [url for url in all_urls if not is_amazon_url(url)]

        # Case 1: Agar message mein non-Amazon links hain (chahe Amazon ho ya na ho)
        if non_amazon_links_in_message:
            # Poore message par duplicate check karein
            if not duplicate_detector.is_duplicate(clean_url(text_content)):
                logger.info(f"✅ Non-Amazon message found. Forwarding message {message.id} to EarnKaro Bot once.")
                try:
                    await client.forward_messages(
                        chat_id=Config.EARNKARO_BOT_USERNAME,
                        from_chat_id=channel_id,
                        message_ids=message.id
                    )
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"❌ Failed to forward message {message.id} to EarnKaro: {e}")
            else:
                logger.info(f"🔄 Skipping duplicate non-Amazon message forwarding for message ID: {message.id}")
            return # Yahan function khatam kar dein

        # Case 2: Agar message mein SIRF Amazon ke links hain
        elif amazon_links_in_message:
            logger.info(f"✅ Amazon-only message found. Processing each link individually.")
            for url in amazon_links_in_message:
                # Har Amazon link par alag se duplicate check karein
                if duplicate_detector.is_duplicate(clean_url(url)):
                    logger.info(f"🔄 Skipping duplicate Amazon URL: {url}")
                    continue
                
                message_data = extract_message_data(message)
                payload = {"url": url, "original_text": message_data["text"], "images": message_data["images"], "channel_info": message_data["channel_info"]}
                await token_bot_api.process_amazon_link(payload)

    except Exception as e:
        logger.error(f"❌ Error in process_message_logic for message {message.id}: {e}", exc_info=True)


# --- Real-time Handler and Poller (No Change) ---
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))
@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    await process_message_logic(client, message)

async def periodic_checker(client: Client):
    logger.info("✅ Active Polling service started.")
    while True:
        try:
            logger.info("... Polling all channels for new messages ...")
            channel_ids = list(map(int, Config.CHANNELS))
            for channel_id in channel_ids:
                try:
                    async for message in client.get_chat_history(chat_id=channel_id, limit=Config.POLLING_MESSAGE_LIMIT):
                        await process_message_logic(client, message)
                except Exception as e:
                    logger.warning(f"⚠️ Could not poll channel {channel_id}. Reason: {e}. Skipping.")
                    continue
            logger.info(f"... Polling cycle complete. Waiting for 4 minutes ...")
            await asyncio.sleep(240)
        except Exception as e:
            logger.error(f"❌ Critical error in periodic_checker: {e}", exc_info=True)
            await asyncio.sleep(60)
