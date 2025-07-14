#!/usr/bin/env python3
"""
Simple test script to verify RAG system setup
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8011"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_system():
    """Test system components"""
    try:
        response = requests.get(f"{BASE_URL}/test")
        if response.status_code == 200:
            result = response.json()
            print("✅ System test completed")
            print(f"   ChromaDB: {result.get('chromadb', {}).get('status', 'unknown')}")
            print(f"   LLM: {result.get('llm', {}).get('status', 'unknown')}")
            print(f"   Overall: {result.get('overall', {}).get('status', 'unknown')}")
            return result.get('overall', {}).get('status') == 'healthy'
        else:
            print(f"❌ System test failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ System test failed: {e}")
        return False

def test_ingest():
    """Test document ingestion"""
    try:
        test_content = """
        FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ 
        based on standard Python type hints. It was created by Sebastian Ramirez and is one of the 
        fastest Python frameworks available, with performance comparable to NodeJS and Go.
        
        Key features include:
        - Fast: Very high performance, on par with NodeJS and Go
        - Fast to code: Increase the speed to develop features by about 200% to 300%
        - Fewer bugs: Reduce about 40% of human (developer) induced errors
        - Intuitive: Great editor support. Completion everywhere. Less time debugging
        - Easy: Designed to be easy to use and learn. Less time reading docs
        - Short: Minimize code duplication. Multiple features from each parameter declaration
        - Robust: Get production-ready code. With automatic interactive documentation
        """
        
        data = {
            "text_content": test_content,
            "metadata": {"source": "test_setup", "category": "documentation"}
        }
        
        response = requests.post(f"{BASE_URL}/ingest/text", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document ingestion passed - {result.get('chunks_created', 0)} chunks created")
            return True
        else:
            print(f"❌ Document ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Document ingestion failed: {e}")
        return False

def test_query():
    """Test query functionality"""
    try:
        data = {
            "question": "What is FastAPI and what are its key features?",
            "max_chunks": 3
        }
        
        response = requests.post(f"{BASE_URL}/query", json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Query test passed")
            print(f"   Answer: {result.get('answer', 'No answer')[:100]}...")
            print(f"   Sources: {len(result.get('sources', []))} sources found")
            return True
        else:
            print(f"❌ Query test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Query test failed: {e}")
        return False

def test_knowledge_base_info():
    """Test knowledge base info endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/knowledge-base/info")
        if response.status_code == 200:
            result = response.json()
            print("✅ Knowledge base info test passed")
            print(f"   Total chunks: {result.get('total_chunks', 0)}")
            print(f"   Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Knowledge base info test failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Knowledge base info test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting RAG System Tests")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
        if i == max_retries - 1:
            print("❌ Server not ready after 30 seconds")
            sys.exit(1)
    
    tests = [
        ("Health Check", test_health),
        ("System Test", test_system),
        ("Document Ingestion", test_ingest),
        ("Query Test", test_query),
        ("Knowledge Base Info", test_knowledge_base_info)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️  {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your RAG system is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 