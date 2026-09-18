"""
Inspect ICAR Excel file structure - sheets, columns, sample data
"""
import pandas as pd
import openpyxl
from pathlib import Path

RAW_DIR = Path("data/icar_raw")

files = [
    ("List-1",  "ICAR_List1_SAUs_DUs_CAUs_Universities_Colleges_Programmes.xlsx"),
    ("List-1A", "ICAR_List1A_Constituent_Colleges_Faculties.xlsx"),
    ("List-2",  "ICAR_List2_Private_Public_Affiliated_Colleges.xlsx"),
    ("List-3",  "ICAR_List3_Constituent_Affiliated_General_Universities_Public.xlsx"),
]

for list_name, fname in files:
    fpath = RAW_DIR / fname
    print("=" * 70)
    print(f"FILE: {list_name} - {fname}")
    print("=" * 70)
    
    wb = openpyxl.load_workbook(fpath, read_only=True)
    print(f"Sheets: {wb.sheetnames}")
    wb.close()
    
    for sheet_name in openpyxl.load_workbook(fpath, read_only=True).sheetnames:
        try:
            df = pd.read_excel(fpath, sheet_name=sheet_name, header=None)
            print(f"\n  Sheet: '{sheet_name}' - Shape: {df.shape}")
            
            # Print all rows to understand structure
            print(f"  First 10 rows (all columns):")
            pd.set_option('display.max_columns', 50)
            pd.set_option('display.max_colwidth', 80)
            pd.set_option('display.width', 300)
            for i, row in df.head(10).iterrows():
                non_null = {j: str(v)[:80] for j, v in row.items() if pd.notna(v) and str(v).strip()}
                if non_null:
                    print(f"    Row {i}: {non_null}")
            
            print(f"  Last 5 rows:")
            for i, row in df.tail(5).iterrows():
                non_null = {j: str(v)[:80] for j, v in row.items() if pd.notna(v) and str(v).strip()}
                if non_null:
                    print(f"    Row {i}: {non_null}")
        except Exception as e:
            print(f"  Error reading sheet '{sheet_name}': {e}")
    
    print()
