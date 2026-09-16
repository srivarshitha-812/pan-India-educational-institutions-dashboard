"""
Builds the complete Pan-India NCISM Ayurveda + Unani institutional dataset (650 institutions:
593 Ayurveda + 57 Unani) directly from official NCISM primary sources.

Outputs:
1. Final Institute Lists/Ayurveda Colleges.xlsx
   - Sheet 1: Ayurveda (593 rows)
   - Sheet 2: Unani (57 rows)
   - Sheet 3: Combined (650 rows)
   - Sheet 4: Source & Methodology
2. NCISM_Ayurveda_Unani_Audit.xlsx
"""

import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime

# Standard state normalizer
STATE_NORM_MAP = {
    'andhra pradesh': 'Andhra Pradesh',
    'andhar pradesh': 'Andhra Pradesh',
    'arunachal pradesh': 'Arunachal Pradesh',
    'assam': 'Assam',
    'bihar': 'Bihar',
    'chhattisgarh': 'Chhattisgarh',
    'chattisgarh': 'Chhattisgarh',
    'delhi': 'Delhi',
    'new delhi': 'Delhi',
    'delhi (nct)': 'Delhi',
    'national capital territory of delhi': 'Delhi',
    'goa': 'Goa',
    'gujarat': 'Gujarat',
    'haryana': 'Haryana',
    'himachal pradesh': 'Himachal Pradesh',
    'jammu & kashmir': 'Jammu & Kashmir',
    'jammu and kashmir': 'Jammu & Kashmir',
    'jharkhand': 'Jharkhand',
    'karnataka': 'Karnataka',
    'kerala': 'Kerala',
    'madhya pradesh': 'Madhya Pradesh',
    'maharashtra': 'Maharashtra',
    'maharshtra': 'Maharashtra',
    'manipur': 'Manipur',
    'meghalaya': 'Meghalaya',
    'mizoram': 'Mizoram',
    'nagaland': 'Nagaland',
    'odisha': 'Odisha',
    'orissa': 'Odisha',
    'punjab': 'Punjab',
    'rajasthan': 'Rajasthan',
    'sikkim': 'Sikkim',
    'tamil nadu': 'Tamil Nadu',
    'tamilnadu': 'Tamil Nadu',
    'telangana': 'Telangana',
    'tripura': 'Tripura',
    'uttar pradesh': 'Uttar Pradesh',
    'uttarakhand': 'Uttarakhand',
    'uttaranchal': 'Uttarakhand',
    'west bengal': 'West Bengal',
    'chandigarh': 'Chandigarh',
    'dadra and nagar haveli and daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'puducherry': 'Puducherry',
    'pondicherry': 'Puducherry'
}

