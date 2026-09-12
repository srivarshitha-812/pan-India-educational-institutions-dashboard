import json, re

with open('data/nmc_all_courses_api.json', encoding='utf-8') as f:
    courses = json.load(f)

with open('data/nmc_all_colleges_api.json', encoding='utf-8') as f:
    colleges = json.load(f)

col_dict = {c['collegeId']: c for c in colleges}

code_to_colleges = {}
col_to_code = {}

for c in courses:
    cid = c['collegeId']
    cname = c['collegeName'].strip()
    if cid not in col_to_code:
        # Check if has prefix
        m = re.match(r'^([A-Z0-9/_-]+):\s*(.*)$', cname)
        if m:
            code = m.group(1).strip()
            clean_name = m.group(2).strip()
        else:
            code = f"NMC-{cid:04d}"
            clean_name = cname
        
        col_to_code[cid] = (code, clean_name, cname)
        code_to_colleges.setdefault(code, []).append(cid)

print(f"Total unique colleges in courses: {len(col_to_code)}")
print(f"Total unique codes: {len(code_to_colleges)}")

duplicates = {k: v for k, v in code_to_colleges.items() if len(v) > 1}
print(f"Duplicate codes: {len(duplicates)}")
if duplicates:
    for k, v in duplicates.items():
        print(f"  Code {k} shared by collegeIds: {v}")
        for cid in v:
            print(f"    cid {cid}: {col_to_code[cid]}")
