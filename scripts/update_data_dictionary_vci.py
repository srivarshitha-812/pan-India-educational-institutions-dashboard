import json
from pathlib import Path

json_path = Path("data/data_dictionary.json")
if not json_path.exists():
    print(f"File {json_path} does not exist.")
    exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    dict_data = json.load(f)

# 1. Add overview item
overview = dict_data.get("overview", [])
ds_name = "VCI National Veterinary Colleges Register"

if not any("Veterinary" in item.get("dataset_name", "") or "VCI" in item.get("dataset_name", "") for item in overview):
    vci_overview = {
        "dataset_name": ds_name,
        "source_authority": "Veterinary Council of India (VCI) / Department of Animal Husbandry & Dairying (DAHD)",
        "sector": "Veterinary Sciences",
        "academic_year": "AY 2026-27 / As on 14.05.2026",
        "as_of_date": "2026-09-18",
        "total_records": "96",
        "states_covered": "26 / 36 (100% Audited)",
        "official_id_field": "VCI Canonical ID / Registration Code (e.g. VCI-REC-001, VCI-PROV-001)",
        "fields_documented": 19,
        "schema_reference": "VCI First Schedule & Provisional Recognition Directory",
        "notes": "100% complete national census of 96 canonical physical veterinary colleges (72 Recognized, 24 Provisionally Recognized) across 26 States/UTs. 10 States/UTs with 0 colleges verified and preserved."
    }
    # Insert before Dashboard Common Architecture
    overview.insert(-1, vci_overview)

