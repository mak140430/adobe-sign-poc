import requests
import json
import os
from fastapi import HTTPException, UploadFile
from app.services.adobe_sign_auth import auth_service
import logging
import http.client as http_client

if os.getenv("DEBUG_HTTP", "false").lower() == "true":
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

class AdobeSignTransientService:
    async def upload_file_to_transient(self, file: UploadFile):
        """
        Upload a file directly from a request to Adobe Sign's transient documents
        """
        if not auth_service.access_token:
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
        with open(temp_file_path, "wb") as temp_file:
            # Read and write the file in chunks to avoid memory issues
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    # Close and delete the temp file
                    temp_file.close()
                    os.remove(temp_file_path)
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
                    )
                
                temp_file.write(chunk)
        
        # Now send the file to Adobe Sign
        url = f"{auth_service.base_uri}api/rest/v6/transientDocuments"
        headers = {
            "Authorization": f"Bearer {auth_service.access_token}"
        }
        
        with open(temp_file_path, "rb") as f:
            files = {
                "File": (file.filename, f, "application/pdf")
            }
            response = requests.post(url, headers=headers, files=files)
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to upload PDF to Adobe Sign transientDocuments: {response.text}"
            )
        return response.json()

adobe_sign_transient_service = AdobeSignTransientService() 