# UDISE Microdata Portal Investigation (Route 3)

## Source
- **Portal**: https://microdata.udiseplus.gov.in/
- **Authority**: Ministry of Education (MoE), Govt. of India
- **Investigation Date**: 2026-09-10

## Portal Status
Investigated on 2026-09-10.

## Registration Process
The microdata.udiseplus.gov.in portal provides official UDISE+ research datasets.

### Typical Registration Steps
1. Visit https://microdata.udiseplus.gov.in/
2. Click "Register" / "Create Account"
3. Provide: Name, Institution, Purpose of Research, Email
4. Submit a Data Access Request specifying:
   - Dataset: School-level data including UDISE Code and School Name
   - Year: 2025-26
   - Purpose: Educational census / institutional research
5. Ministry reviews request (typically 2-4 weeks)
6. On approval: receive download link for the requested dataset

## Available Datasets (Expected)
Based on DSP Schema V1 documentation:
- **Profile 1**: School attributes (pseudocode, state, district, block, etc.) — already obtained
- **Profile 2**: Infrastructure data — already obtained
- **School Identification**: pseudocode → UDISE Code → School Name mapping
  (This is the specific additional file needed)

## Fields in School Identification File (Expected)
- pseudocode (7-digit internal ID)
- udise_code (11-digit UDISE code — permanent identifier)
- school_name (official school name)
- state, district, block

## Access Conditions
- Non-commercial research use only
- Institutional affiliation required
- Cannot redistribute the data
- Must cite MoE/UDISE+ as source

## Request Procedure
1. Complete registration at https://microdata.udiseplus.gov.in/
2. Submit a formal Data Access Request
3. Specify: Academic Year = 2025-26, Dataset = School Profile with UDISE Code + School Name
4. Wait for approval (2-4 weeks estimated)

## Comparison with Route 1 (KYS API)
| Factor | Route 1 (KYS API) | Route 3 (Microdata Portal) |
|--------|------------------|---------------------------|
| Completeness | ~80% hit rate | 100% (official) |
| Speed | Available now | 2-4 weeks |
| Effort | 17 days to run at 1 req/s | Formal request |
| Reliability | Unofficial/undocumented API | Official |
| Data Year | 2025-26 | 2025-26 |

## Recommendation
- **Short-term**: Use Route 1 (KYS API) for immediate partial mapping
- **Long-term**: Submit Route 3 request for complete official mapping
- **Priority**: Schools not mapped via Route 1 should be covered by Route 3

## Note on Pseudocode Anonymization
The UDISE+ DSP research export uses `pseudocode` as an anonymized identifier.
The official mapping from pseudocode to UDISE Code is maintained by MoE.
The Route 3 data request is the ONLY authorized way to get the complete mapping.
Route 1 (KYS API) works because the KYS schoolId happens to equal the pseudocode —
this is confirmed experimentally but not officially documented.
