import re

with open('scratch/aishe_main.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Search for collegeDetails in route or component
matches = [m.start() for m in re.finditer(r'collegeDetails', code)]
print('Matches for collegeDetails:', len(matches))
for pos in matches:
    print('---')
    print(code[max(0, pos-150):min(len(code), pos+350)])

# Search for xlsx or excel or download
for keyword in ['xlsx', 'excel', 'export', 'download', 'mat-table']:
    cnt = len(list(re.finditer(keyword, code, re.I)))
    print(f'Count for {keyword}:', cnt)
