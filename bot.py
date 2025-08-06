# file: bot.py
import os
import logging
import threading
import time
import asyncio
from flask import Flask, jsonify
from pyrogram import Client
from config import Config
from plugins.amazon_monitor import periodic_checker, last_message_ids # Important import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

def create_pyrogram_client():
    """Creates the Pyrogram client instance."""
    try:
        logger.info("🚀 Creating Pyrogram client...")
        client = Client(
            name=":memory:", api_id=Config.API_ID, api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION, phone_number=Config.PHONE_NUMBER,
            plugins=dict(root="plugins"), workers=5, in_memory=True
        )
        logger.info("✅ Pyrogram client created successfully")
        return client
    except Exception as e:
        logger.error(f"❌ Error creating Pyrogram client: {e}", exc_info=True)
        return None

async def run_monitor_bot_async():
    """Runs the monitor bot with the 'Starting Point' logic."""
    try:
        pyrogram_client = create_pyrogram_client()
        if pyrogram_client:
            logger.info("✅ Connecting to Telegram...")
            await pyrogram_client.start()
            logger.info("✅ Client started successfully.")
            
            logger.info("Setting starting point for all channels...")
            channel_ids = list(map(int, Config.CHANNELS))
            for channel_id in channel_ids:
                try:
                    async for last_message in pyrogram_client.get_chat_history(channel_id, limit=1):
                        last_message_ids[channel_id] = last_message.id
                        logger.info(f"✅ Starting point for {channel_id} set to message ID: {last_message.id}")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Could not get last message for {channel_id}: {e}. It will be skipped.")
            logger.info("✅ All starting points have been set.")
            
            logger.info("🚀 Starting active poller in background...")
            asyncio.create_task(periodic_checker(pyrogram_client))

            await asyncio.Future()
            
    except Exception as e:
        logger.error(f"❌ Monitor bot async error: {e}", exc_info=True)

def run_monitor_bot_in_thread():
    """Runs the async bot logic in a separate thread."""
    logger.info("🚀 Preparing background thread for monitor bot...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_monitor_bot_async())

# --- Startup Logic and Flask Routes ---
logger.info("🚀 Initializing application...")
monitor_thread = threading.Thread(target=run_monitor_bot_in_thread, daemon=True)
monitor_thread.start()
logger.info("✅ Monitor bot background thread has been started.")

@app.route('/')
def home():
    return jsonify({ "service": "Amazon Monitor Bot", "status": "running" })
