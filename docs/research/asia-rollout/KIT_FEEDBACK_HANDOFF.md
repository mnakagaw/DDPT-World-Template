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
