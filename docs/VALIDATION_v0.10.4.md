# AreaData v0.10.4 validation record

Date: 2026-09-23  
Scope: Census Dashboard Kit v1.9.0 source-feedback exporter, schema 1.0 validation, initial committed-evidence backfill and workflow integration.

## Fixed upstream contract

- Kit version: `1.9.0`
- Commit: `c67e2e2f2144cf59d6735ce26910933a481337ce`
- Contract SHA-256: `eb290289ef5d7b43247817c553d83e5a7cc837cf8920ec16b51a718ba09f39f8`
- Schema SHA-256: `3425f0355acaf9aa0a2845084f142a5c52c74b7a18b12c908412e0552af86d32`

## Export boundary

The exporter reads the committed country registry and Latin America regional research inventory. It emits only public HTTP(S) source metadata from official national, subnational or international authorities. It rejects credentials, secret query parameters, localhost, loopback, private addresses, absolute or parent-traversing evidence paths, raw directories, unknown schema fields and evidence paths absent from `origin_commit`.

Evidence stages remain separate. An AreaData stage does not set the Kit acquisition or adoption state. The initial research inventory is exported conservatively as `official_location_verified`; only registry entries explicitly marked as catalogue-content or content verified become `content_inspected`.

## Initial backfill

The final bundle was generated only after the exporter and its evidence inputs existed in committed revision `064ca314c610a60686d43f90b9b27729ac9b4414`. It contains 106 sources for 22 countries: 101 `official_location_verified` and 5 `content_inspected`. Its SHA-256 is `91fea347b3239da8df7a0f0f79132707e056c6da2188b28214e948971cd5bc00`.

## Checks

- `npm run check`: PASS, 110 JavaScript modules and JSON templates.
- `npm test`: PASS, 195/195 tests.
- Deterministic regeneration: PASS. Re-running with the fixed origin commit and `--check` reproduced the saved bytes.
- GitHub push: pending.
- FTPS: not applicable because this revision does not change generated public-site behavior or assets.
