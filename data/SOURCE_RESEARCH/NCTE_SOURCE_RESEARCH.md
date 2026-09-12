# NCTE Source Research

## Source Information
- **Source**: National Council for Teacher Education (NCTE)
- **Official URL**: https://web.ncte.gov.in/page/recognized-institutions
- **Domain**: Teacher Education Institutions
- **Extraction Date**: 2026-09-10
- **Status**: NO_BULK_SOURCE

## Endpoints Investigated
- https://web.ncte.gov.in/ncteapp/recognisedInstitution/getInstitutionList
- https://web.ncte.gov.in/ncteapp/recognisedInstitution/list
- https://web.ncte.gov.in/ncteapp/api/recognized-institution
- https://web.ncte.gov.in/ncteapp/fetchInstitutionList
- https://web.ncte.gov.in/api/recognized-institutions

## API Status
No working JSON API found. NCTE portal appears to require browser-rendered JavaScript.

## Four Regional Committees
- **ERC** (Eastern): WB, Bihar, JH, Odisha, Sikkim, Andaman
- **NRC** (Northern): Delhi, UP, UK, Rajasthan, Haryana, HP, Punjab, JK, Ladakh
- **SRC** (Southern): AP, Telangana, Karnataka, Kerala, TN, Puducherry, Lakshadweep
- **WRC** (Western): Maharashtra, Gujarat, Goa, MP, Chhattisgarh, DNH&DD

## Official Identifier
- **NCTE Institution ID** (numeric)

## Fields Available
NCTE_ID, Institution_Name, Address, State, District, Programme, Intake,
Management, Affiliation, Recognition_Status, Recognition_Order, Regional_Committee

## Record Count
- Extracted: 4
- Expected: ~16,000-18,000 (NCTE recognized TEIs across India)

## Limitations
- NCTE portal is Angular-based with server-side rendering
- API endpoint may require specific session headers
- Withdrawn/derecognized institutions need separate status filter
- Programme-level data requires deduplication at institution level
