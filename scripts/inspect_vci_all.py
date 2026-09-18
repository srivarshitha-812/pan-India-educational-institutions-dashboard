import docx
import pdfplumber
import json
import re

print("="*60)
print("1. RECOGNIZED COLLEGES DOCX (as on 14.5.26)")
print("="*60)
doc_rec = docx.Document('data/vci_raw/list of Recognzied vety. colleges (as on 14.5.26)_0.docx')
t1 = doc_rec.tables[0]
rec_docx_rows = []
curr_state = ""
curr_univ = ""
for ri, r in enumerate(t1.rows):
    if ri == 0:
        continue # header
    raw_cells = [c.text.strip().replace('\n', ' ') for c in r.cells]
    # In table with 6 columns: Sl.No, State, Sr., Name of University, Sr., Name of College
    # Cells can be merged or empty
    col_state = raw_cells[1] if len(raw_cells) > 1 else ""
    col_univ = raw_cells[3] if len(raw_cells) > 3 else ""
    col_college = raw_cells[5] if len(raw_cells) > 5 else raw_cells[-1]

    if col_state and col_state != 'State':
        curr_state = col_state.strip()
    if col_univ and col_univ not in ['Name of University', '-do-']:
        curr_univ = col_univ.strip()
    elif col_univ == '-do-':
        pass # keep curr_univ

    if col_college and col_college not in ['Name of College']:
        rec_docx_rows.append({
            'row_idx': ri,
            'state': curr_state,
            'university': curr_univ,
            'college': col_college,
            'raw': raw_cells
        })

print(f"Total recognized college rows in DOCX: {len(rec_docx_rows)}")
for r in rec_docx_rows[:10]:
    print(f"  [{r['state']}] Univ: {r['university']} | College: {r['college']}")

print("="*60)
print("2. PROVISIONALLY RECOGNIZED DOCX (as on 14.5.26)")
print("="*60)
doc_prov = docx.Document('data/vci_raw/List of Provisionally recognized vety. colleges (as on 14.5.26) (1).docx')
prov_docx_rows = []
curr_sector = "Government Sector"
# Check paragraphs for sector headers
for p in doc_prov.paragraphs:
    txt = p.text.strip()
    if 'Private' in txt:
        curr_sector = "Private Sector"

t_prov = doc_prov.tables[0]
curr_state = ""
curr_univ = ""
for ri, r in enumerate(t_prov.rows):
    if ri == 0:
        continue
    raw_cells = [c.text.strip().replace('\n', ' ') for c in r.cells]
    # S.No, State, Name of College, Name of Affiliating University
    c_state = raw_cells[1] if len(raw_cells) > 1 else ""
    c_college = raw_cells[2] if len(raw_cells) > 2 else ""
    c_univ = raw_cells[3] if len(raw_cells) > 3 else ""

    if c_state and c_state != 'State':
        curr_state = c_state.strip()
    if c_univ and c_univ != '-do-':
        curr_univ = c_univ.strip()
    
    # Check if this row indicates a sector change
    full_row_text = " ".join(raw_cells)
    if 'Private Sector' in full_row_text:
        curr_sector = "Private Sector"
        continue

    if c_college and 'Name of College' not in c_college:
        prov_docx_rows.append({
            'row_idx': ri,
            'sector': curr_sector,
            'state': curr_state,
            'college': c_college,
            'university': curr_univ,
            'raw': raw_cells
        })

print(f"Total provisional college rows in DOCX: {len(prov_docx_rows)}")
for r in prov_docx_rows[:10]:
    print(f"  [{r['state']}] ({r['sector']}) Univ: {r['university']} | College: {r['college']}")

print("="*60)
print("3. RECOGNIZED COLLEGES PDF (ListofRecognizedVeterinaryColleges.pdf)")
print("="*60)
with pdfplumber.open('data/vci_raw/ListofRecognizedVeterinaryColleges.pdf') as pdf:
    pdf_text = ""
    for page in pdf.pages:
        pdf_text += (page.extract_text() or "") + "\n"
# Count colleges in PDF
pdf_colleges = re.findall(r'(\d+)\s+([A-Z][^\n]+(?:College|Faculty|Institute|Department)[^\n]+)\s+(\d+)', pdf_text)
print(f"Regex found in recognized PDF: {len(pdf_colleges)} college entries")

print("="*60)
print("4. COMPOSITE IB AY 2026-27 ANNEXURE 2 & 6 (CompositIBAY2026-27.pdf)")
print("="*60)
with pdfplumber.open('data/vci_raw/CompositIBAY2026-27.pdf') as pdf:
    # Annexure 2 is on pages 16-20
    print("Extracting Annexure 2 (Participating colleges & seats)...")
    annex2_text = ""
    for p_num in range(15, 21):
        annex2_text += (pdf.pages[p_num].extract_text() or "") + "\n"
    
    # Annexure 6 is on pages 24-33 (Addresses & Nodal officers)
    print("Extracting Annexure 6 (College Addresses & Nodal Officers)...")
    annex6_text = ""
    for p_num in range(23, len(pdf.pages)):
        annex6_text += (pdf.pages[p_num].extract_text() or "") + "\n"

print("Annexure 2 sample lines:")
for line in annex2_text.split('\n')[:15]:
    if line.strip():
        print("  ", line.strip())

print("\nAnnexure 6 sample lines:")
for line in annex6_text.split('\n')[:15]:
    if line.strip():
        print("  ", line.strip())
