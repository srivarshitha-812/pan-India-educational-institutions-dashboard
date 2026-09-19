import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ckpt_file = BASE / "data" / "checkpoints" / "ncvt_national_checkpoint.json"

with open(ckpt_file, "r", encoding="utf-8") as f:
    ckpt = json.load(f)

all_records_by_state = ckpt.get("all_records_by_state", {})
audit_log = ckpt.get("audit_log", [])

all_records = []
for state, recs in all_records_by_state.items():
    all_records.extend(recs)

print(f"Total raw records in checkpoint: {len(all_records)}")

# Deduplication
seen_codes = set()
seen_comp = set()
unique_records = []
duplicates = []

for r in all_records:
    code = (r.get("iti_code") or "").strip()
    state = (r.get("state") or "").strip().upper()
    dist = (r.get("district") or "").strip().upper()
    name = (r.get("name") or "").strip().upper()
    comp = f"{state}|{dist}|{name}"
    
    if code:
        if code in seen_codes:
            duplicates.append(r)
            continue
        seen_codes.add(code)
    else:
        if comp in seen_comp:
            duplicates.append(r)
            continue
        seen_comp.add(comp)
    unique_records.append(r)

print(f"Unique canonical records: {len(unique_records)}")
print(f"Duplicate records merged: {len(duplicates)}")

# State and District breakdown
states_covered = set()
districts_covered = set()
missing_code = 0
missing_name = 0
missing_state = 0
missing_dist = 0
govt_count = 0
pvt_count = 0

for r in unique_records:
    code = (r.get("iti_code") or "").strip()
    name = (r.get("name") or "").strip()
    st = (r.get("state") or "").strip()
    dt = (r.get("district") or "").strip()
    mgmt = (r.get("management_type") or "").lower()
    
    if not code: missing_code += 1
    if not name: missing_name += 1
    if not st: missing_state += 1
    else: states_covered.add(st.upper())
    if not dt: missing_dist += 1
    else: districts_covered.add(f"{st.upper()}|{dt.upper()}")
    
    if "gov" in mgmt: govt_count += 1
    else: pvt_count += 1

print(f"States/UTs covered: {len(states_covered)}")
print(f"Districts covered: {len(districts_covered)}")
print(f"Missing ITI Codes: {missing_code}")
print(f"Missing Names: {missing_name}")
print(f"Missing States: {missing_state}")
print(f"Missing Districts: {missing_dist}")
print(f"Govt ITIs: {govt_count}")
print(f"Private ITIs: {pvt_count}")

# Check audit log for inaccessible states
print("\n--- Inaccessible / Failed States in Audit Log ---")
for a in audit_log:
    if a.get("status") != "SUCCESS" or a.get("records_collected", 0) == 0:
        print(f"State: {a.get('state')} | Status: {a.get('status')} | Records: {a.get('records_collected')} | Error: {a.get('error')[:80] if a.get('error') else 'None'}")
