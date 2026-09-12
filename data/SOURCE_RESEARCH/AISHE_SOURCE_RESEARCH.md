# AISHE Source Research

## Source Information
- **Source**: All India Survey on Higher Education (AISHE)
- **Managing Authority**: Ministry of Education, Govt. of India
- **Official Portal**: https://aishe.gov.in/
- **HE Directory**: https://dashboard.aishe.gov.in/hedirectory
- **Domain**: All Higher Education Institutions (Universities, Colleges, Standalone)
- **Latest Published Year**: 2022-23 (survey data with AY lag)
- **Extraction Date**: 2026-09-10
- **Status**: HTML_EXTRACTION

## API Discovery Result
No JSON API found — used HTML scraping

## Endpoints Investigated
- https://dashboard.aishe.gov.in/api/hedirectory
- https://dashboard.aishe.gov.in/api/institutions
- https://dashboard.aishe.gov.in/hedirectory/api/getInstList
- https://aishe.gov.in/api/institutions
- (+ 6 other variants)

## Official Identifier
- **AISHE Code** (U-XXXX for universities, C-XXXXX for colleges)

## Fields Available
AISHE_Code, Institution_Name, Level (University/College/Standalone),
Type (State Public/Private/Central/Deemed), Category (Affiliating/Unitary/etc.),
Management, State, District, Address, PIN_Code, Year_Established,
Website, Email, Phone, Courses, Approval_Authority

## Record Counts
- **Total institutions**: 162
- **Unique AISHE codes**: 162

## Levels Covered
- Universities (U-codes)
- Colleges (C-codes)
- Standalone Institutions

## Limitations
- AISHE data has a 1-2 year lag (latest = 2022-23, not 2025-26)
- HE Directory is the most current version but may not reflect all 2025-26 changes
- Some institutions may appear in AISHE but not yet in the HE Directory (newer registrations)
- Affiliated colleges may require separate college-level query per university