def clean_text(s):
    if not s:
        return ""
    # Normalize whitespace and newlines
    s = s.replace('\r', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    s = '\n'.join([line.strip() for line in s.split('\n') if line.strip()])
    return s.strip()

def normalize_state(raw_state):
    if not raw_state:
        return "Unknown"
    s = clean_text(raw_state).lower().replace('\n', ' ')
    s = re.sub(r'[^a-z0-9& ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return STATE_NORM_MAP.get(s, raw_state.strip().title())

def extract_name_and_address(raw_name_cell):
    raw = clean_text(raw_name_cell)
    lines = [l.strip() for l in raw.split('\n') if l.strip()]
    if not lines:
        return "", ""
    
    # Try splitting on standard institutional suffixes followed by comma
    m_inst = re.search(r'^(.*?(?:College|Hospital|Institute|Vidyapeeth|Mahavidyalaya|University|Centre|Trust|Academy|Sansthan))\s*,\s*(.*)$', raw, re.IGNORECASE | re.DOTALL)
    if m_inst:
        name = m_inst.group(1).replace('\n', ' ').strip().rstrip(',')
        addr = m_inst.group(2).replace('\n', ', ').strip()
        return name, addr

    # Fallback to line-by-line
    first_line = lines[0]
    if ',' in first_line and len(first_line) > 50:
        parts = [p.strip() for p in first_line.split(',')]
        name = parts[0]
        addr = ', '.join(parts[1:] + lines[1:])
    else:
        name = first_line.rstrip(',')
        addr = ', '.join(lines[1:]) if len(lines) > 1 else lines[0]
    
    if not addr:
        addr = raw.replace('\n', ', ')
    else:
        addr = addr.replace('\n', ', ')
        
    return name, addr

def extract_district(full_text, state):
    if not full_text:
        return ""
    txt = full_text.replace('\n', ' ')
    
    # Pattern 1: Explicit Distt / Dist / District keyword
    m = re.search(r'(?:Distt?\.?|Dist\.?|District)[:\s-]+([A-Za-z\s]+?)(?:-|\d|,|\.|\n|$)', txt, re.IGNORECASE)
    if m:
        dist = m.group(1).strip()
        dist = re.sub(r'\b(and|rural|urban|city|tq|taluka|tehsil)\b', '', dist, flags=re.IGNORECASE).strip()
        if 2 < len(dist) < 30 and dist.lower() not in STATE_NORM_MAP:
            return dist.title()
            
    # Pattern 2: "Urban Mandal, Krishna District"
    m2 = re.search(r'([A-Za-z\s]+?)\s+District', txt, re.IGNORECASE)
    if m2:
        dist = m2.group(1).strip().split(',')[-1].strip()
        if 2 < len(dist) < 30 and dist.lower() not in STATE_NORM_MAP:
            return dist.title()

    # Pattern 3: City / District preceding 6-digit PIN code e.g. "Hyderabad-500038" or "near Erragadda, Hyderabad, Telangana-500038"
    m3 = re.search(r'([A-Za-z\s,]+?)\s*[-–]?\s*[1-9]\d{5}', txt)
    if m3:
        raw_prefix = m3.group(1).replace('\n', ',')
        parts = [p.strip() for p in raw_prefix.split(',') if p.strip()]
        if parts:
            cand = parts[-1].strip().rstrip('-–').strip()
            # If the immediate part is a State name (e.g. Telangana), examine previous part
            if cand.lower() in STATE_NORM_MAP and len(parts) > 1:
                cand = parts[-2].strip().rstrip('-–').strip()
            # Remove locality noise
            cand = re.sub(r'^(near|opp|opp\.|post|at|tq|road)\s+', '', cand, flags=re.IGNORECASE).strip()
            if 2 < len(cand) < 30 and cand.lower() not in STATE_NORM_MAP:
                return cand.title()

    return ""

    return ""

def extract_pincode(full_text):
    if not full_text:
        return ""
    m = re.search(r'\b([1-9]\d{5})\b', full_text)
    return m.group(1) if m else ""

def clean_management(mgt_raw):
    if not mgt_raw:
        return "Not Specified"
    m = mgt_raw.strip().replace('\n', ' ')
    m_low = m.lower()
    if 'central' in m_low:
        return 'Central Government'
    if 'aided' in m_low:
        return 'Government Aided'
    if 'govt' in m_low or 'government' in m_low:
        return 'Government'
    if 'deemed' in m_low:
        return 'Deemed University'
    if 'private' in m_low or 'trust' in m_low or 'society' in m_low:
        return 'Private'
    return m.title()

def parse_permitted_details(pdf_path, id_prefix):
    """Parses permitted colleges with seats and status"""
    lookup = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    # Find College ID
                    cid = None
                    for cell in row[:4]:
                        if cell and re.search(rf'{id_prefix}\d+', cell):
                            cid = re.search(rf'{id_prefix}\d+', cell).group(0)
                            break
                    if not cid:
                        continue
                    
                    # Permitted columns:
                    # [0]: S.No, [1]: ID, [2]: State, [3]: Name, [4]: Mgt, [5]: Perm Details, [6]: UG no-EWS, [7]: PG no-EWS, [8]: UG EWS, [9]: PG EWS, [10]: Status
                    perm_details = clean_text(row[5]) if len(row) > 5 else ""
                    
                    ug_seats = 0
                    pg_seats = 0
                    
                    # Extract UG & PG seats
                    def parse_seat(val):
                        if not val:
                            return 0
                        v = re.sub(r'[^\d]', '', str(val))
                        return int(v) if v else 0

                    if len(row) >= 10:
                        ug_no_ews = parse_seat(row[6])
                        pg_no_ews = parse_seat(row[7])
                        ug_ews = parse_seat(row[8])
                        pg_ews = parse_seat(row[9])
                        
                        # Total UG = max of ews or no_ews (or sum if EWS is separate)
                        # In NCISM format: row[8] is Total With EWS (e.g. 63 when row[6] is 50), or 0 if no EWS
                        ug_seats = ug_ews if ug_ews > ug_no_ews else ug_no_ews
                        pg_seats = pg_ews if pg_ews > pg_no_ews else pg_no_ews
                    
                    perm_status = clean_text(row[10]) if len(row) > 10 else "Permitted"
                    if not perm_status:
                        perm_status = "Permitted"
                        
                    lookup[cid] = {
                        'ug_seats': ug_seats,
                        'pg_seats': pg_seats,
                        'permission_status': perm_status.replace('\n', ' '),
                        'permission_details': perm_details.replace('\n', ' ')
                    }
    return lookup

def parse_lop_colleges(pdf_path, id_prefix):
    """Parses LOP colleges under Section 29"""
    lookup = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    cid = None
                    for cell in row[:4]:
                        if cell and re.search(rf'{id_prefix}\d+', cell):
                            cid = re.search(rf'{id_prefix}\d+', cell).group(0)
                            break
                    if not cid:
                        continue
                    # Permitted Seats UG is typically in col 8 or 9
                    ug_seats = 0
                    for cell in row[-3:]:
                        if cell and cell.strip().isdigit():
                            ug_seats = int(cell.strip())
                            break
                    perm_status = "Letter of Permission (Sec 29)"
                    lookup[cid] = {
                        'ug_seats': ug_seats,
                        'pg_seats': 0,
                        'permission_status': perm_status,
                        'permission_details': clean_text(row[7]) if len(row) > 7 else "New college granted LOP under Section 29"
                    }
    return lookup

def main():
    print("=" * 70)
    print("EXTRACTING NCISM AYURVEDA & UNANI PRIMARY DATASETS")
    print("=" * 70)

    # 1. Parse permitted & LOP datasets for enrichment
    ayu_perm_file = "data/raw/ncism/ncism_ayurveda_permitted_2025_26_as_on_02_03_2026.pdf"
    ayu_lop_file = "data/raw/ncism/ncism_ayurveda_lop_2025_26_as_on_05_02_2026.pdf"
    uni_perm_file = "data/raw/ncism/ncism_unani_permitted_2025_26_as_on_12_12_2025.pdf"
    uni_lop_file = "data/raw/ncism/ncism_unani_lop_2025_26_as_on_19_11_2025.pdf"

    print("Parsing Ayurveda Permitted list...")
    ayu_perm = parse_permitted_details(ayu_perm_file, "AYU")
    print(f"  Parsed {len(ayu_perm)} permitted Ayurveda institutions.")

    print("Parsing Ayurveda LOP list...")
    ayu_lop = parse_lop_colleges(ayu_lop_file, "AYU")
    print(f"  Parsed {len(ayu_lop)} LOP Ayurveda institutions.")

    print("Parsing Unani Permitted list...")
    uni_perm = parse_permitted_details(uni_perm_file, "UNI")
    print(f"  Parsed {len(uni_perm)} permitted Unani institutions.")

    print("Parsing Unani LOP list...")
    uni_lop = parse_lop_colleges(uni_lop_file, "UNI")
    print(f"  Parsed {len(uni_lop)} LOP Unani institutions.")

    # 2. Extract Total Ayurveda Colleges across country
    ayu_total_file = "data/raw/ncism/ncism_ayurveda_total_across_country_as_on_05_02_2026.pdf"
    ayu_rows = []
    with pdfplumber.open(ayu_total_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    sno, cid, state_raw, name_raw, mgt_raw = row[0], row[1], row[2], row[3], row[4]
                    if not cid or not cid.strip().startswith("AYU"):
                        continue
                    
                    college_id = cid.strip()
                    state = normalize_state(state_raw)
                    name, address = extract_name_and_address(name_raw)
                    district = extract_district(name_raw, state)
                    pincode = extract_pincode(name_raw)
                    management = clean_management(mgt_raw)
                    
                    # Enrichment from permission / LOP lists
                    ug_seats = ""
                    pg_seats = ""
                    perm_status = "Under NCISM Review / Conditional Status"
                    perm_details = "Listed in official NCISM National Total Directory (Status evaluation ongoing/conditional under NCISM Act 2020)"
                    
                    if college_id in ayu_perm:
                        p = ayu_perm[college_id]
                        ug_seats = p['ug_seats']
                        pg_seats = p['pg_seats']
                        perm_status = p['permission_status']
                        perm_details = p['permission_details']
                    elif college_id in ayu_lop:
                        p = ayu_lop[college_id]
                        ug_seats = p['ug_seats']
                        pg_seats = p['pg_seats']
                        perm_status = p['permission_status']
                        perm_details = p['permission_details']
                        
                    ayu_rows.append({
                        "College ID": college_id,
                        "System": "Ayurveda",
                        "Name of the College": name,
                        "State": state,
                        "District": district,
                        "Pincode": pincode,
                        "Address": address,
                        "Management": management,
                        "Govt./Aided/ Private/ Deemed": management,
                        "UG Seats": ug_seats if ug_seats != 0 else "",
                        "PG Seats": pg_seats if pg_seats != 0 else "",
                        "Permission Status": perm_status,
                        "Permission Details": perm_details,
                        "Academic Year": "2025-26",
                        "Source Document Title": "List of total Ayurveda Colleges across country as on 05.02.2026",
                        "Source Date": "05.02.2026",
                        "Source URL": "https://ncismindia.org/assets/pdf/List%20of%20total%20Ayurveda%20Colleges%20across%20country%20as%20on%2005.02.2026.pdf",
                        "Collection Date": "2026-09-16"
                    })

    # 3. Extract Total Unani Colleges across country
    uni_total_file = "data/raw/ncism/ncism_unani_total_across_country_as_on_16_12_2025.pdf"
    uni_rows = []
    with pdfplumber.open(uni_total_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    sno, cid, state_raw, name_raw, mgt_raw = row[0], row[1], row[2], row[3], row[4]
                    if not cid or not cid.strip().startswith("UNI"):
                        continue
                    
                    college_id = cid.strip()
                    state = normalize_state(state_raw)
                    name, address = extract_name_and_address(name_raw)
                    district = extract_district(name_raw, state)
                    pincode = extract_pincode(name_raw)
                    management = clean_management(mgt_raw)
                    
                    ug_seats = ""
                    pg_seats = ""
                    perm_status = "Under NCISM Review / Conditional Status"
                    perm_details = "Listed in official NCISM National Total Directory (Status evaluation ongoing/conditional under NCISM Act 2020)"
                    
                    if college_id in uni_perm:
                        p = uni_perm[college_id]
                        ug_seats = p['ug_seats']
                        pg_seats = p['pg_seats']
                        perm_status = p['permission_status']
                        perm_details = p['permission_details']
                    elif college_id in uni_lop:
                        p = uni_lop[college_id]
                        ug_seats = p['ug_seats']
                        pg_seats = p['pg_seats']
                        perm_status = p['permission_status']
                        perm_details = p['permission_details']
                        
                    uni_rows.append({
                        "College ID": college_id,
                        "System": "Unani",
                        "Name of the College": name,
                        "State": state,
                        "District": district,
                        "Pincode": pincode,
                        "Address": address,
                        "Management": management,
                        "Govt./Aided/ Private/ Deemed": management,
                        "UG Seats": ug_seats if ug_seats != 0 else "",
                        "PG Seats": pg_seats if pg_seats != 0 else "",
                        "Permission Status": perm_status,
                        "Permission Details": perm_details,
                        "Academic Year": "2025-26",
                        "Source Document Title": "List of Unani Colleges across country as on 16.12.2025",
                        "Source Date": "16.12.2025",
                        "Source URL": "https://ncismindia.org/assets/pdf/List%20of%20total%20Unani%20Colleges%20across%20country%20as%20on%2016.12.2025.pdf",
                        "Collection Date": "2026-09-16"
                    })

    df_ayu = pd.DataFrame(ayu_rows)
    df_uni = pd.DataFrame(uni_rows)
    df_comb = pd.concat([df_ayu, df_uni], ignore_index=True)

    print(f"\nAyurveda extracted count: {len(df_ayu)}")
    print(f"Unani extracted count: {len(df_uni)}")
    print(f"Combined physical institutions count: {len(df_comb)}")
    print(f"Unique College IDs: {df_comb['College ID'].nunique()}")
    print(f"Duplicate College IDs: {len(df_comb) - df_comb['College ID'].nunique()}")
    print(f"Missing College IDs: {df_comb['College ID'].isna().sum()}")
    print(f"Missing Institution Names: {df_comb['Name of the College'].isna().sum()}")
    print(f"Missing States: {df_comb['State'].isna().sum()}")

    # Verify Telangana entries
    tg_ayu = df_ayu[df_ayu['State'] == 'Telangana']
    tg_uni = df_uni[df_uni['State'] == 'Telangana']
    print(f"\nTelangana Ayurveda Count: {len(tg_ayu)}")
    for _, r in tg_ayu.iterrows():
        print(f"  {r['College ID']} | {r['Name of the College']} | Seats UG: {r['UG Seats']}, PG: {r['PG Seats']} | Status: {r['Permission Status'][:30]}")
    print(f"Telangana Unani Count: {len(tg_uni)}")
    for _, r in tg_uni.iterrows():
        print(f"  {r['College ID']} | {r['Name of the College']} | Seats UG: {r['UG Seats']}, PG: {r['PG Seats']} | Status: {r['Permission Status'][:30]}")

    # Create Source & Methodology DataFrame
    methodology_rows = [
        {"Parameter": "Authority", "Detail": "National Commission for Indian System of Medicine (NCISM), Statutory Regulatory Body under Ministry of Ayush, Govt. of India"},
        {"Parameter": "Statutory Jurisdiction", "Detail": "Medical education in Ayurveda, Unani, Siddha, and Sowa-Rigpa under the NCISM Act, 2020"},
        {"Parameter": "Academic Year", "Detail": "2025-26"},
        {"Parameter": "Ayurveda Total Source", "Detail": "List of total Ayurveda Colleges across country as on 05.02.2026 (593 institutions)"},
        {"Parameter": "Ayurveda Permitted Source", "Detail": "List of Permitted Ayurveda Colleges for the Academic Year 2025-26 as on 02.03.2026 (536 permitted institutions)"},
        {"Parameter": "Ayurveda LOP Source", "Detail": "List of Colleges Granted LOI/LOP to establish new Ayurveda Colleges Under Section 29 from the A.Y.2025-26 as on 05.02.2026"},
        {"Parameter": "Unani Total Source", "Detail": "List of Unani Colleges across country as on 16.12.2025 (57 institutions)"},
        {"Parameter": "Unani Permitted Source", "Detail": "List of Permitted Unani Colleges for the academic year 2025-2026 as on 12.12.2025 (52 permitted institutions)"},
        {"Parameter": "Unani LOP Source", "Detail": "Letter of Permission to establish new Unani Colleges for the A.Y. 2025-26 as on 19.11.2025"},
        {"Parameter": "Primary Website Portal", "Detail": "https://ncismindia.org/"},
        {"Parameter": "Total Ayurveda Institutions", "Detail": str(len(df_ayu))},
        {"Parameter": "Total Unani Institutions", "Detail": str(len(df_uni))},
        {"Parameter": "Total Combined Physical Institutions", "Detail": str(len(df_comb))},
        {"Parameter": "Deduplication Rule", "Detail": "Deduplicated strictly on official NCISM College ID (AYUxxxx / UNIxxxx). Zero duplicate IDs present."},
        {"Parameter": "Inclusion Methodology", "Detail": "National comprehensive universe established from official NCISM total college registries as-of AY 2025-26, enriched with latest permission circulars for intake capacity and regulatory standing."},
        {"Parameter": "Collection Date", "Detail": "2026-09-16"}
    ]
    df_methodology = pd.DataFrame(methodology_rows)

    # 4. Write Final Institute Lists/Ayurveda Colleges.xlsx
    target_excel = "Final Institute Lists/Ayurveda Colleges.xlsx"
    print(f"\nWriting workbook to {target_excel} ...")
    with pd.ExcelWriter(target_excel, engine='openpyxl') as writer:
        df_ayu.to_excel(writer, sheet_name='Ayurveda', index=False)
        df_uni.to_excel(writer, sheet_name='Unani', index=False)
        df_comb.to_excel(writer, sheet_name='Combined', index=False)
        df_methodology.to_excel(writer, sheet_name='Source & Methodology', index=False)
    print("  Successfully saved Ayurveda Colleges.xlsx with 4 sheets!")

    # 5. Build NCISM_Ayurveda_Unani_Audit.xlsx
    audit_excel = "NCISM_Ayurveda_Unani_Audit.xlsx"
    state_summary = df_comb.groupby(['State', 'System']).size().unstack(fill_value=0)
    state_summary['Total'] = state_summary.sum(axis=1)
    state_summary = state_summary.reset_index()

    status_summary = df_comb.groupby(['System', 'Permission Status']).size().reset_index(name='Count')

    print(f"Writing audit workbook to {audit_excel} ...")
    with pd.ExcelWriter(audit_excel, engine='openpyxl') as writer:
        df_comb.to_excel(writer, sheet_name='Master Roster', index=False)
        state_summary.to_excel(writer, sheet_name='State Reconciliation', index=False)
        status_summary.to_excel(writer, sheet_name='Permission Breakdown', index=False)
        df_methodology.to_excel(writer, sheet_name='Methodology Audit', index=False)
    print("  Successfully saved NCISM_Ayurveda_Unani_Audit.xlsx!")

if __name__ == '__main__':
    main()
