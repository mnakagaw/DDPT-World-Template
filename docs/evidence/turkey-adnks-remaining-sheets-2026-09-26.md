# TÜİK ADNKS 2025: five unadopted sheets

Read-only audit of the official [TÜİK seven-sheet 2025 ADNKS workbook](https://www.tuik.gov.tr/media/announcements/2025ADNKS_FavoriTablolar.xlsx) on 2026-09-26. Workbook SHA-256 `72e36cf8f1eeb2e8c12480e14148b42448c6aad05d19932d94add37f360980c1`. The province and district sheets remain the separately integrated annual address-register series; ADNKS is not a census.

| Unadopted sheet | Source rows | Numeric columns | Review result |
|---|---:|---|---|
| `BÜYÜKŞEHİR B. NÜFUSU` | 30 | total, male, female: 30 each | Metropolitan municipality population; do not equate with every province. |
| `BELEDİYE NÜFUSU` | 1,377 | total, male, female: 1,377 each | Municipality and legal-character codes require their own planning-unit crosswalk. |
| `MAHALLE NÜFUSU` | 32,254 | total: 32,254; male/female: 32,060 each | 194 rows have `C`-suppressed sex values; neighborhoods of population ≤10 and organized industrial zones are omitted by the source. |
| `KÖY NÜFUSU` | 18,183 | total: 18,183; male: 18,157; female: 18,153 | 26 `C`-suppressed sex pairs and four additional `-` female cells; villages without registered residential addresses are omitted. |
| `KENT-KIR SINIFLAMASI` | 50,437 | none; categorical degree of urbanisation | 39,693 rural, 5,676 dense urban, 5,068 medium urban source rows. The 50,437 classification rows match all **published** neighborhood and village rows one-to-one by official source codes, with zero ambiguous or unmatched rows. This does not restore omitted units or establish complete population coverage. |

For all rows where total, male and female are numeric, the sex sum agrees with total. The classification uses 1 km² density grids and distinct urbanisation categories; it is not the workbook's simpler `il/ilçe merkezleri` versus `belde/köyler` split. Municipality population cannot be added to district population as an independent partition without role and coverage analysis. These five sheets remain `not_adopted_pending_geographic_and_planning_review`.

The reproducible audit is `scripts/audit-turkey-adnks-2025-remaining.py`; detailed source headings, method notes, field-state counts and first-row locators are in the ignored `.work/asia-middle-east/turkey-adnks-2025-remaining-audit.json`. No additional Turkey indicator was published by this audit.
