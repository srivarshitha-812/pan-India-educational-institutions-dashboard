# NCH Source Research

## Source Information
- **Source**: National Commission for Homoeopathy (NCH)
- **Official Website**: https://nch.org.in/
- **Direct PDF URL**: https://nch.org.in/upload/Permission-Status%20as%20on%2003-08-2026.pdf
- **Domain**: Homoeopathy Education Institutions
- **Academic Year**: 2026-27
- **Document Date (As-on)**: 2026-08-03
- **Extraction Date**: 2026-09-15
- **Status**: COMPLETE ✓

## Source Document Description

The NCH publishes an annual **"Status of Permission/Denial"** PDF document, accessible from
the **Colleges** menu on `nch.org.in`. The document for AY 2026-27 is dated **03-08-2026** and
covers all Homoeopathic Medical Colleges in India that have applied to the MARBH (Medical Assessment
and Rating Board for Homoeopathy) for UG (BHMS) and/or PG (MD Homoeopathy) permissions.

### PDF Columns
| Column | Description |
|--------|-------------|
| No | Serial number (1–299) |
| College Name | Full name + address + email |
| STATE | State/UT |
| College Code | Official NCH college code |
| Govt/Pvt | Management type |
| Seat Intake UG | UG seat intake applied |
| Permission UG (incl. EWS) | UG permission granted seats |
| Seat Intake PG | PG seat intake |
| Permission PG | PG permission |
| Seat Intake PG (Subject Wise) | Subject-wise PG seat breakdown |
| Permission PG (Subject Wise) | Subject-wise PG permission |
| Reduction of Seats | Seat reduction notes |
| MARBH Decision | Final MARBH board decision |
| Scheme | UG / UG+PG / PG |

## Endpoints Investigated
- https://nch.org.in/ (homepage with Colleges menu)
- https://nch.org.in/heb (Homoeopathy Education Board page)
- https://nch.org.in/marbh (MARBH page)
- **https://nch.org.in/upload/Permission-Status%20as%20on%2003-08-2026.pdf** ← primary source (official PDF)

## Extraction Method
- **Tool**: pdfplumber (Python)
- **Method**: Table-based extraction, page-by-page
- **Pages processed**: 25 / 25 (100%)
- **Tables extracted**: 25

## Official Identifier
- **NCH College Code** — primary official ID (3-4 digit numeric, grouped by state)
- 9 colleges have no code yet (newly applied); these use `NCH_DERIVED_<SNo>` as canonical key

## Record Count
| Metric | Value |
|--------|-------|
| Extracted (unique institutions) | **299** |
| College number range | 1 – 299 |
| Number gaps | None (sequential 1–299) |
| Official stated count in PDF | Not explicitly stated |
| Expected national count | ~250–300 |

## Permission Status Breakdown (AY 2026-27)
| Status | Count |
|--------|-------|
| Conditional Permission | 93 |
| Denial | 39 |
| Permission | 52 |
| Permission Withheld | 1 |
| Status Not Available (AY 2026-27) | 114 |

## State/UT Coverage (26 states)
- **Andhra Pradesh**: 8 colleges
- **Arunachal Pradesh**: 1 colleges
- **Assam**: 1 colleges
- **Bihar**: 15 colleges
- **Chandigarh**: 1 colleges
- **Chhattisgarh**: 3 colleges
- **Delhi**: 3 colleges
- **Goa**: 1 colleges
- **Gujarat**: 51 colleges
- **Haryana**: 1 colleges
- **Himachal Pradesh**: 1 colleges
- **Jammu & Kashmir**: 1 colleges
- **Jharkhand**: 7 colleges
- **Karnataka**: 19 colleges
- **Kerala**: 6 colleges
- **Madhya Pradesh**: 29 colleges
- **Maharashtra**: 74 colleges
- **Meghalaya**: 1 colleges
- **Odisha**: 7 colleges
- **Punjab**: 4 colleges
- **Rajasthan**: 15 colleges
- **Tamil Nadu**: 14 colleges
- **Telangana**: 6 colleges
- **Uttar Pradesh**: 16 colleges
- **Uttarakhand**: 2 colleges
- **West Bengal**: 12 colleges

## Fields Available in Output
`SNo`, `Institution_Name`, `Full_Name_Address`, `Email`, `Pincode`, `State`, `District`, `City`,
`NCH_College_Code`, `Identifier_Type`, `Canonical_Key`, `Management_Type`, `Management_Type_Raw`,
`UG_Seat_Intake`, `UG_Permission`, `UG_Permission_Raw`, `PG_Seat_Intake`, `PG_Permission`,
`PG_Seat_Intake_Subject_Wise`, `PG_Permission_Subject_Wise`, `Reduction_of_Seats_Note`,
`MARBH_Decision`, `MARBH_Decision_Raw`, `Overall_Permission_Status`, `Scheme`,
`Academic_Year`, `Source_URL`, `Source_Date`, `Collection_Date`, `Source_Page`

## Fields NOT Available in Source
- **District** (embedded in full address text; not separately parsed)
- **City** (embedded in full address text)
- **University/Affiliating University** (separate document)
- **Geolocation coordinates**
- **Full recognition history / past academic years**
- **Grading** (separate NCH grading document)

## Validation Summary
| Check | Result |
|-------|--------|
| Pages processed | 25/25 – PASS |
| Records extracted | 299 – PASS |
| Number sequence gaps | None – PASS |
| Missing names | 0 – PASS |
| Missing states | 0 – PASS |
| Duplicate college codes | 0 – PASS |
| States/UTs covered | 26 |
| **Overall Status** | **✓ PASS** |

## Limitations
1. 114 colleges have no MARBH Decision recorded for AY 2026-27 — marked as "Status Not Available (AY 2026-27)"
2. 9 colleges have no official NCH College Code yet (newly applied)
3. Address/district/city are embedded in the full name field and not individually structured
4. PG subject-wise data is multi-value text (not split per subject)
5. University affiliation not available in this document
6. Document dated 03-08-2026; colleges that received decisions after this date may not be reflected

## Notes
- NCH replaced the erstwhile Central Council of Homoeopathy (CCH) under NCH Act, 2020
- MARBH = Medical Assessment and Rating Board for Homoeopathy
- UG course: BHMS (5.5 years); PG course: MD Homoeopathy (various subjects)
- Source PDF URL used: `https://nch.org.in/upload/Permission-Status as on 03-08-2026.pdf`
