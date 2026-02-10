"""
Test script to verify local infrastructure (without requiring OpenAI API key).
Tests configuration, database, and storage components only.
"""

import os
import sys

# Set environment to use local config
os.environ['ENV_FILE'] = '.env.local'

print("=" * 60)
print("Testing Local Infrastructure (No API Key Required)")
print("=" * 60)

# Test 1: Configuration Loading
print("\n[Test 1] Loading configuration...")
try:
    from script_to_doc.config import get_settings
    settings = get_settings()
    print(f"✓ Configuration loaded successfully")
    print(f"  - Local mode: {settings.use_local_mode}")
    print(f"  - Data path: {settings.local_data_path}")
    print(f"  - Environment: {settings.environment}")
    print(f"  - Direct processing: {settings.use_direct_processing}")

    if not settings.use_local_mode:
        print("  ✗ ERROR: Local mode is not enabled!")
        print("  Please set USE_LOCAL_MODE=true in .env.local")
        sys.exit(1)

except Exception as e:
    print(f"✗ Configuration loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Database Operations
print("\n[Test 2] Testing database operations...")
try:
    from script_to_doc.local_db import LocalDBClient
    from datetime import datetime

    db = LocalDBClient('./data/test_scripttodoc.db')
    print(f"✓ Database client initialized")

    # Create test job
    test_job = {
        'id': 'test-job-001',
        'user_id': 'test-user',
        'status': 'queued',
        'progress': 0.0,
        'stage': 'init',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'config': {'tone': 'Professional'},
        'input': {'filename': 'test.txt'}
    }

    db.create_item(test_job)
    print(f"✓ Created test job: {test_job['id']}")

    # Read test job
    result = db.read_item('test-job-001', 'test-user')
    print(f"✓ Read test job: {result['id']} - status: {result['status']}")

    # Update test job
    result['status'] = 'completed'
    result['progress'] = 1.0
    db.upsert_item(result)
    print(f"✓ Updated test job status to: completed")

    # Query jobs
    jobs = db.query_items(None, None, partition_key='test-user', max_item_count=10)
    print(f"✓ Query returned {len(jobs)} jobs")

    # Delete test job
    db.delete_item('test-job-001', 'test-user')
    print(f"✓ Deleted test job")

    # Clean up test database
    os.remove('./data/test_scripttodoc.db')
    print(f"✓ Database test passed")

except Exception as e:
    print(f"✗ Database test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Storage Operations
print("\n[Test 3] Testing storage operations...")
try:
    from script_to_doc.local_storage import LocalBlobServiceClient

    storage = LocalBlobServiceClient('./data/test_storage')
    print(f"✓ Storage client initialized")

    # Upload test blob
    blob_client = storage.get_blob_client('uploads', 'test-file.txt')
    test_data = b'Hello from local storage!'
    blob_client.upload_blob(test_data)
    print(f"✓ Uploaded test blob")

    # Download test blob
    downloaded_data = blob_client.download_blob().readall()
    assert downloaded_data == test_data, "Downloaded data doesn't match"
    print(f"✓ Downloaded test blob: {downloaded_data.decode()}")

    # Check blob exists
    assert blob_client.exists(), "Blob should exist"
    print(f"✓ Blob exists check passed")

    # Get blob URL
    url = blob_client.url
    print(f"✓ Blob URL: {url}")
    assert url.startswith("file://"), "URL should be file:// in local mode"

    # List blobs in container
    container_client = storage.get_container_client('uploads')
    blobs = container_client.list_blobs()
    print(f"✓ Listed {len(blobs)} blobs in container")

    # Delete test blob
    blob_client.delete_blob()
    print(f"✓ Deleted test blob")

    # Clean up test storage
    import shutil
    shutil.rmtree('./data/test_storage')
    print(f"✓ Storage test passed")

except Exception as e:
    print(f"✗ Storage test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Dependency Injection
print("\n[Test 4] Testing dependency injection...")
try:
    from api.dependencies import get_cosmos_client, get_blob_service_client, get_service_bus_client

    # Test database client
    db_client = get_cosmos_client()
    print(f"✓ Database client: {type(db_client).__name__}")
    assert 'Local' in type(db_client).__name__, "Should be using local database client"

    # Test storage client
    storage_client = get_blob_service_client()
    print(f"✓ Storage client: {type(storage_client).__name__}")
    assert 'Local' in type(storage_client).__name__, "Should be using local storage client"

    # Test service bus client (should be None in local mode)
    sb_client = get_service_bus_client()
    if sb_client is None:
        print(f"✓ Service Bus client: None (expected in local mode)")
    else:
        print(f"✗ Service Bus client should be None in local mode")
        sys.exit(1)

except Exception as e:
    print(f"✗ Dependency injection test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "=" * 60)
print("✓✓✓ All infrastructure tests passed! ✓✓✓")
print("=" * 60)
print("\n📋 Your local infrastructure is ready!")
print("\nNext steps for your presentation:")
print("\n1. Add your OpenAI API key to backend/.env.local:")
print("   OPENAI_API_KEY=sk-your-actual-key-here")
print("   Get it from: https://platform.openai.com/api-keys")
print("\n2. Start the backend server:")
print("   cd backend")
print("   export ENV_FILE=.env.local")
print("   uvicorn api.main:app --reload --port 8000")
print("\n3. In another terminal, start the frontend:")
print("   cd frontend")
print("   npm run dev")
print("\n4. Open browser to http://localhost:3000")
print("\n5. Upload a sample transcript and test the full workflow!")
print("\n" + "=" * 60)
