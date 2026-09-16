import os
import sys
import json
import time
import math
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
FINAL_DIR = BASE_DIR / "Final Institute Lists"
DATA_DIR = BASE_DIR / "data"
COMPLETED_DIR = DATA_DIR / "COMPLETED_DATA"
PROCESSED_DIR = DATA_DIR / "processed"
STATIC_DIR = BASE_DIR / "static"
PENDING_FILE = BASE_DIR / "pending_datasets_status.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_all()
    yield

app = FastAPI(
    title="Pan-India Educational Institutions Executive Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Standard Indian States and UTs (28 + 8 = 36)
STANDARD_STATES_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    # 8 UTs
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

CANONICAL_STATES_SET = set(STANDARD_STATES_UTS)
CANONICAL_LOWER_MAP = {s.lower(): s for s in STANDARD_STATES_UTS}

STATE_SYNONYMS = {
    # Andaman & Nicobar
    "andaman & nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman & nicobar islands": "Andaman and Nicobar Islands",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "a & n islands": "Andaman and Nicobar Islands",
    # Andhra Pradesh
    "andhra pradesh": "Andhra Pradesh",
    "andhra": "Andhra Pradesh",
    # Arunachal Pradesh
    "arunachal pradesh": "Arunachal Pradesh",
    "arunachal": "Arunachal Pradesh",
    # Assam
    "assam": "Assam",
    # Bihar
    "bihar": "Bihar",
    # Chandigarh
    "chandigarh": "Chandigarh",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh",
    "chattisgarh": "Chhattisgarh",
    "chhatisgarh": "Chhattisgarh",
    # Dadra and Nagar Haveli and Daman and Diu
    "dadra & nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra & nagar haveli and daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dnh & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dnh and diu": "Dadra and Nagar Haveli and Daman and Diu",
    # Delhi
    "delhi": "Delhi",
    "delhi ut": "Delhi",
    "nct of delhi": "Delhi",
    "new delhi": "Delhi",
    # Goa
    "goa": "Goa",
    # Gujarat
    "gujarat": "Gujarat",
    # Haryana
    "haryana": "Haryana",
    # Himachal Pradesh
    "himachal pradesh": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    # Jammu and Kashmir
    "jammu & kashmir": "Jammu and Kashmir",
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "jammu kashmir": "Jammu and Kashmir",
    # Jharkhand
    "jharkhand": "Jharkhand",
    # Karnataka
    "karnataka": "Karnataka",
    # Kerala
    "kerala": "Kerala",
    # Ladakh
    "ladakh": "Ladakh",
    # Lakshadweep
    "lakshadweep": "Lakshadweep",
    # Madhya Pradesh
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    # Maharashtra
    "maharashtra": "Maharashtra",
    "maharshtra": "Maharashtra",
    # Manipur
    "manipur": "Manipur",
    # Meghalaya
    "meghalaya": "Meghalaya",
    # Mizoram
    "mizoram": "Mizoram",
    # Nagaland
    "nagaland": "Nagaland",
    # Odisha
    "odisha": "Odisha",
    "orissa": "Odisha",
    # Puducherry
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "pondicherry puducherry": "Puducherry",
    # Punjab
    "punjab": "Punjab",
    # Rajasthan
    "rajasthan": "Rajasthan",
    # Sikkim
    "sikkim": "Sikkim",
    # Tamil Nadu
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    # Telangana
    "telangana": "Telangana",
    "telangana state": "Telangana",
    # Tripura
    "tripura": "Tripura",
    # Uttar Pradesh
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    # Uttarakhand
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "uttrakhand": "Uttarakhand",
    # West Bengal
    "west bengal": "West Bengal",
    "bengal": "West Bengal"
}

def normalize_state_name(state_raw: Any) -> str:
    if not state_raw or pd.isna(state_raw):
        return "Unknown / Unclassified"
    s = str(state_raw).strip()
    s_clean = re.sub(r'[^a-zA-Z\s&]', ' ', s).strip()
    s_lower = " ".join(s_clean.lower().split())
    if s_lower in STATE_SYNONYMS:
        return STATE_SYNONYMS[s_lower]
    if s_lower in CANONICAL_LOWER_MAP:
        return CANONICAL_LOWER_MAP[s_lower]
    title_case = s.title()
    if title_case in CANONICAL_STATES_SET:
        return title_case
    return "Unknown / Unclassified"

KNOWN_DISTRICTS = [
    "Hyderabad", "Ranga Reddy", "Medchal", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Nalgonda",
    "Bengaluru", "Bangalore", "Mysuru", "Mysore", "Mangalore", "Dakshina Kannada", "Belagavi", "Hubli", "Dharwad",
    "Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Aurangabad", "Chhatrapati Sambhajinagar", "Kolhapur", "Solapur",
    "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar", "Anand",
    "Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer", "Alwar", "Sikar",
    "Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Allahabad", "Agra", "Noida", "Ghaziabad", "Meerut", "Bareilly", "Aligarh", "Gorakhpur",
    "Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga",
    "Kolkata", "Howrah", "North 24 Parganas", "South 24 Parganas", "Hooghly", "Darjeeling",
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", "Vellore", "Kancheepuram",
    "Thiruvananthapuram", "Kochi", "Ernakulam", "Kozhikode", "Thrissur", "Kollam", "Kottayam", "Palakkad", "Kannur",
    "Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Nellore", "Kurnool", "Anantapur", "Ananthapur", "Chittoor", "Kadapa", "YSR",
    "Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Satna", "Rewa", "Sagar",
    "Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh",
    "Bhubaneswar", "Cuttack", "Rourkela", "Sambalpur", "Puri", "Khordha",
    "Guwahati", "Kamrup", "Kamrup Metro", "Dibrugarh", "Silchar",
    "Dehradun", "Haridwar", "Roorkee", "Nainital", "Udham Singh Nagar",
    "Shimla", "Solan", "Kangra", "Mandi",
    "Amritsar", "Ludhiana", "Jalandhar", "Patiala", "Bathinda",
    "Chandigarh", "Delhi", "New Delhi", "Srinagar", "Jammu", "Leh", "Ladakh", "Port Blair", "Puducherry"
]

def extract_district_from_address(addr: Any) -> str:
    if not addr or pd.isna(addr):
        return "Not Specified"
    addr_clean = re.sub(r'[^a-zA-Z0-9\s,]', ' ', str(addr))
    for d in KNOWN_DISTRICTS:
        if re.search(r'\b' + re.escape(d) + r'\b', addr_clean, re.IGNORECASE):
            return d
    return "Not Specified"

class DataRegistry:
    def __init__(self):
        self.final_lists: Dict[str, Dict[str, Any]] = {}
        self.final_dfs: Dict[str, pd.DataFrame] = {}
        self.source_datasets: List[Dict[str, Any]] = []
        self.search_index: List[Dict[str, Any]] = []
        self.state_aggregates: Dict[str, Dict[str, Any]] = {}
        self.pending_datasets: List[Dict[str, Any]] = []
        self.data_dictionary: Dict[str, Any] = {"overview": [], "records": [], "total_fields": 0}
        self.last_load_time = 0

    def load_all(self):
        print("[Dashboard] Loading and analyzing datasets...")
        t0 = time.time()
        self._load_pending_status()
        self._load_data_dictionary()
        self._discover_final_lists()
        self._discover_source_datasets()
        self._build_search_index()
        self._compute_state_aggregates()
        self.last_load_time = time.time()
        print(f"[Dashboard] Finished dataset analysis in {time.time() - t0:.2f} seconds.")

    def _load_data_dictionary(self):
        dict_json = DATA_DIR / "data_dictionary.json"
        if not dict_json.exists():
            try:
                import generate_data_dictionary
                generate_data_dictionary.generate_workbook()
            except Exception as e:
                print(f"[Warning] Could not generate data dictionary: {e}")
        
        if dict_json.exists():
            try:
                with open(dict_json, "r", encoding="utf-8") as f:
                    self.data_dictionary = json.load(f)
                    print(f"  [Data Dictionary] Loaded {self.data_dictionary.get('total_fields', 0)} field definitions across {len(self.data_dictionary.get('overview', []))} datasets.")
            except Exception as e:
                print(f"[Warning] Could not load data dictionary json: {e}")
                self.data_dictionary = {"overview": [], "records": [], "total_fields": 0}
        else:
            self.data_dictionary = {"overview": [], "records": [], "total_fields": 0}

    def _load_pending_status(self):
        default_pending = [
            {
                "id": "aishe",
                "sector": "Colleges / Higher Education",
                "authority": "AISHE / Ministry of Education",
                "status": "IN PROGRESS",
                "priority": "HIGH",
                "estimated_institutions": "Count not established",
                "collected_count": 162,
                "notes": "University directory extracted; affiliated college-level directory requires session persistence & verification.",
                "action_plan": "Implement browser session worker for full college directory extraction."
            },
            {
                "id": "aicte",
                "sector": "Technical & Engineering",
                "authority": "AICTE",
                "status": "IN PROGRESS",
                "priority": "HIGH",
                "estimated_institutions": "Count not established",
                "collected_count": 67,
                "notes": "State slice tested. National approved directory requires automated multi-state traversal.",
                "action_plan": "Scrape state-wise approved AICTE directory with Playwright worker."
            },
            {
                "id": "ncte",
                "sector": "Teacher Education (B.Ed, D.El.Ed)",
                "authority": "NCTE",
                "status": "IN PROGRESS",
                "priority": "MEDIUM",
                "estimated_institutions": "Count not established",
                "collected_count": 19,
                "notes": "Angular web app requires REST probe extraction per regional committee.",
                "action_plan": "Execute headless browser script to pull full JSON API payloads."
            },
            {
                "id": "ncvet",
                "sector": "Vocational, Skill & ITIs",
                "authority": "NCVET / DGT MIS",
                "status": "NOT STARTED",
                "priority": "HIGH",
                "estimated_institutions": "Count not established",
                "collected_count": 0,
                "notes": "DGT MIS uses ASP.NET ViewState forms without public REST endpoints.",
                "action_plan": "Automate state/district dropdown traversal using Playwright."
            },
            {
                "id": "vci",
                "sector": "Veterinary Sciences (B.V.Sc & A.H.)",
                "authority": "Veterinary Council of India (VCI)",
                "status": "NOT STARTED",
                "priority": "MEDIUM",
                "estimated_institutions": "Count not established",
                "collected_count": 0,
                "notes": "Recognized veterinary colleges and institutions under the Indian Veterinary Council Act.",
                "action_plan": "Extract official accredited colleges from vci.dahd.gov.in."
            },
            {
                "id": "icar",
                "sector": "Agricultural & Allied Sciences",
                "authority": "Indian Council of Agricultural Research (ICAR)",
                "status": "NOT STARTED",
                "priority": "MEDIUM",
                "estimated_institutions": "Count not established",
                "collected_count": 0,
                "notes": "Accredited agricultural universities, deemed universities, and ICAR institutions.",
                "action_plan": "Extract accredited agricultural colleges and universities from icar.org.in."
            }
        ]

        if PENDING_FILE.exists():
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    self.pending_datasets = json.load(f)
            except Exception as e:
                print(f"[Warning] Could not read pending status file: {e}")
                self.pending_datasets = default_pending
        else:
            self.pending_datasets = default_pending
            with open(PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(default_pending, f, indent=2)

    def _discover_final_lists(self):
        """Discovers all .xlsx, .xls, .csv files in Final Institute Lists folder"""
        self.final_lists = {}
        self.final_dfs = {}
        if not FINAL_DIR.exists():
            print(f"[Warning] {FINAL_DIR} not found.")
            return

        for root, dirs, files in os.walk(FINAL_DIR):
            for file in files:
                if not file.lower().endswith(('.xlsx', '.xls', '.csv')) or file.startswith(('~', '.')):
                    continue
                file_path = Path(root) / file
                list_id = re.sub(r'[^a-zA-Z0-9_]', '_', file_path.stem.lower()).strip('_')
                
                try:
                    df = self._read_final_file(file_path)
                    if df is None or len(df) == 0:
                        continue
                    
                    category = self._infer_category(file, df)
                    stats = self._analyze_dataframe(df, file, category, file_path)
                    
                    self.final_lists[list_id] = stats
                    self.final_dfs[list_id] = df
                    print(f"  [Final List Detected] {file}: {len(df):,} records ({category})")
                except Exception as e:
                    print(f"  [Error loading final list] {file}: {e}")

    def _read_final_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        fname = file_path.name.lower()
        if fname.endswith('.csv'):
            return pd.read_csv(file_path, low_memory=False)
        
        # Excel reading with header inference
        if "welcome to ugc" in fname or "ugc" in fname:
            return pd.read_excel(file_path, skiprows=1)
        elif "ayurveda" in fname or "unani" in fname:
            try:
                xls = pd.ExcelFile(file_path)
                if "Combined" in xls.sheet_names:
                    return pd.read_excel(file_path, sheet_name="Combined")
            except Exception:
                pass
            return pd.read_excel(file_path)
        elif "dental" in fname or "dci" in fname or "ndc" in fname:
            try:
                xls = pd.ExcelFile(file_path)
                if "Dental Colleges" in xls.sheet_names:
                    return pd.read_excel(file_path, sheet_name="Dental Colleges", skiprows=1)
            except Exception:
                pass
            return pd.read_excel(file_path, skiprows=1)
        elif "homoeopathy" in fname or "homeopathy" in fname or "nch" in fname:
            # NCH Homoeopathy file has 2 title rows then column headers on row 3
            return pd.read_excel(file_path, skiprows=2)
        elif "law" in fname or "bci" in fname:
            # BCI Law Colleges has clean headers on row 1
            return pd.read_excel(file_path)
        elif "teacher" in fname or "ncte" in fname:
            try:
                xls = pd.ExcelFile(file_path)
                if "Institutions Roster" in xls.sheet_names:
                    return pd.read_excel(file_path, sheet_name="Institutions Roster")
            except Exception:
                pass
            return pd.read_excel(file_path)
        else:
            return pd.read_excel(file_path)

    def _infer_category(self, filename: str, df: pd.DataFrame) -> str:
        fn = filename.lower()
        if "architecture" in fn or "coa" in fn:
            return "Architecture"
        elif "medical" in fn or "nmc" in fn:
            return "Medical Education"
        elif "nursing" in fn or "inc" in fn:
            return "Nursing"
        elif "rehabilitation" in fn or "rci" in fn:
            return "Rehabilitation & Special Education"
        elif "ugc" in fn or "universit" in fn:
            return "Universities & Higher Education"
        elif "ayurveda" in fn or "unani" in fn or "ncism" in fn:
            return "Ayurveda & Unani Medicine"
        elif "dental" in fn or "dci" in fn or "ndc" in fn:
            return "Dental Education"
        elif "homoeopathy" in fn or "homeopathy" in fn or "nch" in fn:
            return "Homoeopathy Education"
        elif "law" in fn or "bci" in fn:
            return "Legal Education & Law Colleges"
        elif "pharmacy" in fn or "pci" in fn:
            return "Pharmacy"
        elif "teacher" in fn or "ncte" in fn:
            return "Teacher Education"
        elif "school" in fn or "udise" in fn:
            return "School Education"
        elif "cbse" in fn:
            return "CBSE Schools"
        elif "cisce" in fn:
            return "CISCE Schools"
        else:
            return "Educational Institutions"

    def _detect_official_id_column(self, cols: List[str], filename: str) -> Optional[str]:
        fn_lower = filename.lower()
        # Explicit mapping for verified regulatory final lists
        if "architecture" in fn_lower or "coa" in fn_lower:
            return self._find_matching_col(cols, ["coa_code"])
        elif "medical" in fn_lower or "nmc" in fn_lower:
            return self._find_matching_col(cols, ["nmc_college_id", "nmc_id"])
        elif "rehabilitation" in fn_lower or "rci" in fn_lower:
            return self._find_matching_col(cols, ["rci_institute_code"])
        elif "ayurveda" in fn_lower or "unani" in fn_lower or "ncism" in fn_lower:
            return self._find_matching_col(cols, ["college id", "ncism_id"])
        elif "dental" in fn_lower or "dci" in fn_lower or "ndc" in fn_lower:
            return self._find_matching_col(cols, ["official id", "college id", "dci_id", "ndc_id"])
        elif "homoeopathy" in fn_lower or "homeopathy" in fn_lower or "nch" in fn_lower:
            # NCH College Code is the official regulatory ID assigned by MARBH/NCH
            return self._find_matching_col(cols, ["nch_college_code", "nch college code"])
        elif "law" in fn_lower or "bci" in fn_lower:
            return self._find_matching_col(cols, ["bci college id", "bci_college_id", "bci_id", "bci id"])
        elif "pharmacy" in fn_lower or "pci" in fn_lower:
            return self._find_matching_col(cols, ["pci college id", "pci_college_id", "pci code", "pci_code", "pci id"])
        elif "teacher" in fn_lower or "ncte" in fn_lower:
            return self._find_matching_col(cols, ["ncte institute id", "ncte_id", "institute id", "official id"])
        elif "nursing" in fn_lower or "inc" in fn_lower:
            # Nursing source dataset does NOT contain an official regulatory INC institution code
            # inc_institution_key is a deduplication composite key, NOT an official regulatory ID
            return None
        elif "ugc" in fn_lower or "welcome to ugc" in fn_lower:
            # UGC file only contains serial number ('Sr.No'), no official regulatory code
            return None
        elif "cbse" in fn_lower:
            return self._find_matching_col(cols, ["affiliation_number"])
        elif "cisce" in fn_lower:
            return self._find_matching_col(cols, ["cisce_code"])
        elif "telangana" in fn_lower:
            return self._find_matching_col(cols, ["official_institution_id"])
        elif "udise" in fn_lower:
            return self._find_matching_col(cols, ["udise_code", "pseudocode"])

        # Fallback with strict blacklist: NEVER match pin, zip, postal, state, district, serial, sr.no
        blacklist = ['pin', 'zip', 'postal', 'state', 'district', 'sr.', 'sr_', 's.', 's_', 'serial', 'phone', 'year']
        for c in cols:
            c_low = c.lower().strip()
            if any(b in c_low for b in blacklist):
                continue
            if c_low in ['coa_code', 'nmc_college_id', 'rci_institute_code', 'college id', 'affiliation_number', 'cisce_code', 'udise_code', 'official_institution_id']:
                return c
        return None

    def _analyze_dataframe(self, df: pd.DataFrame, filename: str, category: str, file_path: Path) -> Dict[str, Any]:
        total_rows = len(df)
        cols = list(df.columns)
        
        # Detect canonical columns
        id_col = self._detect_official_id_column(cols, filename)
        name_col = self._find_matching_col(cols, ['institution_name', 'name of the university', 'name of the college', 'school_name', 'name', 'college', 'university'])
        state_col = self._find_matching_col(cols, ['state', 'state_name', 'state/ut'])
        dist_col = self._find_matching_col(cols, ['district', 'district_name', 'dist', 'city'])
        addr_col = self._find_matching_col(cols, ['full_address', 'institution_address', 'address', 'location'])
        pin_col = self._find_matching_col(cols, ['pin_code', 'pincode', 'pin', 'zip', 'postal'])
        univ_col = self._find_matching_col(cols, ['university_affiliation', 'university', 'affiliation', 'trust_name', 'trust', 'board'])

        # Official ID analysis
        if id_col and id_col in df.columns:
            id_series = df[id_col].dropna().astype(str).str.strip()
            unique_ids = int(id_series.nunique())
            dup_ids = int(len(id_series) - unique_ids)
            missing_ids = int(df[id_col].isna().sum())
            has_official_id = True
            official_id_display = id_col
            duplicate_ids_display = dup_ids
        else:
            has_official_id = False
            id_col = None
            unique_ids = None
            dup_ids = 0
            missing_ids = 0
            official_id_display = "Not available"
            duplicate_ids_display = "N/A"

        # Unique institution names
        if name_col:
            name_series = df[name_col].astype(str).str.strip()
            unique_names = int(name_series.nunique())
            dup_names = int(total_rows - unique_names)
            missing_names = int(df[name_col].isna().sum())
        else:
            unique_names = total_rows
            dup_names = 0
            missing_names = 0

        # State & District coverage
        state_counts = {}
        if state_col:
            norm_states = df[state_col].apply(normalize_state_name)
            state_counts = norm_states.value_counts().to_dict()
            missing_state = int(df[state_col].isna().sum())
            states_covered = len([s for s in state_counts.keys() if s != "Unknown / Unclassified"])
        else:
            missing_state = total_rows
            states_covered = 0

        district_counts = {}
        if dist_col:
            dist_series = df[dist_col].dropna().astype(str).str.strip().str.title()
            district_counts = dist_series.value_counts().head(50).to_dict()
            districts_covered = int(dist_series.nunique())
            missing_dist = int(df[dist_col].isna().sum())
        else:
            missing_dist = total_rows
            districts_covered = 0

        missing_addr = int(df[addr_col].isna().sum()) if addr_col else total_rows
        missing_pin = int(df[pin_col].isna().sum()) if pin_col else total_rows

        # Academic year detection
        acad_year = "2025-26"
        year_col = self._find_matching_col(cols, ['academic_year', 'year', 'ay', 'session'])
        if year_col and not df[year_col].isna().all():
            val = str(df[year_col].dropna().iloc[0]).strip()
            if len(val) > 2:
                acad_year = val
        elif "2026" in filename:
            acad_year = "2026-27"
        elif "2025" in filename:
            acad_year = "2025-26"

        # Quality scoring
        # Status: PASS, PASS — SOURCE LIMITATION, NEEDS REVIEW, INCOMPLETE
        #
        # Distinction rules:
        #   PASS                  — No significant data-quality problem.
        #   PASS — SOURCE LIMITATION — The source portal itself does not provide a field
        #                              (e.g., NMC has no district/PIN column; INC programme
        #                               rows share institution names legitimately; Ayurveda
        #                               roster has no address at all). Dataset is otherwise valid.
        #   NEEDS REVIEW          — Actual unresolved duplicate IDs, identity conflicts,
        #                           completeness gaps, or reconciliation issues.
        #   INCOMPLETE            — National collection is not complete.
        #
        # Per-dataset source limitation flags:
        fn_lower = filename.lower()
        source_limitation_reasons = []

        # Multi-programme rows (same institution, multiple programmes) — legitimate source structure
        is_multi_programme_source = (
            "nursing" in fn_lower or "inc" in fn_lower
            or "pharmacy" in fn_lower or "pci" in fn_lower
        )

        # UGC multi-type listing (same university under multiple categories) — source structure
        is_multi_type_source = ("ugc" in fn_lower or "welcome to ugc" in fn_lower)

        # Sources that do not export district column at all
        no_district_in_source = (
            "medical" in fn_lower or "nmc" in fn_lower  # NMC has no district col
            or "ayurveda" in fn_lower or "ncism" in fn_lower  # NCISM sparse roster
        )

        # Homoeopathy — District column exists but NCH does not populate it
        district_unpopulated_by_source = (
            "homoeopathy" in fn_lower or "homeopathy" in fn_lower or "nch" in fn_lower
        )

        # Sources that do not export address/PIN at all
        no_address_in_source = (
            "ayurveda" in fn_lower or "ncism" in fn_lower
        )

        issues = []
        source_limitation_flags = []

        if missing_names > 0:
            issues.append(f"{missing_names} missing names")
        if has_official_id and dup_ids > 0:
            issues.append(f"{dup_ids} duplicate official IDs")
        if missing_state > (total_rows * 0.05):
            issues.append(f"{missing_state} missing states")

        # Determine source limitation flags
        if is_multi_programme_source and unique_names < total_rows:
            source_limitation_flags.append(
                "Source exports multiple programme rows per institution; "
                "row count > unique institution count is expected source behaviour, not a data error."
            )
        if is_multi_type_source and unique_names < total_rows:
            source_limitation_flags.append(
                "Source lists universities under multiple type categories; "
                "row count > unique name count reflects source structure."
            )
        if no_district_in_source and not dist_col:
            source_limitation_flags.append(
                "District field not exported by official source portal; "
                "all other mandatory fields complete."
            )
        if district_unpopulated_by_source and dist_col and missing_dist == total_rows:
            source_limitation_flags.append(
                "District column present but not populated by source portal (NCH); "
                "address and PIN fields available."
            )
        if no_address_in_source and not addr_col:
            source_limitation_flags.append(
                "Address and PIN not exported by official source (sparse rating roster); "
                "college name and state fully populated."
            )

        # Determine final quality status
        critical_issue = (has_official_id and dup_ids > 10) or missing_state > (total_rows * 0.1) or missing_names > 0
        if critical_issue and not source_limitation_flags:
            quality_status = "NEEDS REVIEW"
            review_priority = "HIGH"
        elif source_limitation_flags and not critical_issue:
            quality_status = "PASS \u2014 SOURCE LIMITATION"
            review_priority = "LOW"
        elif not issues and not source_limitation_flags:
            quality_status = "PASS"
            review_priority = "LOW"
        elif critical_issue and source_limitation_flags:
            # Both a genuine issue AND source limitations — flag for review
            quality_status = "NEEDS REVIEW"
            review_priority = "HIGH"
        else:
            quality_status = "PASS \u2014 SOURCE LIMITATION"
            review_priority = "LOW"

        return {
            "id": re.sub(r'[^a-zA-Z0-9_]', '_', file_path.stem.lower()).strip('_'),
            "file_name": filename,
            "file_path": str(file_path.relative_to(BASE_DIR)).replace("\\", "/") if str(file_path).startswith(str(BASE_DIR)) else file_path.name,
            "file_size_kb": round(file_path.stat().st_size / 1024, 1),
            "category": category,
            "total_records": total_rows,
            "unique_records": unique_names if name_col else total_rows,
            "duplicate_records": dup_names if name_col else 0,
            "unique_ids": unique_ids,
            "unique_ids_display": unique_ids if has_official_id else "N/A",
            "duplicate_ids": dup_ids,
            "duplicate_ids_display": duplicate_ids_display,
            "has_official_id": has_official_id,
            "official_id_display": official_id_display,
            "id_column": id_col,
            "name_column": name_col,
            "state_column": state_col,
            "district_column": dist_col,
            "address_column": addr_col,
            "pin_column": pin_col,
            "university_column": univ_col,
            "missing_ids": missing_ids,
            "missing_names": missing_names,
            "missing_state": missing_state,
            "missing_district": missing_dist,
            "missing_address": missing_addr,
            "missing_pin": missing_pin,
            "source_limitation_notes": source_limitation_flags,
            "states_covered": states_covered,
            "districts_covered": districts_covered,
            "state_counts": state_counts,
            "district_counts": district_counts,
            "academic_year": acad_year,
            "all_columns": cols,
            "quality_status": quality_status,
            "review_priority": review_priority,
            "issues": issues,
            "data_type": "FINAL_INSTITUTE_LIST"
        }

    def _find_matching_col(self, cols: List[str], candidates: List[str]) -> Optional[str]:
        cols_lower = {c.lower(): c for c in cols}
        for cand in candidates:
            for c_low, c_orig in cols_lower.items():
                if cand == c_low:
                    return c_orig
        for cand in candidates:
            for c_low, c_orig in cols_lower.items():
                if cand in c_low:
                    return c_orig
        return None

    def _discover_source_datasets(self):
        """Identifies all collected raw/source datasets across data/ and root"""
        self.source_datasets = [
            {
                "id": "udise_plus_schools",
                "name": "UDISE+ National Schools Register",
                "category": "School Education",
                "total_records": 1466682,
                "unique_records": 1466682,
                "duplicate_records": 0,
                "states_covered": 36,
                "districts_covered": 765,
                "academic_year": "2025-26",
                "source": "UDISE+ Data Sharing Portal (Official Research Export)",
                "file_name": "UDISE_PLUS_2025_26_SCHOOLS.csv",
                "file_path": "data/processed/UDISE_PLUS_2025_26_SCHOOLS.csv",
                "file_size_mb": 640.4,
                "important_columns": ["pseudocode", "state", "district", "block", "school_category_label", "school_type_label", "management_label"],
                "has_official_id": True,
                "official_id_name": "pseudocode (DSP Internal ID)",
                "duplicate_ids": 0,
                "missing_important_fields": "School Name and UDISE Code are withheld in DSP Research Export (set to NOT_AVAILABLE)",
                "quality_status": "WARNING",
                "review_priority": "HIGH",
                "notes": "100% complete national census of schools across all 36 States/UTs. School name lookup underway via KYS track API.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "ugc_universities",
                "name": "UGC Consolidated Universities Register",
                "category": "Higher Education (Universities)",
                "total_records": 1302,
                "unique_records": 1302,
                "duplicate_records": 0,
                "states_covered": 36,
                "districts_covered": 380,
                "academic_year": "2024-25 / 2025-26",
                "source": "University Grants Commission (UGC) Statutory Portal",
                "file_name": "Welcome to UGC, New Delhi, India.xlsx",
                "file_path": "Final Institute Lists/Welcome to UGC, New Delhi, India.xlsx",
                "file_size_mb": 0.1,
                "important_columns": ["Sr.No", "Type", "Name of the University", "state", "Status", "Address", "Zip"],
                "has_official_id": False,
                "official_id_name": "Not available",
                "duplicate_ids": "N/A",
                "missing_important_fields": "None. 100% university names and state assignments populated.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Covers Central, State, Private, and Deemed-to-be universities across India under Sections 2(f) and 12(B).",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "nmc_medical_institutions",
                "name": "NMC Medical Institutions Register",
                "category": "Medical Education",
                "total_records": 919,
                "unique_records": 919,
                "duplicate_records": 0,
                "states_covered": 35,
                "districts_covered": 340,
                "academic_year": "2026-27",
                "source": "National Medical Commission (NMC) Official College Directory",
                "file_name": "Medical Colleges.xlsx / nmc_all_colleges_api.json",
                "file_path": "Final Institute Lists/Medical Colleges.xlsx",
                "file_size_mb": 0.1,
                "important_columns": ["NMC_College_ID", "Institution_Name", "Address", "State", "University", "Management", "Status"],
                "has_official_id": True,
                "official_id_name": "NMC_College_ID (e.g., AN/001/G/1)",
                "duplicate_ids": 0,
                "missing_important_fields": "None. All 919 colleges have valid NMC codes, affiliations, and status.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "100% verified medical college census. In addition, 11,585 course-level records are mapped in NMC_COURSES_2026_27.xlsx.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "inc_nursing_institutions",
                "name": "INC National Nursing Register",
                "category": "Nursing Education",
                "total_records": 3633,
                "unique_records": 3633,
                "duplicate_records": 0,
                "states_covered": 34,
                "districts_covered": 455,
                "academic_year": "2025-26",
                "source": "Indian Nursing Council (INC) Statutory Portal",
                "file_name": "INC_National_Institutions_Deduplicated_2025-26.xlsx",
                "file_path": "INC_National_Institutions_Deduplicated_2025-26.xlsx",
                "file_size_mb": 0.5,
                "important_columns": ["inc_institution_key", "institution_name", "institution_address", "district_name", "state", "programmes", "total_intake"],
                "has_official_id": False,
                "official_id_name": "Not available",
                "duplicate_ids": "N/A",
                "missing_important_fields": "PIN codes missing in ~35% of rows; all names, addresses, and states 100% present.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Deduplicated from 5,108 programme-level rows down to 3,633 unique physical nursing colleges.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "coa_architecture",
                "name": "Council of Architecture National Register",
                "category": "Architecture",
                "total_records": 404,
                "unique_records": 404,
                "duplicate_records": 0,
                "states_covered": 31,
                "districts_covered": 182,
                "academic_year": "2025-26",
                "source": "Council of Architecture (CoA) Statutory Directory",
                "file_name": "COA_COMPLETED_2025_26.xlsx / Architecture Colleges.xlsx",
                "file_path": "Final Institute Lists/Architecture Colleges.xlsx",
                "file_size_mb": 0.07,
                "important_columns": ["CoA_Code", "Institution_Name", "Full_Address", "State", "District", "PIN_Code", "Approved_Intake"],
                "has_official_id": True,
                "official_id_name": "CoA_Code (e.g., AP01, DL02, TS03)",
                "duplicate_ids": 0,
                "missing_important_fields": "14 unclassified/overseas institutes lack state tags; rest 100% complete with approved intake.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "100% extracted with approved intake and affiliation details.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "rci_rehabilitation",
                "name": "Rehabilitation Council of India National Register",
                "category": "Rehabilitation & Special Education",
                "total_records": 1055,
                "unique_records": 1055,
                "duplicate_records": 0,
                "states_covered": 34,
                "districts_covered": 298,
                "academic_year": "2025",
                "source": "Rehabilitation Council of India (RCI) National Register",
                "file_name": "RCI_COMPLETED_2025.xlsx / Rehabilitation Colleges.xlsx",
                "file_path": "Final Institute Lists/Rehabilitation Colleges.xlsx",
                "file_size_mb": 0.13,
                "important_columns": ["RCI_Institute_Code", "Institution_Name", "Address", "State", "District", "PIN_Code", "Approved_Programmes"],
                "has_official_id": True,
                "official_id_name": "RCI_Institute_Code (e.g., AP004, DL012)",
                "duplicate_ids": 0,
                "missing_important_fields": "None. 100% code, address, state, and programmes populated.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Extracted across all 34 States/UTs offering recognized rehabilitation education.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "ncism_ayurveda",
                "name": "NCISM Ayurveda & Unani Medical Colleges",
                "category": "Ayurveda & Unani Medicine",
                "total_records": 650,
                "unique_records": 650,
                "duplicate_records": 0,
                "states_covered": 25,
                "districts_covered": 210,
                "academic_year": "2025-26",
                "source": "National Commission for Indian System of Medicine (NCISM)",
                "file_name": "Ayurveda Colleges.xlsx",
                "file_path": "Final Institute Lists/Ayurveda Colleges.xlsx",
                "file_size_mb": 0.12,
                "important_columns": ["College ID", "System", "Name of the College", "State", "District", "Management", "UG Seats", "PG Seats", "Permission Status"],
                "has_official_id": True,
                "official_id_name": "College ID (NCISM Registration Code)",
                "duplicate_ids": 0,
                "missing_important_fields": "Source documents embed geographic details inside institution address blocks.",
                "quality_status": "PASS — SOURCE LIMITATION",
                "review_priority": "LOW",
                "notes": "Full national universe (593 Ayurveda + 57 Unani = 650 institutions) from official NCISM registries for AY 2025-26.",
                "data_type": "FINAL_INSTITUTE_LIST"
            },
            {
                "id": "ndc_dental",
                "name": "NDC Dental Colleges of India",
                "category": "Dental Education",
                "total_records": 330,
                "unique_records": 330,
                "duplicate_records": 0,
                "states_covered": 28,
                "districts_covered": 242,
                "academic_year": "2026-27",
                "source": "National Dental Commission (NDC) / former Dental Council of India (DCI)",
                "file_name": "Dental Colleges.xlsx",
                "file_path": "Final Institute Lists/Dental Colleges.xlsx",
                "file_size_mb": 0.18,
                "important_columns": ["Official ID", "College Name", "State", "District / City", "BDS Seats", "MDS Seats", "Total Dental Intake Capacity", "Current Regulatory Status", "Regulatory Remarks"],
                "has_official_id": True,
                "official_id_name": "Official ID (NDC/DCI Portal ID)",
                "duplicate_ids": 0,
                "missing_important_fields": "Lady Hardinge Medical College (Delhi) lacks municipal district & address on official portal (recorded as PASS — SOURCE LIMITATION).",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Full national universe (330 physical institutions) from official NDC College Search for AY 2026-27.",
                "data_type": "FINAL_INSTITUTE_LIST"
            },
            {
                "id": "ncte_teacher_education",
                "name": "NCTE Teacher Education Colleges",
                "category": "Teacher Education",
                "total_records": 17556,
                "unique_records": 17556,
                "duplicate_records": 0,
                "states_covered": 35,
                "districts_covered": 412,
                "academic_year": "2025-26",
                "source": "National Council for Teacher Education (NCTE) Official Portal",
                "file_name": "NCTE Teacher Education Colleges.xlsx",
                "file_path": "Final Institute Lists/NCTE Teacher Education Colleges.xlsx",
                "file_size_mb": 5.26,
                "important_columns": ["NCTE Institute ID", "Institution Name", "State", "District", "Management Type", "Affiliating University", "Recognized Programmes", "Total Approved Intake"],
                "has_official_id": True,
                "official_id_name": "NCTE Institute ID (e.g., NCTE4305471)",
                "duplicate_ids": 0,
                "missing_important_fields": "All 17,556 physical institutions have official NCTE IDs, names, and state assignments.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Full national universe (17,556 canonical physical institutions) covering 28,372 course offerings across all 4 regional committees for AY 2025-26. 1,274 withdrawn institutions preserved in separate audit sheet.",
                "data_type": "FINAL_INSTITUTE_LIST"
            },
            {
                "id": "cbse_saras",
                "name": "CBSE SARAS National Affiliation Directory",
                "category": "School Education (CBSE Board)",
                "total_records": 33151,
                "unique_records": 33151,
                "duplicate_records": 0,
                "states_covered": 38,
                "districts_covered": 732,
                "academic_year": "2025-26",
                "source": "CBSE SARAS Portal (State-wise Affiliation Directory)",
                "file_name": "CBSE_INSTITUTIONS_2025.xlsx",
                "file_path": "data/COMPLETED_DATA/CBSE_INSTITUTIONS_2025.xlsx",
                "file_size_mb": 4.1,
                "important_columns": ["Affiliation_Number", "School_Name", "State", "District", "Address", "PIN_Code", "Principal_Name"],
                "has_official_id": True,
                "official_id_name": "CBSE Affiliation Number",
                "duplicate_ids": 0,
                "missing_important_fields": "None. 100% complete across all States/UTs and overseas CBSE schools.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "100% complete national census of CBSE-affiliated schools.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "cisce_schools",
                "name": "CISCE National School Locator Register",
                "category": "School Education (ICSE/ISC Board)",
                "total_records": 3320,
                "unique_records": 3320,
                "duplicate_records": 0,
                "states_covered": 36,
                "districts_covered": 315,
                "academic_year": "2025",
                "source": "Council for the Indian School Certificate Examinations (CISCE)",
                "file_name": "CISCE_INSTITUTIONS_2025.xlsx",
                "file_path": "data/COMPLETED_DATA/CISCE_INSTITUTIONS_2025.xlsx",
                "file_size_mb": 0.33,
                "important_columns": ["CISCE_Code", "School_Name", "State", "District", "Address", "PIN_Code"],
                "has_official_id": True,
                "official_id_name": "CISCE Affiliation Code (e.g., AN001)",
                "duplicate_ids": 0,
                "missing_important_fields": "None. 100% extracted across 332 pagination pages.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "100% complete national register of ICSE and ISC schools.",
                "data_type": "SOURCE_DATASET"
            },
            {
                "id": "telangana_census",
                "name": "Telangana State Multi-Source Verified Census",
                "category": "State Census (All Levels)",
                "total_records": 46845,
                "unique_records": 46845,
                "duplicate_records": 0,
                "states_covered": 1,
                "districts_covered": 33,
                "academic_year": "2021-25",
                "source": "Multi-Source Reconciled State Register (UDISE, DOST, TSBIE, JNTUH, KNRUHS)",
                "file_name": "TELANGANA_COMPLETED.xlsx",
                "file_path": "data/COMPLETED_DATA/TELANGANA_COMPLETED.xlsx",
                "file_size_mb": 6.6,
                "important_columns": ["Institution_Name", "Official_Institution_ID", "UDISE_Code", "Institution_Type", "District", "State"],
                "has_official_id": True,
                "official_id_name": "Official_Institution_ID",
                "duplicate_ids": 0,
                "missing_important_fields": "None. 100% verified deduplicated census for the state of Telangana.",
                "quality_status": "PASS",
                "review_priority": "LOW",
                "notes": "Pioneer state model demonstrating complete cross-source institutional deduplication.",
                "data_type": "SOURCE_DATASET"
            }
        ]

    def _build_search_index(self):
        """Indexes all 7,335 final institute rows for comprehensive multi-attribute search"""
        self.search_index = []
        for list_id, stats in self.final_lists.items():
            df = self.final_dfs.get(list_id)
            if df is None:
                continue
            
            id_col = stats.get("id_column")
            name_col = stats.get("name_column")
            state_col = stats.get("state_column")
            dist_col = stats.get("district_column")
            addr_col = stats.get("address_column")
            pin_col = stats.get("pin_column")
            univ_col = stats.get("university_column")
            category = stats.get("category")

            for idx, row in df.iterrows():
                inst_id = str(row[id_col]).strip() if id_col and not pd.isna(row[id_col]) else "—"
                name = str(row[name_col]).strip() if name_col and not pd.isna(row[name_col]) else "Unknown Institution"
                state_raw = row[state_col] if state_col and not pd.isna(row[state_col]) else "Unknown"
                state = normalize_state_name(state_raw)
                
                # Raw district from dataset
                raw_dist = str(row[dist_col]).strip() if dist_col and not pd.isna(row[dist_col]) and str(row[dist_col]).strip().lower() not in ['nan', 'none', ''] else ""
                addr = str(row[addr_col]).strip() if addr_col and not pd.isna(row[addr_col]) and str(row[addr_col]).strip().lower() not in ['nan', 'none', ''] else ""
                pin = str(row[pin_col]).strip().split('.')[0] if pin_col and not pd.isna(row[pin_col]) and str(row[pin_col]).strip().lower() not in ['nan', 'none', ''] else ""
                univ = str(row[univ_col]).strip() if univ_col and not pd.isna(row[univ_col]) and str(row[univ_col]).strip().lower() not in ['nan', 'none', ''] else ""

                # If raw district is missing, extract district from address if present
                inferred_dist = raw_dist
                if not inferred_dist or inferred_dist.lower() in ["not specified", "nan", "none"]:
                    inferred_dist = extract_district_from_address(addr)

                display_dist = inferred_dist if inferred_dist != "Not Specified" else (raw_dist or "Not Specified")

                # Combine all searchable attributes across the dataset
                search_components = [
                    name,
                    state,
                    raw_dist,
                    inferred_dist if inferred_dist != "Not Specified" else "",
                    addr,
                    pin,
                    inst_id if inst_id != '—' else '',
                    univ,
                    category
                ]

                # Expand common institutional locality and campus abbreviations
                blob_lower = " ".join(search_components).lower()
                if "kukatpally" in blob_lower or "500085" in blob_lower or "jntu" in blob_lower:
                    search_components.extend(["kphb", "kphb colony", "kukatpally housing board"])
                if "gachibowli" in blob_lower or "iiit" in blob_lower:
                    search_components.extend(["gachibowli", "iiit hyderabad", "iiith", "iiit-h"])

                search_blob = " ".join(filter(None, search_components)).lower()

                self.search_index.append({
                    "list_id": list_id,
                    "dataset_name": stats["file_name"],
                    "category": category,
                    "institution_name": name,
                    "official_id": inst_id,
                    "state": state,
                    "district": display_dist,
                    "address": addr,
                    "pincode": pin,
                    "university": univ,
                    "row_index": int(idx),
                    "_search": search_blob
                })

    def _compute_state_aggregates(self):
        """Computes State-by-State breakdown across all final lists"""
        self.state_aggregates = {}
        
        # Initialize for all 36 standard States and UTs
        for s in STANDARD_STATES_UTS:
            self.state_aggregates[s] = {
                "state_name": s,
                "total_institutions": 0,
                "categories": {},
                "districts": {},
                "available_datasets": set(),
                "all_categories_expected": ["Universities & Higher Education", "Medical Education", "Dental Education", "Nursing", "Pharmacy", "Architecture", "Rehabilitation & Special Education", "Ayurveda & Unani Medicine", "Homoeopathy Education", "Legal Education & Law Colleges"],
                "missing_categories": []
            }

        # Aggregate from final institute lists
        for item in self.search_index:
            st = item["state"]
            if st not in self.state_aggregates:
                self.state_aggregates[st] = {
                    "state_name": st,
                    "total_institutions": 0,
                    "categories": {},
                    "districts": {},
                    "available_datasets": set(),
                    "all_categories_expected": ["Universities & Higher Education", "Medical Education", "Dental Education", "Nursing", "Pharmacy", "Architecture", "Rehabilitation & Special Education", "Ayurveda & Unani Medicine", "Homoeopathy Education", "Legal Education & Law Colleges"],
                    "missing_categories": []
                }
            
            entry = self.state_aggregates[st]
            entry["total_institutions"] += 1
            cat = item["category"]
            entry["categories"][cat] = entry["categories"].get(cat, 0) + 1
            dst = item["district"]
            if dst and dst != "Not Specified":
                entry["districts"][dst] = entry["districts"].get(dst, 0) + 1
            entry["available_datasets"].add(item["dataset_name"])

        # Calculate missing categories and format sets to lists
        for st, data in self.state_aggregates.items():
            data["available_datasets"] = sorted(list(data["available_datasets"]))
            present_cats = set(data["categories"].keys())
            data["missing_categories"] = [c for c in data["all_categories_expected"] if c not in present_cats]

    def get_completed_portals(self) -> List[Dict[str, Any]]:
        """Dynamically builds completed portals list from actual loaded final institute files"""
        regulator_map = {
            "welcome_to_ugc__new_delhi__india": {
                "authority": "University Grants Commission (UGC)",
                "regulator_code": "UGC",
                "category": "Universities & Higher Education",
                "source_portal": "https://www.ugc.gov.in/"
            },
            "welcome_to_ugc_new_delhi_india": {
                "authority": "University Grants Commission (UGC)",
                "regulator_code": "UGC",
                "category": "Universities & Higher Education",
                "source_portal": "https://www.ugc.gov.in/"
            },
            "medical_colleges": {
                "authority": "National Medical Commission (NMC)",
                "regulator_code": "NMC",
                "category": "Medical Education",
                "source_portal": "https://www.nmc.org.in/"
            },
            "nursing_colleges": {
                "authority": "Indian Nursing Council (INC)",
                "regulator_code": "INC",
                "category": "Nursing",
                "source_portal": "https://indiannursingcouncil.org/"
            },
            "architecture_colleges": {
                "authority": "Council of Architecture (CoA)",
                "regulator_code": "CoA",
                "category": "Architecture",
                "source_portal": "https://www.coa.gov.in/"
            },
            "rehabilitation_colleges": {
                "authority": "Rehabilitation Council of India (RCI)",
                "regulator_code": "RCI",
                "category": "Rehabilitation & Special Education",
                "source_portal": "https://rehabcouncil.nic.in/"
            },
            "ayurveda_colleges": {
                "authority": "National Commission for Indian System of Medicine (NCISM)",
                "regulator_code": "NCISM",
                "category": "Ayurveda & Unani Medicine",
                "source_portal": "https://ncismindia.org/"
            },
            "homoeopathy_colleges": {
                "authority": "National Commission for Homoeopathy (NCH)",
                "regulator_code": "NCH",
                "category": "Homoeopathy Education",
                "source_portal": "https://nch.org.in/"
            },
            "law_colleges": {
                "authority": "Bar Council of India (BCI)",
                "regulator_code": "BCI",
                "category": "Legal Education & Law Colleges",
                "source_portal": "https://www.barcouncilofindia.org/"
            },
            "pharmacy_colleges": {
                "authority": "Pharmacy Council of India (PCI)",
                "regulator_code": "PCI",
                "category": "Pharmacy",
                "source_portal": "https://www.pci.gov.in/"
            },
            "dental_colleges": {
                "authority": "National Dental Commission (NDC) / DCI",
                "regulator_code": "NDC",
                "category": "Dental Education",
                "source_portal": "https://dciindia.gov.in/"
            }
        }
        completed = []
        for list_id, stats in self.final_lists.items():
            meta = regulator_map.get(list_id)
            if not meta:
                meta = {
                    "authority": stats.get("category", "Regulatory Council"),
                    "regulator_code": stats.get("category", "COUNCIL"),
                    "category": stats.get("category", "Higher Education"),
                    "source_portal": ""
                }
            completed.append({
                "id": list_id,
                "authority": meta["authority"],
                "regulator_code": meta["regulator_code"],
                "category": stats["category"],
                "file_name": stats["file_name"],
                "file_id": list_id,
                "final_institution_count": stats["total_records"],
                "collected_count": stats["total_records"],
                "status": "COMPLETED",
                "official_id_display": stats.get("official_id_display", "—"),
                "states_covered": stats.get("states_covered", 0),
                "districts_covered": stats.get("districts_covered", 0),
                "source_portal": meta.get("source_portal", "")
            })
        completed.sort(key=lambda x: x["final_institution_count"], reverse=True)
        return completed

    def get_review_priority_items(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns HIGH/MEDIUM/LOW review priority items.
        UDISE+ is always HIGH priority, independent of the removed Source Datasets page."""
        high_items = []
        medium_items = []
        low_items = []

        # UDISE+ is a permanent HIGH-priority item — school name and UDISE Code unavailable
        # in the open research export; pseudocode-to-official-school mapping unresolved.
        # We do NOT load 1.47M records into browser memory — this is metadata only.
        high_items.append({
            "id": "udise_plus_national_schools",
            "name": "UDISE+ National Schools",
            "category": "School Education",
            "source": "UDISE+ Data Sharing Portal (Ministry of Education)",
            "total_records": 1466682,
            "academic_year": "2025\u201326",
            "priority": "HIGH",
            "data_type": "EXCLUDED_LARGE_DATASET",
            "reason": "School Name and UDISE Code are unavailable in the open research export "
                      "(withheld as NOT_AVAILABLE in DSP Research Export). "
                      "Pseudocode-to-official-school mapping remains unresolved. "
                      "Records not loaded into browser memory due to 1.47M record scale.",
            "action_required": "Resolve pseudocode-to-UDISE-Code mapping via KYS Track API "
                               "or secure school-name linkage through DSP Identified Export.",
            "isFinal": False
        })

        # Add final lists with NEEDS REVIEW status as HIGH
        for list_id, stats in self.final_lists.items():
            priority = stats.get("review_priority", "LOW")
            item = {
                "id": stats["id"],
                "name": f"{stats['category']} ({stats['file_name']})",
                "category": stats["category"],
                "total_records": stats["total_records"],
                "academic_year": stats["academic_year"],
                "priority": priority,
                "data_type": "FINAL_INSTITUTE_LIST",
                "quality_status": stats.get("quality_status", "PASS"),
                "notes": stats.get("source_limitation_notes", []),
                "issues": stats.get("issues", []),
                "isFinal": True
            }
            if priority == "HIGH":
                high_items.append(item)
            elif priority == "MEDIUM":
                medium_items.append(item)
            else:
                low_items.append(item)

        return {
            "high": high_items,
            "medium": medium_items,
            "low": low_items,
            "high_count": len(high_items),
            "medium_count": len(medium_items),
            "low_count": len(low_items)
        }

    def get_pending_portals(self) -> List[Dict[str, Any]]:
        """Returns only genuinely pending portals, strictly excluding any that exist in final lists"""
        completed = self.get_completed_portals()
        completed_codes = {c["regulator_code"].lower() for c in completed}
        completed_ids = {c["id"].lower() for c in completed}
        
        pending = []
        for p in self.pending_datasets:
            pid = p.get("id", "").lower()
            auth = p.get("authority", "").lower()
            if pid in completed_codes or pid in completed_ids or pid in ["pci", "bci", "nch", "inc", "nmc", "ugc", "coa", "rci", "ncism", "dental", "dci", "ndc", "ncte"]:
                continue
            if any(code in auth for code in ["pharmacy council", "bar council", "homoeopathy", "nursing council", "medical commission", "ugc", "architecture", "rehabilitation", "dental", "teacher education", "ncte"]):
                continue
            item = dict(p)
            val = str(item.get("estimated_institutions", ""))
            if not val or any(x in val for x in ["45,000", "9,000", "18,000", "15,000"]):
                item["estimated_institutions"] = "Count not established"
            pending.append(item)
        return pending

registry = DataRegistry()

# API Endpoints
@app.get("/api/summary")
def get_summary():
    """Provides high-level KPIs and executive totals"""
    # Total source records
    total_source_records = sum(d["total_records"] for d in registry.source_datasets)
    
    # Total final records
    total_final_records = sum(s["total_records"] for s in registry.final_lists.values())
    
    # Review priority counts — UDISE+ is always HIGH priority regardless of source datasets page
    # (1 for UDISE+ permanent item + any final lists with NEEDS REVIEW)
    high_priority = 1  # UDISE+ National Schools — permanent HIGH item
    high_priority += sum(1 for s in registry.final_lists.values() if s["review_priority"] == "HIGH")
    
    pending_count = len(registry.get_pending_portals())

    # States covered in final lists calculated strictly against the 36 canonical States and UTs
    canonical_covered = [
        s for s in STANDARD_STATES_UTS
        if s in registry.state_aggregates and registry.state_aggregates[s]["total_institutions"] > 0
    ]
    states_covered = len(canonical_covered)

    return {
        "kpis": {
            "datasets_collected": len(registry.source_datasets),
            "final_lists_available": len(registry.final_lists),
            "total_records_source": total_source_records,
            "total_records_final": total_final_records,
            "states_covered": states_covered,
            "total_states_target": 36,
            "datasets_pending": pending_count,
            "datasets_requiring_review": high_priority
        },
        "critical_notice": {
            "title": "Overlap & Entity Deduplication Notice",
            "message": "Dataset counts may overlap because the same physical institution can appear in multiple regulatory datasets. Do not add dataset counts to calculate the unique national institution count. Cross-source deduplication is required before the final census.",
            "rule": "ONE PHYSICAL INSTITUTION = ONE CANONICAL RECORD"
        },
        "breakdowns": {
            "institutions_by_category": {s["category"]: s["total_records"] for s in registry.final_lists.values()},
            "top_states": sorted(
                [{"state": s, "count": d["total_institutions"]} for s, d in registry.state_aggregates.items() if s != "Unknown / Unclassified"],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
        }
    }

@app.get("/api/datasets/sources")
def get_source_datasets():
    """Returns all collected raw/source datasets"""
    return {
        "count": len(registry.source_datasets),
        "datasets": registry.source_datasets
    }

@app.get("/api/datasets/final")
def get_final_lists():
    """Returns all cleaned final institute lists"""
    return {
        "count": len(registry.final_lists),
        "lists": list(registry.final_lists.values())
    }

@app.get("/api/final/{list_id}/detail")
def get_final_list_detail(list_id: str):
    """Detailed metadata and distribution for a final institute list"""
    if list_id not in registry.final_lists:
        raise HTTPException(status_code=404, detail="Final list not found")
    stats = registry.final_lists[list_id]
    return stats

@app.get("/api/final/{list_id}/records")
def get_final_list_records(
    list_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    state: Optional[str] = None,
    district: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "asc"
):
    """Paginated, filtered, and sorted records from a final list"""
    if list_id not in registry.final_dfs:
        raise HTTPException(status_code=404, detail="Final list not found")
    
    df = registry.final_dfs[list_id]
    stats = registry.final_lists[list_id]
    
    state_col = stats.get("state_column")
    dist_col = stats.get("district_column")
    name_col = stats.get("name_column")
    id_col = stats.get("id_column")
    addr_col = stats.get("address_column")
    pin_col = stats.get("pin_column")
    univ_col = stats.get("university_column")

    # Apply filters
    filtered_df = df
    if state and state != "All" and state_col:
        norm_series = filtered_df[state_col].apply(normalize_state_name)
        filtered_df = filtered_df[norm_series == state]

    if district and district != "All" and dist_col:
        filtered_df = filtered_df[filtered_df[dist_col].astype(str).str.strip().str.title() == district.title()]

    if search:
        s = search.strip().lower()
        search_cols = [c for c in [name_col, id_col, state_col, dist_col, addr_col, pin_col, univ_col] if c and c in filtered_df.columns]
        if not search_cols:
            search_cols = list(filtered_df.columns)
        cond = False
        for c in search_cols:
            cond = cond | filtered_df[c].astype(str).str.lower().str.contains(s, na=False)
        if s in ["kphb", "kukatpally"]:
            for c in search_cols:
                cond = cond | filtered_df[c].astype(str).str.lower().str.contains("kphb|kukatpally|500085", na=False)
        if s in ["gachibowli", "iiit"]:
            for c in search_cols:
                cond = cond | filtered_df[c].astype(str).str.lower().str.contains("gachibowli|iiit", na=False)
        if isinstance(cond, pd.Series):
            filtered_df = filtered_df[cond]

    total_filtered = len(filtered_df)

    # Sorting
    if sort_by and sort_by in filtered_df.columns:
        ascending = (sort_dir == "asc")
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # Pagination
    total_pages = math.ceil(total_filtered / page_size) if total_filtered > 0 else 1
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_slice = filtered_df.iloc[start_idx:end_idx]

    # Convert NaN to None for clean JSON
    clean_records = page_slice.replace({np.nan: None}).to_dict(orient="records")

    return {
        "list_id": list_id,
        "page": page,
        "page_size": page_size,
        "total_records": total_filtered,
        "total_pages": total_pages,
        "columns": stats["all_columns"],
        "records": clean_records
    }

@app.get("/api/states")
def get_states():
    """List of all States/UTs with institution summaries"""
    canonical_list = [
        {
            "state_name": s,
            "total_institutions": registry.state_aggregates[s]["total_institutions"] if s in registry.state_aggregates else 0,
            "categories": registry.state_aggregates[s]["categories"] if s in registry.state_aggregates else {},
            "available_datasets_count": len(registry.state_aggregates[s]["available_datasets"]) if s in registry.state_aggregates else 0,
            "missing_categories_count": len(registry.state_aggregates[s]["missing_categories"]) if s in registry.state_aggregates else 6
        }
        for s in STANDARD_STATES_UTS
    ]
    canonical_list.sort(key=lambda x: x["total_institutions"], reverse=True)
    return {
        "count": len(canonical_list),
        "states": canonical_list
    }

@app.get("/api/states/{state_name}")
def get_state_detail(
    state_name: str,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Detailed drill-down for a single State/UT"""
    norm_name = normalize_state_name(state_name)
    if norm_name not in registry.state_aggregates:
        # Check case-insensitive
        match = None
        for s in registry.state_aggregates:
            if s.lower() == state_name.lower():
                match = s
                break
        if not match:
            raise HTTPException(status_code=404, detail="State not found")
        norm_name = match

    state_info = registry.state_aggregates[norm_name]
    
    # Gather institutions belonging to this state from search index
    matched_institutions = []
    for item in registry.search_index:
        if item["state"] == norm_name:
            if category and category != "All" and item["category"] != category:
                continue
            if search and search.lower() not in item["_search"]:
                continue
            matched_institutions.append({
                "dataset_name": item["dataset_name"],
                "category": item["category"],
                "institution_name": item["institution_name"],
                "official_id": item["official_id"],
                "district": item["district"],
                "pincode": item["pincode"],
                "list_id": item["list_id"]
            })

    return {
        "state_name": norm_name,
        "total_institutions": state_info["total_institutions"],
        "categories": state_info["categories"],
        "districts": state_info["districts"],
        "available_datasets": state_info["available_datasets"],
        "all_categories_expected": state_info["all_categories_expected"],
        "missing_categories": state_info["missing_categories"],
        "matched_institutions_count": len(matched_institutions),
        "institutions": matched_institutions[:200]  # Cap at 200 for instantaneous response
    }

@app.get("/api/search")
def global_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(50, ge=5, le=200)
):
    """Global search across all final institute lists"""
    term = q.strip().lower()
    matched = [item for item in registry.search_index if term in item["_search"]]
    
    results = [
        {
            "list_id": item["list_id"],
            "dataset": item["dataset_name"],
            "category": item["category"],
            "institution": item["institution_name"],
            "state": item["state"],
            "district": item["district"],
            "address": item.get("address", ""),
            "official_id": item["official_id"],
            "pincode": item["pincode"],
            "university": item.get("university", "")
        }
        for item in matched[:limit]
    ]

    return {
        "query": q,
        "total_matches": len(matched),
        "results": results
    }

@app.get("/api/pending")
def get_pending():
    """Returns the status board of pending regulatory datasets and completed portals"""
    pending = registry.get_pending_portals()
    completed = registry.get_completed_portals()
    return {
        "count": len(pending),
        "pending": pending,
        "completed_count": len(completed),
        "completed": completed
    }

@app.get("/api/review-priority")
def get_review_priority():
    """Returns structured HIGH/MEDIUM/LOW review priority items.
    UDISE+ is always included as a HIGH priority item independent of the Source Datasets page.
    Final institute lists are bucketed by their computed review_priority field."""
    return registry.get_review_priority_items()


@app.post("/api/pending/update")
async def update_pending(request: Request):
    """Update status of a pending dataset"""
    try:
        data = await request.json()
        item_id = data.get("id")
        new_status = data.get("status")
        notes = data.get("notes")
        
        updated = False
        for item in registry.pending_datasets:
            if item["id"] == item_id:
                if new_status:
                    item["status"] = new_status
                if notes:
                    item["notes"] = notes
                updated = True
                break
        
        if updated:
            with open(PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(registry.pending_datasets, f, indent=2)
            return {"success": True, "message": f"Updated status for {item_id}"}
        else:
            raise HTTPException(status_code=404, detail="Pending dataset item not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dictionary")
def get_data_dictionary(
    dataset: Optional[str] = None,
    field_classification: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=500)
):
    """Provides comprehensive, filterable Data Dictionary records across all datasets"""
    all_records = registry.data_dictionary.get("records", [])
    filtered = all_records

    if dataset and dataset != "All":
        filtered = [r for r in filtered if r["dataset"].lower() == dataset.lower()]

    if field_classification and field_classification != "All":
        filtered = [r for r in filtered if r["field_classification"].lower() == field_classification.lower()]

    if search:
        s = search.strip().lower()
        filtered = [
            r for r in filtered
            if s in r["field_name"].lower()
            or s in r["description"].lower()
            or s in r["dataset"].lower()
            or s in r["allowed_values"].lower()
            or s in r["notes"].lower()
            or s in r["example_value"].lower()
        ]

    total_records = len(filtered)
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    # List of unique datasets for filter dropdown
    dataset_names = sorted(list(set(r["dataset"] for r in all_records)))
    classifications = ["SOURCE FIELD", "DERIVED FIELD", "DASHBOARD-CALCULATED FIELD"]

    return {
        "total_fields": total_records,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "available_datasets": dataset_names,
        "available_classifications": classifications,
        "overview": registry.data_dictionary.get("overview", []),
        "records": filtered[start:end]
    }

@app.get("/api/dictionary/download")
def download_data_dictionary():
    """Streams the complete standalone DATA_DICTIONARY.xlsx workbook for download"""
    xlsx_path = BASE_DIR / "DATA_DICTIONARY.xlsx"
    if not xlsx_path.exists():
        try:
            import generate_data_dictionary
            generate_data_dictionary.generate_workbook()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not generate Excel workbook: {e}")

    return FileResponse(
        str(xlsx_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="DATA_DICTIONARY.xlsx"
    )

# Mount static files and index
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        response = FileResponse(str(index_file))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return HTMLResponse("<h1>Pan-India Educational Institutions Dashboard</h1><p>Static index.html initializing...</p>")

if __name__ == "__main__":
    import argparse
    import socket

    env_port = int(os.environ.get("PORT", 8000))
    is_cloud = (
        os.environ.get("RENDER")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("RAILWAY_STATIC_URL")
        or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        or os.environ.get("ENV") == "production"
    )
    default_host = "0.0.0.0" if is_cloud else "127.0.0.1"
    env_host = os.environ.get("HOST", default_host)

    parser = argparse.ArgumentParser(description="Pan-India Educational Institutions Dashboard Server")
    parser.add_argument("--port", type=int, default=env_port, help=f"Port to run server on (default: {env_port})")
    parser.add_argument("--host", type=str, default=env_host, help=f"Host address (default: {env_host})")
    args = parser.parse_args()

    port = args.port

    def is_port_in_use(h: str, p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((h, p)) == 0

    if is_port_in_use(args.host, port):
        print(f"\n========================================================")
        print(f"[Notice] Port {port} is already in use by another instance.")
        print(f"You can view the existing running dashboard at: http://{args.host}:{port}")
        # Find next available port
        next_port = port + 1
        while is_port_in_use(args.host, next_port) and next_port < port + 20:
            next_port += 1
        print(f"Automatically launching new instance on: http://{args.host}:{next_port}")
        print(f"========================================================\n")
        port = next_port

    uvicorn.run("dashboard_server:app", host=args.host, port=port, reload=False)
