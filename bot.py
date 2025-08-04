import os
import logging
import threading
import time
import asyncio
from flask import Flask, jsonify
from pyrogram import Client
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)

# Global variable to store monitor bot status
monitor_bot_status = {
    "running": False,
    "last_check": None,
    "telegram_connected": False,
    "channels_monitored": 0,
    "links_processed": 0
}

def create_pyrogram_client():
    """Pyrogram client ko create karne ke liye helper function"""
    try:
        logger.info("🚀 Creating Pyrogram client...")
        logger.info(f"🔧 API_ID: {Config.API_ID}")
        logger.info(f"🔧 API_HASH: {'*' * len(Config.API_HASH)}")
        logger.info(f"🔧 PHONE_NUMBER: {Config.PHONE_NUMBER}")
        logger.info(f"🔧 CHANNELS: {Config.CHANNELS}")
        logger.info(f"🔧 API_URL: {Config.TOKEN_BOT_API_URL}")
        
        client = Client(
            name=":memory:",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION,
            phone_number=Config.PHONE_NUMBER,
            plugins=dict(root="plugins"),
            workers=5,
            in_memory=True
        )
        logger.info("✅ Pyrogram client created successfully")
        return client
    except Exception as e:
        logger.error(f"❌ Error creating Pyrogram client: {e}")
        return None

async def run_monitor_bot_async():
    """Run the monitor bot asynchronously"""
    try:
        logger.info("🚀 Starting monitor bot asynchronously...")
        
        # Client banayein
        pyrogram_client = create_pyrogram_client()
        
        if pyrogram_client:
            monitor_bot_status["running"] = True
            monitor_bot_status["telegram_connected"] = True
            monitor_bot_status["channels_monitored"] = len(Config.CHANNELS)
            
            logger.info("✅ Starting monitor bot client...")
            await pyrogram_client.start()
        else:
            logger.error("❌ Client initialization failed.")
            monitor_bot_status["running"] = False
            
    except Exception as e:
        logger.error(f"❌ Monitor bot error: {e}")
        monitor_bot_status["running"] = False

def run_monitor_bot():
    """Run the monitor bot in background with event loop"""
    try:
        logger.info("🚀 Starting monitor bot in background...")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function
        loop.run_until_complete(run_monitor_bot_async())
        
    except Exception as e:
        logger.error(f"❌ Monitor bot thread error: {e}")
        monitor_bot_status["running"] = False

# Flask routes
@app.route('/')
def home():
    """Home route for health check"""
    monitor_bot_status["last_check"] = time.time()
    return jsonify({
        "service": "Amazon Monitor Bot",
        "status": "running" if monitor_bot_status["running"] else "stopped",
        "telegram_connected": monitor_bot_status["telegram_connected"],
        "channels_monitored": monitor_bot_status["channels_monitored"],
        "links_processed": monitor_bot_status["links_processed"],
        "last_check": monitor_bot_status["last_check"]
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    monitor_bot_status["last_check"] = time.time()
    return jsonify({
        "status": "healthy" if monitor_bot_status["running"] else "unhealthy",
        "telegram_connected": monitor_bot_status["telegram_connected"],
        "channels": len(Config.CHANNELS),
        "uptime": monitor_bot_status["last_check"]
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    monitor_bot_status["last_check"] = time.time()
    return jsonify({
        "bot_status": "running" if monitor_bot_status["running"] else "stopped",
        "telegram_connected": monitor_bot_status["telegram_connected"],
        "channels_monitored": monitor_bot_status["channels_monitored"],
        "links_processed": monitor_bot_status["links_processed"],
        "api_url": Config.TOKEN_BOT_API_URL,
        "last_check": monitor_bot_status["last_check"]
    })

if __name__ == "__main__":
    try:
        print("🚀 Amazon Monitor Bot Starting...")
        logger.info("🚀 Amazon Monitor Bot Starting...")
        
        # Log all environment variables (without sensitive data)
        logger.info("🔧 Environment Variables:")
        logger.info(f"  - API_ID: {os.environ.get('API_ID', 'NOT SET')}")
        logger.info(f"  - API_HASH: {'SET' if os.environ.get('API_HASH') else 'NOT SET'}")
        logger.info(f"  - PHONE_NUMBER: {os.environ.get('PHONE_NUMBER', 'NOT SET')}")
        logger.info(f"  - STRING_SESSION: {'SET' if os.environ.get('STRING_SESSION') else 'NOT SET'}")
        logger.info(f"  - CHANNELS: {os.environ.get('CHANNELS', 'NOT SET')}")
        logger.info(f"  - TOKEN_BOT_API_URL: {os.environ.get('TOKEN_BOT_API_URL', 'NOT SET')}")
        
        # Start monitor bot in background thread
        monitor_thread = threading.Thread(target=run_monitor_bot, daemon=True)
        monitor_thread.start()
        logger.info("✅ Monitor bot started in background thread")
        
        # Give the monitor bot time to start
        time.sleep(5)
        
        # Get the port from environment variable
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🌐 Starting Flask app on port {port}")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
