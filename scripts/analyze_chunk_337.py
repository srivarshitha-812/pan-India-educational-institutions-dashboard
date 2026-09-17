import re

with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for collegeDetails occurrences
matches = [m.start() for m in re.finditer(r'collegeDetails', text)]
print('Matches for collegeDetails:', len(matches))
for i, pos in enumerate(matches[:5]):
    print(f'=== Match {i+1} ===')
    print(text[max(0, pos-100):min(len(text), pos+400)])

# Find service or http methods near collegeDetails
# Search for class or component names
comp_matches = re.findall(r'class\s+([A-Za-z0-9_]+College[A-Za-z0-9_]*)', text)
print('College classes:', comp_matches)

# Search for export methods (excel / pdf)
export_matches = [m.start() for m in re.finditer(r'exportTo(Excel|Pdf|XLS|PDF)', text, re.I)]
print('Export methods found:', len(export_matches))
for i, pos in enumerate(export_matches[:5]):
    print(f'=== Export Match {i+1} ===')
    print(text[max(0, pos-100):min(len(text), pos+400)])
