import json
from collections import Counter

with open('data/nmc_all_colleges_api.json', encoding='utf-8') as f:
    colleges = json.load(f)

with open('data/nmc_all_courses_api.json', encoding='utf-8') as f:
    courses = json.load(f)

print(f"Colleges count: {len(colleges)}")
print(f"Courses count: {len(courses)}")

# Inspect college fields
print("\nCollege fields:")
sample_col = colleges[0]
for k in sample_col:
    vals = [c.get(k) for c in colleges if c.get(k) is not None and str(c.get(k)).strip() != '']
    print(f"  {k}: {len(vals)} non-empty (e.g. {repr(vals[0]) if vals else 'None'})")

# Inspect course fields
print("\nCourse fields:")
sample_crs = courses[0]
for k in sample_crs:
    vals = [c.get(k) for c in courses if c.get(k) is not None and str(c.get(k)).strip() != '']
    print(f"  {k}: {len(vals)} non-empty (e.g. {repr(vals[0]) if vals else 'None'})")

# Check unique colleges in courses vs colleges API
col_ids_in_courses = set(c['collegeId'] for c in courses if c.get('collegeId'))
col_ids_in_colleges = set(c['collegeId'] for c in colleges if c.get('collegeId'))

print(f"\nUnique collegeId in courses: {len(col_ids_in_courses)}")
print(f"Unique collegeId in colleges list: {len(col_ids_in_colleges)}")
print(f"Overlap: {len(col_ids_in_courses & col_ids_in_colleges)}")
print(f"In courses but not in colleges list: {len(col_ids_in_courses - col_ids_in_colleges)}")
print(f"In colleges list but not in courses: {len(col_ids_in_colleges - col_ids_in_courses)}")
