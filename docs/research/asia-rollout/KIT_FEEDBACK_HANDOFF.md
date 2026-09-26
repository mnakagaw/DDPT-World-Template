# Asia source feedback to Census Dashboard Kit — 2026-09-26

This handoff records the source-location loop for the current Asia work. It transfers public source leads and reuse cautions, not observations, raw files, candidate acceptance, or permission to publish a country edition.

| Step | Repository / artifact | Commit / result |
|---|---|---|
| AreaData source selection and evidence | `DDPT-World-Template`, `config/kit-source-feedback-selections.json` | `6c348e5f1452f6b523cd4a09b2144a3295c7ac75` |
| AreaData exported bundle | `evidence/KIT_SOURCE_FEEDBACK.json` | `d7a35e6266d1dbaec56d0e6b955d93c37e6c5dae` |
| Kit import | `Census-Dashboard-Kit`, `config/areadata-source-feedback.json` | `bd9f45f558619ad99f78e3b1ac5db30313be68c3`, branch `codex/asia-source-feedback-20260926` |

The bundle has 30 source leads in eight countries: BFA 14, BGD 2, IRQ 4, LAO 2, SAU 1, TUR 1, UGA 3, YEM 3. The Iraq COSIT table catalogue and Yemen CSO/law leads are part of the current Middle East continuation. Other leads were already recorded in AreaData and are carried forward without claiming a new discovery. All 30 exported stages are capped at `official_location_identified` pending independent source audit; the Kit import starts every lead at `not_acquired_by_kit_preflight`.

Kit's importer dry-run and actual import each accepted 30 source leads. The merge inserted 6, updated 24 and left 31 total records. The additional origin events on older sources record this export without changing their current-project acquisition status. `npm run check`, `npm test` (173/173) and `npm run verify:kit` passed in the isolated Kit worktree. The Kit branch was pushed to GitHub and `git ls-remote` matched `bd9f45f558619ad99f78e3b1ac5db30313be68c3`.

The next country adapter must recheck its URL, acquire and inspect the source, match official territorial codes and boundary versions, and adopt only verified tables and indicators. This import does not change the Asia country status counts or the independent `ACCEPT` gate.

## Iraq age/sex PDF and national plan continuation

On 2026-09-26 AreaData identified two further specific official URLs: a 2024 COSIT age/sex PDF within the already identified census catalogue, and the Ministry of Planning's national 2024–2028 plan PDF. [The scoped source audit](../../evidence/iraq-cosit-2024-age-sex-national-plan-2026-09-26.md) separates adopted governorate-total census fields from unreviewed age bands and sub-governorate rows, and a national plan reference from any governorate plan or execution claim. This is a new specific source location, not a claim that the original COSIT catalogue was newly discovered again.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData selection, import scripts and source evidence | `60251388fbb78bab7f8e0d15a42e03603e3a0bfd` on `codex/asia-domestic-continuation-20260926` | Iraq r5 validator zero errors/warnings; build and CSV/HTML source/value checks passed. |
| AreaData export | `8ab084878c423315768a8985deba3488dc4c8e48`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `115fac18763e7508689ba757bc03b02ad2fb9d21555fe90321edf3875f328661` | Export has 32 leads in eight countries; `origin_commit` is `60251388fbb78bab7f8e0d15a42e03603e3a0bfd`. All remain `official_location_identified`. |
| Kit import | `2ad6c340d5a0d5b5dc379a51504b5aedb9df00e1` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 32, inserted two and updated 30 (33 total records). `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. Pushed branch head equals `git ls-remote` result. |

The Kit records carry source URLs, provenance and cautions. They do not carry raw PDFs or adopted numeric observations, and each next country project starts its own acquisition and independent review. AreaData's Iraq edition is still partial; the Asia independent `ACCEPT` count is zero and no site was published.

## Yemen Taiz yearbook and planning source continuation

AreaData next acquired three CSO-authored 2004 tables from IHSN, the Taiz CSO branch's 2024 statistical yearbook and a Taiz planning-office 2024 progress/2025 priorities presentation. [The source audit](../../evidence/yemen-taiz-official-sources-2026-09-26.md) records the original hashes, table arithmetic and document meanings. In particular, the yearbook's 23 district rows conflict with its printed governorate totals and male/female labels, and no official 2024-to-2017 district crosswalk is established. The planning presentation gives estimated project costs, not an approved budget, actual expenditure or an official evaluation. **No Yemen domestic observation or local document was adopted.**

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData source evidence, scripts and selection | `dec40a6a2160102a8b02226559330eb8efe2dcca` on `codex/asia-domestic-continuation-20260926` | Yemen r2 dataset SHA-256 `fa6a57f80ad698e09c158717eea0416588e8caa2f12636dc824bb7b6c1d03c56`; country validator zero errors, two expected national-only/planning warnings; local site built. `npm run check` and `npm test` 218/218 passed. |
| AreaData export | `0443784718e5ef8df2879150101c4bd1255e1b1d`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `051342a5062280c63b1abdb80f59d5040b2dc57c8cc2ec97b9c622a0fe1faeb7` | Export contains 35 leads in eight countries, including six Yemen leads. `origin_commit` is `dec40a6a2160102a8b02226559330eb8efe2dcca`; every lead remains `official_location_identified`. |
| Kit import | `14b5f19a7652897cc3989778e4daaa2b67133e7e` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 35, inserted three and updated 32 (36 total records). `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. Both GitHub branch heads matched `git ls-remote`. |

