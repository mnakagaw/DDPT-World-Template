# Iran AreaData — handoff, 2026-09-26

## Status

The first Middle East work-group country is an **initial national-only bootstrap**, not an accepted domestic country edition. `create-country.mjs` created one national territory and 12 indicators; no local observations or planning documents have been adopted. It is not connected to the Asia portal, independently audited, or published. The existing world international-statistics portfolio is reused rather than recollected here.

## Source evidence checked

- `evidence/SOURCE_PREFLIGHT.md` reports that official country-specific source locations were not yet pre-researched. Its cross-country candidates have not been checked for Iran and must not be treated as acquisitions.
- The UNSD census listing in `data/census/world-census-listings-v1.8.1.json` names the Statistical Centre of Iran and lists the 2016 population and housing census (24 September–20 November 2016); its catalogue entry has no direct original link and no acquired data.
- A [UNSD metadata response supplied by Iran](https://unstats.un.org/unsd/demographic-social/products/dyb/documents/metadata/Asia/PE/Iran-2019-PE-Metadata.pdf) identifies the 2016 census as the base for its 2019 population-estimate report and points to the Statistical Centre's census pages. The [official census page URL](https://www.amar.org.ir/english/Population-and-Housing-Censuses/Census-2016-General-Results) could not be fetched in this session. Source location is a lead; original tables, variables, and current availability remain unverified.
- `raw/geoboundaries-adm1-metadata.json` reports 33 ADM1 features in a 2017 reference boundary, while its downloaded simplified geometry has 32 features. The shapes include two `IR-21 Mazandaran` features and a Tehran feature without an ISO subdivision code. The generator correctly adopted 0 ADM1 units after the count mismatch. This is a reference boundary lead, not a verified official administrative-code join.

## Next steps

1. Recheck the official SCI census catalogue and acquire permitted 2016 tables with URL, retrieval receipt, hash, sheet/table locator, definitions, and complete variable inventory. Confirm whether a newer completed census and local results exist before changing the adopted year.
2. Obtain official province/county/district codes and versioned boundaries, reconcile them against census geography, and resolve or replace the failed geoBoundaries acquisition. Do not join by province name alone.
3. Research official planning law, legal planning unit, subordinate analysis geography, planning guidance, plans, budget, implementation, and evaluation sources. Record separate states for identified, acquired, matched, and adopted evidence.
4. Adopt verified subnational observations; test selection of two non-equivalent local areas, parent reset, maps, diagnostics, planning outputs, and CSV/HTML/Markdown exports.
5. Run country validation and independent acceptance before connecting to the Asia entry or publishing. New official source locations can then be returned to the Kit with evidence stage no higher than verified.
