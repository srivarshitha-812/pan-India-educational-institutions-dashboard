"""
inspect_rci_coa.py
Inspect saved HTML for RCI and CoA to identify extraction structure.
"""
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent.parent

def inspect_rci():
    rci_p = BASE / "data" / "raw" / "rci" / "rci_jsp_response.html"
    if not rci_p.exists():
        print("RCI file not found")
        return
    content = rci_p.read_text(encoding="utf-8", errors="replace")
    print(f"RCI content length: {len(content):,} chars")
    soup = BeautifulSoup(content, "html.parser")
    selects = soup.find_all("select")
    print("RCI selects:", [(s.get("name"), s.get("id")) for s in selects])
    for s in selects:
        opts = s.find_all("option")
        print(f"  Select name={s.get('name')}: {len(opts)} options")
        for o in opts[:10]:
            print(f"    val='{o.get('value')}' text='{o.get_text(strip=True)}'")

def inspect_coa():
    coa_p = BASE / "data" / "raw" / "coa" / "coa_institutions_page.html"
    if not coa_p.exists():
        print("CoA file not found")
        return
    content = coa_p.read_text(encoding="utf-8", errors="replace")
    print(f"\nCoA content length: {len(content):,} chars")
    soup = BeautifulSoup(content, "html.parser")
    tables = soup.find_all("table")
    print(f"CoA tables: {len(tables)}")
    links = soup.find_all("a", href=True)
    pdf_links = [l for l in links if ".pdf" in l["href"].lower() or "download" in l["href"].lower() or "status" in l["href"].lower()]
    print(f"CoA document/list links: {len(pdf_links)}")
    for l in pdf_links[:10]:
        print(f"  text='{l.get_text(strip=True)}' href='{l['href']}'")

if __name__ == "__main__":
    inspect_rci()
    inspect_coa()
