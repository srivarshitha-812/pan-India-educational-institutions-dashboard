import re

with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Search for Qa definition
matches = [m.start() for m in re.finditer(r'(let|var|const)\s+Qa\s*=\s*(class|\(\(\))', text)]
print('Matches for Qa definition:', len(matches))
for pos in matches:
    print('--- Qa definition ---')
    print(text[pos:pos+2500])
