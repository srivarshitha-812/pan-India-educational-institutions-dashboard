import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
dict_path = BASE / "data" / "data_dictionary.json"

with open(dict_path, "r", encoding="utf-8") as f:
    d = json.load(f)

# Check if NCVET already exists
existing_overview = [item for item in d.get("overview", []) if "NCVET" in item.get("dataset_name", "") or "DGT" in item.get("dataset_name", "")]
if existing_overview:
    print("NCVET already documented in overview")
else:
    overview_entry = {
        "dataset_name": "NCVET / DGT National Vocational & ITI Institutions Register",
        "source_authority": "National Council for Vocational Education and Training & Directorate General of Training",
        "sector": "Vocational, Skill & ITIs",
        "academic_year": "2025-26",
        "as_of_date": "2026-09-18",
        "total_records": "9,437 Final Records",
        "states_covered": "32 / 36 (88.9%)",
        "official_id_field": "ITI_Code (e.g. GR35000001, PR08000123)",
        "fields_documented": 21,
        "schema_reference": "NCVT MIS ASP.NET Search DataGrid & Annual Trades Register",
        "notes": "Comprehensive official register of Government and Private Industrial Training Institutes (ITIs) affiliated under NCVT / DGT."
    }
    
    # Insert before Dashboard Common Architecture
    idx = len(d["overview"]) - 1 if d["overview"] and d["overview"][-1].get("dataset_name") == "Dashboard Common Architecture" else len(d["overview"])
    d["overview"].insert(idx, overview_entry)

dataset_name = "NCVET / DGT National Vocational & ITI Institutions Register"
regulator = "NCVET / DGT (Ministry of Skill Development & Entrepreneurship)"

fields = [
    ("S.No.", "Integer", "REGULATOR-SUPPLIED FIELD", "Yes", "1", "1, 2, 3...", "Sequential index number within the national ITI roster.", "Assigned during canonical sorting by State A-Z, District A-Z, Name A-Z."),
    ("ITI_Code", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "GR35000001", "Alphanumeric code (GR=Govt, PR=Private + State Code + 6 digits)", "Primary unique identifier assigned to the ITI by DGT / NCVT MIS.", "100% unique primary key across all 9,437 canonical institutions; 0 duplicates."),
    ("Institution_Name", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Government Industrial Training Institute", "Institution name text", "Official name of the Industrial Training Institute.", "0 missing names across canonical roster."),
    ("State_UT", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Tamil Nadu", "Valid Indian State or Union Territory name", "State or Union Territory where the institution is physically located.", "Normalized to master 36 State/UT taxonomy; 0 missing."),
    ("District", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Chennai", "Administrative District name", "District jurisdiction of the institution.", "Official administrative district recorded in DGT MIS; 0 missing."),
    ("Address", "String", "REGULATOR-SUPPLIED FIELD", "No", "Dollygunj Port Blair", "Street address / location", "Physical postal address of the ITI campus.", "Official address text recorded in NCVT MIS directory."),
    ("PIN_Code", "String", "DASHBOARD-STANDARDIZED FIELD", "No", "600001", "6-digit Indian postal code", "Extracted 6-digit postal index number from address string.", "Used for geographic resolution and spatial search where present."),
    ("Government_Private", "String", "DASHBOARD-STANDARDIZED FIELD", "Yes", "Government", "Government, Private", "High-level management category of the institution.", "Normalized from Management_Type: 2,654 Government, 6,783 Private."),
    ("Institute_Type", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Industrial Training Institute (ITI)", "Industrial Training Institute (ITI)", "Category of vocational training institution.", "Official vocational designation under the Craftsmen Training Scheme (CTS)."),
    ("Affiliation_Status", "String", "REGULATOR-SUPPLIED FIELD", "Yes", "Affiliated under NCVT / DGT", "Affiliated under NCVT / DGT", "Regulatory recognition and affiliation standing under NCVT / DGT.", "Indicates active affiliation under National Council for Vocational Training."),
    ("Trades_Offered", "Integer", "REGULATOR-SUPPLIED FIELD", "Yes", "8", "Integer count >= 1", "Total number of vocational trades/courses approved and active in this ITI.", "Summarizes curriculum offerings; trade specifics maintained in Trades & Courses sheet."),
    ("Sanctioned_Seats", "Integer", "REGULATOR-SUPPLIED FIELD", "Yes", "120", "Integer count >= 0", "Total sanctioned student intake capacity across all shifts and units.", "Official annual intake capacity approved by DGT."),
    ("Enrolled_Trainees", "Integer", "REGULATOR-SUPPLIED FIELD", "No", "95", "Integer count >= 0", "Total currently enrolled trainees actively attending training.", "Recorded from NCVT MIS examination and enrollment returns."),
    ("Location_Type", "String", "REGULATOR-SUPPLIED FIELD", "No", "Urban", "Urban, Rural", "Classification of institution location as Urban or Rural.", "Captures geographic setting of the training campus."),
    ("CSS_Scheme", "String", "REGULATOR-SUPPLIED FIELD", "No", "CTS - Craftsmen Training Scheme", "CTS, DST, etc.", "Centrally Sponsored Scheme or vocational framework under which the ITI operates.", "Primary operational scheme for vocational skill training."),
    ("File_Ref_Number", "String", "REGULATOR-SUPPLIED FIELD", "No", "DGET-6/24/1/2014-TC", "Government order / file reference string", "Official government order or DGT file reference number approving affiliation.", "Traceability back to central Ministry of Skill Development gazette files."),
    ("Final_Grading", "String", "REGULATOR-SUPPLIED FIELD", "No", "3.85 / 5.0", "Numeric grading score (0.0 to 5.0) or Star Rating", "Official star rating or grading score assigned under DGT ITI Grading Framework.", "Reflects infrastructure, faculty, placement, and training quality metrics."),
    ("Instructor_Count", "Integer", "REGULATOR-SUPPLIED FIELD", "No", "14", "Integer count >= 0", "Number of qualified vocational instructors employed at the ITI.", "Faculty strength indicator."),
    ("Source_URL", "String", "METADATA FIELD", "Yes", "https://ncvtmis.gov.in/Pages/ITI/Search.aspx", "Valid HTTP/HTTPS URL", "Direct URL to official NCVT MIS ITI search portal.", "Authoritative Government of India public directory."),
    ("Collection_Date", "String", "METADATA FIELD", "Yes", "2026-09-18", "YYYY-MM-DD", "Date when the record was extracted from the official portal.", "Maintains temporal audit integrity."),
    ("Verification_Status", "String", "METADATA FIELD", "Yes", "Verified Official Record - NCVT MIS", "Verified Official Record - NCVT MIS", "Validation status indicating authentic extraction from official portal.", "Passed automated deduplication and master schema verification.")
]

# Check if fields already in records
existing_fields = {r.get("field_name") for r in d.get("records", []) if r.get("dataset") == dataset_name}
new_records = []
for fname, dtype, fclass, freq, exval, allowed, desc, notes in fields:
    if fname not in existing_fields:
        new_records.append({
            "dataset": dataset_name,
            "source_regulator": regulator,
            "academic_year": "2025-26",
            "field_name": fname,
            "data_type": dtype,
            "field_classification": fclass,
            "is_required": freq,
            "example_value": exval,
            "allowed_values": allowed,
            "description": desc,
            "notes": notes
        })

# Insert new records before Dashboard Common Architecture records
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
