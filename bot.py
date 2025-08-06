# bot.py (FINAL - STARTING POINT LOGIC)
import os
import logging
import threading
import time
import asyncio
from flask import Flask, jsonify
from pyrogram import Client
from config import Config
# Naya import
from plugins.amazon_monitor import periodic_checker, last_message_ids

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

def create_pyrogram_client():
    """Pyrogram client ko create karne ke liye helper function"""
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
    """Run the monitor bot asynchronously with the correct startup order."""
    try:
        logger.info("🚀 Starting monitor bot asynchronously...")
        pyrogram_client = create_pyrogram_client()
        
        if pyrogram_client:
            # Step 1: PEHLE client ko start karein
            logger.info("✅ Connecting to Telegram...")
            await pyrogram_client.start()
            logger.info("✅ Client started successfully.")
            
            # Step 2: AB, har channel ke liye "starting point" set karein
            logger.info("Setting starting point for all channels...")
            channel_ids = list(map(int, Config.CHANNELS))
            for channel_id in channel_ids:
                try:
                    # Channel ka aakhri message haasil karein
                    async for last_message in pyrogram_client.get_chat_history(channel_id, limit=1):
                        last_message_ids[channel_id] = last_message.id
                        logger.info(f"✅ Starting point for channel {channel_id} set to message ID: {last_message.id}")
                    await asyncio.sleep(1) # Rate limit se bachne ke liye thora delay
                except Exception as e:
                    logger.error(f"❌ Could not get last message for channel {channel_id}: {e}. It will be skipped.")
            logger.info("✅ All starting points have been set.")
            
            # Step 3: AAKHIR mein poller start karein
            logger.info("🚀 Starting active poller for public channels in background...")
            asyncio.create_task(periodic_checker(pyrogram_client))

            await asyncio.Future() # Hamesha chalta rehne ke liye
            
    except Exception as e:
        logger.error(f"❌ Monitor bot async error: {e}", exc_info=True)

def run_monitor_bot_in_thread():
    """Runs the async bot logic in a separate thread."""
    try:
        logger.info("🚀 Preparing background thread for monitor bot...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_monitor_bot_async())
    except Exception as e:
        logger.error(f"❌ Monitor bot thread error: {e}", exc_info=True)

# --- Startup Logic and Flask Routes ---
logger.info("🚀 Initializing application...")
monitor_thread = threading.Thread(target=run_monitor_bot_in_thread, daemon=True)
monitor_thread.start()
logger.info("✅ Monitor bot background thread has been started.")

@app.route('/')
def home():
    return jsonify({ "service": "Amazon Monitor Bot", "status": "running" })

@app.route('/status')
def status():
    return jsonify({ "last_message_ids_count": len(last_message_ids) })

if __name__ == "__main__":
    logger.info("Running in local development mode.")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
