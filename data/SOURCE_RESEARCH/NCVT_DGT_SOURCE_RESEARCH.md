# NCVT_DGT Source Research

## Source Information
- **Source**: NCVT MIS / Directorate General of Training
- **Official URL**: https://ncvtmis.gov.in/
- **Domain**: Industrial Training Institutes (ITIs)
- **Extraction Date**: 2026-09-10
- **Status**: NO_BULK_SOURCE

## Endpoints Investigated
- https://ncvtmis.gov.in/pages/Institute/InstSearch.aspx
- https://ncvtmis.gov.in/api/institutes
- https://skillindiadigital.gov.in/api/institute/list

## API Discovery Result
No public JSON API found. Portal requires browser interaction or CAPTCHA.

## Official Identifier
NCVT MIS Institute Code

## Fields Available
ITI_Name, State, District, Management, Trades, Seats, Grading, Affiliation_Status

## Record Count
- **Extracted**: 0
- **Expected**: ~14,000+ ITIs (Govt + Pvt)

## Limitations
NCVT MIS uses ASP.NET WebForms with ViewState. No public REST JSON API confirmed. May need Playwright or NCVT MIS data download.

## Notes
Official NCVT ITI count: ~14,000+ as of 2024. NCVT MIS 2.0 may have open API.
