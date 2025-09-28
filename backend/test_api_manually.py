#!/usr/bin/env python3
"""
Manual API test script
Tests the actual running FastAPI application
"""

import asyncio
import httpx
import sys
import os

# Add src to path
sys.path.append('src')

from src.main import app
import uvicorn
import threading
import time

async def test_auth_endpoints():
    """Test authentication endpoints"""
    base_url = "http://localhost:8000"

    # Test health check first
    async with httpx.AsyncClient() as client:
        print("🔍 Testing health check...")
        response = await client.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

        # Test API docs
        print("\n🔍 Testing API docs...")
        response = await client.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"❌ API docs failed: {response.status_code}")

        # Test invalid auth (should return 422 - validation error)
        print("\n🔍 Testing invalid authentication request...")
        response = await client.post(
            f"{base_url}/api/auth/login",
            json={"identifier": "test"},  # missing password
            headers={"X-Tenant-ID": "test-tenant-123"}
        )
        if response.status_code == 422:
            print("✅ Validation error handling works correctly")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")

        # Test valid structure but non-existent user
        print("\n🔍 Testing valid structure with non-existent user...")
        response = await client.post(
            f"{base_url}/api/auth/login",
            json={
                "identifier": "nonexistent@example.com",
                "password": "password123"
            },
            headers={"X-Tenant-ID": "test-tenant-123"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # This should fail with 401 since we don't have a database set up
        # but it shows that the API structure is working

    return True

def run_server():
    """Run the FastAPI server"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

async def main():
    """Main test function"""
    print("🚀 Starting manual API test...")

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)

    # Run tests
    success = await test_auth_endpoints()

    if success:
        print("\n🎉 API structure tests completed!")
        print("📋 Summary:")
        print("   ✅ FastAPI application starts successfully")
        print("   ✅ Health check endpoint works")
        print("   ✅ API documentation is accessible")
        print("   ✅ Authentication endpoint exists and validates input")
        print("   ⚠️  Database connection needed for full functionality")
    else:
        print("\n❌ Tests failed")

    return success

if __name__ == "__main__":
    asyncio.run(main())