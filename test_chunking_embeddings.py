#!/usr/bin/env python3
"""
Test script for evaluating chunking and embedding model performance.
Tests the document processing pipeline with different configurations.
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.utils.document_processor import document_processor
from app.utils.database import chroma_db
from sentence_transformers import SentenceTransformer


class ChunkingEmbeddingTester:
    def __init__(self):
        self.doc_processor = document_processor
        self.chroma_db = chroma_db
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        print(f"🔧 Initialized with model: {settings.embedding_model}")
        print(f"📏 Chunk size: {settings.chunk_size}, Overlap: {settings.chunk_overlap}")

    def test_chunking_strategy(self, text: str, test_name: str = "Test") -> Dict[str, Any]:
        """Test chunking strategy on sample text."""
        print(f"\n📝 Testing chunking for: {test_name}")
        print(f"Original text length: {len(text)} characters")

        # Create chunks
        chunks = self.doc_processor.chunk_text(text, {"source": test_name})

        # Analyze chunks
        chunk_lengths = [len(chunk["content"]) for chunk in chunks]
        avg_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0

        results = {
            "test_name": test_name,
            "original_length": len(text),
            "num_chunks": len(chunks),
            "avg_chunk_length": avg_length,
            "min_chunk_length": min(chunk_lengths) if chunk_lengths else 0,
            "max_chunk_length": max(chunk_lengths) if chunk_lengths else 0,
            "chunks": chunks
        }

        print(f"📊 Results:")
        print(f"  Number of chunks: {results['num_chunks']}")
        print(f"  Average chunk length: {results['avg_chunk_length']:.1f}")
        print(f"  Min/Max chunk length: {results['min_chunk_length']}/{results['max_chunk_length']}")

        # Show first few chunks
        print(f"\n📄 First 3 chunks preview:")
        for i, chunk in enumerate(chunks[:3]):
            preview = chunk["content"][:100] + "..." if len(chunk["content"]) > 100 else chunk["content"]
            print(f"  Chunk {i+1}: {preview}")

        return results

    def test_embedding_quality(self, queries: List[str], documents: List[str]) -> Dict[str, Any]:
        """Test embedding quality with sample queries and documents."""
        print(f"\n🧠 Testing embedding quality...")

        # Create embeddings
        query_embeddings = self.embedding_model.encode(queries)
        doc_embeddings = self.embedding_model.encode(documents)

        # Calculate similarities
        similarities = []
        for i, query in enumerate(queries):
            query_emb = query_embeddings[i]
            query_similarities = []

            for j, doc in enumerate(documents):
                doc_emb = doc_embeddings[j]
                similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
                query_similarities.append({
                    "document_index": j,
                    "document_preview": doc[:100] + "..." if len(doc) > 100 else doc,
                    "similarity": float(similarity)
                })

            # Sort by similarity
            query_similarities.sort(key=lambda x: x["similarity"], reverse=True)
            similarities.append({
                "query": query,
                "top_matches": query_similarities[:3]  # Top 3 matches
            })

        # Display results
        for sim in similarities:
            print(f"\n🔍 Query: '{sim['query']}'")
            print(f"   Top matches:")
            for match in sim["top_matches"]:
                print(f"     Score: {match['similarity']:.3f} - {match['document_preview']}")

        return {"query_results": similarities}

    def test_semantic_understanding(self) -> Dict[str, Any]:
        """Test semantic understanding with challenging examples."""
        print(f"\n🎯 Testing semantic understanding...")

        # Test cases: semantically similar but different words
        test_cases = [
            {
                "query": "user authentication problems",
                "documents": [
                    "Users are having trouble logging into the system",
                    "Login failures have been reported by customers",
                    "The authentication service is experiencing issues",
                    "People can't sign in to their accounts",
                    "Pizza recipes and cooking instructions",
                    "Database connection timeout errors"
                ]
            },
            {
                "query": "how to deploy new features",
                "documents": [
                    "Deployment guide for releasing new functionality",
                    "Steps to rollout updates to production",
                    "CI/CD pipeline for feature releases",
                    "Publishing changes to the live environment",
                    "User interface design principles",
                    "Customer support ticket management"
                ]
            },
            {
                "query": "performance optimization",
                "documents": [
                    "Speed improvements and efficiency gains",
                    "Making the application run faster",
                    "Reducing response times and latency",
                    "System performance tuning techniques",
                    "Email marketing best practices",
                    "Database schema design patterns"
                ]
            }
        ]

        results = []
        for test_case in test_cases:
            print(f"\n🧪 Test case: '{test_case['query']}'")

            # Get embeddings
            query_emb = self.embedding_model.encode([test_case["query"]])[0]
            doc_embeddings = self.embedding_model.encode(test_case["documents"])

            # Calculate similarities
            similarities = []
            for i, doc in enumerate(test_case["documents"]):
                doc_emb = doc_embeddings[i]
                similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
                similarities.append({
                    "document": doc,
                    "similarity": float(similarity),
                    "relevant": i < 4  # First 4 are relevant, last 2 are not
                })

            # Sort by similarity
            similarities.sort(key=lambda x: x["similarity"], reverse=True)

            # Check if relevant documents ranked higher
            top_3_relevant = sum(1 for sim in similarities[:3] if sim["relevant"])

            print(f"   📊 Top 3 matches (should be relevant):")
            for i, sim in enumerate(similarities[:3]):
                relevance = "✅ Relevant" if sim["relevant"] else "❌ Irrelevant"
                print(f"     {i+1}. Score: {sim['similarity']:.3f} - {relevance}")
                print(f"        {sim['document']}")

            results.append({
                "query": test_case["query"],
                "top_3_relevant_count": top_3_relevant,
                "all_similarities": similarities
            })

        # Calculate overall performance
        total_tests = len(results)
        good_results = sum(1 for r in results if r["top_3_relevant_count"] >= 2)

        print(f"\n📈 Semantic Understanding Results:")
        print(f"   Tests passed: {good_results}/{total_tests}")
        print(f"   Success rate: {(good_results/total_tests)*100:.1f}%")

        return {
            "test_results": results,
            "success_rate": (good_results/total_tests)*100
        }

    def test_full_pipeline(self, sample_text: str) -> Dict[str, Any]:
        """Test the full pipeline: chunking -> embedding -> storage -> retrieval."""
        print(f"\n🔄 Testing full pipeline...")

        # Step 1: Chunk the text
        print("1. 📝 Chunking text...")
        chunks = self.doc_processor.process_text(sample_text, {"source": "pipeline_test"})
        print(f"   Created {len(chunks)} chunks")

        # Step 2: Store in ChromaDB (this will create embeddings)
        print("2. 💾 Storing in ChromaDB...")
        start_time = time.time()

        try:
            contents = [chunk["content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            chunk_ids = self.chroma_db.add_documents(contents, metadatas)
            storage_time = time.time() - start_time
            print(f"   ✅ Stored {len(chunk_ids)} chunks in {storage_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Storage failed: {e}")
            return {"error": str(e)}

        # Step 3: Test retrieval with various queries
        print("3. 🔍 Testing retrieval...")
        test_queries = [
            "What is this document about?",
            "main topics discussed",
            "key points and conclusions"
        ]

        retrieval_results = []
        for query in test_queries:
            start_time = time.time()
            results = self.chroma_db.query_documents(query, n_results=3)
            query_time = time.time() - start_time

            print(f"   Query: '{query}'")
            print(f"   Found {len(results['documents'])} results in {query_time:.3f}s")

            retrieval_results.append({
                "query": query,
                "num_results": len(results["documents"]),
                "query_time": query_time,
                "results": results
            })

        return {
            "chunks_created": len(chunks),
            "storage_time": storage_time,
            "retrieval_tests": retrieval_results
        }

    def run_comprehensive_test(self, test_file_path: str = None):
        """Run all tests with sample data."""
        print("=" * 80)
        print("🧪 COMPREHENSIVE CHUNKING & EMBEDDING TESTS")
        print("=" * 80)

        # Sample texts for testing
        sample_texts = {
            "Technical Documentation": """
            User Authentication System

            Our authentication system provides secure access control for all users. The system implements OAuth 2.0
            standards with JWT tokens for session management. Users can log in using email/password, social logins,
            or single sign-on (SSO) providers.

            When authentication fails, the system logs the attempt and may temporarily lock the account for security.
            Common authentication problems include expired passwords, account lockouts, and network connectivity issues.

            To deploy new authentication features, follow these steps:
            1. Update the authentication service configuration
            2. Test in staging environment
            3. Deploy to production using blue-green deployment
            4. Monitor authentication success rates

            Performance optimization for authentication includes caching user credentials, optimizing database queries,
            and implementing connection pooling for better response times.
            """,

            "Meeting Notes": """
            Weekly Team Standup - January 15, 2025

            Attendees: Alice, Bob, Charlie, Diana

            Sprint Progress:
            - User onboarding flow: 80% complete (Alice)
            - Performance improvements: In testing (Bob)
            - New feature deployment: Ready for release (Charlie)
            - Bug fixes: 3 resolved, 2 remaining (Diana)

            Blockers:
            - Authentication service experiencing intermittent issues
            - Database performance degradation during peak hours
            - CI/CD pipeline failing for feature branch deployments

            Action Items:
            - Alice: Complete onboarding flow by Friday
            - Bob: Investigate performance bottlenecks
            - Charlie: Coordinate deployment with DevOps team
            - Diana: Continue working on remaining bug fixes

            Next meeting: January 22, 2025
            """,

            "User Manual": """
            Getting Started Guide

            Welcome to our platform! This guide will help you get started quickly and effectively.

            Creating Your Account:
            To begin, visit our registration page and provide your email address and a secure password.
            You'll receive a verification email - click the link to activate your account.

            Setting Up Your Profile:
            After logging in, complete your profile with your name, role, and preferences.
            This helps us personalize your experience and improve our recommendations.

            Navigating the Interface:
            The main dashboard shows your recent activity and quick access to key features.
            Use the navigation menu to explore different sections of the platform.

            Troubleshooting Common Issues:
            If you can't sign in, try resetting your password or clearing your browser cache.
            For performance issues, ensure you have a stable internet connection.
            Contact support if problems persist.
            """
        }

        # Test external file if provided
        if test_file_path and Path(test_file_path).exists():
            try:
                text, metadata = self.doc_processor.extract_text_from_file(test_file_path)
                sample_texts[f"File: {Path(test_file_path).name}"] = text
                print(f"📁 Added test file: {test_file_path}")
            except Exception as e:
                print(f"⚠️  Failed to load test file: {e}")

        all_results = {}

        # Test 1: Chunking Strategy
        print(f"\n" + "="*50)
        print("TEST 1: CHUNKING STRATEGY")
        print("="*50)

        chunking_results = {}
        for name, text in sample_texts.items():
            chunking_results[name] = self.test_chunking_strategy(text, name)
        all_results["chunking"] = chunking_results

        # Test 2: Embedding Quality
        print(f"\n" + "="*50)
        print("TEST 2: EMBEDDING QUALITY")
        print("="*50)

        # Use chunks from first text for embedding test
        first_chunks = list(chunking_results.values())[0]["chunks"]
        documents = [chunk["content"] for chunk in first_chunks[:6]]  # First 6 chunks
        queries = [
            "authentication problems",
            "how to deploy features",
            "user onboarding process"
        ]

        embedding_results = self.test_embedding_quality(queries, documents)
        all_results["embedding_quality"] = embedding_results

        # Test 3: Semantic Understanding
        print(f"\n" + "="*50)
        print("TEST 3: SEMANTIC UNDERSTANDING")
        print("="*50)

        semantic_results = self.test_semantic_understanding()
        all_results["semantic_understanding"] = semantic_results

        # Test 4: Full Pipeline
        print(f"\n" + "="*50)
        print("TEST 4: FULL PIPELINE")
        print("="*50)

        # Use the technical documentation for pipeline test
        pipeline_results = self.test_full_pipeline(sample_texts["Technical Documentation"])
        all_results["full_pipeline"] = pipeline_results

        # Summary
        print(f"\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)

        print(f"✅ Chunking tests completed for {len(chunking_results)} documents")
        print(f"✅ Embedding quality test completed")

        semantic_success = semantic_results.get("success_rate", 0)
        print(f"✅ Semantic understanding: {semantic_success:.1f}% success rate")

        if "error" not in pipeline_results:
            print(f"✅ Full pipeline test: {pipeline_results['chunks_created']} chunks processed")
        else:
            print(f"❌ Full pipeline test failed: {pipeline_results['error']}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{timestamp}.json"

        try:
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

        return all_results


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test chunking and embedding pipeline")
    parser.add_argument("--file", help="Path to test file (optional)")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")

    args = parser.parse_args()

    tester = ChunkingEmbeddingTester()

    if args.quick:
        # Quick test with just semantic understanding
        print("🚀 Running quick semantic understanding test...")
        results = tester.test_semantic_understanding()
        print(f"\n📊 Quick test result: {results['success_rate']:.1f}% success rate")
    else:
        # Full comprehensive test
        results = tester.run_comprehensive_test(args.file)


if __name__ == "__main__":
    main()