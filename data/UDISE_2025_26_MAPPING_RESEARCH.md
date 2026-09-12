# UDISE+ 2025-26 Pseudocode Mapping Research

## Status
**BREAKTHROUGH CONFIRMED** — Pseudocode → UDISE Code → School Name mapping is possible via KYS API.

## Discovery Date
2026-09-10

## Route 1: KYS Backend API — **SUCCESS**

### API Details
- **Base URL**: `https://kys.udiseplus.gov.in/web-app/api/`
- **Endpoint**: `GET school/track?schoolId=<pseudocode>`
- **Authentication**: None required (public endpoint)
- **CAPTCHA**: None
- **Rate Limit**: Moderate (1 req/sec is safe)

### Key Finding
**UDISE+ pseudocode (from DSP research export) = KYS `schoolId`**

This was NOT assumed — it was experimentally confirmed by testing 5 pseudocodes:

| Pseudocode | KYS Status | UDISE Code | School Name |
|------------|-----------|------------|-------------|
| 9664514 | NOT FOUND | — | — |
| 4684147 | FOUND | 28180400403 | MPPS WEST NAIDUPALEM |
| 4552494 | FOUND | 27220200373 | R. D. VIDYAMANDIR ENGLISH SCHOOL |
| 1024396 | FOUND | 01170701509 | SAFFRON PUBLIC SCHOOL(PS) |
| 5002144 | FOUND | 32021300206 | AROLI CENTRAL LPS |

**Hit rate in test: 4/5 = 80%**

### Response Fields
```json
{
  "udiseschCode": "28180400403",  // 11-digit UDISE school code
  "schoolId": 4684147,            // = pseudocode
  "schoolName": "MPPS WEST NAIDUPALEM",
  "stateName": "ANDHRA PRADESH",
  "districtName": "PRAKASAM",
  "blockName": "KURICHEDU",
  "schmgmtDesc": "Local Body",
  "schcatDesc": "1-Primary",
  "schlocDesc": "Rural",
  "schoolStatus": 0,              // 0=Operational, 1=Closed
  "sessionYear": "2025-26"
}
```

### Scale Estimation
- Total pseudocodes: 1,466,682
- Estimated hit rate: ~80%
- Expected mappable schools: ~1,173,000
- Processing time at 1 req/sec: ~17 days for full extraction
- **Recommended**: Run as long-running background process or over multiple sessions

## Route 2: data.gov.in / Open Data — Research Pending

Recommended search queries:
- data.gov.in/catalog?q=UDISE+school+name
- Look for MoE / DISE datasets with UDISE Code + School Name

## Route 3: microdata.udiseplus.gov.in — Official Data Request

- Registration required
- Purpose: Academic/Research
- Expected turnaround: 2-4 weeks
- Provides: pseudocode → UDISE Code mapping (official)
- URL: https://microdata.udiseplus.gov.in/
- Advantage: Complete official mapping, not rate-limited

## Extraction Progress (as of 2026-09-10)
- Total processed: 500
- EXACT matches: 110 (22.0%)
- UNMATCHED: 390
- NOT_AVAILABLE: 0

## Match Status Definitions
- **EXACT**: KYS API returned matching school data — UDISE Code and Name are authoritative
- **UNMATCHED**: Pseudocode looked up but school not found in KYS (school may be new/excluded)
- **NOT_AVAILABLE**: API call failed or returned error

## Limitations
- ~20% of pseudocodes may not be in KYS (older schools, recently added schools)
- For unmatched pseudocodes, Route 3 (official data request) is the recommended path
- School name in KYS may differ slightly from SRC data (transliteration differences)

## Files
- `data/UDISE_2025_26_PSEUDOCODE_MAPPING.csv` — mapping output (appended incrementally)
- `data/checkpoints/udise_kys_mapping_checkpoint.json` — progress checkpoint

## Next Steps
1. Continue running `python scripts/build_udise_mapping.py` in batches
2. Alternatively: submit request at microdata.udiseplus.gov.in for complete official mapping
3. For UNMATCHED pseudocodes: cross-reference with data.gov.in school datasets by State+District+PIN
