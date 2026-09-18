import pdfplumber
import re
import json

# Check ListofRecognizedVeterinaryColleges.pdf
with pdfplumber.open('data/vci_raw/ListofRecognizedVeterinaryColleges.pdf') as pdf:
    pdf_rows = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                cleaned = [c.replace('\n', ' ').strip() if c else '' for c in row]
                if any(cleaned):
                    pdf_rows.append(cleaned)

print(f"ListofRecognizedVeterinaryColleges.pdf extracted rows: {len(pdf_rows)}")
for r in pdf_rows[:8]:
    print("  ", r)

# Check Annexure 2 & 6 of CompositIBAY2026-27.pdf
with pdfplumber.open('data/vci_raw/CompositIBAY2026-27.pdf') as pdf:
    ib_colleges = []
    # Annexure 6: pages 24 to 33
    for p_num in range(23, len(pdf.pages)):
        tables = pdf.pages[p_num].extract_tables()
        for t in tables:
            for row in t:
                cleaned = [c.replace('\n', ' ').strip() if c else '' for c in row]
                # Look for row that has state or university or college
                if len(cleaned) >= 5 and any(k in cleaned[3].lower() or k in cleaned[4].lower() for k in ['college', 'faculty', 'institute', 'department']):
                    ib_colleges.append(cleaned)

print(f"CompositIBAY2026-27.pdf Annexure 6 extracted college rows: {len(ib_colleges)}")
for c in ib_colleges[:8]:
    print("  ", c[:5])
