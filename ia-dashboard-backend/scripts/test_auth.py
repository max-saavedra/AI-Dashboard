#!/usr/bin/env python3
"""
scripts/test_auth.py

Test authentication flow:
1. Signup (create new user)
2. Use returned token
3. Access protected endpoints
"""

from app.core.config import get_settings
import asyncio
import httpx
import sys
from pathlib import Path
import time

# Ensure project path
root_path = Path(__file__).parent.parent.absolute()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

settings = get_settings()

BASE_URL = "http://localhost:8000/api/v1"


async def test_signup():
    """Create a new user and return token."""
    print("\n" + "="*60)
    print("STEP 1: Signup Endpoint")
    print("="*60)

    timestamp = int(time.time())
    email = f"test{timestamp}@example.com"
    password = "TestPassword123!"

    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "email": email,
            "password": password,
        }

        print(f"\nPOST {BASE_URL}/auth/signup")
        print(f"Email: {email}")
        print("Waiting for response... (this may take 10-20 seconds)")

        try:
            response = await client.post(
                f"{BASE_URL}/auth/signup",
                json=payload,
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                print("\n✓ Signup SUCCESS")
                print(f"User ID: {data['user_id']}")
                print(f"Email: {data['email']}")
                print(f"Access Token: {data['access_token'][:40]}...")

                return data["access_token"]

            else:
                print("\n✗ Signup FAILED")
                error_data = response.json()
                print(f"Status: {response.status_code}")
                print(f"Detail: {error_data.get('detail', response.text)}")
                return None

        except httpx.TimeoutException as e:
            print(f"\n✗ TIMEOUT ERROR: {e}")
            print("Supabase server is taking too long to respond.")
            print("Check your internet connection and Supabase status.")
            return None
        except Exception as e:
            print(f"\n✗ ERROR: {type(e).__name__}: {e}")
            return None


async def test_list_chats_without_token():
    """Should fail"""
    print("\n" + "="*60)
    print("STEP 2: Access WITHOUT Token (should fail)")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/chats",
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 401:
                print("✓ Correctly rejected - missing token")
            else:
                print("✗ Unexpected response:", response.text)

        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}: {e}")


async def test_list_chats(token: str):
    """Should succeed"""
    print("\n" + "="*60)
    print("STEP 3: Access WITH Token")
    print("="*60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {token}",
        }

        try:
            response = await client.get(
                f"{BASE_URL}/chats",
                headers=headers,
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✓ SUCCESS - Retrieved {len(data)} chats")
                if data:
                    for chat in data:
                        print(f"  - {chat['name']}")
            else:
                print("✗ FAILED")
                error_data = response.json()
                print(f"Detail: {error_data.get('detail', response.text)}")

        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}: {e}")


async def test_login():
    """Test login endpoint"""
    print("\n" + "="*60)
    print("STEP 4: Login with Test Account")
    print("="*60)

    # Try login with a test account (won't exist on first run)
    email = "testlogin@example.com"
    password = "TestPassword123!"

    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "email": email,
            "password": password,
        }

        print(f"\nPOST {BASE_URL}/auth/login")
        print(f"Email: {email}")

        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json=payload,
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\n✓ Login SUCCESS")
                print(f"User ID: {data['user_id']}")
                print(f"Email: {data['email']}")
                return data["access_token"]
            else:
                print("\n✗ Login FAILED (account may not exist yet)")
                error_data = response.json()
                print(f"Detail: {error_data.get('detail', response.text)}")
                return None

        except Exception as e:
            print(f"\n✗ ERROR: {type(e).__name__}: {e}")
            return None


async def main():
    print("\n" + "█"*60)
    print("█ AUTH FLOW TEST".center(60) + "█")
    print("█"*60)
    print(f"\nBackend URL: {BASE_URL}")

    # 1. Test without token
    await test_list_chats_without_token()

    # 2. Signup a new user
    token = await test_signup()

    if token:
        # 3. Test with token
        await test_list_chats(token)

    # 4. Try to login
    login_token = await test_login()

    print("\n" + "="*60)
    print("Test Suite Completed")
    print("="*60)

    if token:
        print("\n✓ SIGNUP: Success")
    else:
        print("\n✗ SIGNUP: Failed (check Supabase configuration)")

    if login_token:
        print("✓ LOGIN: Success")
    else:
        print("✗ LOGIN: Failed (account may not exist)")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
