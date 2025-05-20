from fastapi import FastAPI, HTTPException, Body, Query, Depends, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, validator, Field
import os
import logging
from typing import Optional, List
import re
from datetime import datetime

from app.services.adobe_sign_auth import auth_service
from app.services.adobe_sign_library import adobe_sign_transient_service, MAX_FILE_SIZE
from app.services.adobe_sign_agreements import adobe_sign_agreement_service
from app.services.token_store import token_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("adobe_sign.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("adobe-sign-poc")

# Create the FastAPI application with file size limits
app = FastAPI(
    title="Adobe Sign POC",
    # Limit request body size
    max_request_size=MAX_FILE_SIZE + 1024 * 1024,  # Add a buffer for non-file parts of request
)

class UploadResponse(BaseModel):
    transient_document_id: str

class CreateAgreementRequest(BaseModel):
    transient_document_id: str
    recipient_emails: List[str]
    agreement_name: str = "Agreement"
    
    @validator('recipient_emails')
    def validate_emails(cls, emails):
        # Validate email format
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        invalid_emails = []
        
        for email in emails:
            if not re.match(email_regex, email):
                invalid_emails.append(email)
        
        if invalid_emails:
            raise ValueError(f"Invalid email format for: {', '.join(invalid_emails)}")
        
        # Validate array length - maximum 2 recipients
        if len(emails) > 2:
            raise ValueError(f"Maximum 2 recipients allowed, but {len(emails)} were provided")
        
        # Ensure at least 1 recipient
        if len(emails) == 0:
            raise ValueError("At least one recipient email is required")
            
        return emails

@app.get("/")
async def root():
    return {"message": "Adobe Sign API POC is running"}

# Authentication routes
@app.get("/auth/url")
async def get_auth_url():
    """Get the Adobe Sign authorization URL"""
    logger.info("Generating Adobe Sign authorization URL")
    auth_url = auth_service.get_authorization_url()
    logger.info(f"Auth URL generated: {auth_url}")
    return {"auth_url": auth_url}

@app.get("/redirect")
async def auth_callback(code: str):
    """Handle the callback from Adobe Sign with the authorization code"""
    logger.info("===============================================")
    logger.info("AUTH CALLBACK TRIGGERED")
    logger.info(f"Received authorization code: {code[:5]}..." if code else "No code received")
    
    try:
        logger.info("Attempting to exchange code for token")
        token_data = await auth_service.exchange_code_for_token(code)
        logger.info("Token exchange successful!")
        logger.info(f"Access token received (first 10 chars): {token_data.get('access_token', '')[:10]}..." if token_data.get('access_token') else "No access token in response")
        logger.info(f"Token expires in: {token_data.get('expires_in', 'N/A')} seconds")
        
        # Check token storage status
        if token_store.is_token_valid():
            logger.info("Tokens successfully stored and validated")
        
        logger.info("Authentication flow completed successfully")
        logger.info("===============================================")
        
        # Return a more user-friendly response
        return {
            "status": "success",
            "message": "Authentication successful. Tokens have been stored.",
            "expires_in": token_data.get("expires_in"),
            "token_type": token_data.get("token_type")
        }
    except Exception as e:
        logger.error(f"Error exchanging code: {str(e)}", exc_info=True)
        logger.info("===============================================")
        raise HTTPException(status_code=400, detail=f"Error exchanging code: {str(e)}")

@app.get("/auth/status")
async def auth_status():
    """Check the current authentication status"""
    if token_store.is_token_valid():
        expires_at = token_store.tokens.get("expires_at")
        expires_in = int(expires_at - datetime.now().timestamp()) if expires_at else 0
        
        return {
            "authenticated": True,
            "expires_in_seconds": expires_in,
            "api_access_point": token_store.get_api_access_point()
        }
    else:
        # Check if we have a refresh token
        refresh_token = token_store.get_refresh_token()
        if refresh_token:
            return {
                "authenticated": False,
                "message": "Token expired but can be refreshed"
            }
        else:
            return {
                "authenticated": False,
                "message": "Not authenticated"
            }

# Document upload route
@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document_file(file: UploadFile = File(...)):
    """Upload a PDF file directly to create a transient document ID"""
    try:
        result = await adobe_sign_transient_service.upload_file_to_transient(file)
        return {"transient_document_id": result["transientDocumentId"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

# Agreement routes
@app.post("/agreements/create")
async def create_agreement(request: CreateAgreementRequest):
    """Create an agreement and send it for signing to multiple recipients"""
    try:
        result = await adobe_sign_agreement_service.create_agreement(
            request.transient_document_id,
            request.recipient_emails,
            agreement_name=request.agreement_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agreement creation failed: {str(e)}")

@app.get("/agreements/{agreement_id}")
async def get_agreement(agreement_id: str):
    """Get agreement details by ID"""
    try:
        result = await adobe_sign_agreement_service.get_agreement(agreement_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch agreement: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8081,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )