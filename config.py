"""
Configuration module for Pan-India Educational Institution Data Collection System.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
LOG_DIR = DATA_DIR / "logs"

# Sub-directories for raw data by source
RAW_DIRS = {
    "udise": RAW_DATA_DIR / "udise",
    "aishe": RAW_DATA_DIR / "aishe",
    "ugc": RAW_DATA_DIR / "ugc",
    "aicte": RAW_DATA_DIR / "aicte",
    "nmc": RAW_DATA_DIR / "nmc",
    "ncte": RAW_DATA_DIR / "ncte",
    "bci": RAW_DATA_DIR / "bci",
}

# Create required directories
for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CHECKPOINT_DIR, LOG_DIR] + list(RAW_DIRS.values()):
    d.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = PROCESSED_DATA_DIR / "education_master.db"

# Output Report Paths
OUTPUT_MASTER_XLSX = PROCESSED_DATA_DIR / "master_institutions.xlsx"
OUTPUT_MASTER_CSV = PROCESSED_DATA_DIR / "master_institutions.csv"
OUTPUT_VERIFICATION_REPORT = PROCESSED_DATA_DIR / "verification_report.xlsx"
OUTPUT_QUALITY_REPORT = PROCESSED_DATA_DIR / "data_quality_report.xlsx"
OUTPUT_STATE_SUMMARY = PROCESSED_DATA_DIR / "state_summary.xlsx"
OUTPUT_SOURCE_SUMMARY = PROCESSED_DATA_DIR / "source_summary.xlsx"

# Scraper & Network Settings
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_WORKERS = 3
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
RATE_LIMIT_DELAY = 0.5  # seconds between requests to same domain

# Official Portal Base URLs
PORTAL_URLS = {
    "udise": "https://kys.udiseplus.gov.in",
    "udise_main": "https://www.udiseplus.gov.in",
    "aishe": "https://aishe.gov.in",
    "aishe_dashboard": "https://dashboard.aishe.gov.in",
    "ugc": "https://www.ugc.gov.in",
    "aicte": "https://facilities.aicte-india.org",
    "nmc": "https://www.nmc.org.in",
    "ncte": "https://ncte.gov.in",
    "bci": "https://www.barcouncilofindia.org",
}

# Standard States and Union Territories of India
INDIAN_STATES = [
    "ANDAMAN AND NICOBAR ISLANDS", "ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR",
    "CHANDIGARH", "CHHATTISGARH", "DADRA AND NAGAR HAVELI AND DAMAN AND DIU", "DELHI", "GOA",
    "GUJARAT", "HARYANA", "HIMACHAL PRADESH", "JAMMU AND KASHMIR", "JHARKHAND", "KARNATAKA",
    "KERALA", "LADAKH", "LAKSHADWEEP", "MADHYA PRADESH", "MAHARASHTRA", "MANIPUR", "MEGHALAYA",
    "MIZORAM", "NAGALAND", "ODISHA", "PUDUCHERRY", "PUNJAB", "RAJASTHAN", "SIKKIM",
    "TAMIL NADU", "TELANGANA", "TRIPURA", "UTTAR PRADESH", "UTTARAKHAND", "WEST BENGAL"
]

# Standard Master Output Columns
MASTER_COLUMNS = [
    "Institution ID",
    "Institution Name",
    "Education Level",
    "Institution Type",
    "Institution Category",
    "Management Type",
    "Official Institution ID",
    "UDISE Code",
    "AISHE Code",
    "AICTE ID",
    "NMC ID",
    "NCTE ID",
    "Other Regulator ID",
    "State",
    "District",
    "Block/Mandal",
    "City/Town/Village",
    "Full Address",
    "PIN Code",
    "Latitude",
    "Longitude",
    "University Affiliation",
    "Board/Affiliation",
    "Courses/Programmes",
    "Year Established",
    "Website",
    "Email",
    "Phone",
    "Recognition Status",
    "Recognition Authority",
    "Approval Status",
    "Approval Authority",
    "Source Database",
    "Source URL",
    "Collection Date",
    "Last Verification Date",
    "Verification Status",
    "Remarks"
]
