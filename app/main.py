from fastapi import FastAPI, HTTPException, Body, Query, Depends, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
import os
from typing import Optional

from app.services.adobe_sign_auth import auth_service
from app.services.adobe_sign_library import adobe_sign_transient_service, MAX_FILE_SIZE
from app.services.adobe_sign_agreements import adobe_sign_agreement_service

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
    recipient_email: str
    agreement_name: str = "Agreement"

@app.get("/")
async def root():
    return {"message": "Adobe Sign API POC is running"}

# Authentication routes
@app.get("/auth/url")
async def get_auth_url():
    """Get the Adobe Sign authorization URL"""
    auth_url = auth_service.get_authorization_url()
    return {"auth_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle the callback from Adobe Sign with the authorization code"""
    try:
        token_data = await auth_service.exchange_code_for_token(code)
        return token_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exchanging code: {str(e)}")

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
    """Create an agreement and send it for signing"""
    try:
        result = adobe_sign_agreement_service.create_agreement(
            request.transient_document_id,
            request.recipient_email,
            agreement_name=request.agreement_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agreement creation failed: {str(e)}")

@app.get("/agreements/{agreement_id}")
async def get_agreement(agreement_id: str):
    """Get agreement details by ID"""
    try:
        # You'll need to add this method to your agreement_service
        result = adobe_sign_agreement_service.get_agreement(agreement_id)
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