import httpx
from fastapi import HTTPException
from urllib.parse import urlencode

from app.config import settings

class AdobeSignAuth:
    """
    Handles authentication with Adobe Sign API.
    
    This service is responsible for:
    1. Generating the authorization URL for OAuth flow
    2. Exchanging authorization code for access token
    3. Storing the access token for subsequent API calls
    """

    def  __init__(self):
        self.base_uri = settings.ADOBE_SIGN_BASE_URI
        self.web_uri = settings.ADOBE_SIGN_WEB_URI
        self.client_id = settings.ADOBE_SIGN_CLIENT_ID
        self.client_secret = settings.ADOBE_SIGN_CLIENT_SECRET
        self.redirect_uri = settings.ADOBE_SIGN_REDIRECT_URI
        self.access_token = None
        self.refresh_token = None

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
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            
            return token_data

auth_service = AdobeSignAuth()
            
            