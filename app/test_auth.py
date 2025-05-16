# app/test_auth.py
import asyncio
from app.services.adobe_sign_auth import auth_service

async def test_auth_flow():
    # Step 1: Get the authorization URL
    auth_url = auth_service.get_authorization_url()
    print("\n=== Authorization URL ===")
    print(f"Please visit this URL in your browser:\n{auth_url}")
    
    # Add this right after getting the auth_url
    print("\n=== Debug Info ===")
    print(f"Client ID: {auth_service.client_id}")
    print(f"Redirect URI: {auth_service.redirect_uri}")
    
    # Step 2: Wait for user to input the code
    print("\n=== Authorization Code ===")
    print("After authorizing, you'll be redirected to a URL with a 'code' parameter.")
    print("Please copy that code and paste it here:")
    code = input("Authorization code: ").strip()
    
    # Step 3: Exchange the code for a token
    try:
        token_data = await auth_service.exchange_code_for_token(code)
        print("\n=== Token Data ===")
        print(f"Access Token: {token_data['access_token'][:10]}...")
        print(f"Refresh Token: {token_data['refresh_token'][:10]}...")
        print(f"Expires In: {token_data.get('expires_in')} seconds")
        print("\nAuthentication successful!")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())