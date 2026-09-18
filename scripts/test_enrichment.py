import json
import re

with open('data/vci_raw/parsed_recognized.json') as f:
    rec = json.load(f)
with open('data/vci_raw/parsed_provisional.json') as f:
    prov = json.load(f)
with open('data/vci_raw/annexure6_addresses.json') as f:
    annex6 = json.load(f)

print(f"Recognized: {len(rec)}, Provisional: {len(prov)}, Annex6: {len(annex6)}")

# Build lookup by keywords from Annexure 6
def match_annex6(name, state):
    clean_name = re.sub(r'\(.*?\)', '', name).lower()
    # Extract distinctive words
    words = [w for w in re.split(r'[^a-z0-9]', clean_name) if len(w) > 3 and w not in ['college', 'veterinary', 'science', 'sciences', 'animal', 'husbandry', 'research', 'institute', 'faculty']]
    
    best_match = None
    best_score = 0
    for a in annex6:
        if a['state'].lower()[:4] == state.lower()[:4]:
            a_clean = re.sub(r'\(.*?\)', '', a['college_name']).lower()
            a_addr = a['address'].lower()
            score = sum(1 for w in words if w in a_clean or w in a_addr)
            if score > best_score:
                best_score = score
                best_match = a
    if best_score > 0:
        return best_match
    return None

matched_rec = 0
for r in rec:
    m = match_annex6(r['college_name'], r['state'])
    if m:
        matched_rec += 1

print(f"Matched {matched_rec}/{len(rec)} recognized colleges with Annexure 6 rich addresses!")
