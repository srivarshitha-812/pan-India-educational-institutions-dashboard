"""
Unit tests for deduplication and verification engine.
"""
import pytest
from pathlib import Path
from src.database import Database
from src.models import MasterInstitution, EducationLevel, VerificationStatus
from src.deduplicator import Deduplicator
from src.verifier import Verifier

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_master.db"
    return Database(db_file)

def test_deduplicator_exact_aishe_merge(temp_db):
    dedup = Deduplicator(temp_db)
    
    # 1. Insert initial AISHE institution
    inst1 = MasterInstitution(
        institution_id="",
        name="SWARNA BHARATHI INSTITUTE OF SCIENCE AND TECHNOLOGY",
        education_level=EducationLevel.TECHNICAL.value,
        official_institution_id="C-27515",
        aishe_code="C-27515",
        state="TELANGANA",
        district="KHAMMAM",
        full_address="Arempula, Khammam",
        pincode="507002"
    )
    id1 = dedup.merge_or_insert(inst1, regulator_name="AISHE")

    # 2. Insert incoming AICTE institution with same name & district
    inst2 = MasterInstitution(
        institution_id="",
        name="SWARNA BHARATHI INST OF SCIENCE & TECH",
        education_level=EducationLevel.TECHNICAL.value,
        official_institution_id="1-3324501234",
        aicte_id="1-3324501234",
        state="TELANGANA",
        district="KHAMMAM",
        full_address="Sri Shivani Nagar, Khammam",
        pincode="507002",
        approval_authority="AICTE"
    )
    id2 = dedup.merge_or_insert(inst2, regulator_name="AICTE")

    # Must be merged into single Master Institution
    assert id1 == id2
    
    merged = temp_db.get_institution_by_id(id1)
    assert merged["aishe_code"] == "C-27515"
    assert merged["aicte_id"] == "1-3324501234"
    assert "AICTE" in merged["approval_authority"]

def test_verifier_rules(temp_db):
    dedup = Deduplicator(temp_db)
    verifier = Verifier(temp_db)

    # School record with UDISE
    s_inst = MasterInstitution(
        institution_id="",
        name="GOVERNMENT HIGH SCHOOL KHAMMAM",
        education_level=EducationLevel.SECONDARY.value,
        official_institution_id="36040100101",
        udise_code="36040100101",
        state="TELANGANA",
        district="KHAMMAM"
    )
    dedup.merge_or_insert(s_inst)

    # De-recognised NCTE record
    d_inst = MasterInstitution(
        institution_id="",
        name="DEFUNCT TEACHER COLLEGE",
        education_level=EducationLevel.TEACHER_EDUCATION.value,
        official_institution_id="SRCAPP-9999",
        ncte_id="SRCAPP-9999",
        state="TELANGANA",
        district="KHAMMAM",
        recognition_status="DE-RECOGNISED"
    )
    dedup.merge_or_insert(d_inst)

    # Run verifier
    verifier.verify_all()

    s_row = temp_db.find_by_official_id("udise_code", "36040100101")
    assert s_row["verification_status"] == VerificationStatus.VERIFIED.value

    d_row = temp_db.find_by_official_id("ncte_id", "SRCAPP-9999")
    assert d_row["verification_status"] == VerificationStatus.DE_RECOGNISED.value
