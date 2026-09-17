import re

with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for occurrences of dataSource.data = 
matches = [m.start() for m in re.finditer(r'dataSource\.data\s*=', text)]
print('Matches for dataSource.data = :', len(matches))
for i, pos in enumerate(matches):
    print(f'=== Match {i+1} ===')
    print(text[max(0, pos-200):min(len(text), pos+300)])
