#!/usr/bin/env python3
"""
Test cache functionality specifically
"""

import requests
import json
import time

BACKEND_URL = "https://runtime-freedom.preview.emergentagent.com/api"

def test_cache_behavior():
    """Test incremental vs full reindex cache behavior"""
    session = requests.Session()
    
    print("=== CACHE BEHAVIOR TEST ===")
    
    # 1. Get initial cache stats
    print("\n1. Initial cache stats:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        initial_stats = response.json()
        print(f"   Cache stats: {initial_stats}")
    
    # 2. Trigger full reindex (should clear cache)
    print("\n2. Triggering full reindex (clear_cache=true)...")
    response = session.post(f"{BACKEND_URL}/documents/reindex?clear_cache=true")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    
    # Wait for processing
    time.sleep(6)
    
    # 3. Check cache stats after full reindex
    print("\n3. Cache stats after full reindex:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        after_full_stats = response.json()
        print(f"   Cache stats: {after_full_stats}")
    
    # 4. Check document status
    print("\n4. Document status after full reindex:")
    response = session.get(f"{BACKEND_URL}/documents/status")
    if response.status_code == 200:
        doc_status = response.json()
        print(f"   Document status: {doc_status}")
    
    # 5. Trigger incremental reindex (should use cache)
    print("\n5. Triggering incremental reindex (use cache)...")
    response = session.post(f"{BACKEND_URL}/documents/reindex")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    
    # Wait for processing
    time.sleep(4)
    
    # 6. Check cache stats after incremental reindex
    print("\n6. Cache stats after incremental reindex:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        after_incremental_stats = response.json()
        print(f"   Cache stats: {after_incremental_stats}")
    
    # 7. Final document status
    print("\n7. Final document status:")
    response = session.get(f"{BACKEND_URL}/documents/status")
    if response.status_code == 200:
        final_status = response.json()
        print(f"   Document status: {final_status}")
    
    print("\n=== ANALYSIS ===")
    print(f"Expected behavior:")
    print(f"- Full reindex should clear cache and process all files")
    print(f"- Incremental reindex should populate cache and skip unchanged files")
    print(f"- Cache should show 3 documents, 6 chunks after processing")

if __name__ == "__main__":
    test_cache_behavior()