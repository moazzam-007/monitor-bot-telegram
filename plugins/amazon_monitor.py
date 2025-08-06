# plugins/amazon_monitor.py (BULLETPROOF VERSION)
import asyncio
from pyrogram import Client, filters
from config import Config
from services.api_client import TokenBotAPI
from services.duplicate_detector import DuplicateDetector
import re
import logging
import json
import os

# --- Initializations ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
token_bot_api = TokenBotAPI()
duplicate_detector = DuplicateDetector(time_window_hours=48) # Duplicate window 48 ghante tak barha diya

# --- Nayi "Persistent ID Tracking" Logic ---
LAST_IDS_FILE = 'last_processed_ids.json'
last_processed_ids = {} # Format: {channel_id: message_id}
message_counter = 0 # Batch saving ke liye naya counter
SAVE_BATCH_SIZE = 10 # Har 10 real-time messages ke baad save karein

def load_last_ids():
    """Restart ke baad, purani IDs ko file se load karein."""
    global last_processed_ids
    if os.path.exists(LAST_IDS_FILE):
        with open(LAST_IDS_FILE, 'r') as f:
            try:
                loaded_ids = json.load(f)
                # Keys ko integer mein convert karein, yeh zaroori hai
                last_processed_ids = {int(k): v for k, v in loaded_ids.items()}
                logger.info(f"✅ Loaded {len(last_processed_ids)} last processed IDs from {LAST_IDS_FILE}")
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"⚠️ Could not read {LAST_IDS_FILE}. Starting fresh.")
                last_processed_ids = {}
    else:
        logger.info(f"📄 {LAST_IDS_FILE} not found. Starting with a fresh slate.")
        last_processed_ids = {}

def save_last_ids():
    """Nayi process ki hui IDs ko file mein save karein."""
    global message_counter
    try: # File operation ke liye Error Handling
        with open(LAST_IDS_FILE, 'w') as f:
            json.dump(last_processed_ids, f, indent=4)
        message_counter = 0 # Counter reset karein
        logger.info(f"💾 Saved {len(last_processed_ids)} last processed IDs to {LAST_IDS_FILE}")
    except Exception as e:
        logger.error(f"❌ Failed to save last processed IDs: {e}")

# App start hote hi purani IDs load karein
load_last_ids()

# --- Helper Functions ---
def clean_url(url):
    """Clean and normalize URL"""
    # (Yeh function aapke utils/helpers.py mein hona chahiye)
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
    """Check if a given URL is from Amazon."""
    amazon_patterns = [r'https?://(?:www\.)?amazon\.', r'https?://amzn\.to', r'https?://a\.co']
    for pattern in amazon_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False

# --- Core Logic Function ---
async def process_message_logic(client, message, is_from_poller=False):
    global message_counter
    try:
        channel_id = message.chat.id
        channel_title = getattr(message.chat, 'title', 'Unknown')

        # Check karein ke message pehle se process to nahi ho chuka
        if message.id <= last_processed_ids.get(channel_id, 0):
            return # Agar purana message hai to ignore karein

        text_content = message.caption or message.text or ""
        if not text_content: return
        all_urls = re.findall(r'https?://[^\s]+', text_content, re.IGNORECASE)
        if not all_urls: return
        
        task_successful = False
        for url in all_urls:
            if duplicate_detector.is_duplicate(clean_url(url)):
                continue

            if is_amazon_url(url):
                message_data = extract_message_data(message)
                payload = {"url": url, "original_text": message_data["text"], "images": message_data["images"], "channel_info": message_data["channel_info"]}
                response = await token_bot_api.process_amazon_link(payload)
                if response and response.get('status') == 'success':
                    task_successful = True
            else:
                try:
                    await client.forward_messages(chat_id=Config.EARNKARO_BOT_USERNAME, from_chat_id=channel_id, message_ids=message.id)
                    task_successful = True
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"❌ Failed to forward message {message.id} to EarnKaro: {e}")
        
        # ID sirf tab update karein jab task kamyab ho
        if task_successful:
            last_processed_ids[channel_id] = message.id
            if not is_from_poller:
                message_counter += 1

    except Exception as e:
        logger.error(f"❌ Error in process_message_logic for message {message.id}: {e}", exc_info=True)

# --- Real-time Message Handler ---
channel_filters = filters.chat(list(map(int, Config.CHANNELS)))
@Client.on_message(channel_filters)
async def monitor_channel_messages(client, message):
    """Real-time handler, ab batch saving ke saath."""
    await process_message_logic(client, message)
    if message_counter >= SAVE_BATCH_SIZE:
        save_last_ids()

# --- Active Polling Logic ---
async def periodic_checker(client: Client):
    """Har 4 minute mein sirf naye messages check karta hai."""
    logger.info("✅ Active Polling service started.")
    while True:
        try:
            logger.info("... Polling all channels for new messages ...")
            channel_ids = list(map(int, Config.CHANNELS))
            new_messages_found_in_cycle = 0

            for channel_id in channel_ids:
                try:
                    last_id = last_processed_ids.get(channel_id, 0)
                    messages_to_process = []
                    async for message in client.get_chat_history(chat_id=channel_id, limit=Config.POLLING_MESSAGE_LIMIT):
                        if message.id > last_id:
                            messages_to_process.append(message)
                        else:
                            break 
                    
                    if messages_to_process:
                        for message in reversed(messages_to_process):
                            await process_message_logic(client, message, is_from_poller=True)
                        new_messages_found_in_cycle += len(messages_to_process)

                except Exception as e:
                    logger.warning(f"⚠️ Could not poll channel {channel_id}. Reason: {e}. Skipping.")
                    continue
            
            if new_messages_found_in_cycle > 0:
                save_last_ids()

            logger.info(f"... Polling cycle complete. Found {new_messages_found_in_cycle} new messages. Waiting for 4 minutes ...")
            await asyncio.sleep(240)
        except Exception as e:
            logger.error(f"❌ Critical error in periodic_checker: {e}", exc_info=True)
            await asyncio.sleep(60)
