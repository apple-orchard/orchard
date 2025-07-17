#!/usr/bin/env python3
"""
API endpoint testing for chunking and embedding pipeline.
Tests the API endpoints to verify the full system works correctly.
"""

import requests
import json
import time
from typing import Dict, Any, List
import tempfile
import os

class APITester:
    def __init__(self, base_url: str = "http://localhost:8011"):
        self.base_url = base_url.rstrip('/')

    def test_health(self) -> bool:
        """Test if the API is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def test_system_status(self) -> Dict[str, Any]:
        """Test system status endpoint."""
        try:
            response = requests.get(f"{self.base_url}/test")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_text_ingestion(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test text ingestion through API."""
        payload = {
            "text_content": text,
            "metadata": metadata or {}
        }

        try:
            response = requests.post(
                f"{self.base_url}/ingest/text",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_file_ingestion(self, file_path: str) -> Dict[str, Any]:
        """Test file ingestion through API."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/ingest/file",
                    files=files
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_query(self, question: str, max_chunks: int = 5) -> Dict[str, Any]:
        """Test querying through API."""
        payload = {
            "question": question,
            "max_chunks": max_chunks
        }

        try:
            response = requests.post(
                f"{self.base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_knowledge_base_info(self) -> Dict[str, Any]:
        """Test knowledge base info endpoint."""
        try:
            response = requests.get(f"{self.base_url}/knowledge-base/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def run_api_tests(self):
        """Run comprehensive API tests."""
        print("🌐 API ENDPOINT TESTS")
        print("=" * 50)

        # Test 1: Health Check
        print("\n1. 🏥 Health Check")
        if self.test_health():
            print("   ✅ API is running")
        else:
            print("   ❌ API is not responding")
            return

        # Test 2: System Status
        print("\n2. 🔧 System Status")
        status = self.test_system_status()
        if "error" not in status:
            print("   ✅ System status OK")
            print(f"   📊 ChromaDB: {status.get('chromadb', {}).get('status', 'unknown')}")
            print(f"   🤖 Ollama: {status.get('ollama', {}).get('status', 'unknown')}")
        else:
            print(f"   ❌ System status error: {status['error']}")

        # Test 3: Knowledge Base Info (before ingestion)
        print("\n3. 📚 Knowledge Base Info (before)")
        kb_info_before = self.test_knowledge_base_info()
        if "error" not in kb_info_before:
            count_before = kb_info_before.get('collection_info', {}).get('count', 0)
            print(f"   📊 Documents before: {count_before}")
        else:
            print(f"   ❌ Knowledge base info error: {kb_info_before['error']}")
            count_before = 0

        # Test 4: Text Ingestion
        print("\n4. 📝 Text Ingestion")
        test_text = """
        Authentication System Overview

        Our authentication system provides secure user access through multiple methods:
        1. Email/password authentication
        2. Social media login integration
        3. Single sign-on (SSO) capabilities

        Common authentication issues include:
        - Password reset failures
        - Account lockout problems
        - Session timeout errors

        Performance optimization strategies:
        - Implement credential caching
        - Use connection pooling
        - Monitor response times
        """

        ingestion_result = self.test_text_ingestion(
            test_text,
            {"source": "api_test", "test_type": "authentication_docs"}
        )

        if "error" not in ingestion_result:
            chunks_created = ingestion_result.get('chunks_created', 0)
            print(f"   ✅ Text ingested successfully")
            print(f"   📊 Chunks created: {chunks_created}")
        else:
            print(f"   ❌ Text ingestion failed: {ingestion_result['error']}")
            return

        # Test 5: Knowledge Base Info (after ingestion)
        print("\n5. 📚 Knowledge Base Info (after)")
        time.sleep(1)  # Give it a moment to process
        kb_info_after = self.test_knowledge_base_info()
        if "error" not in kb_info_after:
            count_after = kb_info_after.get('collection_info', {}).get('count', 0)
            print(f"   📊 Documents after: {count_after}")
            print(f"   📈 New documents: {count_after - count_before}")
        else:
            print(f"   ❌ Knowledge base info error: {kb_info_after['error']}")

        # Test 6: Query Testing
        print("\n6. 🔍 Query Testing")
        test_queries = [
            "How does authentication work?",
            "What are common login problems?",
            "How to optimize authentication performance?",
            "authentication system overview"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: '{query}'")
            start_time = time.time()
            query_result = self.test_query(query)
            query_time = time.time() - start_time

            if "error" not in query_result:
                answer = query_result.get('answer', 'No answer')
                sources = query_result.get('sources', [])
                chunks_retrieved = query_result.get('metadata', {}).get('chunks_retrieved', 0)

                print(f"     ⏱️  Response time: {query_time:.2f}s")
                print(f"     📊 Chunks retrieved: {chunks_retrieved}")
                print(f"     📝 Answer preview: {answer[:100]}...")
                print(f"     📚 Sources: {len(sources)}")
            else:
                print(f"     ❌ Query failed: {query_result['error']}")

        # Test 7: File Ingestion (create a temp file)
        print("\n7. 📄 File Ingestion")
        test_file_content = """
        Deployment Guide

        This guide covers how to deploy new features to production:

        1. Prepare the deployment
           - Run all tests
           - Update documentation
           - Review code changes

        2. Deploy to staging
           - Deploy to staging environment
           - Perform integration testing
           - Validate functionality

        3. Production deployment
           - Use blue-green deployment strategy
           - Monitor application metrics
           - Rollback if issues arise

        Performance monitoring during deployment:
        - Track response times
        - Monitor error rates
        - Check resource utilization
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_file_content)
            temp_file = f.name

        try:
            file_result = self.test_file_ingestion(temp_file)
            if "error" not in file_result:
                print(f"   ✅ File ingested successfully")
                print(f"   📊 Chunks created: {file_result.get('chunks_created', 0)}")
            else:
                print(f"   ❌ File ingestion failed: {file_result['error']}")
        finally:
            os.unlink(temp_file)  # Clean up temp file

        # Test 8: Final Query Test with New Content
        print("\n8. 🔍 Final Query Test")
        final_query = "How to deploy new features?"
        final_result = self.test_query(final_query)

        if "error" not in final_result:
            answer = final_result.get('answer', 'No answer')
            chunks_retrieved = final_result.get('metadata', {}).get('chunks_retrieved', 0)
            print(f"   ✅ Query successful")
            print(f"   📊 Chunks retrieved: {chunks_retrieved}")
            print(f"   📝 Answer: {answer[:200]}...")
        else:
            print(f"   ❌ Final query failed: {final_result['error']}")

        print("\n" + "=" * 50)
        print("🎉 API TESTS COMPLETED")
        print("=" * 50)


def main():
    """Main API test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test API endpoints for chunking and embeddings")
    parser.add_argument("--url", default="http://localhost:8011", help="API base URL")

    args = parser.parse_args()

    tester = APITester(args.url)
    tester.run_api_tests()


if __name__ == "__main__":
    main()