# file: config.py (FINAL-FINAL-CORRECTED VERSION)
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram User Account Configuration
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER")
    STRING_SESSION = os.getenv("STRING_SESSION")
    
    # Monitoring Configuration
    CHANNELS_STR = os.getenv("CHANNELS", "")
    CHANNELS = [x.strip() for x in CHANNELS_STR.split(',') if x.strip()]
    
    # API URL for your Logic Bot
    TOKEN_BOT_API_URL = os.getenv("TOKEN_BOT_API_URL")
    EXTRAPE_BOT_USERNAME = os.getenv('EXTRAPE_BOT_USERNAME')
    
    
    # EarnKaro Bot Username
    EARNKARO_BOT_USERNAME = os.getenv('EARNKARO_BOT_USERNAME')

    # Polling Configuration
    POLLING_MESSAGE_LIMIT = int(os.getenv('POLLING_MESSAGE_LIMIT', '20'))
    
    # === YEH LINE MISSING THI ===
    # API call ke liye timeout (seconds mein)
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))


# Validation
required_vars = [
    "API_ID",
    "API_HASH",
    "PHONE_NUMBER",
    "STRING_SESSION",
    "CHANNELS",
    "TOKEN_BOT_API_URL",
    "EARNKARO_BOT_USERNAME"
]

if any(not os.getenv(var) for var in required_vars):
    missing = [var for var in required_vars if not os.getenv(var)]
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

Config.API_ID = int(Config.API_ID)
