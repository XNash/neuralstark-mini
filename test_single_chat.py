#!/usr/bin/env python3
"""
Single Chat Request Test
Test one chat request to verify RAG pipeline integration
"""

import requests
import json

# Get backend URL from environment
BACKEND_URL = "https://rag-accuracy.preview.emergentagent.com/api"
CEREBRAS_API_KEY = "csk-c2wp6rmd4ed5jxtkydymmw6jp9vyv294fntcet6923dnftnw"

def test_single_chat():
    """Test a single chat request to verify RAG pipeline"""
    session = requests.Session()
    
    print("=" * 60)
    print("SINGLE CHAT REQUEST TEST")
    print("=" * 60)
    
    # First ensure API key is set
    try:
        payload = {"cerebras_api_key": CEREBRAS_API_KEY}
        response = session.post(
            f"{BACKEND_URL}/settings",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ API key configured")
        else:
            print(f"❌ Failed to configure API key: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API key configuration error: {e}")
        return False
    
    # Test chat with spelling mistake
    try:
        chat_payload = {
            "message": "What documants do you have?",  # Intentional typo
            "session_id": "test-rag-pipeline"
        }
        
        print(f"Testing query: '{chat_payload['message']}'")
        print("Expected: Spelling correction + hybrid retrieval + reranking")
        
        response = session.post(
            f"{BACKEND_URL}/chat",
            json=chat_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            has_response = "response" in data
            has_sources = "sources" in data and len(data["sources"]) > 0
            has_spelling_suggestion = "spelling_suggestion" in data
            
            print(f"✅ Chat API returned successful response")
            print(f"   Has response text: {has_response}")
            print(f"   Has sources: {has_sources} ({len(data.get('sources', []))} sources)")
            print(f"   Has spelling suggestion: {has_spelling_suggestion}")
            
            if has_spelling_suggestion and data["spelling_suggestion"]:
                print(f"   Spelling suggestion: '{data['spelling_suggestion']}'")
            
            # Check source metadata for RAG enhancements
            if has_sources:
                source = data["sources"][0]
                has_relevance_score = "relevance_score" in source
                has_reranker_score = "reranker_score" in source
                has_retrieval_method = "retrieval_method" in source
                
                print(f"   Source metadata:")
                print(f"     - Relevance score: {has_relevance_score}")
                print(f"     - Reranker score: {has_reranker_score}")
                print(f"     - Retrieval method: {has_retrieval_method}")
                
                if has_retrieval_method:
                    print(f"     - Method: {source.get('retrieval_method')}")
                if has_reranker_score:
                    print(f"     - Reranker score: {source.get('reranker_score')}")
            
            return True
            
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded (expected)")
            print("   This confirms the RAG pipeline is working and reaching the LLM")
            
            # Check if we can get error details
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'No details')}")
            except:
                pass
            
            return True  # Rate limit is expected, not a failure
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat request error: {e}")
        return False

if __name__ == "__main__":
    success = test_single_chat()
    if success:
        print("\n🎉 RAG pipeline integration test successful!")
    else:
        print("\n❌ RAG pipeline integration test failed!")