# PAN-INDIA Educational Institution Data Collection & Verification System

A production-grade data collection, normalization, deduplication, and regulatory verification platform covering the entire spectrum of educational institutions across India:
1. Pre-primary
2. Primary
3. Upper Primary
4. Secondary
5. Higher Secondary
6. Colleges
7. Universities
8. Standalone higher-education institutions
9. Technical/engineering institutions
10. Medical institutions
11. Dental institutions
12. Pharmacy institutions
13. Law institutions
14. Teacher-education institutions
15. Management institutions
16. Institutes of National Importance (INIs)
17. Other recognised higher-education institutions

---

## 🏛️ Authoritative Primary Data Sources

| Domain / Level | Statutory Regulatory Authority | Portal | Identifier |
| :--- | :--- | :--- | :--- |
| **School Education** | Ministry of Education / UDISE+ | [kys.udiseplus.gov.in](https://kys.udiseplus.gov.in/) | **UDISE Code** (11 digits) |
| **Higher Education** | Ministry of Education / AISHE | [aishe.gov.in](https://aishe.gov.in/) | **AISHE Code** (e.g. `U-0496`, `C-27481`, `S-10420`) |
| **Universities / HEIs** | University Grants Commission (UGC) | [ugc.gov.in](https://www.ugc.gov.in/) | **UGC Ref / Gazette** |
| **Technical / Engineering / Management** | AICTE | [facilities.aicte-india.org](https://facilities.aicte-india.org/) | **AICTE Permanent ID** |
| **Medical Education** | National Medical Commission (NMC) | [nmc.org.in](https://www.nmc.org.in/) | **NMC College ID** |
| **Teacher Education** | National Council for Teacher Education (NCTE) | [ncte.gov.in](https://ncte.gov.in/) | **NCTE File / Ref ID** |
| **Law Education** | Bar Council of India (BCI) | [barcouncilofindia.org](https://www.barcouncilofindia.org/) | **BCI Approval Ref** |

---

## 🚀 Getting Started & CLI Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. School Education Collection (UDISE+)
```bash
# Specific District in a State (Smallest test: Telangana -> Khammam)
python scraper.py --category schools --state TELANGANA --district KHAMMAM

# All Districts in a State
python scraper.py --category schools --state TELANGANA

# All-India School Collection
python scraper.py --category schools --all-india
```

### 3. Higher Education Collection (AISHE)
```bash
# State-level Higher Education (Universities, Colleges, Standalones, INIs)
python scraper.py --category higher_education --state TELANGANA

# All-India Higher Education
python scraper.py --category higher_education --all-india
```

### 4. Professional & Statutory Regulators
```bash
# UGC Universities
python scraper.py --category universities --state TELANGANA

# AICTE Technical & Engineering Institutions
python scraper.py --category technical --state TELANGANA

# NMC Medical Colleges & MBBS/PG Seats
python scraper.py --category medical --state TELANGANA

# NCTE Teacher Education (Recognised vs De-recognised)
python scraper.py --category teacher_education --state TELANGANA

# BCI Law Institutions
python scraper.py --category law --state TELANGANA
```

### 5. Full Pipeline & All-India Execution
```bash
# Complete collection across all categories & regulators for a state
python scraper.py --category all --state TELANGANA

# Resume interrupted collection from last checkpoint
python scraper.py --resume

# Force re-run and reset checkpoints
python scraper.py --force

# Generate all output reports & verification audits
python scraper.py --export
```

---

## 📊 Generated Output Files

All output files are generated in `data/processed/`:

1. **`master_institutions.xlsx`**: Master Excel database with all 38 standardized columns.
2. **`master_institutions.csv`**: UTF-8 BOM CSV representation for large-scale analysis.
3. **`verification_report.xlsx`**: Complete audit trail showing the statutory evidence, verification rules applied, and timestamps for each institution.
4. **`data_quality_report.xlsx`**: Data completeness analytics, missing field audits, breakdown by level, type, state, and district.
5. **`state_summary.xlsx`**: Cross-tabulation of institution counts by state and education level.
6. **`source_summary.xlsx`**: Regulator-level audit summary and checkpoint logs.

---

## 🔒 Verification System & State Machine

| Status | Definition & Statutory Evidence |
| :--- | :--- |
| **`VERIFIED`** | Explicitly validated by statutory authority (UDISE+ code for schools, UGC gazette for universities, AICTE approval for technical institutes, NMC for medical, NCTE for teacher ed, BCI for law). |
| **`PARTIALLY VERIFIED`** | Listed in primary directory (e.g. AISHE) with valid official ID; secondary statutory gazette confirmation in progress. |
| **`NEEDS VERIFICATION`** | Missing definitive official registry code or ambiguous entity. |
| **`DE-RECOGNISED`** | Explicitly listed in regulator derecognition or withdrawal gazette. |
| **`CLOSED/INACTIVE`** | Recorded as defunct, zero intake, or closed in official registers. |
| **`DUPLICATE`** | Redundant duplicate resolved and linked into master canonical entity. |

---

## 🔍 Auditability: Single-Row Provenance

Every record in `master_institutions.xlsx` answers:
- **Where did this institution come from?** $\rightarrow$ `Source Database` and `Source URL`
- **How was it verified?** $\rightarrow$ `Recognition Authority`, `Approval Authority`, `Verification Status`, `Last Verification Date`, and `Remarks`
