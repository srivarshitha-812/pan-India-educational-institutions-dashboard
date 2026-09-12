import json, re

with open('data/nmc_all_colleges_api.json', encoding='utf-8') as f:
    colleges = json.load(f)

with open('data/nmc_all_courses_api.json', encoding='utf-8') as f:
    courses = json.load(f)

# Build a lookup map of colleges from colleges API by collegeId
col_map = {c['collegeId']: c for c in colleges}

# Analyze course collegeName formats
print("Analyzing collegeName in courses:")
names = set(c['collegeName'] for c in courses)
print(f"Distinct collegeName strings in courses: {len(names)}")

with_prefix = 0
without_prefix = 0
samples_without = []

for name in names:
    # check for pattern like XX/000/X/0:
    if re.match(r'^[A-Z]{2,4}/[A-Z0-9/_-]+:\s*', name):
        with_prefix += 1
    else:
        without_prefix += 1
        samples_without.append(name)

print(f"Names with code prefix: {with_prefix}")
print(f"Names without code prefix: {without_prefix}")
print("Samples without code prefix:")
for s in samples_without[:10]:
    print("  ", repr(s))

# Check state and university in courses per collegeId
print("\nChecking state and university consistency per collegeId in courses:")
col_states = {}
col_univs = {}
for c in courses:
    cid = c['collegeId']
    col_states.setdefault(cid, set()).add(c.get('stateName'))
    col_univs.setdefault(cid, set()).add(c.get('univName'))

multi_state = {k: v for k, v in col_states.items() if len(v) > 1}
multi_univ = {k: v for k, v in col_univs.items() if len(v) > 1}
print(f"Colleges with >1 state: {len(multi_state)}")
print(f"Colleges with >1 university: {len(multi_univ)}")
if multi_univ:
    for k, v in list(multi_univ.items())[:5]:
        print(f"  College {k}: {v}")
