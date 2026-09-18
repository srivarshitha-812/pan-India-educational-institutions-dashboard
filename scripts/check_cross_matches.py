import json

with open('data/vci_raw/parsed_recognized.json') as f:
    rec = json.load(f)
with open('data/vci_raw/parsed_provisional.json') as f:
    prov = json.load(f)

print(f"Recognized count: {len(rec)}")
print(f"Provisional count: {len(prov)}")

print("\nCross-checking each provisional entry:")
for pi, p in enumerate(prov):
    p_name = p['college_name']
    p_state = p['state']
    p_univ = p['university']
    
    # Check if there is an exact or near match in rec
    matches = []
    for ri, r in enumerate(rec):
        r_name = r['college_name']
        r_state = r['state']
        r_univ = r['university']
        
        # Check if state matches and any key town/city or distinctive word matches
        if p_state.lower() == r_state.lower():
            matches.append((ri+1, r_name, r_univ))
            
    print(f"\nProv #{pi+1}: [{p_state}] {p_name} ({p.get('sector', '')}) :: {p_univ}")
    if matches:
        print(f"  Colleges in same state in Recognized list ({len(matches)}):")
        for m in matches:
            print(f"    Rec #{m[0]}: {m[1]} :: {m[2]}")
    else:
        print(f"  -> State {p_state} not present in Recognized list! (New state coverage!)")
