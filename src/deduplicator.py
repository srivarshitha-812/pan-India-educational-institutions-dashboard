"""
Cross-Regulator Deduplication & Entity Resolution Engine (Optimized Batch Mode).
"""
import uuid
import re
import json
from typing import Optional, Dict, Any, List, Tuple
from src.database import Database
from src.models import MasterInstitution, RegulatoryRecord, VerificationStatus
from src.cleaner import normalize_name, clean_state, clean_district
from src.logger import logger

class Deduplicator:
    def __init__(self, db: Database):
        self.db = db

    def generate_institution_id(self, prefix: str = "INST") -> str:
        """Generates a unique internal institution ID."""
        return f"{prefix}-IND-{uuid.uuid4().hex[:8].upper()}"

    def find_match(self, inst: MasterInstitution) -> Optional[str]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Official ID checks
            if inst.udise_code:
                cursor.execute("SELECT institution_id FROM institutions WHERE udise_code = ?;", (inst.udise_code,))
                row = cursor.fetchone()
                if row:
                    return row["institution_id"]

            if inst.aishe_code:
                cursor.execute("SELECT institution_id FROM institutions WHERE aishe_code = ?;", (inst.aishe_code,))
                row = cursor.fetchone()
                if row:
                    return row["institution_id"]

            if inst.aicte_id:
                cursor.execute("SELECT institution_id FROM institutions WHERE aicte_id = ?;", (inst.aicte_id,))
                row = cursor.fetchone()
                if row:
                    return row["institution_id"]

            if inst.nmc_id:
                cursor.execute("SELECT institution_id FROM institutions WHERE nmc_id = ?;", (inst.nmc_id,))
                row = cursor.fetchone()
                if row:
                    return row["institution_id"]

            if inst.ncte_id:
                cursor.execute("SELECT institution_id FROM institutions WHERE ncte_id = ?;", (inst.ncte_id,))
                row = cursor.fetchone()
                if row:
                    return row["institution_id"]

            # 2. Composite matching: Normalized Name + State + District
            norm_name = normalize_name(inst.name)
            state = clean_state(inst.state)
            district = clean_district(inst.district)

            if norm_name and state and district:
                cursor.execute("""
                SELECT institution_id, name, pincode FROM institutions 
                WHERE state = ? AND district = ?;
                """, (state, district))
                candidates = cursor.fetchall()
                for cand in candidates:
                    cand_norm = normalize_name(cand["name"])
                    if cand_norm == norm_name:
                        return cand["institution_id"]
                    if inst.pincode and cand["pincode"] and inst.pincode == cand["pincode"]:
                        if self._is_fuzzy_match(cand_norm, norm_name):
                            return cand["institution_id"]

        return None

    def _is_fuzzy_match(self, name1: str, name2: str) -> bool:
        words1 = set(re.findall(r"\w+", name1.upper()))
        words2 = set(re.findall(r"\w+", name2.upper()))
        if not words1 or not words2:
            return False
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) >= 0.85

    def merge_or_insert(self, inst: MasterInstitution, regulator_name: str = "", raw_payload: str = "") -> str:
        existing_id = self.find_match(inst)
        if existing_id:
            self._merge_into_existing(existing_id, inst)
            target_id = existing_id
        else:
            if not inst.institution_id:
                inst.institution_id = self.generate_institution_id()
            self.db.upsert_institution(inst)
            target_id = inst.institution_id

        if regulator_name:
            reg_rec = RegulatoryRecord(
                institution_id=target_id,
                regulator_name=regulator_name,
                regulator_code=inst.official_institution_id or inst.udise_code or inst.aishe_code or inst.aicte_id or "",
                raw_name=inst.name,
                status_code=inst.approval_status or inst.recognition_status or "ACTIVE",
                source_url=inst.source_url,
                raw_payload_json=raw_payload
            )
            self.db.add_regulatory_record(reg_rec)

        return target_id

    def batch_insert_schools(self, institutions: List[MasterInstitution], regulator_name: str = "UDISE+"):
        """Ultra-fast batch insertion for school datasets inside a single transaction."""
        if not institutions:
            return
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for inst in institutions:
                if not inst.institution_id:
                    inst.institution_id = self.generate_institution_id()
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

                # Add regulatory record in same transaction
                cursor.execute("""
                INSERT INTO regulatory_records 
                (institution_id, regulator_name, regulator_code, raw_name, approval_year, status_code, source_url, raw_payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    inst.institution_id, regulator_name, inst.udise_code or "",
                    inst.name, "", "OPERATIONAL", inst.source_url, "",
                    inst.collection_date
                ))
            conn.commit()

    def _merge_into_existing(self, existing_id: str, incoming: MasterInstitution):
        current = self.db.get_institution_by_id(existing_id)
        if not current:
            return

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            udise = current["udise_code"] or incoming.udise_code
            aishe = current["aishe_code"] or incoming.aishe_code
            aicte = current["aicte_id"] or incoming.aicte_id
            nmc = current["nmc_id"] or incoming.nmc_id
            ncte = current["ncte_id"] or incoming.ncte_id
            other_id = current["other_regulator_id"] or incoming.other_regulator_id

            website = current["website"] or incoming.website
            email = current["email"] or incoming.email
            phone = current["phone"] or incoming.phone
            pincode = current["pincode"] or incoming.pincode
            full_address = current["full_address"] or incoming.full_address
            univ_affil = current["university_affiliation"] or incoming.university_affiliation

            courses = current["courses_programmes"] or ""
            if incoming.courses_programmes and incoming.courses_programmes not in courses:
                courses = f"{courses}, {incoming.courses_programmes}".strip(", ")

            rec_auth = current["recognition_authority"] or ""
            if incoming.recognition_authority and incoming.recognition_authority not in rec_auth:
                rec_auth = f"{rec_auth}, {incoming.recognition_authority}".strip(", ")

            app_auth = current["approval_authority"] or ""
            if incoming.approval_authority and incoming.approval_authority not in app_auth:
                app_auth = f"{app_auth}, {incoming.approval_authority}".strip(", ")

            cursor.execute("""
            UPDATE institutions SET
                udise_code = ?,
                aishe_code = ?,
                aicte_id = ?,
                nmc_id = ?,
                ncte_id = ?,
                other_regulator_id = ?,
                website = ?,
                email = ?,
                phone = ?,
                pincode = ?,
                full_address = ?,
                university_affiliation = ?,
                courses_programmes = ?,
                recognition_authority = ?,
                approval_authority = ?,
                last_verification_date = ?
            WHERE institution_id = ?;
            """, (
                udise, aishe, aicte, nmc, ncte, other_id,
                website, email, phone, pincode, full_address,
                univ_affil, courses, rec_auth, app_auth,
                incoming.last_verification_date, existing_id
            ))
            conn.commit()
