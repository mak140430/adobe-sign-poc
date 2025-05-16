import requests
from fastapi import HTTPException
from app.services.adobe_sign_auth import auth_service

class AdobeSignAgreementService:
    def create_agreement(self, transient_document_id: str, recipient_email: str, agreement_name: str = "Test Agreement"):
        if not auth_service.access_token:
            raise HTTPException(status_code=401, detail="Not authenticated with Adobe Sign.")

        url = f"{auth_service.base_uri}api/rest/v6/agreements"
        headers = {
            "Authorization": f"Bearer {auth_service.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "fileInfos": [
                {"transientDocumentId": transient_document_id}
            ],
            "name": agreement_name,
            "participantSetsInfo": [
                {
                    "memberInfos": [{"email": recipient_email}],
                    "order": 1,
                    "role": "SIGNER"
                }
            ],
            "signatureType": "ESIGN",
            "state": "IN_PROCESS"
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 201):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create agreement: {response.text}"
            )
        return response.json()

adobe_sign_agreement_service = AdobeSignAgreementService()
