import json
from pathlib import Path
from collections import Counter, defaultdict

raw_dir = Path("data/raw/aishe")
files = [
    ("Category 1: Affiliated Colleges", raw_dir / "aishe_category_1_affiliated.json"),
    ("Category 2: Constituent / University Colleges", raw_dir / "aishe_category_2_constituent.json"),
    ("Category 3: PG Centre / Off-Campus Centres", raw_dir / "aishe_category_3_pg_centres.json"),
    ("Category 4: Recognized Centres", raw_dir / "aishe_category_4_recognized_centres.json"),
    ("Category 5: Autonomous Colleges", raw_dir / "aishe_category_5_autonomous.json")
]

all_records = []
cat_records = {}

for cat_name, filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data.get("institutionDirectoryDto", [])
    cat_records[cat_name] = records
    for r in records:
        r["_source_category"] = cat_name
        all_records.append(r)

print(f"Total raw records loaded: {len(all_records)}")
for cat_name, recs in cat_records.items():
    print(f"  {cat_name}: {len(recs)} records")

# Inspect AISHE codes
codes = [r.get("aisheCode", "").strip() for r in all_records if r.get("aisheCode")]
code_counts = Counter(codes)
unique_codes = set(codes)
duplicate_codes = {k: v for k, v in code_counts.items() if v > 1}

print(f"\nTotal AISHE codes present: {len(codes)}")
print(f"Unique AISHE codes: {len(unique_codes)}")
print(f"Duplicate AISHE codes: {len(duplicate_codes)}")

# Inspect overlapping categories for duplicate codes
print("\nSample duplicate AISHE codes and their categories:")
code_to_recs = defaultdict(list)
for r in all_records:
    c = r.get("aisheCode", "").strip()
    if c in duplicate_codes:
        code_to_recs[c].append(r)

sample_dups = list(duplicate_codes.keys())[:10]
for c in sample_dups:
    recs = code_to_recs[c]
    cats = [r["_source_category"] for r in recs]
    types = [r.get("institutionType") for r in recs]
    names = [r.get("name") for r in recs]
    print(f"  AISHE Code {c} ({len(recs)} times):")
    print(f"    Name: {names[0]}")
    print(f"    Categories: {cats}")
    print(f"    Types: {types}")

# Check States & Districts
states = Counter([r.get("stateName", "").strip() for r in all_records])
print(f"\nStates covered ({len(states)}):")
for s, cnt in sorted(states.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {s}: {cnt}")

districts = set([f"{r.get('stateName')}:{r.get('districtName')}" for r in all_records])
print(f"\nUnique State:District combinations: {len(districts)}")

# Check missing values
missing_aishe = sum(1 for r in all_records if not r.get("aisheCode"))
missing_name = sum(1 for r in all_records if not r.get("name"))
missing_state = sum(1 for r in all_records if not r.get("stateName"))
missing_district = sum(1 for r in all_records if not r.get("districtName"))
print(f"\nMissing fields:")
print(f"  Missing AISHE Code: {missing_aishe}")
print(f"  Missing Name: {missing_name}")
print(f"  Missing State: {missing_state}")
print(f"  Missing District: {missing_district}")
