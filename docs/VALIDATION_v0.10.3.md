# AreaData v0.10.3 validation record

Date: 2026-09-23
Scope: Census Dashboard Kit v1.8.1 world Census source-preflight import, dataset validation, source UI and CSV export.

## Fixed upstream inputs

- Repository: `https://github.com/mnakagaw/Census-Dashboard-Kit`
- Version: `1.8.1`
- Commit: `6622118aa702a6f1d8eeaa84e1c5982a0fb954b5`
- Registry: `config/world-source-preflight.json`
- Downloaded registry SHA-256: `448d4b5ec264191ae45dc1fc75a19c346b4dee5d8594ca86bb4f45f664846a95`
- Validation record: `docs/VALIDATION_v1.8.1.md`
- Downloaded validation-record SHA-256: `1c669b0897932d72115773c1fe66655cebf430763a8bae28754486e9ee10097a`

The hashes above are calculated from the files at the fixed commit. The generated-file hashes written inside the upstream validation narrative describe an earlier generation state and do not equal the final bytes at commit `6622118...`; AreaData verifies the actual fixed-commit bytes.

## Imported contract

The normalized bundle contains 250 ISO3-identified country/area records. AreaData joins a generated dataset to these records by ISO3 only. It does not use local display-name matching.

The following states remain separate:

1. UNSD latest completed listing;
2. UNSD latest completed listing carrying a link;
3. source-body acquisition;
4. content verification;
5. observation adoption.

The screen and CSV expose the two listing fields independently and label acquisition, verification and adoption as incomplete. KNA, LCA, SPM, VCT and SXM use the corrected UNSD identities. The Netherlands footnote is removed by the upstream fixed registry before ISO3 import.

## Algeria guard

- Latest UNSD listing: 2020 round, 25 September 2022, no UNSD link.
- Latest linked listing: 2010 round, 16-30 April 2008, `http://rgph2008.ons.dz/`.
- Adopted domestic Census data year: 2008.
- A domestic Census-series observation after 2008 fails dataset validation.
- A separate international reference series dated 2022 remains permitted.

This guard prevents a 2022 listing date from becoming a fabricated 2022 Census observation.

## Checks

- `npm run check`: PASS, 107 JavaScript modules and JSON templates.
- `node --test tests/world-census-preflight.test.mjs`: PASS, 5 tests.
- `npm test` on the isolated fixed-commit implementation: PASS, 189/189 tests.
- `npm run check` on the current Americas release source: PASS, 112 modules and JSON templates.
- `npm test` on the current Americas release source: PASS, 196/196 tests.
- Americas dataset validation after importing 57 in-scope records: PASS with no errors or warnings.
- Local browser: PASS. The Japanese database page showed 57 source-listing rows, separate latest/latest-linked columns, the fixed commit/hash and corrected KNA/LCA/SPM/VCT/SXM identities; browser console warnings/errors: 0.
- FTPS publication: PASS. The release changed 13 of 67 site files; all 13 remote predecessor files matched the expected v0.10.2 hashes and were backed up before replacement. The other 54 files were unchanged. Each uploaded file was re-read from the final remote path and matched the v0.10.3 candidate hash.
- Public HTTPS file verification: PASS, 66/66 web-accessible files matched the local candidate byte-for-byte. The existing `.htaccess` was excluded from HTTP verification and was not replaced.
- Public browser: PASS. The Japanese database page showed 57 source-listing rows, the four expected columns, the fixed commit/hash, corrected KNA/LCA/SPM/VCT/SXM identities and the warning that a listing or link does not establish acquisition, verification or adoption. Browser console warnings/errors: 0.
- Public scope note: the current published page is the Americas release and therefore exposes 57 in-scope records. The normalized repository bundle contains 250 records. Algeria is outside this public screen; its 2008-only domestic-data guard is covered by dataset validation and the mandatory test above.

The existence of the upstream validation record is not treated as an AreaData audit result. This record reports only checks executed against this AreaData revision.
