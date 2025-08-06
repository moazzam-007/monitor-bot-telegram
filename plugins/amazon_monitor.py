# file: plugins/amazon_monitor.py
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

# === "STARTING POINT" MEMORY ===
# Yeh dictionary startup par `bot.py` se fill hogi
last_message_ids = {} # Format: {channel_id: message_id}

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

# --- Core Logic Function ---
async def process_message_logic(client, message):
    try:
        channel_id = message.chat.id
        # Check karein ke message humare "starting point" se naya hai ya nahi
        if message.id <= last_message_ids.get(channel_id, 0):
            return # Agar purana message hai to ignore karein

        # Naye message ki ID ko foran memory mein update karein
        last_message_ids[channel_id] = message.id
        
        text_content = message.caption or message.text or ""
        if not text_content: return
        all_urls = re.findall(r'https?://[^\s]+', text_content, re.IGNORECASE)
        if not all_urls: return
        
        for url in all_urls:
            if duplicate_detector.is_duplicate(clean_url(url)):
                continue

            if is_amazon_url(url):
                message_data = extract_message_data(message)
                payload = {"url": url, "original_text": message_data["text"], "images": message_data["images"], "channel_info": message_data["channel_info"]}
                await token_bot_api.process_amazon_link(payload)
            else:
                try:
                    await client.forward_messages(chat_id=Config.EARNKARO_BOT_USERNAME, from_chat_id=channel_id, message_ids=message.id)
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"❌ Failed to forward message {message.id} to EarnKaro: {e}")

    except Exception as e:
        logger.error(f"❌ Error in process_message_logic for message {message.id}: {e}", exc_info=True)

# --- Real-time Message Handler ---
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))
@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    await process_message_logic(client, message)

# --- Active Polling Logic ---
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
