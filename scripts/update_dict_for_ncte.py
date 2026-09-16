import json

ncte_records = [
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "S.No",
        "data_type": "Integer",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "1",
        "allowed_values": "Sequential positive integers (1 to 17,556)",
        "description": "Sequential institutional index for enumeration in the Pan-India census roster.",
        "notes": "Generated during census deduplication and synthesis."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "NCTE Institute ID",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "Yes",
        "example_value": "NCTE1410672",
        "allowed_values": "Alphanumeric string prefix NCTE + numeric identifier",
        "description": "Authoritative institutional identifier assigned by National Council for Teacher Education portal.",
        "notes": "Primary key uniquely identifying each physical campus. 100% unique across the roster."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Institution Name",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "Yes",
        "example_value": "Arunachal University of Studies",
        "allowed_values": "Official statutory institution name",
        "description": "Full statutory name of the recognized teacher education college or university department.",
        "notes": "Verbatim from official NCTE portal registry."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "State",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "Yes",
        "example_value": "Arunachal Pradesh",
        "allowed_values": "36 Standard States and Union Territories",
        "description": "State or Union Territory where the physical teacher education campus is situated.",
        "notes": "Harmonized to the national census canonical 36 States/UTs catalog across 4 Regional Committees."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "District",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "Lohit",
        "allowed_values": "District name or 'Unassigned'",
        "description": "Administrative district location of the institution campus.",
        "notes": "Extracted from official NCTE portal listings; where not specified in portal, labeled 'Unassigned'."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "PIN Code",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "792103",
        "allowed_values": "6-digit postal code or 'Not Specified'",
        "description": "Postal index number of the institution campus.",
        "notes": "Extracted from registered campus address."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Address",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "Vill - Deobeel, Street/Road - NH-52, Taluka/Mandal - Namsai",
        "allowed_values": "Postal address text or 'Not Specified'",
        "description": "Complete statutory physical premises address of the teacher education institution.",
        "notes": "Preserved from official NCTE regulatory records."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Management Type",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "Private Institution",
        "allowed_values": "Government / Private / University / Self-Financed / Constituent",
        "description": "Statutory management and governance classification of the institution.",
        "notes": "Official NCTE management classification."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Affiliating University",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "Rajiv Gandhi University",
        "allowed_values": "Name of affiliating state/central university or board",
        "description": "Statutory examining body or university to which the teacher education programmes are affiliated.",
        "notes": "Official affiliating body declared in NCTE recognition records."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Regional Committee",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "Yes",
        "example_value": "ERC",
        "allowed_values": "ERC, NRC, SRC, WRC",
        "description": "NCTE Regional Committee holding statutory jurisdiction (Eastern, Northern, Southern, or Western).",
        "notes": "ERC (Eastern), NRC (Northern), SRC (Southern), WRC (Western)."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Recognition Status",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "Yes",
        "example_value": "Recognized",
        "allowed_values": "Recognized / Permitted",
        "description": "Current legal regulatory recognition status under the NCTE Act, 1993.",
        "notes": "All 17,556 institutions in this roster are active recognized entities. Withdrawn institutions are maintained in a separate sheet."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Recognized Programmes",
        "data_type": "String",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "B.Ed, D.El.Ed, M.Ed",
        "allowed_values": "Comma-separated list of recognized teacher education course names",
        "description": "Summary of all recognized professional education programmes offered at this physical campus.",
        "notes": "Aggregated across all official recognition orders for this campus."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Total Approved Intake",
        "data_type": "Integer (String)",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "350",
        "allowed_values": "Total sanctioned annual intake (seats) or 'Not Specified'",
        "description": "Combined total annual student intake approved by NCTE across all active recognized courses at this institution.",
        "notes": "Summed across all recognized course orders."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Total Recognized Courses",
        "data_type": "Integer",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "4",
        "allowed_values": "Positive integer (e.g. 1, 2, 3...)",
        "description": "Total number of distinct NCTE-approved academic programmes/units operating at this campus.",
        "notes": "Calculated from institutional programme breakdown."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Latest Applicable Session",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "2017-2018",
        "allowed_values": "Academic session string (e.g. 2019-2020, 2026-27)",
        "description": "Latest regulatory academic session or order revision year recorded by NCTE.",
        "notes": "Extracted from official order details."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Contact Number",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "0380-6202797 / 9540542220",
        "allowed_values": "Telephone/mobile number string",
        "description": "Official institutional telephone or mobile contact number.",
        "notes": "As published on official NCTE portal directory."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Email",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "registrar@arunachaluniversity.ac.in",
        "allowed_values": "Valid email address format",
        "description": "Official institutional contact email address.",
        "notes": "As published on official NCTE portal directory."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Website",
        "data_type": "String",
        "field_classification": "SOURCE FIELD",
        "is_required": "No",
        "example_value": "www.arunachaluniversity.ac.in",
        "allowed_values": "Web URL domain",
        "description": "Official website URL of the teacher education institution.",
        "notes": "As published on official NCTE portal directory."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Official Source Portal",
        "data_type": "String",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "NCTE Official Portal (web.ncte.gov.in)",
        "allowed_values": "Authoritative portal label",
        "description": "Designated official government regulatory portal providing the statutory data.",
        "notes": "National Council for Teacher Education statutory web portal."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Source URL",
        "data_type": "String",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "https://web.ncte.gov.in/page-regional-committee-institution-lists/3/arunachal-pradesh",
        "allowed_values": "Valid HTTP/HTTPS URL",
        "description": "Direct official URL endpoint where the state institutional list is published.",
        "notes": "Traceable source endpoint for regulatory auditing."
    },
    {
        "dataset": "NCTE National Teacher Education Colleges Register",
        "source_regulator": "National Council for Teacher Education (NCTE)",
        "academic_year": "2025-26",
        "field_name": "Collection Date",
        "data_type": "String",
        "field_classification": "DERIVED FIELD",
        "is_required": "Yes",
        "example_value": "2026-09-16",
        "allowed_values": "YYYY-MM-DD date format",
        "description": "Date on which the institutional record was retrieved from the official NCTE portal.",
        "notes": "Timestamp of the census crawling pass."
    }
]

