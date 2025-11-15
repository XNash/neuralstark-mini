#!/usr/bin/env python3
"""
Simple RAG Test - Quick verification of RAG system functionality
"""

import requests
import json
import time

# Backend URL and API key
BACKEND_URL = "https://rag-analyzer.preview.emergentagent.com/api"
CEREBRAS_API_KEY = "csk-tdtfvf3xtvntkhm2k6enfky2cny9y9x686pxet3dp2h5dcvm"

def test_api_health():
    """Test if API is responding"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Documents indexed: {data.get('documents_indexed')}")
            return True
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def setup_api_key():
    """Configure API key"""
    try:
        payload = {"cerebras_api_key": CEREBRAS_API_KEY}
        response = requests.post(
            f"{BACKEND_URL}/settings",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"API key setup: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"API key setup failed: {e}")
        return False

def test_simple_query():
    """Test a simple query"""
    try:
        payload = {
            "message": "What documents do you have?",
            "session_id": "test-session-" + str(int(time.time()))
        }
        
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Chat query: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response length: {len(data.get('response', ''))}")
            print(f"Sources found: {len(data.get('sources', []))}")
            print(f"Spelling suggestion: {data.get('spelling_suggestion')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Chat query failed: {e}")
        return False

def main():
    print("🔍 SIMPLE RAG SYSTEM TEST")
    print("=" * 40)
    
    # Wait for backend to be ready
    print("Waiting for backend to be ready...")
    for i in range(10):
        if test_api_health():
            print("✅ Backend is ready!")
            break
        print(f"Attempt {i+1}/10 - waiting 30 seconds...")
        time.sleep(30)
    else:
        print("❌ Backend not ready after 5 minutes")
        return False
    
    # Setup API key
    if setup_api_key():
        print("✅ API key configured")
    else:
        print("❌ API key setup failed")
        return False
    
    # Test simple query
    if test_simple_query():
        print("✅ Simple query test passed")
        return True
    else:
        print("❌ Simple query test failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 RAG system is working!")
    else:
        print("\n💥 RAG system has issues")