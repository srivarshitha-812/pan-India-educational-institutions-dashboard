import json
from pathlib import Path

# Load existing data_dictionary.json
json_path = Path("data/data_dictionary.json")
with open(json_path, "r", encoding="utf-8") as f:
    dict_data = json.load(f)

# 1. Add overview item
overview = dict_data.get("overview", [])
# Check if AISHE already exists
if not any("AISHE" in item.get("dataset_name", "") for item in overview):
    # Insert before Dashboard Common Architecture
    aishe_overview = {
        "dataset_name": "AISHE National Colleges & Higher Education Register",
        "source_authority": "All India Survey on Higher Education (AISHE) / Ministry of Education",
        "sector": "Colleges & Higher Education",
        "academic_year": "2022-23 / 2023-24",
        "as_of_date": "2026-09-17",
        "total_records": "54,142",
        "states_covered": "36 / 36 (100%)",
        "official_id_field": "AISHE Code (e.g. C-6575, C-59634)",
        "fields_documented": 20,
        "schema_reference": "AISHE Higher Education Institution Directory Portal",
        "notes": "100% complete national directory of affiliated colleges, constituent colleges, autonomous colleges, PG centres, and recognized centres across all 36 States/UTs."
    }
    overview.insert(-1, aishe_overview)

# 2. Add field records
records = dict_data.get("records", [])
ds_name = "AISHE National Colleges & Higher Education Register"
if not any(r.get("dataset") == ds_name for r in records):
    aishe_fields = [
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "AISHE Code",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "C-59634",
            "allowed_values": "Official C-XXXXX alphanumeric identifier",
            "description": "Unique statutory institutional code assigned by the Ministry of Education / AISHE to each higher education college.",
            "notes": "Primary key for higher education colleges across India."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Institution Name",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Sri Jagannath Prasad Mahavidyalaya",
            "allowed_values": "Official college title string",
            "description": "Full official registered legal name of the college or higher education institution.",
            "notes": "Verified against official AISHE directory."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Institution Type",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Affiliated College",
            "allowed_values": "Affiliated College, Constituent College, Autonomous College, PG Centre, Recognized Centre",
            "description": "Functional institutional classification of the college within the higher education ecosystem.",
            "notes": "Preserves official statutory type."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "College Category",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Affiliated Colleges",
            "allowed_values": "Affiliated Colleges, Constituent / University Colleges, PG Centre / Off-Campus Centres, Recognized Centres, Autonomous Colleges",
            "description": "AISHE portal classification category under which the institution was surveyed and published.",
            "notes": "Reconciled with multiple tags if college is autonomous."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Affiliation Type",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Affiliated",
            "allowed_values": "Affiliated, Constituent, Autonomous, PG Centre / Off-Campus, Recognized Centre",
            "description": "Nature of affiliation between the college and its parent statutory university.",
            "notes": "Enables granular filtering of institutional governance models."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Affiliating University ID",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "U-0509",
            "allowed_values": "Official U-XXXX university code",
            "description": "AISHE unique university identifier of the affiliating or examining university.",
            "notes": "Direct relational link to UGC Consolidated Universities Register."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Affiliating University Name",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "Dr. B. R. Ambedkar University, Agra",
            "allowed_values": "Official university name string",
            "description": "Official name of the university to which the college is academically affiliated.",
            "notes": "Enables university-wise aggregation of affiliated colleges."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Affiliating University Type",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "State Public University",
            "allowed_values": "Central University, State Public University, State Private University, Deemed to be University, INI",
            "description": "Statutory category of the affiliating university.",
            "notes": "Identifies legal university framework."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "State",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Uttar Pradesh",
            "allowed_values": "One of 36 Canonical States & UTs",
            "description": "Standardized State or Union Territory where the institution's physical campus is located.",
            "notes": "100% coverage across all 36 States/UTs."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "District",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Agra",
            "allowed_values": "Official Indian revenue district name",
            "description": "Official revenue district jurisdiction where the institution is physically situated.",
            "notes": "Covers 763 districts nationwide."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Address",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "Dabrai Shamsabad Agra, agra",
            "allowed_values": "Postal address string",
            "description": "Complete postal street address and locality of the college campus.",
            "notes": "Reported by institution in official AISHE survey filing."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "PIN Code",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "283125",
            "allowed_values": "6-digit Indian Postal Index Number",
            "description": "Postal Index Number of the institution's delivery post office.",
            "notes": "Extracted where explicitly available in official address filings."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Location",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "Rural",
            "allowed_values": "Rural, Urban",
            "description": "Geographic urbanization classification of the college campus.",
            "notes": "Critical for rural vs urban higher education accessibility analytics."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Management Type",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "Private Un-Aided",
            "allowed_values": "Government, Private Aided, Private Un-Aided, University",
            "description": "Financial and administrative management category of the college.",
            "notes": "Distinguishes government, government-aided, and private unaided colleges."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Year of Establishment",
            "data_type": "Integer (String)",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "2016",
            "allowed_values": "4-digit Gregorian calendar year",
            "description": "Year in which the college was officially founded or established.",
            "notes": "Populated for 98.2% of institutions."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Website",
            "data_type": "String (URL)",
            "field_classification": "SOURCE FIELD",
            "is_required": "No",
            "example_value": "www.jpcollege.in.com",
            "allowed_values": "Valid web URL string",
            "description": "Official institutional portal or web address of the college.",
            "notes": "Available for over 48,000 institutions."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Status",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "ACTIVE / RECOGNISED",
            "allowed_values": "ACTIVE / RECOGNISED",
            "description": "Regulatory recognition and active directory status of the institution.",
            "notes": "Confirmed active in official public directory."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Source URL",
            "data_type": "String (URL)",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "https://dashboard.aishe.gov.in/hedirectory/",
            "allowed_values": "Official government portal URL",
            "description": "Source public endpoint from which the record was extracted.",
            "notes": "Ministry of Education official higher education directory."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Survey / Academic Year",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "2022-23 / 2023-24 (Survey AY 2020-23)",
            "allowed_values": "Academic year string",
            "description": "Survey reference and publication academic year of the official directory data.",
            "notes": "Preserves official time horizon per AISHE DCF guidelines."
        },
        {
            "dataset": ds_name,
            "source_regulator": "AISHE / Ministry of Education",
            "academic_year": "2022-23 / 2023-24",
            "field_name": "Collection Date",
            "data_type": "String (Date)",
            "field_classification": "DASHBOARD-CALCULATED FIELD",
            "is_required": "Yes",
            "example_value": "2026-09-17",
            "allowed_values": "YYYY-MM-DD date string",
            "description": "Calendar date on which the official public dataset was extracted.",
            "notes": "Ensures auditability of extraction snapshot."
        }
    ]
    # Insert before Dashboard Common Architecture
    dashboard_arch_idx = len(records)
    for i, r in enumerate(records):
        if r.get("dataset") == "Dashboard Common Architecture":
            dashboard_arch_idx = i
            break
    records[dashboard_arch_idx:dashboard_arch_idx] = aishe_fields

dict_data["overview"] = overview
dict_data["total_fields"] = len(records)
dict_data["records"] = records

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(dict_data, f, indent=2)

print(f"Updated data_dictionary.json with AISHE Colleges! Total datasets: {len(overview)}, Total fields: {len(records)}")
