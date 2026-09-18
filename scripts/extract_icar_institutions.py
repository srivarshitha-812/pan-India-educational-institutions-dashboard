"""
ICAR Agricultural Institutions Dataset Extractor
Processes all 4 official ICAR accreditation Excel files and builds final workbook.

Sources (from https://icar.org.in/en/list-accreditation-status-agricultural-universitiescollegesinstitutionprogrammes):
- List-1:  ICAR Accredited Agricultural SAUs/DUs/CAUs Universities, their Colleges and degree programmes
- List-1A: ICAR Accredited Constituent Colleges or Faculties of Agricultural Universities and their programmes
- List-2:  ICAR Accredited Private Colleges Affiliated to SAUs/General Universities (Private and Public)
- List-3:  ICAR Accredited Constituent/Affiliated Colleges of General Universities (Public)

Rules:
  ONE PHYSICAL INSTITUTION = ONE CANONICAL RECORD
  No synthetic data. Every record must trace to an official ICAR source.
"""
import re
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date
from collections import defaultdict

RAW_DIR = Path("data/icar_raw")
OUTPUT_DIR = Path("Final Institute Lists")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_DATE = date.today().isoformat()
SOURCE_URL = "https://icar.org.in/en/list-accreditation-status-agricultural-universitiescollegesinstitutionprogrammes"
PUBLICATION_DATE = "2024-2026 (latest available on icar.org.in as of 2026-09-18)"

# ─────────────────────────────────────────────────────────────────────────────
# STATE INFERENCE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

STATE_KEYWORDS = {
    "Andhra Pradesh": ["andhra pradesh", "ap ", "guntur", "visakhapatnam", "vizag", "tirupati", "kurnool",
                       "anantapur", "nellore", "vijayawada", "bapatla", "lam"],
    "Arunachal Pradesh": ["arunachal", "itanagar", "nirjuli"],
    "Assam": ["assam", "jorhat", "guwahati", "biswanath", "chariali", "golaghat"],
    "Bihar": ["bihar", "sabour", "patna", "purnea", "saharsa", "kisanganj", "dumraon",
              "noorsarai", "agwanpur", "bhagalpur"],
    "Chhattisgarh": ["chhattisgarh", "raipur", "durg", "bilaspur", "iga"],
    "Goa": ["goa"],
    "Gujarat": ["gujarat", "anand", "junagarh", "junagadh", "gandhinagar", "navsari", "sardar krushinagar", "dantiwada",
                "vadodara", "ahmedabad", "surat", "amreli"],
    "Haryana": ["haryana", "hisar", "bawal", "rohtak", "sirsa", "gurugram", "faridabad"],
    "Himachal Pradesh": ["himachal", "palampur", "kangra", "solan", "chaudhary", "sirmour", "sirmaur", "baru sahib", "h.p"],
    "Jharkhand": ["jharkhand", "ranchi", "kanke", "khunti", "dumka"],
    "Karnataka": ["karnataka", "bengaluru", "bangalore", "bidar", "dharwad", "hassan",
                  "mandya", "raichur", "shimoga", "shivamogga", "vijayapur", "bagalkot",
                  "mangaluru", "hubli", "davanagere", "mysuru", "mysore", "ranebennur",
                  "arabhavi", "mudhol", "ilkal"],
    "Kerala": ["kerala", "thrissur", "vellayani", "vellanikkara", "padannakkad",
               "mannuthy", "tavanur", "tavanur", "veldnikkara", "kumarakom",
               "kerala university", "kufos", "kvasu", "fisheries", "ocean studies"],
    "Madhya Pradesh": ["madhya pradesh", "mp,", " m.p", "satna", "jabalpur", "gwalior", "bhopal",
                       "sehore", "tikamgarh", "ganjbasoda", "chitrakoot", "rewa",
                       "jnkvv", "rkdf", "itm gwalior"],
    "Maharashtra": ["maharashtra", "pune", "nagpur", "akola", "rahuri", "kolhapur",
                    "parbhani", "latur", "wardha", "osmanabad", "solapur", "dhule",
                    "mahatma phule", "dapoli", "vasad", "vasantrao"],
    "Manipur": ["manipur", "imphal"],
    "Meghalaya": ["meghalaya", "shillong", "umiam", "barapani"],
    "Mizoram": ["mizoram", "aizawl"],
    "Nagaland": ["nagaland", "kohima", "medziphema"],
    "Odisha": ["odisha", "bhubaneswar", "bhuvaneshwar", "berhampur", "sambalpur",
               "baripada", "paralakhemundi", "srikakulam", "odisha university"],
    "Punjab": ["punjab", "ludhiana", "bathinda", "gurdaspur", "kapurthala", "amritsar", "phagwara"],
    "Rajasthan": ["rajasthan", "bikaner", "udaipur", "jhalawar", "swai madhopur",
                  "bharatpur", "sri ganganagar", "jaipur", "kota", "sriganganagar"],
    "Sikkim": ["sikkim", "gangtok", "ravangla"],
    "Tamil Nadu": ["tamil nadu", "coimbatore", "dindigul", "vellore", "erode",
                   "krishnagiri", "dharmapuri", "madurai", "trichy", "tiruchirapalli",
                   "thiruvannamalai", "ranipet", "annamalai", "pollachi",
                   "thanjavur", "virudhunagar", "namakkal", "chengalpattu",
                   "mettuplayam", "radhapuram", "tirunelveli", "thoothukudi"],
    "Telangana": ["telangana", "hyderabad", "warangal", "rajendranagar",
                  "nizamabad", "malla reddy university", "secunderabad"],
    "Tripura": ["tripura", "agartala", "lembucherra"],
    "Uttar Pradesh": ["uttar pradesh", "up ", " up,", "lucknow", "kanpur", "varanasi",
                      "banaras", "faizabad", "gorakhpur", "meerut", "mathura",
                      "moradabad", "jaunpur", "pant nagar", "pantnagar",
                      "purvanchal", "narendra dev", "bhu", "jhansi", "banda"],
    "Uttarakhand": ["uttarakhand", "uttaranchal", "pantnagar", "pauri",
                    "garhwal", "hbg", "dehradun"],
    "West Bengal": ["west bengal", "mohanpur", "kalyani", "sriniketan",
                    "birbhum", "purba", "nadia", "visva bharti"],
    "Andaman and Nicobar Islands": ["andaman", "nicobar", "port blair"],
    "Chandigarh": ["chandigarh"],
    "Delhi": ["delhi", "new delhi"],
    "Jammu and Kashmir": ["jammu", "kashmir", "srinagar", "katra"],
    "Ladakh": ["ladakh", "leh"],
    "Puducherry": ["puducherry", "pondicherry", "karaikal"]
}

