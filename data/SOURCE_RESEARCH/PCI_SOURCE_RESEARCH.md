# PCI Source Research: Pharmacy Colleges & Institutions

## 1. Executive Summary

| Attribute | Details |
| :--- | :--- |
| **Regulatory Authority** | **Pharmacy Council of India (PCI)** |
| **Statutory Act** | Pharmacy Act, 1948 (Act No. 8 of 1948) |
| **Official Portal** | `https://www.pci.gov.in/` |
| **Direct Section** | Approved Institutes (`/en/approved-institute/*`) |
| **Collection Date** | 2026-09-15 |
| **Universe Scope** | Complete National Register of Approved Pharmacy Institutions |
| **Raw Stream Filings** | **16,033 course-level regulatory records** |
| **Total Physical Institutions** | **6,664 physical colleges/institutions** (Deduplicated by official PCI Code) |
| **Official Identifier** | **PCI College Code** (`naming_series`: e.g. `PCI-1`, `PCI-6`, `PCI-15`) |
| **Geographic Coverage** | **32 States & Union Territories** |
| **Rule Adherence** | **ONE PHYSICAL INSTITUTION = ONE CANONICAL RECORD** |

---

## 2. Official Statutory Streams & Endpoint Architecture

The Pharmacy Council of India publishes its national approved directory across 8 distinct regulatory qualification streams via authenticated DataTables AJAX endpoints:

| Approval Category | Official Portal Route | Raw Stream Records |
| :--- | :--- | :---: |
| **Approved Diploma Institutions u/s 12** | `/en/approved-institute/approved-diploma-institutions-u-s-12/` | 5,127 |
| **Approved institutions for M.Pharm Courses** | `/en/approved-institute/approved-institutions-for-m-pharm-courses/` | 3,909 |
| **Diploma Institutions Only For Conduct** | `/en/approved-institute/diploma-institutions-only-for-conduct/` | 2,797 |
| **Approved Degree Institutions u/s 12** | `/en/approved-institute/approved-degree-institutions-us-12/` | 2,228 |
| **Degree Institutions Only For Conduct** | `/en/approved-institute/degree-institutions-only-for-conduct/` | 1,292 |
| **Approved Institutions for Pharm.D** | `/en/approved-institute/approved-institutions-for-pharm-d/` | 458 |
| **Approved Institutions for Pharm.D (Post Baccalaureate)** | `/en/approved-institute/approved-institutions-for-pharmd-post-baccalaureate/` | 194 |
| **Approved Institutions for Bridge Course** | `/en/approved-institute/approved-institutions-for-bridge-course/` | 28 |
| **Total Regulatory Course Entries** | | **16,033** |

---

## 3. Entity Resolution & Deduplication Methodology

### The Problem: Multi-Stream Filings per Physical Campus
A typical pharmacy college offers multiple courses (e.g., both D.Pharm and B.Pharm, plus specialized M.Pharm branches and Pharm.D). Counting stream rows separately would artificially inflate the national pharmacy institution count by 2.4x (16,033 vs 6,664).

### Resolution Rule
Each physical pharmacy college in India is assigned a unique statutory **PCI Code** (`naming_series`, e.g., `PCI-1`, `PCI-6`, `PCI-108`).
1. All 16,033 regulatory records were mapped and grouped by `PCI College ID`.
2. 4,478 institutions (67.2%) offer multiple streams and were consolidated into their parent physical institution.
3. 2,186 institutions offer a single stream.
4. Exactly **6,664 unique physical colleges** were established with **0 duplicate physical IDs**.

---

## 4. Geographic Distribution (Top States)

| State / UT | Physical Institutions | % of National Total |
| :--- | :---: | :---: |
| **Uttar Pradesh** | 2,278 | 34.2% |
| **Maharashtra** | 822 | 12.3% |
| **Rajasthan** | 477 | 7.2% |
| **Karnataka** | 401 | 6.0% |
| **Madhya Pradesh** | 395 | 5.9% |
| **West Bengal** | 293 | 4.4% |
| **Haryana** | 232 | 3.5% |
| **Jharkhand** | 174 | 2.6% |
| **Tamil Nadu** | 174 | 2.6% |
| **Andhra Pradesh** | 169 | 2.5% |
| **Telangana** | 151 | 2.3% |
| **Punjab** | 149 | 2.2% |
| **Gujarat** | 133 | 2.0% |
| **Uttarakhand** | 133 | 2.0% |
| **Odisha** | 132 | 2.0% |
| **Bihar** | 127 | 1.9% |
| **Chhattisgarh** | 127 | 1.9% |
| **Other 15 States/UTs** | 297 | 4.5% |
| **Total Physical Institutions** | **6,664** | **100.0%** |

---

## 5. Schema & Field Completeness

| Field Name | Completeness | Extraction Logic |
| :--- | :---: | :--- |
| `S.No` | 100.0% | 1 to 6,664 sequential index |
| `Institution Name` | 100.0% | Official name from PCI register |
| `State` | 100.0% | Standardized to canonical 36 States/UTs schema |
| `District` | 89.6% | Resolved by cross-referencing state district masters and regex |
| `City` | 89.6% | Extracted city/locality token |
| `Address` | 100.0% | Full campus, road, mandal, or village string |
| `University / Affiliating University` | 100.0% | Primary examining authority or state technical university |
| `Management Type` | 100.0% | Government / University Constituent vs Private Self-Financed |
| `Approval Status` | 100.0% | Approved u/s 12, Conduct of Course, or Approved |
| `Programmes / Courses` | 100.0% | Unified list of B.Pharm, D.Pharm, M.Pharm, Pharm.D |
| `PCI College ID` | 100.0% | Official statutory PCI Code (`PCI-XXXX`) |
| `Approval Year / Academic Year` | 100.0% | Latest approved academic session (e.g. 2026-2027) |
| `Intake / Seats` | 100.0% | Aggregated seats where specified or council norms |
| `Remarks` | 100.0% | Stream decision counts and AEBAS directives |
| `Source URL` | 100.0% | `https://www.pci.gov.in/` |
| `Collection Date` | 100.0% | `2026-09-15` |
