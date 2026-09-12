# INC Source Research

## Source Information
- **Source**: Indian Nursing Council
- **Official URL**: https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx
- **Domain**: Nursing and Midwifery Education Institutions
- **Extraction Date**: 2026-09-10
- **Status**: NO_BULK_SOURCE

## Endpoints Investigated
- https://online.indiannursingcouncil.org/Reports/YearlyReportByState.aspx
- https://online.indiannursingcouncil.org/api/institutions

## API Discovery Result
No public JSON API found. Portal requires browser interaction or CAPTCHA.

## Official Identifier
INC Institution Code

## Fields Available
Institution_Name, State, District, Sector, Programme, Intake, Recognition_Status

## Record Count
- **Extracted**: 0
- **Expected**: ~5,000+

## Limitations
INC portal uses ASP.NET WebForms with ViewState. State-by-state extraction requires simulating form posts with ViewState token. No public JSON API found. Browser automation (Playwright) recommended for full extraction.

## Notes
Programme-level data requires deduplication at institution level.
