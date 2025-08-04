import os
import logging
from pyrogram import Client
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_pyrogram_client():
    """Pyrogram client ko create karne ke liye helper function"""
    try:
        # Client ko memory-based session ke saath initialize karein
        # Pyrogram ka session string Env var se aayega
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
        return client
    except Exception as e:
        logger.error(f"❌ Pyrogram client ko initialize karne mein error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Amazon Monitor Bot Starting...")
    
    # Log configuration
    logger.info(f"🔧 Configured channels: {Config.CHANNELS}")
    logger.info(f"🔧 API URL: {Config.TOKEN_BOT_API_URL}")
    
    # Client banayein
    pyrogram_client = create_pyrogram_client()
    
    if pyrogram_client:
        # Client run karein
        pyrogram_client.run()
    else:
        logger.error("❌ Client initialization failed. Exiting.")
