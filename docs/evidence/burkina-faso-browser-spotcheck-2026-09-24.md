# Burkina Faso local browser spot check 2026-09-24

This is a **producer spot check**, not the 42-scenario acceptance or an independent audit. The test used local Chrome at 1366×900 against `http://127.0.0.1:4175/`, with the BFA dataset SHA-256 `53e2de7488ea6fd3657270006a858a609f80e3b3d969dcda2d129048c4681aa7` and AreaData template commit `8d2f01d` plus then-uncommitted Word/screening changes. The later dataset SHA-256 `53d17c6d10f60cdea5fcb8c317e43e37123c680a37d9af386875f9eb0715baa2` adds four source-location records and their planning links; this browser flow was not repeated after that change. The private in-app browser bridge was unavailable, so headless Chrome/Playwright exercised native `<select>` controls. Screenshots remain in the ignored local `tmp/` directory.

| Step | Observed result |
| --- | --- |
| Open national territorial page with `metric=BFA_RGPH2019_POP_TOTAL&period=latest-available` | `h1` Burkina Faso; URL retained selected metric and latest-available; seven theme headings included Burkina Faso. |
| Native region dropdown → `Whole Centre` | `h1` Centre; URL territory became `BFA:gbOpen:ADM1:92566538B14190085014946`. |
| Native province dropdown → `Whole Kadiogo` | `h1` Kadiogo; URL territory became `BFA:RGPH2019:ADM2:KADIOGO`. |
| Native commune dropdown → `Komki-Ipala` | `h1` Komki-Ipala; URL territory became `BFA:RGPH2019:ADM3:KADIOGO:KOMKIIPALA`. The ancestor dropdown showed `Belongs to Centre · a lower area is selected`, separate from its actionable `Whole Centre` option. |
| Same ancestor dropdown → `Whole Centre` | `h1` and URL returned immediately to Centre; the province selector reset to its whole-area state. Metric and latest-available period remained in the URL. The location map visibly highlighted Centre. |

The final screenshot is `tmp/bfa-browser-parent-reset-20260924.png`. The test did not check every indicator value, planning documents, downloaded CSV/Word, browser back/forward, quick reversed responses, keyboard interaction or printed output after this reselection. Accordingly A01, A21–A23, A35 and A42 remain **未実施** in the formal ledger.
