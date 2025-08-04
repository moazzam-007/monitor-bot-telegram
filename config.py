import os
import logging

logger = logging.getLogger(__name__)

class Config:
    # Telegram Configuration
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    PHONE_NUMBER = os.environ.get("PHONE_NUMBER")
    STRING_SESSION = os.environ.get("STRING_SESSION")
    
    # Monitoring Configuration
    CHANNELS_STR = os.environ.get("CHANNELS", "")
    CHANNELS = [x.strip() for x in CHANNELS_STR.split(',') if x.strip()]
    
    # Token Bot API Configuration
    TOKEN_BOT_API_URL = os.environ.get("TOKEN_BOT_API_URL")
    API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "30"))
    
    # Logging Configuration
    LOG_GROUP_ID = os.environ.get("LOG_GROUP_ID")
    
    # Debug Mode
    DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"

# Validate required environment variables
required_vars = [
    "API_ID",
    "API_HASH",
    "PHONE_NUMBER",
    "STRING_SESSION",
    "CHANNELS",
    "TOKEN_BOT_API_URL"
]

missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

logger.info("✅ All required environment variables are set")
