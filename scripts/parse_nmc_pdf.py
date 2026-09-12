import PyPDF2, re

reader = PyPDF2.PdfReader('../College and Course Search _ NMC.pdf')
print(f"Total pages: {len(reader.pages)}")

# Print text of first 3 pages with utf-8 encoding to file
with open('data/pdf_extracted_sample.txt', 'w', encoding='utf-8') as out:
    for i in range(min(5, len(reader.pages))):
        out.write(f"\n--- PAGE {i+1} ---\n")
        out.write(reader.pages[i].extract_text() or '')

print("Wrote first 5 pages to data/pdf_extracted_sample.txt")
