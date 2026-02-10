#!/usr/bin/env python3
"""
Verify that the Cosmos DB jobs container is empty.
Run this script to check if the database has been fully cleaned.
"""

from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv
import sys

def main():
    load_dotenv()

    endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    key = os.getenv("AZURE_COSMOS_KEY")
    database_name = os.getenv("AZURE_COSMOS_DATABASE", "scripttodoc")
    container_name = os.getenv("AZURE_COSMOS_CONTAINER_JOBS", "jobs")

    print("=" * 80)
    print("COSMOS DB VERIFICATION")
    print("=" * 80)
    print()
    print(f"Endpoint: {endpoint}")
    print(f"Database: {database_name}")
    print(f"Container: {container_name}")
    print()

    try:
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Query all documents
        print("Querying all documents...")
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        print(f"Documents found: {len(items)}")
        print()

        if len(items) == 0:
            print("✅ SUCCESS: Cosmos DB is completely empty!")
            print()
            return 0
        else:
            print(f"⚠️  WARNING: {len(items)} documents still exist:")
            print()

            for i, item in enumerate(items, 1):
                print(f"{i}. ID: {item.get('id')}")
                print(f"   Status: {item.get('status', 'N/A')}")
                print(f"   user_id: {item.get('user_id', 'MISSING')}")
                print(f"   userId: {item.get('userId', 'MISSING')}")
                print(f"   Created: {item.get('created_at', 'N/A')}")
                print()

            print("If these documents still appear after 5 minutes, they may need")
            print("manual deletion via Azure Portal Data Explorer.")
            print()
            return 1

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
