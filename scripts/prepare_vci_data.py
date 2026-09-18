import json
import re

with open('data/vci_raw/parsed_recognized.json') as f:
    rec = json.load(f)
with open('data/vci_raw/parsed_provisional.json') as f:
    prov = json.load(f)
with open('data/vci_raw/annexure6_addresses.json') as f:
    annex6 = json.load(f)

# Build a clean lookup for Annexure 6
# Clean state name from annex6 e.g. "ndhra Pradesh" -> "Andhra Pradesh"
state_fix = {
    'ndhra Pradesh': 'Andhra Pradesh',
    'ssam': 'Assam',
    'ihar': 'Bihar',
    'hhattisgarh': 'Chhattisgarh',
    'ujarat': 'Gujarat',
    'aryana': 'Haryana',
    'imachal Pradesh': 'Himachal Pradesh',
    'ammu & Kashmir': 'Jammu and Kashmir',
    'harkhand': 'Jharkhand',
    'arnataka': 'Karnataka',
    'erala': 'Kerala',
    'adhya Pradesh': 'Madhya Pradesh',
    'aharashtra': 'Maharashtra',
    'izoram': 'Mizoram',
    'disha': 'Odisha',
    'uducherry': 'Puducherry',
    'unjab': 'Punjab',
    'ajasthan': 'Rajasthan',
    'amil Nadu': 'Tamil Nadu',
    'elangana': 'Telangana',
    'ripura': 'Tripura',
    'ttar Pradesh': 'Uttar Pradesh',
    'ttarakhand': 'Uttarakhand',
    'est Bengal': 'West Bengal'
}

for a in annex6:
    st = a['state'].strip()
    for k, v in state_fix.items():
        if st == k or st.endswith(k):
            a['state_clean'] = v
            break
    if 'state_clean' not in a:
        a['state_clean'] = st

print(f"Cleaned {len(annex6)} Annexure 6 entries")