These three new Yemen records are new specific public locations; the other carried leads retain their earlier provenance. Kit import remains a source-location preflight, and the independent Asia `ACCEPT` count is still zero. No Yemen site was published.

### Taiz plan source follow-up

The Taiz planning office's separate [42-page English plan PDF](https://www.mopic-taiz.com/wp-content/uploads/2023/11/Taiz-Economic-and-Social-Development-Plan-3-1.pdf) was then acquired and visually checked. Its printed page 3 states that the plan covers **17 named liberated districts**, so it cannot inherit the yearbook's 23-district or provider's whole-governorate scope. Approval, budgets, execution and evaluation remain separate unknowns. It was registered as one further source lead, with no Yemen observation or territory document adopted.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData plan source evidence, collector and selection | `ea09dccdcd07ae376b2849481248458c8509fa10` | Yemen r2 dataset SHA-256 `f1c9439f4b66b2cd8562937aac1a92f5e91ec717cb8dfacd808c3bbfd8817bae`; validator zero errors and two expected warnings, site built, `npm run check` and `npm test` 218/218 passed. |
| AreaData export | `a4442ef9486794f15dc6b58f9e14c87a6d4b0b18`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `4adf6531008934e8bc1ae025d984c8c8dd9688f7af3aefbe72917b956d212a43` | 36 leads in eight countries, seven for Yemen; `origin_commit` is `ea09dccdcd07ae376b2849481248458c8509fa10`; all stages are `official_location_identified`. |
| Kit import | `e48d47733a007f40cc3f99a84440bd2c2717f59d` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 36, inserted one and updated 35 (37 total records). `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. Both GitHub branch heads matched `git ls-remote`. |

This lead preserves the 17-district restriction for the next Kit preflight. The Asia `ACCEPT` count remains zero, and no country site was published.

## Saudi GASTAT detailed-age Tableau location

AreaData identified the official [GASTAT Population by Detailed Age view](https://tableau.stats.gov.sa/views/TA3-PopulationbydetailedAgebyRegionGovernorateNationalityandGender_17298115570530/NW-PopulationbydetailedAgebyRegionGovernorateNationalityandGender) and its metadata code `TTCENPOP0105`. [The evidence record](../../evidence/saudi-gastat-tableau-source-location-2026-09-26.md) states that the reference period, complete row coverage and original export were **not** verified. This is one new specific URL lead, separate from the previously transferred MOH yearbook source. Saudi r2 keeps 13 indicators, 326 observations and zero documents; this Tableau view contributes no adopted value.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData source evidence, registration script and selection | `8de3d9eb0781e62a63ba585de6aeba738f6edead` | Saudi r2 dataset SHA-256 `d45e8c2a7a7ff6f2deb7fca60c5cd6e30746b094cade2b4eea1c3e8ee2ac649b`; country validator zero errors and one missing-planning warning, site built, `npm run check` and `npm test` 218/218 passed. |
| AreaData exported bundle | `2d7ef023c0c8d6a2f674551a241247e63b89e675`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `63218bad4241a5a370f608ead7b6891f9ea5306a36657986b12b788c3f45b4cc` | 37 leads in eight countries; `origin_commit` is `8de3d9eb0781e62a63ba585de6aeba738f6edead`; all stages are `official_location_identified`. |
| Kit import | `789acb46961ebce0623da8015ee94037e60fc66a` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 37, inserted one and updated 36 (38 total records). `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. The new Kit source stays `not_acquired_by_kit_preflight`. |

