import requests
import json
import os
from fastapi import HTTPException, UploadFile
from app.services.adobe_sign_auth import auth_service
from app.services.token_store import token_store
import logging
import http.client as http_client

if os.getenv("DEBUG_HTTP", "false").lower() == "true":
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

logger = logging.getLogger("adobe-sign-poc")

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

class AdobeSignTransientService:
    async def upload_file_to_transient(self, file: UploadFile):
        """
        Upload a file directly from a request to Adobe Sign's transient documents
        """
        # Make sure we have a valid token, refresh if needed
        await auth_service.refresh_token_if_needed()
        access_token = auth_service.access_token
        if not access_token:
            raise HTTPException(status_code=401, detail="Not authenticated with Adobe Sign.")

        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no filename")
            
        if not file.content_type or "pdf" not in file.content_type.lower():
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Check file size by reading a small portion first
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        # Create a temporary file to store the chunks
        temp_file_path = f"/tmp/{file.filename}"
        
        try:
            # Ensure file is at the beginning
            await file.seek(0)
            
            with open(temp_file_path, "wb") as temp_file:
                # Read and write the file in chunks to avoid memory issues
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413, 
                            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
                        )
                    
                    temp_file.write(chunk)
            
            # Get base URI from stored settings
            base_uri = token_store.get_api_access_point() or auth_service.base_uri
            
            # Now send the file to Adobe Sign
            url = f"{base_uri}api/rest/v6/transientDocuments"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            with open(temp_file_path, "rb") as f:
                files = {
                    "File": (file.filename, f, "application/pdf")
                }
                response = requests.post(url, headers=headers, files=files)
            
            if response.status_code not in (200, 201):
                # If unauthorized, try to refresh token and retry
                if response.status_code == 401:
                    logger.warning("Unauthorized request, attempting to refresh token")
                    refresh_result = await auth_service.refresh_token_if_needed()
                    if refresh_result:
                        # Reset the file position to the beginning
                        await file.seek(0)
                        
                        # Retry with new token
                        headers["Authorization"] = f"Bearer {auth_service.access_token}"
                        
                        with open(temp_file_path, "rb") as f:
                            files = {
                                "File": (file.filename, f, "application/pdf")
                            }
                            response = requests.post(url, headers=headers, files=files)
                        
                        # If still failing after refresh, raise error
                        if response.status_code not in (200, 201):
                            raise HTTPException(
                                status_code=response.status_code,
                                detail=f"Failed to upload PDF to Adobe Sign transientDocuments: {response.text}"
                            )
                        
                        return response.json()
                
                # If we got here, the request failed
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to upload PDF to Adobe Sign transientDocuments: {response.text}"
                )
                
            return response.json()
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

adobe_sign_transient_service = AdobeSignTransientService() 