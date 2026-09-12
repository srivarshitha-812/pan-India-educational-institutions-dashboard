from bs4 import BeautifulSoup
from pathlib import Path
import re

content = Path('data/raw/rci/rci_jsp_response.html').read_text(encoding='utf-8', errors='replace')
soup = BeautifulSoup(content, 'html.parser')
forms = soup.find_all('form')
print('Forms:', [(f.get('action'), f.get('method')) for f in forms])

keywords = ['Institute', 'College', 'School', 'Centre', 'Center', 'University']
for kw in keywords:
    matches = soup.find_all(string=lambda text: text and kw in text)
    print(f'Keyword "{kw}": {len(matches)} matches')
    sample = [m.strip() for m in matches[:5] if len(m.strip()) > 5]
    print('  Sample:', sample[:3])

# Check all tags
tag_counts = {}
for tag in soup.find_all(True):
    tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
print('Top tags in document:', sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15])
