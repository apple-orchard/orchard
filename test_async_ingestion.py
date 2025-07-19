#!/usr/bin/env python3
"""
Test script for async ingestion functionality.
Tests the new async endpoints and job tracking.
"""

import requests
import time
import json

API_BASE = "http://localhost:8011"

def test_async_text_ingestion():
    """Test async text ingestion."""
    print("🧪 Testing async text ingestion...")

    # Start async ingestion
    response = requests.post(f"{API_BASE}/ingest/text/async", json={
        "text_content": "This is a test document for async ingestion. It contains information about testing async functionality.",
        "metadata": {"source": "async_test", "type": "test_document"}
    })

    if response.status_code != 200:
        print(f"❌ Failed to start async ingestion: {response.text}")
        return None

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Started async job: {job_id}")
    print(f"   Status: {job_data['status']}")
    print(f"   Type: {job_data['job_type']}")

    return job_id

def test_async_batch_ingestion():
    """Test async batch ingestion."""
    print("\n🧪 Testing async batch ingestion...")

    messages = [
        {"text": "First batch message about user authentication.", "metadata": {"msg_id": "1"}},
        {"text": "Second batch message about deployment processes.", "metadata": {"msg_id": "2"}},
        {"text": "Third batch message about performance optimization.", "metadata": {"msg_id": "3"}}
    ]

    response = requests.post(f"{API_BASE}/ingest/batch/async", json={
        "messages": messages,
        "metadata": {"batch_id": "test_batch", "source": "async_test"}
    })

    if response.status_code != 200:
        print(f"❌ Failed to start batch ingestion: {response.text}")
        return None

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Started batch job: {job_id}")
    print(f"   Status: {job_data['status']}")
    print(f"   Type: {job_data['job_type']}")

    return job_id

def check_job_status(job_id):
    """Check the status of a job."""
    response = requests.get(f"{API_BASE}/jobs/{job_id}")

    if response.status_code != 200:
        print(f"❌ Failed to get job status: {response.text}")
        return None

    return response.json()

def wait_for_job_completion(job_id, timeout=30):
    """Wait for a job to complete."""
    print(f"⏳ Waiting for job {job_id} to complete...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        status = check_job_status(job_id)
        if not status:
            return False

        print(f"   Progress: {status['progress']:.1%} - {status['message']}")

        if status['status'] in ['completed', 'failed', 'cancelled']:
            if status['status'] == 'completed':
                print(f"✅ Job completed! Chunks created: {status['chunks_created']}")
                return True
            else:
                print(f"❌ Job {status['status']}: {status.get('error_message', 'Unknown error')}")
                return False

        time.sleep(1)

    print(f"⏰ Job timed out after {timeout} seconds")
    return False

def test_job_listing():
    """Test job listing functionality."""
    print("\n📋 Testing job listing...")

    response = requests.get(f"{API_BASE}/jobs")
    if response.status_code != 200:
        print(f"❌ Failed to list jobs: {response.text}")
        return

    jobs_data = response.json()
    print(f"✅ Found {jobs_data['total_count']} jobs")

    for job in jobs_data['jobs'][:5]:  # Show first 5 jobs
        print(f"   Job {job['job_id'][:8]}... - {job['job_type']} - {job['status']}")

def test_job_stats():
    """Test job statistics."""
    print("\n📊 Testing job statistics...")

    response = requests.get(f"{API_BASE}/jobs/stats")
    if response.status_code != 200:
        print(f"❌ Failed to get job stats: {response.text}")
        return

    stats = response.json()
    print("✅ Job statistics:")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Running: {stats['running']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total chunks created: {stats['total_chunks_created']}")

def test_query_after_ingestion():
    """Test querying after async ingestion."""
    print("\n🔍 Testing query after async ingestion...")

    response = requests.post(f"{API_BASE}/query", json={
        "question": "What is async ingestion?"
    })

    if response.status_code != 200:
        print(f"❌ Failed to query: {response.text}")
        return

    result = response.json()
    print(f"✅ Query successful!")
    print(f"   Answer: {result['answer'][:100]}...")
    print(f"   Sources: {len(result.get('sources', []))}")

def main():
    """Main test function."""
    print("🚀 ASYNC INGESTION TESTS")
    print("=" * 50)

    # Test if API is running
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ API is not running. Please start the API first.")
            return
        print("✅ API is running")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the API first.")
        return

    # Test async text ingestion
    job_id1 = test_async_text_ingestion()

    # Test async batch ingestion
    job_id2 = test_async_batch_ingestion()

    # Wait for jobs to complete
    if job_id1:
        wait_for_job_completion(job_id1)

    if job_id2:
        wait_for_job_completion(job_id2)

    # Test job management
    test_job_listing()
    test_job_stats()

    # Test querying
    test_query_after_ingestion()

    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()