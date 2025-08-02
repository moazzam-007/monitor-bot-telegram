from pyrogram import Client
from config import Config
from flask import Flask
import threading
import os

# Flask app for Render hosting
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Amazon Monitor Bot is running! 🤖", 200

def run_flask_app():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Pyrogram client
client = Client(
    ":memory:",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.STRING_SESSION,
    phone_number=Config.PHONE_NUMBER,
    plugins=dict(root="plugins"),
    workers=5,
    in_memory=True
)

if __name__ == "__main__":
    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
    
    # Start Pyrogram client
    print("🚀 Amazon Monitor Bot Starting...")
    client.run()