# Helper to normalize strings for comparison
def norm_str(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

# Match function
def find_a6_match(coll_name, state_name):
    target_norm = norm_str(coll_name)
    best = None
    best_score = 0
    for a in annex6:
        a_st = a.get('state_clean', a['state'])
        if a_st.lower() == state_name.lower() or a_st[:4].lower() == state_name[:4].lower():
            a_norm = norm_str(a['college_name'])
            # Check overlap of substrings
            # Extract distinctive words
            words = [w for w in re.split(r'[^a-zA-Z0-9]', coll_name.lower()) if len(w) > 3 and w not in ['college', 'veterinary', 'science', 'sciences', 'animal', 'husbandry', 'research', 'institute', 'faculty', 'univ', 'university', 'under', 'sector']]
            score = 0
            for w in words:
                if w in a['college_name'].lower() or w in a['address'].lower():
                    score += 1
            if score > best_score:
                best_score = score
                best = a
    if best_score >= 1:
        return best
    return None

# Check matches for recognized colleges
rec_compiled = []
for i, r in enumerate(rec):
    st = r['state'].strip()
    if st.lower() in ['chhatisgarh']:
        st = 'Chhattisgarh'
    if st.lower() in ['jammu & kashmir']:
        st = 'Jammu and Kashmir'
    
    a6 = find_a6_match(r['college_name'], st)
    addr = a6['address'] if a6 else ""
    pin = a6['pin_code'] if a6 else ""
    officer = a6['nodal_officer'] if a6 else ""
    phone = a6['mobile'] if a6 else ""
    email = a6['email'] if a6 else ""
    
    # Check if address contains PIN code if pin is empty
    if not pin and addr:
        pm = re.search(r'\b([1-9][0-9]{2}\s?[0-9]{3})\b', addr)
        if pm:
            pin = pm.group(1).replace(' ', '')
            
    # Determine sector (Govt vs Private)
    c_name = r['college_name']
    sector = "Private" if "pvt" in c_name.lower() or "private" in c_name.lower() else "Government"
    
    rec_compiled.append({
        'vci_serial': f"VCI-REC-{i+1:03d}",
        'official_sr': r['college_serial'] or str(i+1),
        'institution_name': re.sub(r'\s*\([ivx\d]+\)\s*', ' ', re.sub(r'\(The college is under.*?\)', '', c_name)).strip(),
        'raw_name': c_name,
        'state': st,
        'university': r['university'],
        'status': 'Recognized',
        'category': 'Recognized Veterinary College',
        'sector': sector,
        'address': addr,
        'pin_code': pin,
        'nodal_officer': officer,
        'contact_phone': phone,
        'contact_email': email,
        'source_doc': r['source_doc']
    })

print(f"Compiled {len(rec_compiled)} recognized colleges")
matched_count = sum(1 for r in rec_compiled if r['address'])
print(f"Recognized colleges with rich addresses matched: {matched_count}/{len(rec_compiled)}")

# Check provisional
prov_compiled = []
seen_prov = set()
excluded_prov = []

for i, p in enumerate(prov):
    st = p['state'].strip()
    if st.lower() in ['chhatisgarh']:
        st = 'Chhattisgarh'
    if st.lower() in ['jammu & kashmir']:
        st = 'Jammu and Kashmir'
        
    c_name = p['college_name']
    norm_key = (st.lower(), norm_str(c_name)[:25])
    
    # Check for Bilaspur duplicate
    if "bilaspur" in c_name.lower() and st.lower() == "chhattisgarh":
        if "bilaspur" in seen_prov:
            excluded_prov.append({
                'source_row': p['raw_row'],
                'college_name': c_name,
                'state': st,
                'university': p['university'],
                'reason': 'Duplicate entry in provisional source document (listed under both Government and Private Sector); reconciled into single canonical institution at Bilaspur, Chhattisgarh.'
            })
            continue
        seen_prov.add("bilaspur")
        
    a6 = find_a6_match(c_name, st)
    addr = a6['address'] if a6 else ""
    pin = a6['pin_code'] if a6 else ""
    officer = a6['nodal_officer'] if a6 else ""
    phone = a6['mobile'] if a6 else ""
    email = a6['email'] if a6 else ""
    
    if not pin and addr:
        pm = re.search(r'\b([1-9][0-9]{2}\s?[0-9]{3})\b', addr)
        if pm:
            pin = pm.group(1).replace(' ', '')
            
    sector = p.get('sector', 'Government Sector')
    if 'Private' in sector:
        sector_val = 'Private'
    else:
        sector_val = 'Government'
        
    prov_compiled.append({
        'vci_serial': f"VCI-PROV-{len(prov_compiled)+1:03d}",
        'official_sr': p['college_serial'] or str(len(prov_compiled)+1),
        'institution_name': re.sub(r'\(w\.e\.f.*?\)', '', c_name).strip(),
        'raw_name': c_name,
        'state': st,
        'university': p['university'],
        'status': 'Provisionally Recognized',
        'category': 'Provisionally Recognized Veterinary College',
        'sector': sector_val,
        'address': addr,
        'pin_code': pin,
        'nodal_officer': officer,
        'contact_phone': phone,
        'contact_email': email,
        'source_doc': p['source_doc']
    })

print(f"Compiled {len(prov_compiled)} canonical provisional colleges, {len(excluded_prov)} excluded duplicate.")
print(f"Total Canonical Physical Institutions: {len(rec_compiled) + len(prov_compiled)}")

with open('data/vci_raw/rec_compiled.json', 'w') as f:
    json.dump(rec_compiled, f, indent=2)

with open('data/vci_raw/prov_compiled.json', 'w') as f:
    json.dump(prov_compiled, f, indent=2)

with open('data/vci_raw/excluded_prov.json', 'w') as f:
    json.dump(excluded_prov, f, indent=2)
