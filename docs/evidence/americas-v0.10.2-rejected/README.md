# Americas v0.10.2 audit status

This directory preserves the evidence for the public v0.10.2 transport and the later independent re-audit.

- `FTP_DEPLOYMENT_FINAL.json` records the completed resumable FTPS deployment.
- `PUBLIC_VERIFICATION_FINAL.json` records the HTTPS status, MIME type, byte length, and SHA-256 check for every managed public file.
- `INDEPENDENT_REAUDIT_2026-09-21.md` supersedes the earlier `ACCEPT` decision and classifies v0.10.2 as **REJECT — BLOCKING**.

The deployment receipts prove that the audited files reached the public host unchanged. They do not prove that the 57 country and area editions had adequate data coverage. The re-audit found that source-review completion, country-edition completion, Census-history coverage, domestic hierarchy coverage, and international population coverage had been conflated.

Do not reuse the earlier v0.10.2 `ACCEPT` or describe this release as 57 completed country editions. A replacement release needs corrected completion rules, country-state isolation, source evidence tied to its final dataset hash, new deployment receipts, and a separate independent audit.
