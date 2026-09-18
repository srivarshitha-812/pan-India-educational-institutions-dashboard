import docx
import pdfplumber
import json
import re

# Parse Recognized Colleges from DOCX
doc_rec = docx.Document('data/vci_raw/list of Recognzied vety. colleges (as on 14.5.26)_0.docx')
t1 = doc_rec.tables[0]
recognized_list = []
curr_state = ""
curr_univ = ""
curr_sr_univ = ""

for ri, r in enumerate(t1.rows):
    if ri == 0:
        continue
    cells = [c.text.strip().replace('\n', ' ') for c in r.cells]
    
    # Col 0: Sl. No (State serial)
    # Col 1: State
    # Col 2: Sr. (Univ serial)
    # Col 3: Name of University
    # Col 4: Sr. (College serial)
    # Col 5: Name of College
    state_cell = cells[1] if len(cells) > 1 else ""
    univ_sr_cell = cells[2] if len(cells) > 2 else ""
    univ_cell = cells[3] if len(cells) > 3 else ""
    coll_sr_cell = cells[4] if len(cells) > 4 else ""
    coll_cell = cells[5] if len(cells) > 5 else cells[-1]

    if state_cell and state_cell.upper() != 'STATE':
        curr_state = state_cell.strip().title()
    if univ_sr_cell and univ_sr_cell.strip():
        curr_sr_univ = univ_sr_cell.strip()
    if univ_cell and univ_cell not in ['Name of University', '-do-']:
        curr_univ = univ_cell.strip()

    if coll_cell and 'Name of College' not in coll_cell:
        recognized_list.append({
            'source_doc': 'list of Recognzied vety. colleges (as on 14.5.26)_0.docx',
            'status': 'Recognized',
            'state': curr_state,
            'university': curr_univ,
            'college_serial': coll_sr_cell.strip(),
            'college_name': coll_cell.strip(),
            'raw_row': cells
        })

print(f"Recognized colleges parsed: {len(recognized_list)}")

# Parse Provisional Colleges from DOCX
doc_prov = docx.Document('data/vci_raw/List of Provisionally recognized vety. colleges (as on 14.5.26) (1).docx')
t_prov = doc_prov.tables[0]
provisional_list = []
curr_state = ""
curr_univ = ""
curr_sector = "Government Sector"

for ri, r in enumerate(t_prov.rows):
    if ri == 0:
        continue
    cells = [c.text.strip().replace('\n', ' ') for c in r.cells]
    
    # Check if this row is a sector header or contains text across cells
    full_text = " ".join(cells)
    if 'Private Sector' in full_text:
        curr_sector = "Private Sector"
        continue
    if 'Government Sector' in full_text:
        curr_sector = "Government Sector"
        continue

    sr_cell = cells[0] if len(cells) > 0 else ""
    state_cell = cells[1] if len(cells) > 1 else ""
    coll_cell = cells[2] if len(cells) > 2 else ""
    univ_cell = cells[3] if len(cells) > 3 else ""

    if state_cell and state_cell.upper() != 'STATE':
        curr_state = state_cell.strip().title()
    if univ_cell and univ_cell not in ['Name of Affiliating University', '-do-']:
        curr_univ = univ_cell.strip()

    if coll_cell and 'Name of College' not in coll_cell and coll_cell.strip():
        # Check if sector info is in notes or parentheses
        provisional_list.append({
            'source_doc': 'List of Provisionally recognized vety. colleges (as on 14.5.26) (1).docx',
            'status': 'Provisionally Recognized',
            'sector': curr_sector,
            'state': curr_state,
            'university': curr_univ,
            'college_serial': sr_cell.strip(),
            'college_name': coll_cell.strip(),
            'raw_row': cells
        })

print(f"Provisional colleges parsed: {len(provisional_list)}")

# Parse Annexure 6 from Composite IB for rich address/contact/PIN code lookup
addresses_map = {}
with pdfplumber.open('data/vci_raw/CompositIBAY2026-27.pdf') as pdf:
    full_annex6 = ""
    for p_num in range(23, len(pdf.pages)):
        full_annex6 += (pdf.pages[p_num].extract_text() or "") + "\n"

print(f"Annexure 6 text length: {len(full_annex6)}")

# Check for overlap between Recognized and Provisional
rec_names = [r['college_name'].lower() for r in recognized_list]
prov_names = [p['college_name'].lower() for p in provisional_list]

print("\n--- Overlap Analysis ---")
overlaps = []
for p in provisional_list:
    p_name = p['college_name'].lower()
    # Normalize for comparison
    clean_p = re.sub(r'\(.*?\)', '', p_name).strip()
    for r in recognized_list:
        r_name = r['college_name'].lower()
        clean_r = re.sub(r'\(.*?\)', '', r_name).strip()
        if clean_p in clean_r or clean_r in clean_p or (len(clean_p) > 10 and clean_p[:15] == clean_r[:15]):
            overlaps.append((p['college_name'], r['college_name'], p['state'], r['state']))

print(f"Possible overlaps found: {len(overlaps)}")
for o in overlaps:
    print(f"  PROV: {o[0]} ({o[2]}) <--> REC: {o[1]} ({o[3]})")

# Output all recognized colleges
with open('data/vci_raw/parsed_recognized.json', 'w') as f:
    json.dump(recognized_list, f, indent=2)

with open('data/vci_raw/parsed_provisional.json', 'w') as f:
    json.dump(provisional_list, f, indent=2)

print("\nSaved parsed_recognized.json and parsed_provisional.json successfully!")
