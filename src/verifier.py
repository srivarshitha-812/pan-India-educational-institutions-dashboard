"""
Category-Specific Verification Engine & State Machine (Batch-Optimized).
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.database import Database
from src.models import VerificationStatus, VerificationRecord
from src.logger import logger

class Verifier:
    def __init__(self, db: Database):
        self.db = db

    def verify_all(self):
        """Runs the verification rules engine across all institutions in the master database."""
        institutions = self.db.get_all_institutions()
        logger.info("Starting verification engine for %d institutions...", len(institutions))
        
        updates = []
        verifs = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for inst_row in institutions:
            inst_id = inst_row["institution_id"]
            status, evidence, rule = self._evaluate_institution(inst_row)
            updates.append((status.value, evidence, inst_id))
            verifs.append((inst_id, rule, status.value, evidence, now_str))

        # Single transaction batch execution
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
            UPDATE institutions SET
                verification_status = ?,
                remarks = ?
            WHERE institution_id = ?;
            """, updates)

            cursor.executemany("""
            INSERT INTO verification (institution_id, rule_name, status, evidence, verified_at)
            VALUES (?, ?, ?, ?, ?);
            """, verifs)
            conn.commit()

        logger.info("Verification engine completed for %d institutions.", len(institutions))

    def _evaluate_institution(self, row: Dict[str, Any]) -> Tuple[VerificationStatus, str, str]:
        """Evaluates verification status based on official statutory evidence."""
        edu_level = row.get("education_level", "")
        udise_code = row.get("udise_code")
        aishe_code = row.get("aishe_code")
        aicte_id = row.get("aicte_id")
        nmc_id = row.get("nmc_id")
        ncte_id = row.get("ncte_id")
        other_id = row.get("other_regulator_id")
        rec_status = (row.get("recognition_status") or "").upper()
        app_status = (row.get("approval_status") or "").upper()
        app_auth = (row.get("approval_authority") or "").upper()

        # Check explicit De-recognition
        if "DE-RECOGNISED" in rec_status or "DE-RECOGNISED" in app_status or "WITHDRAWN" in rec_status:
            return (
                VerificationStatus.DE_RECOGNISED,
                f"Statutory recognition de-recognised or withdrawn by regulator ({row.get('recognition_authority') or row.get('source_database')}).",
                "RULE_DERECOGNITION"
            )

        # Check explicit Closure
        if "CLOSED" in rec_status or "INACTIVE" in rec_status or "CLOSED" in app_status:
            return (
                VerificationStatus.CLOSED_INACTIVE,
                "Institution marked as closed/inactive in official statutory directory.",
                "RULE_CLOSURE"
            )

        # 1. School Education
        if edu_level in ["Pre-primary", "Primary", "Upper Primary", "Secondary", "Higher Secondary"]:
            if udise_code and len(str(udise_code)) >= 10:
                return (
                    VerificationStatus.VERIFIED,
                    f"Strong official evidence: Listed in UDISE+ / Ministry of Education Directory with Code {udise_code}.",
                    "RULE_UDISE_SCHOOL_VERIFIED"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "Missing or invalid UDISE+ code for school institution.",
                "RULE_SCHOOL_NEEDS_VERIF"
            )

        # 2. Universities & INIs
        if edu_level in ["Universities", "Institutes of National Importance"]:
            if aishe_code and ("UGC" in app_auth or "UGC" in (row.get("recognition_authority") or "") or "INI" in (row.get("institution_type") or "")):
                return (
                    VerificationStatus.VERIFIED,
                    f"Verified: AISHE Code {aishe_code} with UGC Gazette / Statutory Act recognition.",
                    "RULE_HEI_UGC_VERIFIED"
                )
            elif aishe_code:
                return (
                    VerificationStatus.PARTIALLY_VERIFIED,
                    f"AISHE registered (Code {aishe_code}); pending statutory UGC gazette cross-check.",
                    "RULE_HEI_AISHE_REGISTERED"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "University record lacks confirmed AISHE / UGC identifier.",
                "RULE_UNIV_NEEDS_VERIF"
            )

        # 3. Technical & Engineering Education
        if edu_level in ["Technical/engineering institutions", "Management institutions", "Pharmacy institutions"]:
            if aicte_id or "AICTE" in app_auth:
                return (
                    VerificationStatus.VERIFIED,
                    f"Verified: AICTE Approved Technical Institution (ID: {aicte_id or 'Verified in Directory'}).",
                    "RULE_AICTE_APPROVED_VERIFIED"
                )
            elif aishe_code:
                return (
                    VerificationStatus.PARTIALLY_VERIFIED,
                    f"Listed in AISHE Higher Education directory (Code {aishe_code}); AICTE approval verification in progress.",
                    "RULE_TECH_AISHE_ONLY"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "Technical institution requires AICTE / AISHE statutory verification.",
                "RULE_TECH_NEEDS_VERIF"
            )

        # 4. Medical & Dental Education
        if edu_level in ["Medical institutions", "Dental institutions"]:
            if nmc_id or "NMC" in app_auth or "NMC" in (row.get("recognition_authority") or ""):
                return (
                    VerificationStatus.VERIFIED,
                    f"Verified: National Medical Commission recognized medical college (NMC ID/Ref: {nmc_id or 'Active'}).",
                    "RULE_NMC_MEDICAL_VERIFIED"
                )
            elif aishe_code:
                return (
                    VerificationStatus.PARTIALLY_VERIFIED,
                    f"AISHE Code {aishe_code} present; NMC course/seat detail cross-reference pending.",
                    "RULE_MED_AISHE_ONLY"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "Medical institution requires NMC recognition confirmation.",
                "RULE_MED_NEEDS_VERIF"
            )

        # 5. Teacher Education
        if edu_level == "Teacher-education institutions":
            if ncte_id or "NCTE" in app_auth or "NCTE" in (row.get("recognition_authority") or ""):
                return (
                    VerificationStatus.VERIFIED,
                    f"Verified: NCTE Recognised Teacher Education Institution (File ID: {ncte_id or 'Active'}).",
                    "RULE_NCTE_RECOGNISED_VERIFIED"
                )
            elif aishe_code:
                return (
                    VerificationStatus.PARTIALLY_VERIFIED,
                    f"AISHE registered (Code {aishe_code}); NCTE regional committee order confirmation pending.",
                    "RULE_NCTE_AISHE_ONLY"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "Teacher education institution requires NCTE recognition order.",
                "RULE_NCTE_NEEDS_VERIF"
            )

        # 6. Law Education
        if edu_level == "Law institutions":
            if "BCI" in app_auth or "BCI" in (row.get("recognition_authority") or "") or other_id:
                return (
                    VerificationStatus.VERIFIED,
                    f"Verified: Bar Council of India Approved Centre of Legal Education (BCI Ref: {other_id or 'Approved'}).",
                    "RULE_BCI_LAW_VERIFIED"
                )
            elif aishe_code:
                return (
                    VerificationStatus.PARTIALLY_VERIFIED,
                    f"AISHE registered law faculty (Code {aishe_code}); BCI approval schedule check pending.",
                    "RULE_LAW_AISHE_ONLY"
                )
            return (
                VerificationStatus.NEEDS_VERIFICATION,
                "Law institution requires BCI statutory approval verification.",
                "RULE_LAW_NEEDS_VERIF"
            )

        # 7. General Colleges & Standalone HEIs
        if aishe_code:
            return (
                VerificationStatus.VERIFIED,
                f"Verified: Official AISHE Higher Education Directory Record (AISHE Code: {aishe_code}).",
                "RULE_AISHE_COLLEGE_VERIFIED"
            )

        return (
            VerificationStatus.NEEDS_VERIFICATION,
            "Institution lacks definitive statutory registry identifier.",
            "RULE_GENERIC_NEEDS_VERIF"
        )
