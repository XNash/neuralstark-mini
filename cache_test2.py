#!/usr/bin/env python3
"""
Test cache functionality with multiple incremental reindexes
"""

import requests
import json
import time

BACKEND_URL = "https://fullstack-projet.preview.emergentagent.com/api"

def test_incremental_cache():
    """Test that incremental reindex skips cached files"""
    session = requests.Session()
    
    print("=== INCREMENTAL CACHE TEST ===")
    
    # 1. Trigger full reindex to clear cache
    print("\n1. Full reindex to establish baseline...")
    response = session.post(f"{BACKEND_URL}/documents/reindex?clear_cache=true")
    time.sleep(6)
    
    # 2. Check cache stats after full reindex
    print("\n2. Cache stats after full reindex:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        stats1 = response.json()
        print(f"   Cache stats: {stats1}")
    
    # 3. First incremental reindex (should process all files and populate cache)
    print("\n3. First incremental reindex (should populate cache)...")
    response = session.post(f"{BACKEND_URL}/documents/reindex")
    time.sleep(5)
    
    # 4. Check cache stats after first incremental
    print("\n4. Cache stats after first incremental:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        stats2 = response.json()
        print(f"   Cache stats: {stats2}")
    
    # 5. Second incremental reindex (should skip all cached files)
    print("\n5. Second incremental reindex (should skip cached files)...")
    start_time = time.time()
    response = session.post(f"{BACKEND_URL}/documents/reindex")
    time.sleep(3)  # Should be faster since files are cached
    end_time = time.time()
    
    # 6. Check cache stats after second incremental
    print("\n6. Cache stats after second incremental:")
    response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if response.status_code == 200:
        stats3 = response.json()
        print(f"   Cache stats: {stats3}")
    
    # 7. Check document status
    print("\n7. Final document status:")
    response = session.get(f"{BACKEND_URL}/documents/status")
    if response.status_code == 200:
        doc_status = response.json()
        print(f"   Document status: {doc_status}")
    
    print(f"\n=== ANALYSIS ===")
    print(f"Expected: Second incremental should be faster and skip cached files")
    print(f"Processing time for second incremental: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    test_incremental_cache()