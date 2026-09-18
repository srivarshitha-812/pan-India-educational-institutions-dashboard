import json

with open('data/vci_raw/parsed_recognized.json') as f:
    rec = json.load(f)
with open('data/vci_raw/parsed_provisional.json') as f:
    prov = json.load(f)

print(f"=== 1. ALL RECOGNIZED COLLEGES ({len(rec)}) ===")
for i, r in enumerate(rec):
    print(f"{i+1:02d}. [{r['state']}] {r['college_name']} :: {r['university']}")

print(f"\n=== 2. ALL PROVISIONAL COLLEGES ({len(prov)}) ===")
for i, p in enumerate(prov):
    print(f"{i+1:02d}. [{p['state']}] ({p.get('sector', '')}) {p['college_name']} :: {p['university']}")
