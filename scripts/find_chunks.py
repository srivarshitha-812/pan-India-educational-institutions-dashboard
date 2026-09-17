import re

with open('scratch/aishe_main.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Look for chunk files
chunks = set(re.findall(r'[\'"]([a-zA-Z0-9\.\_\-]+\.js)[\'"]', code))
print('JS chunks found:', chunks)

# Look for route paths like hedirectory or details
routes = set(re.findall(r'path:[\'"]([^\'"]+)[\'"]', code))
print('Routes found:', routes)

# Look for loadChildren
lazy = re.findall(r'loadChildren:[^,}]+', code)
print('Lazy routes:', lazy)