The Saudi candidate is still partial and has no independent `ACCEPT`; no country site was published. The next Kit project must acquire and inspect the table before using any value.

## Syria national budget and restricted humanitarian source

AreaData then acquired the official [Syrian Ministry of Finance Citizen Budget 2026](https://docs.mof.gov.sy/citizen_budget_2026.pdf) and the public [IOM DTM June 2026 report](https://dtm.iom.int/reports/syrian-arab-republic-population-mobility-and-baseline-assessment-round-17-01-30-june-2026). [The source audit](../../evidence/syria-budget-iom-sources-2026-09-26.md) distinguishes the national budget and its **target** of preparing 14 governorate plans from actual local plans. It also records IOM's requirement for prior written permission for extraction/redistribution. The Kit bundle transfers only URLs, roles and restrictions; it transfers no IOM observations or raw report.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData acquisition scripts, evidence and selection | `63e27099b42e0c42da2773d986ff7e8c6f377d0f` | Syria candidate dataset SHA-256 `a5e30192a35c4817284c1fed6a17514d3b2c72094d865ade646d68815470c9da`; 15 territories, 12 national WDI indicators, 312 records and one national budget reference. Validator zero errors and one national-only warning; site built; browser and national/Aleppo planning outputs checked. `npm run check` and `npm test` 218/218 passed. |
| AreaData export | `866faa3bf308ef638926403d110fd5a900428732`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `68458671013d4cdfee1476dd27e06db06d400e3cab02880ddb50e8fb06cf8571` | 39 leads in nine countries; `origin_commit` is `63e27099b42e0c42da2773d986ff7e8c6f377d0f`. All stages remain `official_location_identified`. |
| Kit import | `b6177d6feb2cc2c42626fde9821d37ce8ff13904` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 39, inserted two and updated 37 (40 total records). `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. Both new Kit leads remain `not_acquired_by_kit_preflight`. |

Syria remains a national-only research candidate with no adopted local numeric observation or independent `ACCEPT`, and no country site was published.

## Jordan DoS 2025 estimates and planning source leads

AreaData acquired the official [DoS end-2025 population-estimates PDF](https://dosweb.dos.gov.jo/DataBank/population/population_Estimares/PopulationEstimates.pdf) and adopted only five country/governorate count fields from Tables 2.2 and 2.3 after source arithmetic checks. Its [source audit](../../evidence/jordan-dos-2025-estimates-official-sources-2026-09-26.md) separates the 2015 census catalogue, 2006 reference shapes, older planning guidance and the published but not-yet-effective 2026 local-administration law. The Kit bundle contains **locations and caveats only**, with no PDF or numeric observations.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData acquisition/import scripts, evidence and selection | `81b2ae8c2c00fdbe12b84f9cebd6ab1f4e6d9b59` on `codex/asia-domestic-continuation-20260926` | Jordan candidate dataset SHA-256 `bcd53b8268c7f5570399230a0cd59355bf9e3892259aeaa0e15411fdae93ad72`; 13 territories, 17 indicators, 377 records, zero documents. Validator zero errors and one planning warning; site built; browser and selected-area HTML/CSV checks passed. `npm run check`, `npm test` 218/218 passed. |
| AreaData feedback bundle | `0dea8a1dc68c6d973ad18748e7fda4335ede3d50`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `bcf0cff35cd30f465bc451f81225708e7877f09d48f048d97ecbd31861f75fa1` | 45 leads in ten countries, six new Jordan leads. `origin_commit` is `81b2ae8c2c00fdbe12b84f9cebd6ab1f4e6d9b59`; every stage is capped at `official_location_identified`. |
| Kit import | `723c7637776bc5a4fffe280d370c11105e577367` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and actual import accepted 45, inserted six and updated 39 (46 total records). Jordan's six records remain `not_acquired_by_kit_preflight`. `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. |

The Ministry of Interior's governorate-name page was recorded in the Jordan source audit but not exported as an `administrative_codes` lead because it does not supply an official code table. Kit must independently acquire and inspect the other originals, verify the effective planning regime and geographic code/boundary edition, and only then consider indicator adoption. Jordan remains partial without independent `ACCEPT`; no country site was published.

The AreaData feedback-bundle commit and Kit import commit were pushed, and `git ls-remote` returned the exact two hashes above for their respective branches.

## UAE federal census, Abu Dhabi and Dubai source locations

AreaData acquired the FCSC historical census tables, SCAD's Abu Dhabi 2024 population report, and Dubai's 2040 structure-plan summary and urban-planning law. It separately identified UAE.Stat's emirate births dataflow and Dubai's 2024 population bulletin without obtaining their data (direct requests returned HTTP 403). The [source audit](../../evidence/uae-official-census-scad-dubai-sources-2026-09-26.md) records adopted fields, page-level nonadoption and geographic limits. The SCAD URL was already present in Kit's UNSD preflight; its return is reuse context, not a new AreaData discovery.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData acquisition/import scripts, evidence and selection | `f68d4ca1be495b4ff61652640b4d59e708da7c1d` on `codex/asia-domestic-continuation-20260926` | UAE candidate and fresh replay each validated and built; all 163 adopted domestic observations and two Dubai document IDs reproduced. Selected HTML/CSV and browser selection checks passed; `npm run check` and `npm test` 218/218 passed. |
| AreaData feedback bundle | `f36764dab55fcb7696581f3c4e90c795b9527c71`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `2753630d462a8728b10d7e56f6066dda3122505852d00848a5434dff6d975f54` | 51 leads in 11 countries, including six UAE leads. `origin_commit` is `f68d4ca1be495b4ff61652640b4d59e708da7c1d`; every stage is `official_location_identified`. |
| Kit import | `2a1e65ecf988f7d321fec4db6d153bae232c5b5c` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and actual import accepted 51, inserted six and updated 45 (52 total records). A repeat dry-run returned 51 unchanged. Six UAE records remain `not_acquired_by_kit_preflight`; `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. |

Both branch heads were pushed and matched `git ls-remote`. The bundle transfers URLs, provenance and reuse cautions, without observations or raw originals. Kit must separately acquire, inspect and match the sources for a future project. UAE remains a partial candidate without independent `ACCEPT`; no UAE site was published.

## Israel CBS 2022 district subset and planning-source locations

AreaData acquired six official CBS 2022 census Excel originals, adopted only 12 broad-geography fields for Nationwide and six districts, and [recorded the remaining field, geography and planning limits](../../evidence/israel-cbs-2022-official-sources-2026-09-26.md). The source's separately reported Judea and Samaria Area reconciles the national value but is not treated as a seventh mapped district. The Kit bundle transfers **source URLs and cautions only**; no Excel body, census value, plan status or country acceptance is transferred.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData scripts, source audit, country status and selection | `7c22fd9b0e1d4e430b6bd479e6d30c1435b39cc7` on `codex/asia-domestic-continuation-20260926` | Israel candidate and fresh replay each validated and built; 84 adopted CBS tuples, original hashes and 3,410-column inventory matched. Selected CSV/HTML and browser selection checks passed. `npm run check` and `npm test` 218/218 passed. |
| AreaData feedback bundle | `d9b675fe1e266b5275c5fc3d8211dd16380bfdef` on the same branch; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `b093ce052c6f2d453ce5e60a40372b7a7dbe0726514030a76994da5f454151b0` | Bundle has 62 public source leads in 12 countries, including 11 Israel leads. `origin_commit` is `7c22fd9b0e1d4e430b6bd479e6d30c1435b39cc7`. Every stage is capped at `official_location_identified`. |
| Kit import | `9011268b243ba29b2dc289197e4ca133bcfe1965` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and actual import accepted 62, inserted 11 and updated 51 (63 total records). Repeat dry-run reported 62 unchanged. All 11 Israel Kit records remain `not_acquired_by_kit_preflight`; Kit `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. |

Both commits were pushed to their respective GitHub branches. Israel remains a partial local candidate with zero adopted planning documents and no independent `ACCEPT`; no Israel site was published. Kit must independently acquire and audit the original tables, official code/boundary editions, current planning law and actual local plan/finance records before using them in another country project.

## Lebanon LFHLCS survey, map and planning-source locations

AreaData acquired the official CAS LFHLCS 2018–19 survey Demography XLS, its full report and 26 English district profiles, plus MOPH nine-governorate/26-caza reference GeoJSON. Only the three HL5 sex-count columns were adopted for nation, eight survey governorates and 26 caza. The [source audit](../../evidence/lebanon-cas-lfhlcs-moph-2026-09-26.md) records that these are **2018 sample-survey estimates, not census values**, and that the survey's eight-governorate reporting scheme is not reconciled to the MOPH map's nine. DGLAC, DGU and MICS leads remain locations only. The Kit bundle transfers public URLs and reuse cautions, with no raw original, numeric observation, local plan or acceptance decision.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData scripts, source audit, country status and selection | `5df17b4e011dc337e8aafc52b5e3eb7635a3cea0` on `codex/asia-domestic-continuation-20260926` | Candidate and fresh replay reproduced four pinned original hashes, 105 adopted survey tuples and full workbook column inventory. Both validated and built; selected CSV/HTML and browser checks passed. `npm run check` and `npm test` 218/218 passed. |
| AreaData feedback bundle | `ce1624b960a5d6d13c3db31954f746f155b5e5c4` on the same branch; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `44cf2ba2314b925c19e155f660d3e8fd8eb449aaed41ddffdfa7aa99a8162570` | Bundle has 72 public source leads in 13 countries, including 10 Lebanon leads. `origin_commit` is `5df17b4e011dc337e8aafc52b5e3eb7635a3cea0`; every stage is capped at `official_location_identified`. |
| Kit import | `111aac8b9bd8d33c76d5f7c5d9953238b1b11749` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 72, inserted 10 and updated 62 (73 total records). Repeat dry-run reported 72 unchanged. All 10 Lebanon records remain `not_acquired_by_kit_preflight`; Kit `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. |

The two GitHub branch heads were checked by `git ls-remote` and matched the commits above. Lebanon remains a partial local candidate with zero verified planning documents and no independent `ACCEPT`; no country site was published. Kit must acquire and audit the originals, geographic edition and local planning evidence independently before promoting any source stage or using a value.

## Oman eCensus, administrative directory and national plan sources

AreaData adopted only the [checked 2020 eCensus population subset and selected pages of one national plan](../../evidence/oman-ecensus-2020-moi-national-plan-2026-09-26.md). The Ministry of Interior 2025 directory and NCSI spatial attributes do not certify the 2020 legal boundary. The two 2025-listed wilayats with null 2020 cells were not filled. Kit receives ten public locations and caveats only.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData scripts, evidence, country status and selection | `e38724e882d186e2e69e5c848333d5536e768885` on `codex/asia-domestic-continuation-20260926` | Oman candidate and fresh replay reproduced 219 adopted 2020 tuples and pinned MOI/plan hashes. Validator zero errors/warnings, build, seven-area HTML/CSV and browser checks passed; `npm run check`, `npm test` 218/218 passed. |
| AreaData feedback bundle | `366ada58f9aef1b6c20fe77356b0192294107668`; previous bundle SHA-256 `f94a0e6ff780fa67e5fa874377399d45f99430d2b24cf264a1eb82056ffea191` | 82 leads in 14 countries, ten for Oman; all capped at `official_location_identified`. The later Palestine bundle supersedes this bundle file while retaining the ten Oman records. |
| Kit import | `b7b3e7b343b03dec1c876d3c26677933d316bd22` on `codex/asia-source-feedback-iraq-20260926` | Dry-run/import accepted 82, inserted ten and updated 72 (83 total records). Repeat dry-run 82 unchanged; Kit check, 173 tests and `verify:kit` passed. All Oman records remain `not_acquired_by_kit_preflight`. |

Oman remains a partial country candidate with no independent `ACCEPT` or Hosting/Public release. Kit must independently acquire, check terms, reconcile dated codes and inspect the remaining eCensus and plan products before using values or planning statuses.

## Palestine PCBS 2017 census and MoLG source locations

AreaData acquired the [PCBS 2017 Final Summary and detailed volume, and two MoLG planning originals](../../evidence/palestine-pcbs-2017-molg-sources-2026-09-26.md). Only four direct Table 2 count fields for 19 source reporting areas were adopted; the 585 locality cells have since been extracted without adoption because their sum differs from the printed national total by 281,163; current legal polygons and individual local plan/finance records remain unassessed. Kit receives seven public source URLs with source-role and period cautions, without PDFs, population counts or national-document content.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData PCBS/MoLG scripts, evidence, country status and selection | `c858618645f3b54464951cc34459ad1e02376100` on `codex/asia-domestic-continuation-20260926` | Candidate and independent bootstrap replay matched 76 PCBS tuples, 19 areas, two national references and seven official source records; country validator zero errors/warnings. Build, seven-area HTML/CSV and browser checks passed; AreaData `npm run check`, `npm test` 218/218 passed. |
| AreaData feedback bundle | `ff80c2dd259fcb2a199d45c741c1b71126ca0a93`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `2c7b90971345114d5050570a59f1765062b6e40aeafb65332ad62a5c3d04099d` | 89 leads in 15 countries, seven for Palestine; bundle `origin_commit` is `c858618645f3b54464951cc34459ad1e02376100`. Every source stage is `official_location_identified`. |
| Kit import | `3cf0622d2da1fd3a8947fe61628c2bc6cf973589` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 89, inserted seven and updated 82 (90 total records). Repeat dry-run returned 89 unchanged. Kit `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. Seven PSE records remain `not_acquired_by_kit_preflight`; remote branch head matched the commit. |

The AreaData and Kit GitHub branch heads are checked separately from local candidate validation. Palestine remains partial with no independent `ACCEPT`; no country site or Asia entrance was deployed to Hosting/Public.

## Kuwait CSB 2021 registration census and planning-source locations

AreaData acquired the official CSB 2021 registration-census Table 1 and Table 51 PDF/XLSX pairs, checked corresponding source rows and adopted only nine Table 1 count fields for the nation and six governorates. The [source audit](../../evidence/kuwait-csb-2021-official-sources-2026-09-26.md) records the nonterritorial “Not Stated” row, the unlinked named-area detail, the difference between the pinned Table 1 total and the census-homepage headline, and the absence of accepted official codes and legal polygons. The Kit bundle conveys nine public source locations and cautions only; it conveys no values, raw originals, planning status or country acceptance.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData scripts, audit, country status and selection | `dde002c9ba972c2ca991ad09eacc4dcfcdbf5421` on `codex/asia-domestic-continuation-20260926` | Candidate and independent replay reproduced 63 domestic tuples and nine official source records. Both validated and built; selected CSV/HTML and browser checks passed. `npm run check` and `npm test` 218/218 passed. |
| AreaData feedback bundle | `688fb80f7adbe7760e7fcee5cb228150c05210e4`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `0267d974437f1faa2138d5bce0340f5f6782e13814d7acbc7c4384384cdb7d34` | 98 leads in 16 countries, nine for Kuwait; `origin_commit` is `dde002c9ba972c2ca991ad09eacc4dcfcdbf5421`. Every stage is capped at `official_location_identified`. |
| Kit import | `70ecf86d075a9d20c58ee52e4ccfa189abee2a5a` on `codex/asia-source-feedback-iraq-20260926` | Dry-run and import accepted 98, inserted nine and updated 89 (99 total records). Repeat dry-run returned 98 unchanged. Nine Kuwait records remain `not_acquired_by_kit_preflight`; Kit `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed. |

The AreaData and Kit GitHub branch heads matched these hashes after push. Kuwait remains a partial local candidate with zero acquired local planning documents and no independent `ACCEPT`; no country site or Asia entrance was deployed to Hosting/Public. Kit must independently acquire and inspect the originals, code and boundary editions, and local planning/finance records before using their values or advancing an evidence stage.

## Georgia Geostat 2024 census and Kutaisi planning-source locations

AreaData acquired and inventoried six official Geostat 2024 census workbooks, the main-results PDF, Kutaisi's 2026–2029 mayor-approved action plan and the original 2026 budget ordinance. It adopted only direct Table 02/06 count fields and the two Kutaisi-only document references. The [Georgia source audit](../../evidence/georgia-geostat-2024-kutaisi-planning-2026-09-26.md) records all 63 acquired numeric columns, 27 Table 02 missing dashes, unadopted settlement/age/migration fields and unresolved official codes/boundaries. Kit receives 18 public source locations and cautions, no values or raw originals.

| Step | Commit / artifact | Verification |
|---|---|---|
| AreaData producer scripts, audit, candidate state and selection | `dee7bbd45b8535293a2d2e65589ace928e9ff847` on `codex/asia-domestic-continuation-20260926` | Candidate dataset SHA-256 `2f93be22179041b3f07cd86ba372ab92399b3774bf0a1ac725d1ba3437a33a75`; fresh replay matched 85 territories, 1,440 domestic records, two Kutaisi documents and 19 Georgia source records. Both validators returned zero errors/warnings; builds, seven-area CSV/HTML and local browser checks passed. AreaData `npm run check`, `npm test` 218/218 passed. |
| AreaData authority-type correction and final feedback bundle | `2d9b249e5b9e1422f4fa280928feb45713e21350` corrected three Kutaisi selection records to Kit's `official_subnational`; bundle commit `987dc585788c43ce873ce8f0ffa52d63aa29e5dc`; `evidence/KIT_SOURCE_FEEDBACK.json` SHA-256 `cb76f9f6927d0781053cd7ce5a187574a747e044212751fa63d23e0ece69b82e` | 116 leads in 17 countries, 18 for Georgia; `origin_commit` is the authority-type correction commit. The initial exported bundle was rejected by Kit dry-run for unsupported `official_local` and was replaced before import. All Georgia stages remain `official_location_identified`. |
| Kit import | `f7230bb0baf80a97b310bb32604fad18e07109ab` on `codex/asia-source-feedback-iraq-20260926` | Dry-run/import accepted 116, inserted 18 and updated 98 (117 total records); repeat dry-run returned 116 unchanged. All 18 Georgia records remain `not_acquired_by_kit_preflight`. Kit `npm run check`, `npm test` 173/173 and `npm run verify:kit` passed; remote branch SHA matched. |

GitHub stores this partial country candidate's reproducible scripts and source decisions. The generated country site, raw originals and receipts remain local/ignored. Independent Georgia acceptance is pending; Hosting/Public is not deployed. Kit must independently acquire, inspect, date and code-match each source before using values or advancing stages.