def format_record(r):
    lines = ["    {"]
    items = list(r.items())
    for k, v in items:
        lines.append(f'        "{k}": {json.dumps(v)},')
    lines[-1] = lines[-1][:-1]
    lines.append("    }")
    return "\n".join(lines)

ncte_overview = {
    "dataset_name": "NCTE National Teacher Education Colleges Register",
    "source_authority": "National Council for Teacher Education (NCTE)",
    "sector": "Teacher Education (B.Ed / D.El.Ed / M.Ed / B.P.Ed / ITEP / etc.)",
    "academic_year": "2025-26",
    "as_of_date": "2026-09-16",
    "total_records": "17,556",
    "states_covered": "35 / 36 (97%)",
    "official_id_field": "NCTE Institute ID (e.g. NCTE1410672)",
    "fields_documented": len(ncte_records),
    "schema_reference": "National Council for Teacher Education Official Portal & Regional Committee Rosters (ERC, NRC, SRC, WRC)",
    "notes": "100% complete national census of recognized teacher education institutions across India under NCTE Act, 1993. Multi-course offerings mapped to dedicated Programmes & Courses catalog (28,372 entries), and 1,274 withdrawn/de-recognized institutions isolated in dedicated audit registry."
}

with open("generate_data_dictionary.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Build block for DICTIONARY_RECORDS
records_block = "    # =========================================================================\n"
records_block += "    # 16. NCTE NATIONAL TEACHER EDUCATION COLLEGES REGISTER (21 Fields)\n"
records_block += "    # =========================================================================\n"
for rec in ncte_records:
    records_block += format_record(rec) + ",\n"

marker_records = "    # =========================================================================\n    # 14. DASHBOARD-CALCULATED & AUDIT FIELDS"
if marker_records not in code:
    marker_records = "    # 14. DASHBOARD-CALCULATED & AUDIT FIELDS"

code = code.replace(marker_records, records_block + marker_records)

# 2. Build block for DATASET_OVERVIEW_META
overview_block = format_record(ncte_overview) + ",\n"
marker_ov = '    {\n        "dataset_name": "Dashboard Common Architecture",'
code = code.replace(marker_ov, overview_block + marker_ov)

# 3. Update dataset_group_map
code = code.replace(
    '"NDC_Dental": "NDC National Dental Colleges Register",',
    '"NDC_Dental": "NDC National Dental Colleges Register",\n        "NCTE_Teacher": "NCTE National Teacher Education Colleges Register",'
)

with open("generate_data_dictionary.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated generate_data_dictionary.py successfully.")
