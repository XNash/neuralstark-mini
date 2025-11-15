#!/usr/bin/env python3
"""
Basic Backend Functionality Test
Tests backend APIs without hitting LLM rate limits
"""

import requests
import json
import time

# Get backend URL from environment
BACKEND_URL = "https://rag-analyzer.preview.emergentagent.com/api"

def test_basic_endpoints():
    """Test basic backend endpoints that don't require LLM"""
    session = requests.Session()
    
    print("=" * 60)
    print("BASIC BACKEND FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test 1: Health Check
    try:
        response = session.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']} - MongoDB: {data['mongodb']}")
            print(f"   Documents indexed: {data['documents_indexed']}")
        else:
            print(f"❌ Health Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check error: {e}")
    
    # Test 2: Document Status
    try:
        response = session.get(f"{BACKEND_URL}/documents/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Document Status: {data['total_documents']} docs, {data['indexed_documents']} indexed")
        else:
            print(f"❌ Document Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Document Status error: {e}")
    
    # Test 3: Settings API
    try:
        response = session.get(f"{BACKEND_URL}/settings")
        if response.status_code == 200:
            data = response.json()
            has_cerebras_key = "cerebras_api_key" in data
            print(f"✅ Settings API: cerebras_api_key field present: {has_cerebras_key}")
        else:
            print(f"❌ Settings API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Settings API error: {e}")
    
    print("\n" + "=" * 60)
    print("BACKEND BASIC FUNCTIONALITY TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_basic_endpoints()