def infer_state(text: str) -> str:
    """Infer Indian state from free-text institution/address.
    Uses word-boundary pattern matching to avoid false positives
    (e.g. 'tura' inside 'horticulture' / 'agricultural').
    """
    if not text or str(text).strip().lower() in ('nan', 'none', ''):
        return "Not Specified"
    t = str(text).lower()
    for state, keywords in STATE_KEYWORDS.items():
        for kw in keywords:
            kw_l = kw.lower().strip()
            if len(kw_l) < 4:
                # Very short keywords: require exact word boundary
                pattern = r'\b' + re.escape(kw_l) + r'\b'
            else:
                # Longer keywords: must not be preceded or followed by alpha chars
                pattern = r'(?<![a-z])' + re.escape(kw_l) + r'(?![a-z])'
            if re.search(pattern, t):
                return state
    return "Not Specified"

def clean_text(val) -> str:
    """Clean text: remove bullet chars, normalize whitespace."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = str(val)
    # Remove bullet characters
    s = re.sub(r'[•\uf0b7\u2022\ufffd\xa0]', ' ', s)
    # Normalize whitespace but preserve meaningful newlines for programme lists
    s = re.sub(r'[ \t]+', ' ', s).strip()
    return s

def clean_name(val) -> str:
    """Clean institution/university name."""
    s = clean_text(val)
    # Remove trailing commas/periods/spaces
    s = re.sub(r'[,\.]+$', '', s).strip()
    return s

def extract_state_from_name(name: str, extra: str = "") -> str:
    """Try to extract state from institution name and extra context."""
    combined = name + " " + extra
    st = infer_state(combined)
    return st

def normalise_period(val) -> str:
    """Normalise accreditation period text."""
    s = clean_text(val)
    s = re.sub(r'\s+', ' ', s).strip()
    return s if s else "Not Stated"

def extract_programmes_flat(val) -> str:
    """Flatten multi-line programme cell to semicolon-separated."""
    s = clean_text(val)
    if not s or s == "_":
        return ""
    lines = [l.strip() for l in re.split(r'[\n\r]+', s) if l.strip() and l.strip() != "_"]
    return "; ".join(lines) if lines else ""

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_list1(path: Path) -> tuple[list, list]:
    """
    List-1: SAUs/DUs/CAUs Universities with constituent colleges.
    Sheet: 'Govt Accre Universities'
    Columns: [Sl.No., University, Grade, Accred Period, College, UG, PG, PhD]
    University fills downward; College row may have university blank.
    Returns: (institutions, programmes)
    """
    df = pd.read_excel(path, sheet_name="Govt Accre Universities", header=None)
    
    institutions = []
    programmes = []
    seen_colleges = set()

    # Headers at row 2 (index 2), data from row 3 (index 3)
    current_univ = ""
    current_grade = ""
    current_period = ""
    serial = 0

    for idx, row in df.iterrows():
        if idx < 3:
            continue  # Skip title and header rows

        sno = clean_text(row.get(0, ""))
        univ_raw = clean_text(row.get(1, ""))
        grade_raw = clean_text(row.get(2, ""))
        period_raw = clean_text(row.get(3, ""))
        college_raw = clean_text(row.get(4, ""))
        ug_raw = row.get(5, "")
        pg_raw = row.get(6, "")
        phd_raw = row.get(7, "")

        # Update university context when present
        if univ_raw and univ_raw.lower() not in ('nan', ''):
            current_univ = clean_name(univ_raw)
        if grade_raw and grade_raw.lower() not in ('nan', ''):
            current_grade = grade_raw
        if period_raw and period_raw.lower() not in ('nan', ''):
            current_period = normalise_period(period_raw)

        college_name = clean_name(college_raw)

        # Skip rows without a college name
        if not college_name or college_name.lower() in ('nan', '', 'college'):
            continue

        # Skip footnote rows
        if college_name.startswith("*") or college_name.lower().startswith("note") or len(college_name) < 5:
            continue

        # Build dedup key
        dedup_key = (current_univ.lower().strip(), college_name.lower().strip())
        is_duplicate = dedup_key in seen_colleges
        if not is_duplicate:
            seen_colleges.add(dedup_key)

        state = extract_state_from_name(college_name, current_univ)
        serial += 1

        ug = extract_programmes_flat(ug_raw)
        pg = extract_programmes_flat(pg_raw)
        phd = extract_programmes_flat(phd_raw)
        all_progs = "; ".join(filter(None, [ug, pg, phd]))

        inst = {
            "ICAR_Serial": serial,
            "Source_List": "List-1",
            "Source_List_Title": "ICAR Accredited Agricultural SAUs/DUs/CAUs Universities, Colleges and Programmes",
            "Institution_Type": "Constituent College",
            "Institution_Category": "Agricultural University Constituent College (SAU/DU/CAU)",
            "Institution_Name": college_name,
            "University_Name": current_univ,
            "Affiliation": current_univ,
            "Accreditation_Grade": current_grade,
            "Accreditation_Period": current_period,
            "Accreditation_Status": "Accredited",
            "State": state,
            "District": "Not Specified",
            "Address": college_name,
            "PIN_Code": "",
            "UG_Programmes": ug,
            "PG_Programmes": pg,
            "PhD_Programmes": phd,
            "Source_Document": "List of ICAR Accredited Agricultural SAUs DUs CAUs Universities their Colleges and degree programmes-List 1.xlsx",
            "Source_URL": SOURCE_URL,
            "Publication_Date": PUBLICATION_DATE,
            "Collection_Date": COLLECTION_DATE,
            "Is_Duplicate": "YES" if is_duplicate else "NO",
            "Duplicate_Reason": "Same college appeared multiple times in List-1" if is_duplicate else "",
        }
        institutions.append(inst)

        # Programme records
        for prog_type, prog_text in [("UG", ug), ("PG", pg), ("PhD", phd)]:
            if prog_text:
                for prog in [p.strip() for p in prog_text.split(";") if p.strip()]:
                    programmes.append({
                        "Source_List": "List-1",
                        "Institution_Name": college_name,
                        "University_Name": current_univ,
                        "State": state,
                        "Programme_Level": prog_type,
                        "Programme_Name": prog,
                        "Accreditation_Period": current_period,
                        "Accreditation_Grade": current_grade,
                    })

    return institutions, programmes


def extract_list1a(path: Path) -> tuple[list, list]:
    """
    List-1A: Constituent Colleges/Faculties of Agricultural Universities.
    Sheet: 'Final List'
    Columns: [S.No., Name of College/University, Period, Bachelor, Master, PhD]
    """
    df = pd.read_excel(path, sheet_name="Final List", header=None)
    
    institutions = []
    programmes = []
    serial = 0

    for idx, row in df.iterrows():
        if idx < 2:
            continue  # Skip title and header

        sno = clean_text(row.get(0, ""))
        name_raw = clean_text(row.get(1, ""))
        period_raw = clean_text(row.get(2, ""))
        ug_raw = row.get(3, "")
        pg_raw = row.get(4, "")
        phd_raw = row.get(5, "")

        name = clean_name(name_raw)
        if not name or name.lower() in ('nan', '') or name.startswith("*"):
            continue
        if not sno or not any(c.isdigit() for c in str(sno)):
            continue

        period = normalise_period(period_raw)
        state = extract_state_from_name(name)
        serial += 1

        ug = extract_programmes_flat(ug_raw)
        pg = extract_programmes_flat(pg_raw)
        phd = extract_programmes_flat(phd_raw)

        inst = {
            "ICAR_Serial": serial,
            "Source_List": "List-1A",
            "Source_List_Title": "ICAR Accredited Constituent Colleges/Faculties of Agricultural Universities",
            "Institution_Type": "Constituent College / Faculty",
            "Institution_Category": "Constituent College or Faculty of Agricultural University",
            "Institution_Name": name,
            "University_Name": name,  # In 1A, the college IS the unit (e.g., Faculty of Fisheries)
            "Affiliation": "",
            "Accreditation_Grade": "",
            "Accreditation_Period": period,
            "Accreditation_Status": "Accredited",
            "State": state,
            "District": "Not Specified",
            "Address": name,
            "PIN_Code": "",
            "UG_Programmes": ug,
            "PG_Programmes": pg,
            "PhD_Programmes": phd,
            "Source_Document": "List of ICAR Accredited Constituent Colleges or Faculties of Agricultural Universities and their programmes-List-1A.xlsx",
            "Source_URL": SOURCE_URL,
            "Publication_Date": PUBLICATION_DATE,
            "Collection_Date": COLLECTION_DATE,
            "Is_Duplicate": "NO",
            "Duplicate_Reason": "",
        }
        institutions.append(inst)

        for prog_type, prog_text in [("UG", ug), ("PG", pg), ("PhD", phd)]:
            if prog_text:
                for prog in [p.strip() for p in prog_text.split(";") if p.strip()]:
                    programmes.append({
                        "Source_List": "List-1A",
                        "Institution_Name": name,
                        "University_Name": name,
                        "State": state,
                        "Programme_Level": prog_type,
                        "Programme_Name": prog,
                        "Accreditation_Period": period,
                        "Accreditation_Grade": "",
                    })

    return institutions, programmes


def extract_list2_or_3(path: Path, list_name: str, sheet: str,
                       list_title: str, inst_category: str,
                       inst_type: str, doc_filename: str,
                       header_skip: int = 4) -> tuple[list, list]:
    """
    List-2 and List-3: Affiliated/Constituent Colleges of SAUs/General Universities.
    Columns: [S.No., University, Period, College, Bachelor, Master, PhD]
    University fills downward; College column is col 3 (List-2/3).
    """
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    
    institutions = []
    programmes = []
    serial = 0

    current_univ = ""
    current_period = ""

    for idx, row in df.iterrows():
        if idx < header_skip:
            continue

        sno = clean_text(row.get(0, ""))
        univ_raw = clean_text(row.get(1, ""))
        period_raw = clean_text(row.get(2, ""))
        college_raw = clean_text(row.get(3, ""))
        ug_raw = row.get(4, "")
        pg_raw = row.get(5, "")
        phd_raw = row.get(6, "")

        # Update university/period context when present
        if univ_raw and univ_raw.lower() not in ('nan', ''):
            current_univ = clean_name(univ_raw)
        if period_raw and period_raw.lower() not in ('nan', ''):
            current_period = normalise_period(period_raw)

        college_name = clean_name(college_raw) if college_raw else ""
        ug = extract_programmes_flat(ug_raw)
        pg = extract_programmes_flat(pg_raw)
        phd = extract_programmes_flat(phd_raw)

        # Determine physical institution
        # If college column is blank but there are programmes, the university itself is the institution
        if not college_name and (ug or pg or phd):
            institution_name = current_univ
            affiliation = ""
        elif college_name and college_name.lower() not in ('nan', '', 'college '):
            institution_name = college_name
            affiliation = current_univ
        else:
            continue  # No usable institution name

        # Skip footnote / header rows
        if institution_name.startswith("*") or institution_name.lower().startswith("note") or len(institution_name) < 5:
            continue
        if not (ug or pg or phd):
            # No programmes listed - still record if it's a named college
            if not college_name:
                continue

        state = extract_state_from_name(institution_name, current_univ)
        serial += 1

        inst = {
            "ICAR_Serial": serial,
            "Source_List": list_name,
            "Source_List_Title": list_title,
            "Institution_Type": inst_type,
            "Institution_Category": inst_category,
            "Institution_Name": institution_name,
            "University_Name": current_univ,
            "Affiliation": affiliation,
            "Accreditation_Grade": "",
            "Accreditation_Period": current_period,
            "Accreditation_Status": "Accredited",
            "State": state,
            "District": "Not Specified",
            "Address": institution_name,
            "PIN_Code": "",
            "UG_Programmes": ug,
            "PG_Programmes": pg,
            "PhD_Programmes": phd,
            "Source_Document": doc_filename,
            "Source_URL": SOURCE_URL,
            "Publication_Date": PUBLICATION_DATE,
            "Collection_Date": COLLECTION_DATE,
            "Is_Duplicate": "NO",
            "Duplicate_Reason": "",
        }
        institutions.append(inst)

        for prog_type, prog_text in [("UG", ug), ("PG", pg), ("PhD", phd)]:
            if prog_text:
                for prog in [p.strip() for p in prog_text.split(";") if p.strip()]:
                    programmes.append({
                        "Source_List": list_name,
                        "Institution_Name": institution_name,
                        "University_Name": current_univ,
                        "State": state,
                        "Programme_Level": prog_type,
                        "Programme_Name": prog,
                        "Accreditation_Period": current_period,
                        "Accreditation_Grade": "",
                    })

    return institutions, programmes


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-LIST DEDUPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def cross_dedup(institutions: list) -> tuple[list, list]:
    """
    Cross-list deduplication using (normalised_college_name, state) as key.
    Returns: (canonical_institutions, reconciliation_audit)
    """
    seen = {}
    reconciliation = []
    canonical = []

    for i, inst in enumerate(institutions):
        name_key = re.sub(r'\s+', ' ', inst["Institution_Name"].lower().strip())
        # Remove common suffixes for matching
        name_key_stripped = re.sub(r',\s*(thrissur|coimbatore|etc\.?|.*)', '', name_key).strip()
        state_key = inst["State"].lower()
        univ_key = re.sub(r'\s+', ' ', inst["University_Name"].lower().strip())[:40]

        key = (name_key_stripped, state_key)
        alt_key = (name_key, state_key)

        matched_key = None
        if key in seen:
            matched_key = key
        elif alt_key in seen:
            matched_key = alt_key

        if matched_key:
            orig = seen[matched_key]
            reconciliation.append({
                "Source_Row_Index": i + 1,
                "Source_List": inst["Source_List"],
                "Institution_Name": inst["Institution_Name"],
                "University_Name": inst["University_Name"],
                "State": inst["State"],
                "Decision": "DUPLICATE",
                "Canonical_Row_Index": orig["_row_idx"] + 1,
                "Canonical_List": orig["Source_List"],
                "Canonical_Institution": orig["Institution_Name"],
                "Match_Key": str(matched_key),
                "Duplicate_Reason": f"Same institution name+state in {orig['Source_List']} and {inst['Source_List']}"
            })
            inst["Is_Duplicate"] = "YES"
            inst["Duplicate_Reason"] = f"Cross-list duplicate: already in {orig['Source_List']}"
        else:
            seen[key] = {**inst, "_row_idx": i}
            seen[alt_key] = {**inst, "_row_idx": i}
            reconciliation.append({
                "Source_Row_Index": i + 1,
                "Source_List": inst["Source_List"],
                "Institution_Name": inst["Institution_Name"],
                "University_Name": inst["University_Name"],
                "State": inst["State"],
                "Decision": "CANONICAL",
                "Canonical_Row_Index": i + 1,
                "Canonical_List": inst["Source_List"],
                "Canonical_Institution": inst["Institution_Name"],
                "Match_Key": str(key),
                "Duplicate_Reason": ""
            })
            inst["_row_idx"] = len(canonical)
            canonical.append(inst)

    return canonical, reconciliation


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("ICAR AGRICULTURAL INSTITUTIONS EXTRACTOR")
print("=" * 70)

all_raw = []
all_programmes = []

# List-1
print("\n[1/4] Extracting List-1: SAUs/DUs/CAUs Universities and Constituent Colleges...")
list1_insts, list1_progs = extract_list1(RAW_DIR / "ICAR_List1_SAUs_DUs_CAUs_Universities_Colleges_Programmes.xlsx")
print(f"  Raw records: {len(list1_insts)}")
all_raw.extend(list1_insts)
all_programmes.extend(list1_progs)

# List-1A
print("\n[2/4] Extracting List-1A: Constituent Colleges/Faculties of Agricultural Universities...")
list1a_insts, list1a_progs = extract_list1a(RAW_DIR / "ICAR_List1A_Constituent_Colleges_Faculties.xlsx")
print(f"  Raw records: {len(list1a_insts)}")
all_raw.extend(list1a_insts)
all_programmes.extend(list1a_progs)

# List-2
print("\n[3/4] Extracting List-2: Private/Public Affiliated Colleges to SAUs/General Universities...")
list2_insts, list2_progs = extract_list2_or_3(
    path=RAW_DIR / "ICAR_List2_Private_Public_Affiliated_Colleges.xlsx",
    list_name="List-2",
    sheet="Sheet1",
    list_title="ICAR Accredited Private Colleges Affiliated to SAUs/General Universities (Private and Public)",
    inst_category="Affiliated Agricultural College (Private/Public) to SAU/General University",
    inst_type="Affiliated College",
    doc_filename="List of ICAR Accredited Private Colleges Affliated to SAUs General Universities (Private and Public)-List-II.xlsx",
    header_skip=4
)
print(f"  Raw records: {len(list2_insts)}")
all_raw.extend(list2_insts)
all_programmes.extend(list2_progs)

# List-3
print("\n[4/4] Extracting List-3: Constituent/Affiliated Colleges of General Universities (Public)...")
list3_insts, list3_progs = extract_list2_or_3(
    path=RAW_DIR / "ICAR_List3_Constituent_Affiliated_General_Universities_Public.xlsx",
    list_name="List-3",
    sheet="Sheet1",
    list_title="ICAR Accredited Constituent/Affiliated Colleges of General Universities (Public)",
    inst_category="Constituent/Affiliated College of General University (Public)",
    inst_type="Constituent / Affiliated College",
    doc_filename="List of ICAR Accredited Constituent affiliated Colleges Programmes of General Universities (Public)- List-III.xlsx",
    header_skip=4
)
print(f"  Raw records: {len(list3_insts)}")
all_raw.extend(list3_insts)
all_programmes.extend(list3_progs)

print(f"\nTotal raw records (all lists): {len(all_raw)}")
print(f"Total programme records: {len(all_programmes)}")

# Cross-list deduplication
print("\nRunning cross-list deduplication...")
canonical_insts, reconciliation = cross_dedup(all_raw)
duplicates = [inst for inst in all_raw if inst.get("Is_Duplicate") == "YES"]

print(f"  Canonical institutions: {len(canonical_insts)}")
print(f"  Duplicate records removed: {len(duplicates)}")

# Assign final ICAR serial numbers and sort
for i, inst in enumerate(canonical_insts, 1):
    inst["ICAR_Serial"] = i

# Sort by State → Institution_Name
canonical_insts.sort(key=lambda x: (x["State"], x["Institution_Name"]))

# Reassign ICAR_Serial after sorting
for i, inst in enumerate(canonical_insts, 1):
    inst["ICAR_Serial"] = i

# ─────────────────────────────────────────────────────────────────────────────
# STATE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

state_counts = defaultdict(lambda: defaultdict(int))
for inst in canonical_insts:
    st = inst["State"]
    cat = inst["Institution_Category"]
    state_counts[st]["Total"] += 1
    state_counts[st][cat] += 1

state_summary_rows = []
for state in sorted(state_counts.keys()):
    row = {"State": state, "Total_Institutions": state_counts[state]["Total"]}
    for k, v in state_counts[state].items():
        if k != "Total":
            row[k] = v
    state_summary_rows.append(row)

# ─────────────────────────────────────────────────────────────────────────────
# SOURCE LISTS RECONCILIATION SHEET
# ─────────────────────────────────────────────────────────────────────────────

source_summary = [
    {
        "Source_List": "List-1",
        "Title": "ICAR Accredited Agricultural SAUs/DUs/CAUs Universities, Colleges and Programmes",
        "Filename": "ICAR_List1_SAUs_DUs_CAUs_Universities_Colleges_Programmes.xlsx",
        "Raw_Records": len(list1_insts),
        "Category": "Constituent Colleges under Agricultural Universities",
        "Source_URL": SOURCE_URL,
        "Publication_Date": PUBLICATION_DATE,
        "Collection_Date": COLLECTION_DATE,
    },
    {
        "Source_List": "List-1A",
        "Title": "ICAR Accredited Constituent Colleges/Faculties of Agricultural Universities",
        "Filename": "ICAR_List1A_Constituent_Colleges_Faculties.xlsx",
        "Raw_Records": len(list1a_insts),
        "Category": "Constituent Colleges/Faculties (non-SAU agricultural universities)",
        "Source_URL": SOURCE_URL,
        "Publication_Date": PUBLICATION_DATE,
        "Collection_Date": COLLECTION_DATE,
    },
    {
        "Source_List": "List-2",
        "Title": "ICAR Accredited Private/Public Affiliated Colleges to SAUs/General Universities",
        "Filename": "ICAR_List2_Private_Public_Affiliated_Colleges.xlsx",
        "Raw_Records": len(list2_insts),
        "Category": "Affiliated Agricultural Colleges (Private/Public)",
        "Source_URL": SOURCE_URL,
        "Publication_Date": PUBLICATION_DATE,
        "Collection_Date": COLLECTION_DATE,
    },
    {
        "Source_List": "List-3",
        "Title": "ICAR Accredited Constituent/Affiliated Colleges of General Universities (Public)",
        "Filename": "ICAR_List3_Constituent_Affiliated_General_Universities_Public.xlsx",
        "Raw_Records": len(list3_insts),
        "Category": "Constituent/Affiliated Agricultural Colleges under General Universities",
        "Source_URL": SOURCE_URL,
        "Publication_Date": PUBLICATION_DATE,
        "Collection_Date": COLLECTION_DATE,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA QUALITY / VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

issues = []
for inst in canonical_insts:
    if inst["State"] == "Not Specified":
        issues.append({
            "ICAR_Serial": inst["ICAR_Serial"],
            "Institution_Name": inst["Institution_Name"],
            "Issue": "State could not be inferred",
            "Severity": "MEDIUM",
            "Field": "State",
        })
    if not inst["UG_Programmes"] and not inst["PG_Programmes"] and not inst["PhD_Programmes"]:
        issues.append({
            "ICAR_Serial": inst["ICAR_Serial"],
            "Institution_Name": inst["Institution_Name"],
            "Issue": "No programmes listed",
            "Severity": "LOW",
            "Field": "Programmes",
        })

print(f"\nData Quality Issues: {len(issues)}")
no_state = sum(1 for inst in canonical_insts if inst["State"] == "Not Specified")
print(f"  Institutions with unknown state: {no_state}")

# ─────────────────────────────────────────────────────────────────────────────
# METHODOLOGY SHEET
# ─────────────────────────────────────────────────────────────────────────────

methodology = [
    {"Item": "Project", "Detail": "Pan-India Educational Institutions Dashboard"},
    {"Item": "Dataset Name", "Detail": "ICAR Agricultural & Allied Institutions"},
    {"Item": "Regulator", "Detail": "Indian Council of Agricultural Research (ICAR)"},
    {"Item": "Primary Source URL", "Detail": SOURCE_URL},
    {"Item": "Secondary Source URL", "Detail": "https://www.icar.org.in/en/node/23694"},
    {"Item": "Sources Processed", "Detail": "4 official ICAR Excel files (List-1, List-1A, List-2, List-3)"},
    {"Item": "Raw Records", "Detail": str(len(all_raw))},
    {"Item": "Canonical Physical Institutions", "Detail": str(len(canonical_insts))},
    {"Item": "Duplicates Removed", "Detail": str(len(duplicates))},
    {"Item": "Programme Records", "Detail": str(len(all_programmes))},
    {"Item": "Institution Count Rule", "Detail": "ONE PHYSICAL INSTITUTION = ONE CANONICAL RECORD"},
    {"Item": "State Inference Method", "Detail": "Keyword matching against institution name, college name, and university name"},
    {"Item": "Deduplication Method", "Detail": "Normalised (institution_name, state) key across all 4 lists"},
    {"Item": "Scope: Research Institutes", "Detail": "ICAR research institutes (not colleges) are NOT included. Scope is limited to ICAR-accredited teaching institutions (colleges, faculties, constituent colleges)."},
    {"Item": "Scope: ICAR Deemed Universities", "Detail": "ICAR Deemed Universities appear as universities in List-1 (their colleges are included as constituent colleges)."},
    {"Item": "Collection Date", "Detail": COLLECTION_DATE},
    {"Item": "Data Synthetic?", "Detail": "NO - all records sourced from official ICAR Excel files"},
    {"Item": "Excluded Records", "Detail": "Footnotes, header rows, blank rows, rows with no institution name"},
]

# ─────────────────────────────────────────────────────────────────────────────
# WRITE OUTPUT WORKBOOK
# ─────────────────────────────────────────────────────────────────────────────

output_path = OUTPUT_DIR / "ICAR Agricultural & Allied Institutions.xlsx"
print(f"\nWriting workbook: {output_path}")

ROSTER_COLS = [
    "ICAR_Serial", "Source_List", "Institution_Type", "Institution_Category",
    "Institution_Name", "University_Name", "Affiliation",
    "Accreditation_Grade", "Accreditation_Period", "Accreditation_Status",
    "State", "District", "Address", "PIN_Code",
    "UG_Programmes", "PG_Programmes", "PhD_Programmes",
    "Source_Document", "Source_URL", "Publication_Date", "Collection_Date",
    "Is_Duplicate", "Duplicate_Reason"
]

PROG_COLS = [
    "Source_List", "Institution_Name", "University_Name", "State",
    "Programme_Level", "Programme_Name", "Accreditation_Period", "Accreditation_Grade"
]

df_roster = pd.DataFrame(canonical_insts)[[c for c in ROSTER_COLS if c in [k for r in canonical_insts for k in r.keys()]]]
df_roster = df_roster.reindex(columns=ROSTER_COLS, fill_value="")

df_progs = pd.DataFrame(all_programmes).reindex(columns=PROG_COLS, fill_value="")

df_reconcile = pd.DataFrame(reconciliation)
df_sources = pd.DataFrame(source_summary)
df_state = pd.DataFrame(state_summary_rows).fillna(0)
df_quality = pd.DataFrame(issues) if issues else pd.DataFrame(columns=["ICAR_Serial", "Institution_Name", "Issue", "Severity", "Field"])
df_method = pd.DataFrame(methodology)

# Duplicates/excluded
all_raw_df = pd.DataFrame(all_raw).reindex(columns=ROSTER_COLS, fill_value="")
df_excluded = all_raw_df[all_raw_df["Is_Duplicate"] == "YES"].reset_index(drop=True)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df_roster.to_excel(writer, sheet_name="Institutions Roster", index=False)
    df_progs.to_excel(writer, sheet_name="Programmes & Accreditation", index=False)
    df_sources.to_excel(writer, sheet_name="Source Lists Reconciliation", index=False)
    df_excluded.to_excel(writer, sheet_name="Excluded or Historical Records", index=False)
    df_state.to_excel(writer, sheet_name="State Summary", index=False)
    df_quality.to_excel(writer, sheet_name="Data Quality & Validation", index=False)
    df_method.to_excel(writer, sheet_name="Source & Methodology", index=False)

print(f"Workbook written successfully.")
print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
print(f"  Total raw records extracted:         {len(all_raw)}")
print(f"  Cross-list duplicates removed:       {len(duplicates)}")
print(f"  Canonical physical institutions:     {len(canonical_insts)}")
print(f"  Programme records:                   {len(all_programmes)}")
print(f"  States/UTs represented:              {len(state_counts)}")
print()
print("Institutions by State/UT:")
for row in sorted(state_summary_rows, key=lambda x: -x["Total_Institutions"]):
    print(f"  {row['State']:<35}: {row['Total_Institutions']}")
print()
print("Institutions by Category:")
cat_counts = defaultdict(int)
for inst in canonical_insts:
    cat_counts[inst["Institution_Category"]] += 1
for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cnt:>4}  {cat}")
print()
print(f"Output: {output_path}")
