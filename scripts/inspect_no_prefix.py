import json, re

with open('data/nmc_all_courses_api.json', encoding='utf-8') as f:
    courses = json.load(f)

with open('data/nmc_all_colleges_api.json', encoding='utf-8') as f:
    colleges = json.load(f)

col_map = {c['collegeId']: c for c in colleges}

seen = {}
for c in courses:
    cid = c['collegeId']
    cname = c['collegeName'].strip()
    if cid not in seen:
        seen[cid] = (cname, c.get('stateName'), c.get('univName'))

no_prefix = []
for cid, (cname, sname, uname) in seen.items():
    if not re.match(r'^[A-Z0-9/_-]+:\s*', cname):
        c_obj = col_map.get(cid, {})
        no_prefix.append((cid, c_obj.get('collegeCode'), cname, sname, uname))

print(f"Total without prefix: {len(no_prefix)}")
for item in no_prefix:
    print(item)
