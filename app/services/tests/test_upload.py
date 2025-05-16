import asyncio
import os
from app.services.adobe_sign_library import adobe_sign_transient_service

def test_upload():
    # Path to the dummy PDF file in the project root
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'dummy_contract.pdf'))
    print(f"Uploading file: {file_path}")
    try:
        result = adobe_sign_transient_service.upload_pdf_to_transient(file_path)
        print("\n=== Upload Result ===")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_upload() 