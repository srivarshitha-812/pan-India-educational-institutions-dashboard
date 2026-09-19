import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
dict_path = BASE / "data" / "data_dictionary.json"

with open(dict_path, "r", encoding="utf-8") as f:
    d = json.load(f)

dataset_name = "AICTE National Technical & Engineering Institutions Register"
regulator = "All India Council for Technical Education (AICTE)"

# Check if overview entry already exists
existing_ov = [item for item in d.get("overview", []) if "AICTE" in item.get("dataset_name", "")]
if not existing_ov:
    overview_entry = {
        "dataset_name": dataset_name,
        "source_authority": regulator,
        "sector": "Technical & Engineering",
        "academic_year": "2024-2025",
        "as_of_date": "2026-09-19",
        "total_records": "13,085 Final Records",
        "states_covered": "35 / 36 (97.2%)",
        "official_id_field": "Permanent_ID (e.g. 1-6538045) / Current_Application_ID (e.g. 1-44525213207)",
        "fields_documented": 17,
        "schema_reference": "AICTE Official Approved Institutes Server & Facility Directory",
        "notes": "Comprehensive official register of approved Technical and Engineering institutions across India."
    }
    # Insert before Dashboard Common Architecture
    idx = len(d["overview"]) - 1 if d["overview"] and d["overview"][-1].get("dataset_name") == "Dashboard Common Architecture" else len(d["overview"])
    d["overview"].insert(idx, overview_entry)

fields = [
    ("S.No.", "Integer", "REGULATOR-SUPPLIED FIELD", "Yes", "1", "1, 2, 3...", "Sequential index number within the national AICTE roster.", "Assigned during canonical sorting by State A-Z, District A-Z, Name A-Z."),
    ("Permanent_ID", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "1-6538045", "Alphanumeric Permanent ID (e.g. 1-XXXXXXX)", "Official permanent institution identifier assigned by AICTE.", "100% unique primary identifier across canonical roster; 0 duplicates."),
    ("Current_Application_ID", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "1-43664029032", "Alphanumeric Application ID (e.g. 1-XXXXXXXXXXX)", "Current academic year extension-of-approval / application ID assigned by AICTE.", "Tracks current approved session standing."),
    ("Institution_Name", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "SIKKIM MANIPAL INSTITUTE OF TECHNOLOGY", "Institution name text", "Official name of the technical or engineering institution.", "0 missing names across canonical roster."),
    ("State_UT", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Sikkim", "Valid Indian State or Union Territory name", "State or Union Territory where the institution is physically located.", "Normalized to master 36 State/UT taxonomy; 0 missing."),
    ("District", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "EAST SIKKIM", "Administrative District name", "District jurisdiction of the technical institution.", "Official administrative district recorded in AICTE register; 0 missing."),
    ("Address", "String", "REGULATOR-SUPPLIED FIELD", "No", "MAJITAR, RANGPO, EAST SIKKIM , PIN-737136", "Street address / campus location", "Physical campus address of the approved institution.", "Official address text recorded in AICTE directory."),
    ("PIN_Code", "String", "DASHBOARD-STANDARDIZED FIELD", "No", "737136", "6-digit Indian postal code", "Extracted 6-digit postal index number from address string.", "Used for geographic resolution and spatial search where present."),
    ("Institution_Type", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "State Private University", "Central University, State University, Private-Self Financing, Govt, etc.", "Official institution type and governance model recognized by AICTE.", "Captures university, affiliated college, or autonomous institute status."),
    ("Management_Category", "String", "DASHBOARD-STANDARDIZED FIELD", "Yes", "Private", "Government, Private", "High-level management category of the institution.", "Normalized governance category: Government or Private."),
    ("Women_Only", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "N", "Y, N", "Flag indicating whether the institution exclusively admits women.", "Official gender reservation indicator from AICTE directory."),
    ("Minority", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "N", "Y, N", "Flag indicating whether the institution has religious or linguistic minority status.", "Official minority status recognized under constitutional provisions."),
    ("Approval_Status", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "AICTE Approved", "AICTE Approved", "Approval and accreditation standing under AICTE Act.", "Affirms valid approval for technical and engineering programmes."),
    ("Academic_Year", "String", "METADATA FIELD", "Yes", "2024-2025", "YYYY-YYYY", "Academic session of approved directory extract.", "Matches official AICTE extension of approval session."),
    ("Source_URL", "String", "METADATA FIELD", "Yes", "https://facilities.aicte-india.org/dashboard/pages/approvedinstitutes.php", "Valid HTTP/HTTPS URL", "Direct URL to official AICTE approved institutions portal.", "Authoritative Government of India public directory."),
    ("Collection_Date", "String", "METADATA FIELD", "Yes", "2026-09-19", "YYYY-MM-DD", "Date when the record was extracted from the official portal.", "Maintains temporal audit integrity."),
    ("Verification_Status", "String", "METADATA FIELD", "Yes", "Verified Official Record - AICTE Portal", "Verified Official Record - AICTE Portal", "Validation status indicating authentic extraction from official portal.", "Passed automated deduplication and master schema verification.")
]

existing_fields = {r.get("field_name") for r in d.get("records", []) if r.get("dataset") == dataset_name}
new_records = []
for fname, dtype, fclass, freq, exval, allowed, desc, notes in fields:
    if fname not in existing_fields:
        new_records.append({
            "dataset": dataset_name,
            "source_regulator": regulator,
            "academic_year": "2024-2025",
            "field_name": fname,
            "data_type": dtype,
            "field_classification": fclass,
            "is_required": freq,
            "example_value": exval,
            "allowed_values": allowed,
            "description": desc,
            "notes": notes
        })

dash_idx = len(d["records"])
for i, r in enumerate(d["records"]):
    if r.get("dataset") == "Dashboard Common Architecture":
        dash_idx = i
        break

d["records"] = d["records"][:dash_idx] + new_records + d["records"][dash_idx:]
d["total_fields"] = len(d["records"])

with open(dict_path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f"Data dictionary updated! Added {len(new_records)} fields. New total fields: {d['total_fields']}")
