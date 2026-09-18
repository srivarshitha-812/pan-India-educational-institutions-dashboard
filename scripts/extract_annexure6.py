import pdfplumber
import re
import json

with pdfplumber.open('data/vci_raw/CompositIBAY2026-27.pdf') as pdf:
    # Pages 24 to 33 contain Annexure 6
    annex6_entries = []
    current_state = ""
    current_univ = ""
    for p_no in range(23, len(pdf.pages)):
        text = pdf.pages[p_no].extract_text() or ""
        # Let's extract tables on this page
        tables = pdf.pages[p_no].extract_tables()
        for t in tables:
            for row in t:
                # Row format: [Sl NO, Name of the State, Name of the University, Sl. NO, Name of the Veterinary College, Address of the College, Nodal officer Name, Mobile No., E-Mail Id]
                cells = [c.replace('\n', ' ').strip() if c else '' for c in row]
                if not cells or len(cells) < 6:
                    continue
                if 'Name of the Veterinary College' in cells[4] or 'Address of the College' in cells[5]:
                    continue
                
                state_c = cells[1] if len(cells) > 1 else ""
                univ_c = cells[2] if len(cells) > 2 else ""
                coll_sr = cells[3] if len(cells) > 3 else ""
                coll_c = cells[4] if len(cells) > 4 else ""
                addr_c = cells[5] if len(cells) > 5 else ""
                officer_c = cells[6] if len(cells) > 6 else ""
                mobile_c = cells[7] if len(cells) > 7 else ""
                email_c = cells[8] if len(cells) > 8 else ""

                if state_c and not state_c.isdigit():
                    # clean state e.g. "1A ndhra Pradesh" -> "Andhra Pradesh"
                    cleaned_state = re.sub(r'^\d+[A-Za-z]?\s*', '', state_c).strip()
                    if cleaned_state:
                        current_state = cleaned_state
                if univ_c:
                    current_univ = univ_c

                if coll_c:
                    # Extract PIN code from address
                    pin_match = re.search(r'\b([1-9][0-9]{5})\b', addr_c)
                    pin = pin_match.group(1) if pin_match else ""
                    annex6_entries.append({
                        'state': current_state,
                        'university': current_univ,
                        'college_serial': coll_sr,
                        'college_name': coll_c,
                        'address': addr_c,
                        'pin_code': pin,
                        'nodal_officer': officer_c,
                        'mobile': mobile_c,
                        'email': email_c
                    })

print(f"Extracted {len(annex6_entries)} entries from Annexure 6")
with open('data/vci_raw/annexure6_addresses.json', 'w') as f:
    json.dump(annex6_entries, f, indent=2)

for e in annex6_entries[:10]:
    print(f"[{e['state']}] {e['college_name']} | PIN: {e['pin_code']} | Addr: {e['address'][:60]}...")
