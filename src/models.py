"""
Data models and Enums for the education collection system.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

class EducationLevel(str, Enum):
    PRE_PRIMARY = "Pre-primary"
    PRIMARY = "Primary"
    UPPER_PRIMARY = "Upper Primary"
    SECONDARY = "Secondary"
    HIGHER_SECONDARY = "Higher Secondary"
    COLLEGES = "Colleges"
    UNIVERSITIES = "Universities"
    STANDALONE_HEI = "Standalone higher-education institutions"
    TECHNICAL = "Technical/engineering institutions"
    MEDICAL = "Medical institutions"
    DENTAL = "Dental institutions"
    PHARMACY = "Pharmacy institutions"
    LAW = "Law institutions"
    TEACHER_EDUCATION = "Teacher-education institutions"
    MANAGEMENT = "Management institutions"
    INI = "Institutes of National Importance"
    OTHER_HEI = "Other recognised higher-education institutions"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY VERIFIED"
    NEEDS_VERIFICATION = "NEEDS VERIFICATION"
    NOT_FOUND = "NOT FOUND"
    DE_RECOGNISED = "DE-RECOGNISED"
    CLOSED_INACTIVE = "CLOSED/INACTIVE"
    DUPLICATE = "DUPLICATE"

@dataclass
class MasterInstitution:
    institution_id: str
    name: str
    education_level: str
    institution_type: str = ""
    institution_category: str = ""
    management_type: str = ""
    official_institution_id: str = ""
    udise_code: Optional[str] = None
    aishe_code: Optional[str] = None
    aicte_id: Optional[str] = None
    nmc_id: Optional[str] = None
    ncte_id: Optional[str] = None
    other_regulator_id: Optional[str] = None
    state: str = ""
    district: str = ""
    block_mandal: str = ""
    city_town_village: str = ""
    full_address: str = ""
    pincode: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    university_affiliation: str = ""
    board_affiliation: str = ""
    courses_programmes: str = ""
    year_established: Optional[int] = None
    website: str = ""
    email: str = ""
    phone: str = ""
    recognition_status: str = ""
    recognition_authority: str = ""
    approval_status: str = ""
    approval_authority: str = ""
    source_database: str = ""
    source_url: str = ""
    collection_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    last_verification_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    verification_status: str = VerificationStatus.NEEDS_VERIFICATION.value
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_master_row(self) -> Dict[str, Any]:
        """Converts to dictionary matching MASTER_COLUMNS."""
        return {
            "Institution ID": self.institution_id,
            "Institution Name": self.name,
            "Education Level": self.education_level,
            "Institution Type": self.institution_type,
            "Institution Category": self.institution_category,
            "Management Type": self.management_type,
            "Official Institution ID": self.official_institution_id or self.udise_code or self.aishe_code or self.aicte_id or "",
            "UDISE Code": self.udise_code or "",
            "AISHE Code": self.aishe_code or "",
            "AICTE ID": self.aicte_id or "",
            "NMC ID": self.nmc_id or "",
            "NCTE ID": self.ncte_id or "",
            "Other Regulator ID": self.other_regulator_id or "",
            "State": self.state,
            "District": self.district,
            "Block/Mandal": self.block_mandal,
            "City/Town/Village": self.city_town_village,
            "Full Address": self.full_address,
            "PIN Code": self.pincode,
            "Latitude": self.latitude if self.latitude is not None else "",
            "Longitude": self.longitude if self.longitude is not None else "",
            "University Affiliation": self.university_affiliation,
            "Board/Affiliation": self.board_affiliation,
            "Courses/Programmes": self.courses_programmes,
            "Year Established": self.year_established if self.year_established else "",
            "Website": self.website,
            "Email": self.email,
            "Phone": self.phone,
            "Recognition Status": self.recognition_status,
            "Recognition Authority": self.recognition_authority,
            "Approval Status": self.approval_status,
            "Approval Authority": self.approval_authority,
            "Source Database": self.source_database,
            "Source URL": self.source_url,
            "Collection Date": self.collection_date,
            "Last Verification Date": self.last_verification_date,
            "Verification Status": self.verification_status,
            "Remarks": self.remarks
        }

@dataclass
class RegulatoryRecord:
    institution_id: str
    regulator_name: str
    regulator_code: str
    raw_name: str
    approval_year: str = ""
    status_code: str = ""
    source_url: str = ""
    raw_payload_json: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ProgrammeRecord:
    institution_id: str
    regulator: str
    programme_name: str
    level: str = ""
    intake: Optional[int] = None
    approval_status: str = "APPROVED"

@dataclass
class VerificationRecord:
    institution_id: str
    rule_name: str
    status: str
    evidence: str
    verified_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
