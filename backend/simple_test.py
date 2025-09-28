#!/usr/bin/env python3
"""
Simple test to verify auth endpoints are working
"""

import sys
sys.path.append('src')

import asyncio
import httpx
from src.main import app
import uvicorn
import threading
import time
import subprocess
import signal
import os

async def test_simple():
    """Simple test of auth endpoints"""
    print("🔍 Testing auth endpoints...")

    base_url = "http://localhost:8001"  # Use different port to avoid conflicts

    try:
        async with httpx.AsyncClient() as client:
            # Test login endpoint with missing field
            print("\n1. Testing login with missing password (should get 422)...")
            response = await client.post(
                f"{base_url}/api/auth/login",
                json={"identifier": "test@example.com"},  # missing password
                headers={"X-Tenant-ID": "test-tenant"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")

            if response.status_code == 422:
                print("   ✅ Validation working correctly")
            else:
                print("   ❌ Unexpected status code")

            # Test login endpoint with both fields (should get 401 - authentication error)
            print("\n2. Testing login with valid format but fake user...")
            response = await client.post(
                f"{base_url}/api/auth/login",
                json={
                    "identifier": "test@example.com",
                    "password": "password123"
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")

            if response.status_code == 401:
                print("   ✅ Authentication error as expected (no database)")
            elif response.status_code == 500:
                print("   ⚠️  Database connection issue (expected)")
            else:
                print("   ❓ Other response")

    except Exception as e:
        print(f"❌ Test failed: {e}")

def run_server():
    """Run server on port 8001"""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

async def main():
    """Main test function"""
    print("🚀 Starting simple API test...")

    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)

    # Test
    await test_simple()

    print("\n🎉 Simple test completed!")

if __name__ == "__main__":
    asyncio.run(main())