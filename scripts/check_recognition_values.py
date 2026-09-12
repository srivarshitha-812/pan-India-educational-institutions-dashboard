import json
from collections import Counter

with open('data/nmc_all_courses_api.json', encoding='utf-8') as f:
    courses = json.load(f)

print("Recognization counts:")
rec_counts = Counter(c.get('recognization') for c in courses)
for k, v in rec_counts.items():
    print(f"  {repr(k)}: {v}")

print("\nSample status for each recognization value:")
for r_val in rec_counts:
    samples = [c.get('status') for c in courses if c.get('recognization') == r_val][:5]
    print(f"  Recognization {r_val}:")
    for s in samples:
        print(f"    {repr(s)}")
