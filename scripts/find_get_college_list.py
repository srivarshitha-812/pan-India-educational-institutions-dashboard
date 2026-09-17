import re

with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = [m.start() for m in re.finditer(r'getCollegeList\(', text)]
print('Matches for getCollegeList:', len(matches))
for pos in matches:
    print('--- getCollegeList ---')
    print(text[max(0, pos-100):min(len(text), pos+400)])
