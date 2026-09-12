"""
cleanup_unnecessary_excels.py
Safely removes all obsolete, redundant, intermediate, and stub Excel files,
while preserving certified deliverables and authoritative source datasets.
"""

import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Whitelist of Excel files to KEEP (relative to BASE)
KEEP_FILES = {
    # The 3 certified completed deliverables + summary requested by the user
    Path("data/COMPLETED_DATA/TELANGANA_COMPLETED.xlsx"),
    Path("data/COMPLETED_DATA/COA_COMPLETED_2025_26.xlsx"),
    Path("data/COMPLETED_DATA/RCI_COMPLETED_2025.xlsx"),
    Path("data/COMPLETED_DATA/COMPLETED_DATA_SUMMARY.xlsx"),
    
    # Master Pan-India Census Workbook (3 tabs: National Census, Excluded NMC, Overseas CBSE)
    Path("data/processed/PAN_INDIA_EDUCATIONAL_INSTITUTES.xlsx"),
    
    # Authoritative primary source extractions
    Path("data/CBSE_INSTITUTIONS_2025.xlsx"),
    Path("data/CISCE_INSTITUTIONS_2025.xlsx"),
    Path("data/NMC_COURSES_2026_27.xlsx"),
    Path("data/PAN_INDIA_SOURCE_COVERAGE_REPORT.xlsx"),
}

def main():
    print("=" * 80)
    print("CLEANUP OF UNNECESSARY EXCEL FILES")
    print("=" * 80)
    
    # 1. Verify kept files exist
    print("\n[1] Verifying preservation whitelist...")
    for rel_path in KEEP_FILES:
        full_path = BASE / rel_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024 * 1024)
            print(f"  [PRESERVED] {rel_path} ({size_mb:.2f} MB)")
        else:
            print(f"  [WARNING] File in whitelist does not exist: {rel_path}")

    # 2. Find all excels in repository
    all_excels = list(BASE.rglob("*.xlsx")) + list(BASE.rglob("*.xls"))
    
    deleted_count = 0
    deleted_bytes = 0
    deleted_list = []
    
    print("\n[2] Identifying and removing unnecessary Excel files...")
    for excel_path in sorted(all_excels):
        rel_path = excel_path.relative_to(BASE)
        
        # Check if in whitelist
        if rel_path in KEEP_FILES:
            continue
            
        file_size = excel_path.stat().st_size
        size_str = f"{file_size / (1024*1024):.2f} MB" if file_size >= 1024*1024 else f"{file_size / 1024:.1f} KB"
        
        # Delete file
        try:
            excel_path.unlink()
            deleted_count += 1
            deleted_bytes += file_size
            deleted_list.append((str(rel_path), size_str))
            print(f"  [DELETED] {str(rel_path):<60} ({size_str})")
        except Exception as e:
            print(f"  [ERROR DELETING] {rel_path}: {e}")
            
    print("\n" + "=" * 80)
    print(f"CLEANUP SUMMARY: Removed {deleted_count} unnecessary Excel files ({deleted_bytes / (1024*1024):.2f} MB freed)")
    print("=" * 80)
    
    # 3. List remaining Excel files
    remaining = list(BASE.rglob("*.xlsx")) + list(BASE.rglob("*.xls"))
    print(f"\nRemaining Excel files in repository ({len(remaining)} total):")
    for r in sorted(remaining):
        rel = str(r.relative_to(BASE))
        size_str = f"{r.stat().st_size / (1024*1024):.2f} MB" if r.stat().st_size >= 1024*1024 else f"{r.stat().st_size / 1024:.1f} KB"
        print(f"  - {rel:<60} ({size_str})")

if __name__ == "__main__":
    main()
