"""
parse_rci_html.py — Parse the RCI JSP response HTML (377K chars)
"""

import re
import html as htmlmod
import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "rci"

# Load the saved HTML
html_path = RAW_DIR / "rci_jsp_response.html"
if not html_path.exists():
    print("ERROR: rci_jsp_response.html not found")
    exit(1)

html_content = html_path.read_text(encoding="utf-8", errors="replace")
print(f"HTML size: {len(html_content):,} chars")

# Print first 2000 chars to see structure
print("\n--- First 2000 chars ---")
print(html_content[:2000])

# Print a section from around the middle to find table data
mid = len(html_content) // 2
print(f"\n--- Middle section (chars {mid}-{mid+2000}) ---")
print(html_content[mid:mid+2000])

# Try to find table rows
print("\n--- Searching for table patterns ---")

# Find all <tr> rows
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.S | re.I)
print(f"Total <tr> rows: {len(rows)}")

# Show first few non-header rows
for i, row in enumerate(rows[:5]):
    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S | re.I)
    def c(x):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', htmlmod.unescape(x))).strip()
    cc = [c(cell) for cell in cells]
    print(f"\nRow {i}: {len(cells)} cells")
    for j, cell in enumerate(cc[:5]):
        print(f"  Cell {j}: {cell[:80]}")

# Try to find institution name patterns
print("\n--- Searching for institution name patterns ---")
inst_patterns = [
    r'(?:NURSING|NURSING COLLEGE|GNM|ANM|BSc|MSc)[^\n<]{5,80}',
    r'(?:College|Institute|School|Training)[^\n<]{5,80}',
]
for pat in inst_patterns:
    matches = re.findall(pat, html_content, re.I)
    if matches:
        print(f"Pattern '{pat[:30]}': {len(matches)} matches")
        for m in matches[:3]:
            print(f"  {m[:80]}")
