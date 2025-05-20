import httpx
from fastapi import HTTPException
from app.services.adobe_sign_auth import auth_service
from app.services.token_store import token_store
import logging
from typing import List

logger = logging.getLogger("adobe-sign-poc")

class AdobeSignAgreementService:
    async def create_agreement(self, transient_document_id: str, recipient_emails: List[str], agreement_name: str = "Test Agreement"):
        """
        Create an agreement with Adobe Sign and send it to multiple recipients
        
        Args:
            transient_document_id: The ID of the uploaded document
            recipient_emails: List of recipient email addresses
            agreement_name: Name of the agreement
            
        Returns:
            The created agreement information
        """
        # Make sure we have a valid token, refresh if needed
        await auth_service.refresh_token_if_needed()
        if not auth_service.access_token:
            raise HTTPException(status_code=401, detail="Not authenticated with Adobe Sign.")

        # Convert single email to list if necessary
        if isinstance(recipient_emails, str):
            recipient_emails = [recipient_emails]

        # Build participant sets with proper order
        participant_sets = []
        for i, email in enumerate(recipient_emails):
            participant_sets.append({
                "memberInfos": [{"email": email}],
                "order": i + 1,
                "role": "SIGNER"
            })

        # Get base URI from stored settings
        base_uri = token_store.get_api_access_point() or auth_service.base_uri
        
        url = f"{base_uri}api/rest/v6/agreements"
        headers = {
            "Authorization": f"Bearer {auth_service.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "fileInfos": [
                {"transientDocumentId": transient_document_id}
            ],
            "name": agreement_name,
            "participantSetsInfo": participant_sets,
            "signatureType": "ESIGN",
            "state": "IN_PROCESS",
            "emailOption": {
                "sendOptions": {
                    "completionEmails": "ALL",
                    "inFlightEmails": "ALL",
                    "initEmails": "ALL"
                }
            },
            "authOptions": {
                "noAuthRequired": True
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                # If token expired, try once more after refresh
                if response.status_code == 401:
                    logger.info("Token expired during agreement creation, refreshing...")
                    refresh_result = await auth_service.refresh_token_if_needed()
                    if refresh_result:
                        # Retry with new token
                        headers["Authorization"] = f"Bearer {auth_service.access_token}"
                        response = await client.post(url, headers=headers, json=payload)
                        if response.status_code in (200, 201):
                            return response.json()

                # If still failing or not an auth issue
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create agreement: {response.text}"
                )
            return response.json()
    
    async def get_agreement(self, agreement_id: str):
        """Get agreement details by ID"""
        # Make sure we have a valid token, refresh if needed
        await auth_service.refresh_token_if_needed()
        if not auth_service.access_token:
            raise HTTPException(status_code=401, detail="Not authenticated with Adobe Sign.")
        
        # Get base URI from stored settings
        base_uri = token_store.get_api_access_point() or auth_service.base_uri
        
        url = f"{base_uri}api/rest/v6/agreements/{agreement_id}"
        headers = {
            "Authorization": f"Bearer {auth_service.access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                # If token expired, try once more after refresh
                if response.status_code == 401:
                    logger.info("Token expired during agreement retrieval, refreshing...")
                    refresh_result = await auth_service.refresh_token_if_needed()
                    if refresh_result:
                        # Retry with new token
                        headers["Authorization"] = f"Bearer {auth_service.access_token}"
                        response = await client.get(url, headers=headers)
                        if response.status_code == 200:
                            return response.json()
                
                # If still failing or not an auth issue
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get agreement: {response.text}"
                )
            return response.json()

adobe_sign_agreement_service = AdobeSignAgreementService()