# 2. Add field records
records = dict_data.get("records", [])
if not any(r.get("dataset") == ds_name for r in records):
    vci_fields = [
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "VCI Canonical ID",
            "data_type": "String",
            "field_classification": "PRIMARY KEY",
            "is_required": "Yes",
            "example_value": "VCI-001",
            "allowed_values": "VCI-XXX sequential canonical identifier",
            "description": "Unique standardized system primary key assigned to each canonical physical veterinary institution.",
            "notes": "Ensures deterministic 1-campus-1-record identity across all VCI documents."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Registration / VCI Code",
            "data_type": "String",
            "field_classification": "REGULATORY ID",
            "is_required": "Yes",
            "example_value": "VCI-REC-001",
            "allowed_values": "VCI-REC-XXX or VCI-PROV-XXX",
            "description": "Official regulatory identifier tracking recognized vs provisionally recognized status under the IVC Act, 1984.",
            "notes": "Preserves official statutory recognition category."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Institution Name",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "College of Veterinary Science, Tirupati",
            "allowed_values": "Official college name string",
            "description": "Full official registered legal name of the veterinary college.",
            "notes": "Cleaned of procedural annotations while preserving exact identity."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Institution Type",
            "data_type": "String",
            "field_classification": "TAXONOMY",
            "is_required": "Yes",
            "example_value": "Veterinary College",
            "allowed_values": "Veterinary College",
            "description": "Broad institutional category under higher education taxonomy.",
            "notes": "Standardized across all VCI records."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "College Category",
            "data_type": "String",
            "field_classification": "REGULATORY CLASSIFICATION",
            "is_required": "Yes",
            "example_value": "Recognized Veterinary College",
            "allowed_values": "Recognized Veterinary College, Provisionally Recognized Veterinary College",
            "description": "Statutory category reflecting whether the college is in the First Schedule or operating under Letter of Permission (LOP).",
            "notes": "Determines qualification validity under IVC Act 1984."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Recognition Status",
            "data_type": "String",
            "field_classification": "STATUS",
            "is_required": "Yes",
            "example_value": "Recognized",
            "allowed_values": "Recognized, Provisionally Recognized",
            "description": "Current active legal recognition status approved by Central Government.",
            "notes": "72 Recognized, 24 Provisionally Recognized."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Management Type",
            "data_type": "String",
            "field_classification": "GOVERNANCE",
            "is_required": "Yes",
            "example_value": "Government",
            "allowed_values": "Government, Private",
            "description": "Sector of governance and funding of the veterinary institution.",
            "notes": "Government Sector or Private Sector."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Affiliation Type",
            "data_type": "String",
            "field_classification": "ACADEMIC STRUCTURE",
            "is_required": "Yes",
            "example_value": "Constituent College",
            "allowed_values": "Constituent College, Affiliated College, Constituent Faculty, Deemed University / National Institute",
            "description": "Relationship between the veterinary college and its parent degree-granting university.",
            "notes": "Identifies campus administrative status."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Affiliating University",
            "data_type": "String",
            "field_classification": "SOURCE FIELD",
            "is_required": "Yes",
            "example_value": "Sri Venkateswara Veterinary University, Tirupati",
            "allowed_values": "Official university name string",
            "description": "Name of the parent or affiliating university granting the B.V.Sc. & A.H. degree.",
            "notes": "Preserves university relationship without double counting university as a college."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "State",
            "data_type": "String",
            "field_classification": "GEOGRAPHY",
            "is_required": "Yes",
            "example_value": "Andhra Pradesh",
            "allowed_values": "Standard 36 States/UTs of India",
            "description": "State or Union Territory where the physical college campus is located.",
            "notes": "Harmonized to project geographic standard."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "District",
            "data_type": "String",
            "field_classification": "GEOGRAPHY",
            "is_required": "Yes",
            "example_value": "Tirupati",
            "allowed_values": "Official revenue district name",
            "description": "Revenue district where the veterinary college campus is situated.",
            "notes": "100% verified using official VCI counseling addresses."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Address",
            "data_type": "String",
            "field_classification": "CONTACT",
            "is_required": "Yes",
            "example_value": "Chittoor Road, Prakasam Nagar Colony, SVVU Campus, Tirupati - 517502, Andhra Pradesh",
            "allowed_values": "Campus address string",
            "description": "Detailed physical campus address of the veterinary college.",
            "notes": "Extracted from official VCI directory and counseling annexures."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "PIN Code",
            "data_type": "String",
            "field_classification": "GEOGRAPHY",
            "is_required": "Yes",
            "example_value": "517502",
            "allowed_values": "6-digit Indian postal PIN code",
            "description": "Postal Index Number of the institution campus.",
            "notes": "Verified against postal boundaries."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Programmes Offered",
            "data_type": "String",
            "field_classification": "CURRICULUM",
            "is_required": "Yes",
            "example_value": "B.V.Sc. & A.H.",
            "allowed_values": "B.V.Sc. & A.H.",
            "description": "Undergraduate professional veterinary degree programme recognized under IVC Act, 1984.",
            "notes": "Bachelor of Veterinary Science & Animal Husbandry."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Website",
            "data_type": "String",
            "field_classification": "WEB LINK",
            "is_required": "Yes",
            "example_value": "https://vci.dahd.gov.in/",
            "allowed_values": "Valid HTTP/HTTPS URL",
            "description": "Official institutional or regulatory portal web address.",
            "notes": "Official VCI authority link."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Source Document",
            "data_type": "String",
            "field_classification": "PROVENANCE",
            "is_required": "Yes",
            "example_value": "list of Recognzied vety. colleges (as on 14.5.26)_0.doc",
            "allowed_values": "Official published document title",
            "description": "Exact name of the official VCI gazette or schedule document.",
            "notes": "Ensures full traceability to original GoI file."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Source URL",
            "data_type": "String",
            "field_classification": "PROVENANCE",
            "is_required": "Yes",
            "example_value": "https://vci.dahd.gov.in/sites/default/files/News%20update/list%20of%20Recognzied%20vety.%20colleges%20%28as%20on%2014.5.26%29_0.doc",
            "allowed_values": "Valid HTTP/HTTPS URL",
            "description": "Direct download link on official vci.dahd.gov.in portal.",
            "notes": "Enables independent verification."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Collection Date",
            "data_type": "String",
            "field_classification": "METADATA",
            "is_required": "Yes",
            "example_value": "2026-09-18",
            "allowed_values": "YYYY-MM-DD",
            "description": "Date when the official VCI record was extracted and verified.",
            "notes": "Timestamp of harvest."
        },
        {
            "dataset": ds_name,
            "source_regulator": "VCI / DAHD",
            "academic_year": "AY 2026-27",
            "field_name": "Academic / Survey Year",
            "data_type": "String",
            "field_classification": "METADATA",
            "is_required": "Yes",
            "example_value": "AY 2026-27 / As on 14.05.2026",
            "allowed_values": "Official academic / reference session string",
            "description": "Academic reference session or official publication date of the schedule.",
            "notes": "Preserves VCI reference timeframe."
        }
    ]
    records.extend(vci_fields)

dict_data["overview"] = overview
dict_data["records"] = records
dict_data["total_fields"] = len(records)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(dict_data, f, indent=2)

print(f"Data dictionary updated with VCI fields! Total documented fields: {len(records)}")
