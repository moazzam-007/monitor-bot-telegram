import os
import logging
import threading
import time
import asyncio
from flask import Flask, jsonify
from pyrogram import Client
from config import Config
from plugins.amazon_monitor import periodic_checker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to store monitor bot status
monitor_bot_status = {
    "running": False, "last_check": None, "telegram_connected": False,
    "channels_monitored": 0, "links_processed": 0
}

def create_pyrogram_client():
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
    """Run the monitor bot asynchronously"""
    try:
        logger.info("🚀 Starting monitor bot asynchronously...")
        pyrogram_client = create_pyrogram_client()
        
        if pyrogram_client:
            monitor_bot_status["running"] = True
            monitor_bot_status["telegram_connected"] = True
            monitor_bot_status["channels_monitored"] = len(Config.CHANNELS)
            
            # === NAYI LOGIC YAHAN ADD KI GAYI HAI ===
            # Client start karne se pehle, sabhi channels ko join/access karein
            logger.info("Ensuring access to all configured channels (warming up cache)...")
            channel_ids = list(map(int, Config.CHANNELS))
            for channel_id in channel_ids:
                try:
                    # Yeh command channel ki details cache mein save kar dega
                    await pyrogram_client.join_chat(channel_id)
                    logger.info(f"✅ Access confirmed for channel: {channel_id}")
                    await asyncio.sleep(2) # Rate limit se bachne ke liye thora delay
                except Exception as e:
                    logger.error(f"❌ Could not join/access channel {channel_id}: {e}")
            logger.info("✅ All channels have been warmed up.")
            # ==========================================

            logger.info("✅ Starting monitor bot client...")
            await pyrogram_client.start()

            logger.info("🚀 Starting active poller for public channels in background...")
            asyncio.create_task(periodic_checker(pyrogram_client))

            await asyncio.Future()
        else:
            logger.error("❌ Client initialization failed.")
            monitor_bot_status["running"] = False
            
    except Exception as e:
        logger.error(f"❌ Monitor bot async error: {e}", exc_info=True)
        monitor_bot_status["running"] = False

# (Baki ka poora code bilkul waisa hi rahega)
def run_monitor_bot_in_thread():
    try:
        logger.info("🚀 Preparing background thread for monitor bot...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_monitor_bot_async())
    except Exception as e:
        logger.error(f"❌ Monitor bot thread error: {e}", exc_info=True)
        monitor_bot_status["running"] = False

logger.info("🚀 Initializing application...")
monitor_thread = threading.Thread(target=run_monitor_bot_in_thread, daemon=True)
monitor_thread.start()
logger.info("✅ Monitor bot background thread has been started.")

@app.route('/')
def home():
    return jsonify({
        "service": "Amazon Monitor Bot",
        "status": "running" if monitor_bot_status["running"] else "stopped",
        "telegram_connected": monitor_bot_status["telegram_connected"]
    })

@app.route('/status')
def status():
    return jsonify(monitor_bot_status)

if __name__ == "__main__":
    logger.info("Running in local development mode. Do not use for production.")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
