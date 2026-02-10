"""
Local SQLite database client (replaces Azure Cosmos DB).

Provides Cosmos DB-compatible API for local development without Azure subscription.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalDBClient:
    """
    Local SQLite database client that emulates Cosmos DB API.

    Provides the same interface as Cosmos DB for job storage and retrieval,
    but uses local SQLite database instead of Azure.
    """

    def __init__(self, db_path: str = "./data/scripttodoc.db"):
        """
        Initialize local database client.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Create schema if needed
        self._ensure_schema()
        logger.info(f"Initialized LocalDBClient with database: {db_path}")

    def _ensure_schema(self):
        """Create jobs table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    stage TEXT,
                    current_step INTEGER,
                    total_steps INTEGER,
                    stage_detail TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    config TEXT,
                    input TEXT,
                    result TEXT,
                    error TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON jobs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)")
            conn.commit()
            logger.info("Database schema initialized successfully")
        finally:
            conn.close()

    def _dict_to_row(self, item: Dict) -> tuple:
        """Convert dictionary to database row tuple."""
        return (
            item.get('id'),
            item.get('user_id'),
            item.get('status'),
            item.get('progress', 0.0),
            item.get('stage'),
            item.get('current_step'),
            item.get('total_steps'),
            item.get('stage_detail'),
            item.get('created_at'),
            item.get('updated_at'),
            json.dumps(item.get('config')) if item.get('config') else None,
            json.dumps(item.get('input')) if item.get('input') else None,
            json.dumps(item.get('result')) if item.get('result') else None,
            item.get('error')
        )

    def _row_to_dict(self, row: tuple, columns: List[str]) -> Dict:
        """Convert database row to dictionary."""
        item = dict(zip(columns, row))

        # Parse JSON fields
        for field in ['config', 'input', 'result']:
            if item.get(field):
                try:
                    item[field] = json.loads(item[field])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse {field} JSON")
                    item[field] = None

        return item

    def create_item(self, item: Dict) -> Dict:
        """
        Create a new job record.

        Args:
            item: Job data dictionary

        Returns:
            Created item dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Ensure timestamps exist
            if 'created_at' not in item:
                item['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in item:
                item['updated_at'] = datetime.utcnow().isoformat()

            row = self._dict_to_row(item)
            conn.execute("""
                INSERT INTO jobs (
                    id, user_id, status, progress, stage, current_step, total_steps,
                    stage_detail, created_at, updated_at, config, input, result, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            conn.commit()

            logger.info(f"Created job: {item['id']} (user: {item['user_id']})")
            return item
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create job {item.get('id')}: {e}")
            raise ValueError(f"Job with id {item.get('id')} already exists")
        finally:
            conn.close()

    def read_item(self, item_id: str, partition_key: str) -> Dict:
        """
        Read a job record by ID and user_id (partition key).

        Args:
            item_id: Job ID
            partition_key: User ID (partition key in Cosmos DB terms)

        Returns:
            Job data dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE id = ? AND user_id = ?",
                (item_id, partition_key)
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Job {item_id} not found for user {partition_key}")

            columns = [desc[0] for desc in cursor.description]
            item = self._row_to_dict(row, columns)

            logger.debug(f"Read job: {item_id}")
            return item
        finally:
            conn.close()

    def upsert_item(self, item: Dict) -> Dict:
        """
        Update or insert a job record.

        Args:
            item: Job data dictionary

        Returns:
            Updated item dictionary
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Update timestamp
            item['updated_at'] = datetime.utcnow().isoformat()

            # Ensure created_at exists for new records
            if 'created_at' not in item:
                item['created_at'] = item['updated_at']

            row = self._dict_to_row(item)
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    id, user_id, status, progress, stage, current_step, total_steps,
                    stage_detail, created_at, updated_at, config, input, result, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            conn.commit()

            logger.debug(f"Upserted job: {item['id']}")
            return item
        finally:
            conn.close()

    def query_items(
        self,
        query: str,
        parameters: Optional[List] = None,
        partition_key: Optional[str] = None,
        max_item_count: int = 100
    ) -> List[Dict]:
        """
        Query job records.

        Note: For local mode, this is simplified. Only supports basic queries.
        In practice, the API only queries by user_id with ordering.

        Args:
            query: SQL-like query string (simplified for local use)
            parameters: Query parameters
            partition_key: User ID to filter by
            max_item_count: Maximum items to return

        Returns:
            List of job dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Simplified query for local mode: get all jobs for user, ordered by created_at
            if partition_key:
                cursor = conn.execute(
                    """
                    SELECT * FROM jobs
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (partition_key, max_item_count)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (max_item_count,)
                )

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            items = [self._row_to_dict(row, columns) for row in rows]
            logger.debug(f"Query returned {len(items)} jobs")
            return items
        finally:
            conn.close()

    def delete_item(self, item_id: str, partition_key: str):
        """
        Delete a job record.

        Args:
            item_id: Job ID
            partition_key: User ID
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "DELETE FROM jobs WHERE id = ? AND user_id = ?",
                (item_id, partition_key)
            )
            conn.commit()
            logger.info(f"Deleted job: {item_id}")
        finally:
            conn.close()


class LocalDatabaseClient:
    """
    Wrapper that provides Cosmos DB-like database/container structure.
    """

    def __init__(self, db_path: str = "./data/scripttodoc.db"):
        self.db_path = db_path
        self._client = LocalDBClient(db_path)

    def get_database_client(self, database_name: str):
        """Get database client (returns self for compatibility)."""
        return self

    def get_container_client(self, container_name: str):
        """Get container client (returns wrapped LocalDBClient)."""
        return LocalContainerClient(self._client)


class LocalContainerClient:
    """
    Container client wrapper for Cosmos DB API compatibility.
    """

    def __init__(self, db_client: LocalDBClient):
        self.db_client = db_client

    def create_item(self, body: Dict, enable_automatic_id_generation: bool = False) -> Dict:
        """Create item with Cosmos DB API."""
        return self.db_client.create_item(body)

    def read_item(self, item: str, partition_key: str) -> Dict:
        """Read item with Cosmos DB API."""
        return self.db_client.read_item(item, partition_key)

    def upsert_item(self, body: Dict) -> Dict:
        """Upsert item with Cosmos DB API."""
        return self.db_client.upsert_item(body)

    def query_items(
        self,
        query: str,
        parameters: Optional[List] = None,
        partition_key: Optional[str] = None,
        max_item_count: int = 100
    ) -> List[Dict]:
        """Query items with Cosmos DB API."""
        return self.db_client.query_items(query, parameters, partition_key, max_item_count)

    def delete_item(self, item: str, partition_key: str):
        """Delete item with Cosmos DB API."""
        return self.db_client.delete_item(item, partition_key)
