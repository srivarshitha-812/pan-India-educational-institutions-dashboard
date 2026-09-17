import re

with open('scratch/aishe_main.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for endpoint patterns: this.http.get( or this.http.post( or URL construction
matches = re.findall(r'(\.get\([^\)]+\)|\.post\([^\)]+\))', text)
print('HTTP calls found:', len(matches))
for m in matches[:25]:
    print(' ', m[:120])

# Look for words around 'college'
college_contexts = [m.start() for m in re.finditer(r'college', text, re.I)]
print('College occurrences:', len(college_contexts))
for idx in college_contexts[:10]:
    print('---')
    print(text[max(0, idx-100):min(len(text), idx+150)])
