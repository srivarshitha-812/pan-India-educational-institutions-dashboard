import pandas as pd

excel_path = 'Final Institute Lists/Ayurveda Colleges.xlsx'
df_ayu = pd.read_excel(excel_path, sheet_name='Ayurveda')
df_uni = pd.read_excel(excel_path, sheet_name='Unani')
df_comb = pd.read_excel(excel_path, sheet_name='Combined')

print("=" * 60)
print("NCISM AYURVEDA & UNANI RECONCILIATION REPORT")
print("=" * 60)
print(f"Ayurveda institution count: {len(df_ayu)}")
print(f"Unani institution count: {len(df_uni)}")
print(f"Combined physical institution count: {len(df_comb)}")
print(f"unique NCISM College IDs: {df_comb['College ID'].nunique()}")
print(f"duplicate College IDs: {len(df_comb) - df_comb['College ID'].nunique()}")
print(f"missing College IDs: {df_comb['College ID'].isna().sum()}")
print(f"missing institution names: {df_comb['Name of the College'].isna().sum()}")
print(f"missing states: {df_comb['State'].isna().sum()}")
missing_dist = df_comb['District'].isna().sum() + (df_comb['District'] == '').sum()
print(f"missing districts: {missing_dist} (Source limitation: NCISM embeds district in address without dedicated column)")

tg_ayu = df_ayu[df_ayu['State'] == 'Telangana']
tg_uni = df_uni[df_uni['State'] == 'Telangana']
print(f"Telangana Ayurveda count: {len(tg_ayu)}")
print(f"Telangana Unani count: {len(tg_uni)}")
print(f"Total Telangana count: {len(tg_ayu) + len(tg_uni)}")
print("\nTelangana institutions:")
for _, r in pd.concat([tg_ayu, tg_uni]).iterrows():
    print(f"  - {r['College ID']}: {r['Name of the College']} (System: {r['System']}, District: {r['District']}, UG Seats: {r['UG Seats']}, PG Seats: {r['PG Seats']})")

print("\nNumber of source documents used: 6")
print("Source URLs:")
print("  1. https://ncismindia.org/assets/pdf/List%20of%20total%20Ayurveda%20Colleges%20across%20country%20as%20on%2005.02.2026.pdf")
print("  2. https://ncismindia.org/assets/pdf/List%20of%20Permitted%20Ayurveda%20Colleges%20for%20the%20A.Y.%202025-26%20as%20on%2002.03.2026.pdf")
print("  3. https://ncismindia.org/assets/pdf/List%20of%20Colleges%20Granted%20LOP%20to%20establish%20New%20Ayurveda%20Colleges%20for%20the%20A.Y.%202025-26%20as%20on%2005.02.2026.pdf")
print("  4. https://ncismindia.org/assets/pdf/List%20of%20total%20Unani%20Colleges%20across%20country%20as%20on%2016.12.2025.pdf")
print("  5. https://ncismindia.org/assets/pdf/List%20of%20Permitted%20Unani%20Colleges%20for%20the%20Academic%20Year%202025-26%20as%20on%2012.12.2025%20.pdf")
print("  6. https://ncismindia.org/assets/pdf/Letter%20of%20Permission%20to%20establish%20new%20Unani%20Colleges%20for%20the%20A.Y.%202025-26%20as%20on%2019.11.2025.pdf")

print("\nAcademic Year / As-Of Dates:")
print("  - Academic Year: 2025-26")
print("  - Ayurveda Total As-Of: 05.02.2026")
print("  - Ayurveda Permitted As-Of: 02.03.2026")
print("  - Ayurveda LOP As-Of: 05.02.2026")
print("  - Unani Total As-Of: 16.12.2025")
print("  - Unani Permitted As-Of: 12.12.2025")
print("  - Unani LOP As-Of: 19.11.2025")
print("  - Collection Date: 2026-09-16")
print("=" * 60)
