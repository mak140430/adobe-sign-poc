import httpx
from fastapi import HTTPException
from urllib.parse import urlencode
import os
import logging

from app.config import settings
from app.services.token_store import token_store

logger = logging.getLogger("adobe-sign-poc")

class AdobeSignAuth:
    """
    Handles authentication with Adobe Sign API.
    
    This service is responsible for:
    1. Generating the authorization URL for OAuth flow
    2. Exchanging authorization code for access token
    3. Storing the access token for subsequent API calls
    4. Refreshing tokens when needed
    """

    def  __init__(self):
        self.base_uri = settings.ADOBE_SIGN_BASE_URI
        self.web_uri = settings.ADOBE_SIGN_WEB_URI
        self.client_id = settings.ADOBE_SIGN_CLIENT_ID
        self.client_secret = settings.ADOBE_SIGN_CLIENT_SECRET
        self.redirect_uri = settings.ADOBE_SIGN_REDIRECT_URI
        # Try to load from token store, fall back to env var if needed
        self.access_token = token_store.get_access_token() or os.getenv("ADOBE_SIGN_ACCESS_TOKEN")
        self.refresh_token = token_store.get_refresh_token()

    def get_authorization_url(self):
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": settings.ADOBE_SIGN_SCOPES
        }
        return f"{self.web_uri}public/oauth/v2?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_uri}oauth/v2/token", data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get access token {response.text}"
                )
            token_data = response.json()
            
            # Store tokens in both the auth service and token store
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            
            # Save to the token store for persistence
            token_store.save_tokens(token_data)
            
            return token_data
    
    async def refresh_token_if_needed(self):
        """Refresh the access token if it's expired"""
        # If token is still valid, just return it
        if token_store.is_token_valid():
            return {"access_token": token_store.get_access_token()}
            
        # If we have a refresh token, try to refresh
        refresh_token = token_store.get_refresh_token()
        if not refresh_token:
            logger.warning("No refresh token available for refreshing access token")
            return None
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_uri}oauth/v2/token", data=data)
                
                if response.status_code != 200:
                    logger.error(f"Failed to refresh token: {response.status_code} {response.text}")
                    return None
                    
                token_data = response.json()
                
                # Update in both auth service and token store
                self.access_token = token_data["access_token"]
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                
                # Save to the token store
                token_store.save_tokens(token_data)
                
                logger.info("Successfully refreshed access token")
                return token_data
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None

auth_service = AdobeSignAuth()
            
            