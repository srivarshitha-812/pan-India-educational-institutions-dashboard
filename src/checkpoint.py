"""
Checkpoint and Resume State Manager.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.database import Database
from src.logger import logger

class CheckpointManager:
    def __init__(self, db: Database):
        self.db = db

    def is_completed(self, source: str, category: str, state: str, district: Optional[str] = None) -> bool:
        """Checks whether a specific source, category, state, and district have completed."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            dist_val = (district or "").upper().strip()
            state_val = (state or "").upper().strip()
            cursor.execute("""
            SELECT status FROM collection_runs
            WHERE source = ? AND category = ? AND state = ? AND district = ?;
            """, (source.lower(), category.lower(), state_val, dist_val))
            row = cursor.fetchone()
            if row and row["status"] == "COMPLETED":
                return True
            return False

    def mark_started(self, source: str, category: str, state: str, district: Optional[str] = None):
        """Marks a collection run as STARTED or IN_PROGRESS."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            dist_val = (district or "").upper().strip()
            state_val = (state or "").upper().strip()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO collection_runs (source, category, state, district, status, updated_at)
            VALUES (?, ?, ?, ?, 'IN_PROGRESS', ?)
            ON CONFLICT(source, category, state, district) DO UPDATE SET
            status = 'IN_PROGRESS',
            updated_at = excluded.updated_at;
            """, (source.lower(), category.lower(), state_val, dist_val, now))
            conn.commit()

    def mark_completed(self, source: str, category: str, state: str, district: Optional[str] = None, count: int = 0):
        """Marks a collection run as COMPLETED with total items collected."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            dist_val = (district or "").upper().strip()
            state_val = (state or "").upper().strip()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO collection_runs (source, category, state, district, items_collected, status, updated_at)
            VALUES (?, ?, ?, ?, ?, 'COMPLETED', ?)
            ON CONFLICT(source, category, state, district) DO UPDATE SET
            items_collected = excluded.items_collected,
            status = 'COMPLETED',
            updated_at = excluded.updated_at;
            """, (source.lower(), category.lower(), state_val, dist_val, count, now))
            conn.commit()
            logger.info("Checkpoint saved: %s | %s | %s | %s (Count: %d)", source, category, state_val, dist_val, count)

    def mark_failed(self, source: str, category: str, state: str, district: Optional[str] = None):
        """Marks a collection run as FAILED."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            dist_val = (district or "").upper().strip()
            state_val = (state or "").upper().strip()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO collection_runs (source, category, state, district, status, updated_at)
            VALUES (?, ?, ?, ?, 'FAILED', ?)
            ON CONFLICT(source, category, state, district) DO UPDATE SET
            status = 'FAILED',
            updated_at = excluded.updated_at;
            """, (source.lower(), category.lower(), state_val, dist_val, now))
            conn.commit()

    def reset_checkpoints(self):
        """Clears all checkpoints when --force is supplied."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM collection_runs;")
            conn.commit()
            logger.info("All checkpoints reset successfully.")

    def get_summary(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM collection_runs ORDER BY source, state, district;")
            return [dict(r) for r in cursor.fetchall()]
