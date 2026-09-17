import re

for fname in ['scratch/337.52e2d3e8e3776afe.js', 'scratch/aishe_main.js']:
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()
    matches = [m.start() for m in re.finditer(r'getEncryptedValue', text)]
    print(f'Matches for getEncryptedValue in {fname}:', len(matches))
    for pos in matches[:3]:
        print('---')
        print(text[max(0, pos-150):min(len(text), pos+300)])
