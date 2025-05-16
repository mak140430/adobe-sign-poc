from app.services.adobe_sign_agreements import adobe_sign_agreement_service
import os
def test_create_agreement():
    # Use your actual transient document ID here
    transient_document_id = os.getenv("ADOBE_SIGN_TRANSIENT_DOC_ID")
    
    # Replace with your own email for testing
    recipient_email = "magakaraev@gmail.com"
    
    try:
        result = adobe_sign_agreement_service.create_agreement(
            transient_document_id, 
            recipient_email,
            agreement_name="Test Agreement from API"
        )
        print("\n=== Agreement Creation Result ===")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_create_agreement()
