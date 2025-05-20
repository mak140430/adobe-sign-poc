import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("adobe-sign-poc")

class TokenStore:
    """
    Store for Adobe Sign OAuth tokens.
    Persists tokens to a JSON file and provides an in-memory cache.
    """
    _instance = None
    TOKENS_FILE = "adobe_tokens.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenStore, cls).__new__(cls)
            cls._instance._load_tokens()
        return cls._instance
    
    def _load_tokens(self):
        """Load tokens from file if it exists"""
        self.tokens = {
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
            "api_access_point": None,
            "web_access_point": None
        }
        
        if os.path.exists(self.TOKENS_FILE):
            try:
                with open(self.TOKENS_FILE, 'r') as f:
                    self.tokens = json.load(f)
                    logger.info(f"Loaded tokens from {self.TOKENS_FILE}")
            except Exception as e:
                logger.error(f"Error loading tokens: {str(e)}")
    
    def save_tokens(self, token_data):
        """
        Save tokens from the Adobe Sign token response
        
        Args:
            token_data: The response from Adobe Sign containing tokens
        """
        # Calculate expiration time
        expires_at = None
        if 'expires_in' in token_data:
            expires_at = (datetime.now() + timedelta(seconds=token_data['expires_in'])).timestamp()
        
        self.tokens = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": expires_at,
            "api_access_point": token_data.get("api_access_point"),
            "web_access_point": token_data.get("web_access_point")
        }
        
        # Save to file
        try:
            with open(self.TOKENS_FILE, 'w') as f:
                json.dump(self.tokens, f)
                logger.info(f"Saved tokens to {self.TOKENS_FILE}")
        except Exception as e:
            logger.error(f"Error saving tokens: {str(e)}")
    
    def get_access_token(self):
        """Get the current access token"""
        return self.tokens.get("access_token")
    
    def get_refresh_token(self):
        """Get the current refresh token"""
        return self.tokens.get("refresh_token")
    
    def get_api_access_point(self):
        """Get the API access point"""
        return self.tokens.get("api_access_point")
    
    def get_web_access_point(self):
        """Get the web access point"""
        return self.tokens.get("web_access_point")
    
    def is_token_valid(self):
        """Check if the access token is still valid"""
        expires_at = self.tokens.get("expires_at")
        if not expires_at:
            return False
            
        # Add a 30-second buffer to avoid edge cases
        return datetime.now().timestamp() < (expires_at - 30)
    
    def clear_tokens(self):
        """Clear all stored tokens"""
        self.tokens = {
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
            "api_access_point": None,
            "web_access_point": None
        }
        
        if os.path.exists(self.TOKENS_FILE):
            try:
                os.remove(self.TOKENS_FILE)
                logger.info(f"Removed token file {self.TOKENS_FILE}")
            except Exception as e:
                logger.error(f"Error removing token file: {str(e)}")

# Create a singleton instance
token_store = TokenStore() 