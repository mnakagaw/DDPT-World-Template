# AreaData 0.5 validation record

Checked 2026-09-15 JST. This record applies to the uncommitted working tree based on `fb523d2`, Node.js `v24.11.1`, and the saved world-source archive whose dataset edition is `2026-09-13T10:24:18.027Z`. A final commit identifier must replace the working-tree reference after release.

## Implemented scope

- AreaData entry, Territorial diagnostic, Thematic diagnostic, Data database and Planning and resources pages.
- Explicit seven-country Central America pilot: BLZ, GTM, SLV, HND, NIC, CRI and PAN. Mexico is excluded and the scope is distinguished from UN M49 013.
- Exact-observation-first, complete non-overlapping population sums; incomplete coverage remains null with a labelled covered subtotal and missing IDs.
- Separate `census` primary series and `international_reference` context series contract.
- Explicit `same_period` and `latest_available_by_component` policies. Mixed census years retain every component ID and actual year and are labelled as not being a same-year total.
- MariaDB 10.6 schema for dataset versions, geography, membership, indicator meaning, observations, aggregation rules/results/components and boundary assets.

## Automated verification

| Check | Result |
|---|---|
| `npm run check` | 43 JavaScript modules and JSON templates passed syntax checks |
| `npm test` | 128 passed, 0 failed |
| `node scripts/validate-country.mjs --project .work/areadata-ca-v0.5-census-contract-2` | 0 errors; one expected warning for no verified country-specific planning documents |
| Generated runtime | 8 territories, 119 source-reported international-reference observations, 15 site files, 313,170 bytes |
| Census preflight | 7/7 countries have registered source locations; 0 acquired datasets, 0 matched geographies and 0 accepted indicator sets in this build |

The mixed-period regression uses fictional values only. It verifies different component years, refusal without an explicit rule, full-cover calculation and component-year export. It is not evidence for a real Central America census total.

## Browser verification

The generated site was served at localhost and inspected in the Codex in-app browser.

| Scenario | Result |
|---|---|
| Entry map and seven country links | Passed; all seven country names and reference map shapes visible |
| Census/reference distinction | Passed; banner says census is primary, not yet integrated, and current values are international reference context |
| Territorial diagnostic | Passed; 2025 reference population total shows all seven country components and component years |
| Data database | Passed; each indicator displays `international_reference · context`; staged census acquisition is visible |
| Planning at the regional root | Passed; regional analysis scope is not presented as a legal planning authority and produces no regional planning draft |
| Country then parent reselection | Passed; selecting Belize changed heading, URL, map and materials to BLZ, then selecting `CUSTOM:CA7` cleared Belize and restored the regional gate while retaining indicator and period |

## Source-state limits

Belize's official 2022 census portal and key-findings report were checked on 2026-09-15. The other six source locations come from the 2026-09-13 Latin America desk-research registry and require refresh plus original-file acquisition. Costa Rica's 2022 product is a corrected official estimate following partial census collection, and Nicaragua's latest detailed candidate remains 2005 while 2024 detailed results are unverified; neither may be silently presented as an ordinary current complete census.

## Not completed in this record

- No official census table has been acquired, hashed, parsed or geographically matched by the Central America generator.
- No municipal-scale performance conclusion is available from the 8-territory scaffold.
- The MariaDB schema was inspected by tests but has not been executed against the CORESERVER database.
- CSV download content is covered by automated tests; browser download files were not manually opened in this run.
- Mobile layout, authenticated operations and all 42 acceptance scenarios were not completed.
- GitHub push, FTPS hosting and public-site verification are not part of this working-tree record.
