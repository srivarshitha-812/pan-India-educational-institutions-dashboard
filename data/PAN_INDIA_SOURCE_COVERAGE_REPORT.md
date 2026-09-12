# Pan-India Educational Institution Census — Source Coverage Report

**Generated**: 2026-09-10

## Status Legend
- ✅ COMPLETE — Full national extraction verified
- ✅⚠️ COMPLETE_WITH_LIMITATIONS — Data present but with known gaps
- 🔵 API_FOUND_BUT_EXTRACTION_INCOMPLETE — API confirmed, extraction running/partial
- ⚠️ PARTIAL — Partial data only (some states/sources missing)
- ❌ NO_BULK_SOURCE — No public API or bulk download found
- 🔒 OFFICIAL_ACCESS_REQUIRED — Formal request required

## Source Summary

| Source | Count | Status | Method | Official ID | Year | Limitations |
|--------|-------|--------|--------|-------------|------|-------------|
| UDISE+ | 1,466,682 | ✅⚠️ COMPLETE_WITH_LIMITATIONS | Official DSP Research Export (Prof1+Prof | pseudocode (DSP), UDISE Code (11-di | 2025-26 | School_Name and UDISE_Code NOT in DSP export. Mapping via KY |
| UDISE+ KYS Mapping | 501 | 🔵 API_FOUND_BUT_EXTRACTION_INCOMPLETE | KYS API — school/track?schoolId=<pseudoc | udiseschCode (11-digit UDISE Code) | 2025-26 | ~80% hit rate confirmed. 1 req/sec required. Full run = 17 d |
| CBSE SARAS | 33,151 | ✅ COMPLETE | State-wise POST with Anti-Forgery and Fo | CBSE Affiliation Number (e.g. 10000 | 2025-26 | None. 100% extracted across all 38 States/UTs/Foreign school |
| CISCE | 3,320 | ✅ COMPLETE | Full HTML pagination (GET https://locate | CISCE Affiliation Code (e.g. AN001, | 2025 | None. 100% of 332 pagination pages extracted nationally. |
| AISHE | 162 | ⚠️ PARTIAL | API/HTML per-state extraction | AISHE Code (U-XXXX, C-XXXXX) | 2022-23 | Universities captured; college-level API requires browser au |
| AICTE | 0 | ⚠️ PARTIAL | AICTE approved directory probe | AICTE Permanent ID | 2024-25 | Public API requires browser session. Telangana slice complet |
| NCTE | 4 | ⚠️ PARTIAL | REST API per-state probe | NCTE Institution ID | 2025 | Angular application. Telangana slice complete (TS EDCET / NC |
| NMC | 11,585 | ❓ EXCLUDED_LEGACY_SOURCE | Official NMC National Register | NMC College ID (e.g. AN/001/G/1) | 2026-27 | Excluded from national census total per user instruction. Pr |
| INC | 0 | ❌ NO_BULK_SOURCE | ASP.NET WebForms ViewState POST | INC Institution Code | 2025 | ASP.NET ViewState portal with dynamic session keys. Browser  |
| PCI | 0 | ❌ NO_BULK_SOURCE | Portal directory inspection | PCI Institution Code | 2025 | No public bulk API. Formal data request or browser automatio |
| BCI | 3 | ⚠️ PARTIAL | Directory inspection | BCI Centre Code | 2025 | No single national downloadable list. Telangana slice comple |
| CoA | 404 | ✅ COMPLETE | Official National Approval Register GET | CoA Code (e.g. AP02, DL01, TS03) | 2025-26 | None. 100% extracted nationally with approved intake. |
| RCI | 1,055 | ✅ COMPLETE | State-wise JSP POST with statewise param | RCI Institute Code (e.g. AP004, DL0 | 2025 | None. 100% extracted across all 34 States/UTs. |
| NCH | 0 | ⚠️ PARTIAL | HTML scraping | NCH Permit Number | 2025 | NCH website content limited. May require browser automation. |
| NCVT/DGT | 0 | ❌ NO_BULK_SOURCE | ASP.NET WebForms (ViewState required) | NCVT MIS Institute Code | 2025 | NCVT MIS uses ASP.NET ViewState. No JSON API confirmed. ~14, |

## Key Discoveries

### UDISE+ Pseudocode → UDISE Code Mapping (BREAKTHROUGH)

**CONFIRMED**: UDISE+ DSP pseudocode = KYS `schoolId`

- **API**: `GET https://kys.udiseplus.gov.in/web-app/api/school/track?schoolId=<pseudocode>`
- **Returns**: udiseschCode (11-digit UDISE Code), schoolName, state, district, block
- **Authentication**: None required (public endpoint)
- **Hit rate**: ~80% (confirmed with 5 test pseudocodes)
- **Full extraction**: 1.47M schools × 1 req/sec ≈ 17 days runtime

### Verified Test Results

| Pseudocode | UDISE Code | School Name | State |
|------------|------------|-------------|-------|
| 4684147 | 28180400403 | MPPS WEST NAIDUPALEM | ANDHRA PRADESH |
| 4552494 | 27220200373 | R. D. VIDYAMANDIR ENGLISH SCHOOL | MAHARASHTRA |
| 1024396 | 01170701509 | SAFFRON PUBLIC SCHOOL(PS) | JAMMU & KASHMIR |
| 5002144 | 32021300206 | AROLI CENTRAL LPS | KERALA |
| 9664514 | NOT FOUND | — | ANDAMAN & NICOBAR |

### KYS API Confirmed Working Endpoints
- `GET /web-app/api/master/year?year=1` → Year list
- `GET /web-app/api/fetchCategoryList` → School category list
- `GET /web-app/api/fetchManagementList` → Management type list
- `GET /web-app/api/school/track?schoolId=<id>` → School identification (pseudocode→UDISE Code+Name)
- `GET /web-app/api/school/profile?schoolId=<id>&yearId=12` → School profile details

## Important Notes

1. **UDISE Code is permanent** — An 11-digit UDISE Code does not change between academic years.
   Schools opened before 2022-23 will have the same UDISE Code in 2025-26.

2. **NMC already complete** — Medical education data was extracted previously.

3. **UGC, NCISM not required** — Excluded per user instructions.

4. **INC/PCI/NCVT require Playwright** — ASP.NET ViewState portals cannot be easily scraped
   with pure HTTP. Playwright browser automation is the recommended approach.

5. **CoA HTML table** — The Council of Architecture publishes a static HTML table.
   Parse directly from https://coa.gov.in/architectural_institutions.php

## Files Generated

- [AISHE_INSTITUTIONS_2022_23.xlsx](AISHE_INSTITUTIONS_2022_23.xlsx) — 162 rows
- [BCI_INSTITUTIONS_2025.xlsx](BCI_INSTITUTIONS_2025.xlsx) — 3 rows
- [CBSE_INSTITUTIONS_2025.xlsx](CBSE_INSTITUTIONS_2025.xlsx) — 33,151 rows
- [CISCE_INSTITUTIONS_2025.xlsx](CISCE_INSTITUTIONS_2025.xlsx) — 3,320 rows
- [COA_INSTITUTIONS_2025.xlsx](COA_INSTITUTIONS_2025.xlsx) — 404 rows
- [INC_INSTITUTIONS_2025.xlsx](INC_INSTITUTIONS_2025.xlsx) — 0 rows
- [NCH_INSTITUTIONS_2025.xlsx](NCH_INSTITUTIONS_2025.xlsx) — 0 rows
- [NCTE_INSTITUTIONS_2025.xlsx](NCTE_INSTITUTIONS_2025.xlsx) — 4 rows
- [NCTE_PROGRAMMES_2025.xlsx](NCTE_PROGRAMMES_2025.xlsx) — 4 rows
- [NCVT_ITI_INSTITUTIONS_2025.xlsx](NCVT_ITI_INSTITUTIONS_2025.xlsx) — 0 rows
- [NMC_COURSES_2026_27.xlsx](NMC_COURSES_2026_27.xlsx) — 11,585 rows
- [PAN_INDIA_SOURCE_COVERAGE_REPORT.xlsx](PAN_INDIA_SOURCE_COVERAGE_REPORT.xlsx) — 15 rows
- [PCI_INSTITUTIONS_2025.xlsx](PCI_INSTITUTIONS_2025.xlsx) — 0 rows
- [RCI_INSTITUTIONS_2025.xlsx](RCI_INSTITUTIONS_2025.xlsx) — 1,055 rows

## Research Documents

- [AISHE_SOURCE_RESEARCH.md](SOURCE_RESEARCH/AISHE_SOURCE_RESEARCH.md)
- [BCI_SOURCE_RESEARCH.md](SOURCE_RESEARCH/BCI_SOURCE_RESEARCH.md)
- [COA_SOURCE_RESEARCH.md](SOURCE_RESEARCH/COA_SOURCE_RESEARCH.md)
- [INC_SOURCE_RESEARCH.md](SOURCE_RESEARCH/INC_SOURCE_RESEARCH.md)
- [NCH_SOURCE_RESEARCH.md](SOURCE_RESEARCH/NCH_SOURCE_RESEARCH.md)
- [NCTE_SOURCE_RESEARCH.md](SOURCE_RESEARCH/NCTE_SOURCE_RESEARCH.md)
- [NCVT_DGT_SOURCE_RESEARCH.md](SOURCE_RESEARCH/NCVT_DGT_SOURCE_RESEARCH.md)
- [OPEN_DATA_UDISE_RESEARCH.md](SOURCE_RESEARCH/OPEN_DATA_UDISE_RESEARCH.md)
- [PCI_SOURCE_RESEARCH.md](SOURCE_RESEARCH/PCI_SOURCE_RESEARCH.md)
- [RCI_SOURCE_RESEARCH.md](SOURCE_RESEARCH/RCI_SOURCE_RESEARCH.md)
- [UDISE_MICRODATA_RESEARCH.md](SOURCE_RESEARCH/UDISE_MICRODATA_RESEARCH.md)

---
*Report generated: 2026-09-10*