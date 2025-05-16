import requests
import json
import os
from fastapi import HTTPException
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

class AdobeSignTransientService:
    def upload_pdf_to_transient(self, file_path: str, file_name: str = None):
        if not auth_service.access_token:
            raise HTTPException(status_code=401, detail="Not authenticated with Adobe Sign.")

        if not file_name:
            file_name = os.path.basename(file_path)

        url = f"{auth_service.base_uri}api/rest/v6/transientDocuments"
        headers = {
            "Authorization": f"Bearer {auth_service.access_token}"
        }

        with open(file_path, "rb") as f:
            files = {
                "File": (file_name, f, "application/pdf")
            }
            response = requests.post(url, headers=headers, files=files)
            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to upload PDF to Adobe Sign transientDocuments: {response.text}"
                )
            return response.json()

adobe_sign_transient_service = AdobeSignTransientService() 