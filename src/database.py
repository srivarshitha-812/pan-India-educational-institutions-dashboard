"""
Relational SQLite Database engine with WAL mode and normalized schema.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DB_PATH
from src.logger import logger
from src.models import MasterInstitution, RegulatoryRecord, ProgrammeRecord, VerificationRecord

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency & reliability
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        """Initializes normalized database schema with indices."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Master institutions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS institutions (
                institution_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                education_level TEXT NOT NULL,
                institution_type TEXT,
                institution_category TEXT,
                management_type TEXT,
                official_institution_id TEXT,
                udise_code TEXT,
                aishe_code TEXT,
                aicte_id TEXT,
                nmc_id TEXT,
                ncte_id TEXT,
                other_regulator_id TEXT,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                block_mandal TEXT,
                city_town_village TEXT,
                full_address TEXT,
                pincode TEXT,
                latitude REAL,
                longitude REAL,
                university_affiliation TEXT,
                board_affiliation TEXT,
                courses_programmes TEXT,
                year_established INTEGER,
                website TEXT,
                email TEXT,
                phone TEXT,
                recognition_status TEXT,
                recognition_authority TEXT,
                approval_status TEXT,
                approval_authority TEXT,
                source_database TEXT,
                source_url TEXT,
                collection_date TEXT,
                last_verification_date TEXT,
                verification_status TEXT,
                remarks TEXT
            );
            """)

            # Cross-Regulator Records table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS regulatory_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_id TEXT NOT NULL,
                regulator_name TEXT NOT NULL,
                regulator_code TEXT,
                raw_name TEXT NOT NULL,
                approval_year TEXT,
                status_code TEXT,
                source_url TEXT,
                raw_payload_json TEXT,
                created_at TEXT,
                FOREIGN KEY (institution_id) REFERENCES institutions (institution_id) ON DELETE CASCADE
            );
            """)

            # Programmes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS programmes (
                programme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_id TEXT NOT NULL,
                regulator TEXT NOT NULL,
                programme_name TEXT NOT NULL,
                level TEXT,
                intake INTEGER,
                approval_status TEXT,
                FOREIGN KEY (institution_id) REFERENCES institutions (institution_id) ON DELETE CASCADE
            );
            """)

            # Sources metadata table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE NOT NULL,
                base_url TEXT NOT NULL,
                endpoint TEXT,
                last_accessed TEXT,
                status TEXT
            );
            """)

            # Verification audit table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification (
                verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence TEXT,
                verified_at TEXT,
                FOREIGN KEY (institution_id) REFERENCES institutions (institution_id) ON DELETE CASCADE
            );
            """)

            # Collection runs / Checkpoints table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                category TEXT,
                state TEXT,
                district TEXT,
                items_collected INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(source, category, state, district)
            );
            """)

            # Indices for lightning-fast queries and deduplication lookup
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_state_dist ON institutions(state, district);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_udise ON institutions(udise_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_aishe ON institutions(aishe_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_aicte ON institutions(aicte_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_name ON institutions(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_edu_level ON institutions(education_level);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_verif_status ON institutions(verification_status);")
            
            conn.commit()
            logger.debug("Database initialized successfully at %s", self.db_path)

    def upsert_institution(self, inst: MasterInstitution):
        """Inserts or updates a master institution record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = inst.to_dict()
            fields = list(data.keys())
            placeholders = ", ".join(["?"] * len(fields))
            updates = ", ".join([f"{f} = excluded.{f}" for f in fields if f != "institution_id"])
            
            sql = f"""
            INSERT INTO institutions ({", ".join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(institution_id) DO UPDATE SET
            {updates};
            """
            cursor.execute(sql, list(data.values()))
            conn.commit()

    def batch_upsert_institutions(self, inst_list: List[MasterInstitution]):
        """Batch inserts or updates multiple institutions efficiently."""
        if not inst_list:
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for inst in inst_list:
                data = inst.to_dict()
                fields = list(data.keys())
                placeholders = ", ".join(["?"] * len(fields))
                updates = ", ".join([f"{f} = excluded.{f}" for f in fields if f != "institution_id"])
                
                sql = f"""
                INSERT INTO institutions ({", ".join(fields)})
                VALUES ({placeholders})
                ON CONFLICT(institution_id) DO UPDATE SET
                {updates};
                """
                cursor.execute(sql, list(data.values()))
            conn.commit()

    def add_regulatory_record(self, record: RegulatoryRecord):
        """Adds a cross-regulator audit record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO regulatory_records 
            (institution_id, regulator_name, regulator_code, raw_name, approval_year, status_code, source_url, raw_payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                record.institution_id, record.regulator_name, record.regulator_code,
                record.raw_name, record.approval_year, record.status_code,
                record.source_url, record.raw_payload_json, record.created_at
            ))
            conn.commit()

    def add_programmes(self, programmes: List[ProgrammeRecord]):
        """Batch inserts programme records."""
        if not programmes:
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for p in programmes:
                cursor.execute("""
                INSERT INTO programmes (institution_id, regulator, programme_name, level, intake, approval_status)
                VALUES (?, ?, ?, ?, ?, ?);
                """, (p.institution_id, p.regulator, p.programme_name, p.level, p.intake, p.approval_status))
            conn.commit()

    def add_verification(self, v: VerificationRecord):
        """Adds verification decision log."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO verification (institution_id, rule_name, status, evidence, verified_at)
            VALUES (?, ?, ?, ?, ?);
            """, (v.institution_id, v.rule_name, v.status, v.evidence, v.verified_at))
            conn.commit()

    def get_institution_by_id(self, institution_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM institutions WHERE institution_id = ?;", (institution_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def find_by_official_id(self, id_type: str, code: str) -> Optional[Dict[str, Any]]:
        valid_cols = ["udise_code", "aishe_code", "aicte_id", "nmc_id", "ncte_id", "other_regulator_id"]
        if id_type not in valid_cols:
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM institutions WHERE {id_type} = ?;", (code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_institutions_by_state(self, state: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM institutions WHERE UPPER(state) = ? ORDER BY district, name;", (state.upper(),))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_institutions(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute("SELECT * FROM institutions ORDER BY state, district, name LIMIT ? OFFSET ?;", (limit, offset))
            else:
                cursor.execute("SELECT * FROM institutions ORDER BY state, district, name;")
            return [dict(r) for r in cursor.fetchall()]

    def count_institutions(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM institutions;")
            return cursor.fetchone()[0]

    def get_verification_records(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT v.verification_id, v.institution_id, i.name as institution_name, i.education_level, 
                   i.state, i.district, v.rule_name, v.status, v.evidence, v.verified_at
            FROM verification v
            JOIN institutions i ON v.institution_id = i.institution_id
            ORDER BY v.verified_at DESC;
            """)
            return [dict(r) for r in cursor.fetchall()]
