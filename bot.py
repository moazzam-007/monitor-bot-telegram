import os
from pyrogram import Client
from config import Config

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
        print(f"❌ Pyrogram client ko initialize karne mein error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Amazon Monitor Bot Starting...")
    
    # Client banayein
    pyrogram_client = create_pyrogram_client()
    
    if pyrogram_client:
        # Client run karein
        pyrogram_client.run()
    else:
        print("❌ Client initialization failed. Exiting.")
