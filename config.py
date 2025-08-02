import os

class Config:
    # Telegram Configuration
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    PHONE_NUMBER = os.environ.get("PHONE_NUMBER")
    STRING_SESSION = os.environ.get("STRING_SESSION")
    
    # Monitoring Configuration
    CHANNELS = os.environ.get("CHANNELS", "").split(",")  # Comma separated channel IDs
    
    # Token Bot API Configuration
    TOKEN_BOT_API_URL = os.environ.get("TOKEN_BOT_API_URL")  # Token bot API endpoint
    API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "30"))  # API timeout in seconds
    
    # Logging Configuration
    LOG_GROUP_ID = os.environ.get("LOG_GROUP_ID")  # Optional logging group
    
    # Debug Mode
    DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"
