import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Adobe Sign API credentials
    ADOBE_SIGN_CLIENT_ID = os.getenv("ADOBE_SIGN_CLIENT_ID")
    ADOBE_SIGN_CLIENT_SECRET = os.getenv("ADOBE_SIGN_CLIENT_SECRET")
    ADOBE_SIGN_REDIRECT_URI = os.getenv("ADOBE_SIGN_REDIRECT_URI")
    ADOBE_SIGN_SCOPES = os.getenv("ADOBE_SIGN_SCOPES")
    
    # Adobe Sign API endpoints
    ADOBE_SIGN_BASE_URI = os.getenv("ADOBE_SIGN_BASE_URI", "https://api.na4.adobesign.com/")
    ADOBE_SIGN_WEB_URI = os.getenv("ADOBE_SIGN_WEB_URI", "https://secure.na4.adobesign.com/")

settings = Settings()