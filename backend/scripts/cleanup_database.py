"""
Cleanup script to delete all jobs from Cosmos DB.
Run this to start fresh with an empty database.
"""

import os
import sys
from pathlib import Path
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def cleanup_database():
    """Delete all jobs from Cosmos DB."""

    # Get Cosmos DB credentials from environment
    cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    cosmos_key = os.getenv("AZURE_COSMOS_KEY")
    cosmos_database = os.getenv("AZURE_COSMOS_DATABASE", "scripttodoc")
    cosmos_container = os.getenv("AZURE_COSMOS_CONTAINER_JOBS", "jobs")

    if not cosmos_endpoint or not cosmos_key:
        print("❌ Error: Missing Cosmos DB credentials in .env file")
        print("   Required: AZURE_COSMOS_ENDPOINT, AZURE_COSMOS_KEY")
        sys.exit(1)

    print(f"🔌 Connecting to Cosmos DB...")
    print(f"   Endpoint: {cosmos_endpoint}")
    print(f"   Database: {cosmos_database}")
    print(f"   Container: {cosmos_container}")

    # Connect to Cosmos DB
    try:
        client = CosmosClient(url=cosmos_endpoint, credential=cosmos_key)
        database = client.get_database_client(cosmos_database)
        container = database.get_container_client(cosmos_container)
    except Exception as e:
        print(f"❌ Failed to connect to Cosmos DB: {e}")
        sys.exit(1)

    print(f"\n📊 Fetching all jobs from database...")

    # Query all items
    try:
        query = "SELECT * FROM c"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        total_items = len(items)

        if total_items == 0:
            print("✅ Database is already empty! No jobs to delete.")
            return

        print(f"\n🗑️  Found {total_items} job(s) to delete:")
        for item in items:
            status = item.get('status', 'unknown')
            doc_title = item.get('config', {}).get('document_title', 'Untitled')
            created_at = item.get('created_at', 'unknown')
            print(f"   - {item['id'][:8]}... | {status:12} | {doc_title[:40]} | {created_at}")

        # Confirm deletion
        confirm = input(f"\n⚠️  Delete all {total_items} job(s)? (yes/no): ").strip().lower()

        if confirm != 'yes':
            print("❌ Deletion cancelled. No changes made.")
            return

        # Delete all items
        print(f"\n🔄 Deleting {total_items} job(s)...")
        deleted_count = 0
        failed_count = 0

        for item in items:
            try:
                container.delete_item(
                    item=item['id'],
                    partition_key=item['user_id']
                )
                deleted_count += 1
                print(f"   ✓ Deleted {item['id'][:8]}... ({deleted_count}/{total_items})")
            except Exception as e:
                failed_count += 1
                print(f"   ✗ Failed to delete {item['id'][:8]}...: {e}")

        print(f"\n✅ Cleanup complete!")
        print(f"   ✓ Successfully deleted: {deleted_count} job(s)")
        if failed_count > 0:
            print(f"   ✗ Failed to delete: {failed_count} job(s)")

        print(f"\n📝 Next steps:")
        print(f"   1. Restart the backend: python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        print(f"   2. Refresh the frontend in your browser")
        print(f"   3. Upload new files to test with a clean slate")

    except Exception as e:
        print(f"❌ Error querying/deleting items: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 70)
    print("🧹 ScriptToDoc Database Cleanup")
    print("=" * 70)
    cleanup_database()
    print("=" * 70)
