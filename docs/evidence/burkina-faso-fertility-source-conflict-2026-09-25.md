# Burkina Faso RGPH 2019 fertility-source conflict

Checked 2026-09-25 against the acquired, hash-verified INSD PDFs. This is a source reconciliation record, not a new adopted indicator.

| Source | Exact location | Relevant reported values |
| --- | --- | --- |
| [RGPH statistical tables](https://web2.insd.bf/sites/default/files/2024-06/Volume%20des%20tableaux%20statistiques_%205e%20RGPH.pdf), SHA-256 `a665f61e49581cb39e85fdd3d70cb699acf3ec7b964dfbb2852fd35cfc19d7f2` | Physical PDF page 52, printed page 28, Table II.10, `ISF` column | Centre 4.1; Centre-Sud 5.4; Est 6.9; Sahel 6.2; national 5.4. National `AMP` is 30.6 years. |
| [RGPH final report](https://microdata.insd.bf/index.php/catalog/69/download/273), SHA-256 `2684ed8c74970b730afb7467da6cc9f038fd2672e4323888198d57aae8bc4105` | Physical/printed page 58, §4.2.2 and Figure 7 | Prose says Centre 4.5, Centre-Sud 4.6, Est 7.2, Sahel 6.2; the figure labels Centre 4.3, Centre-Sud 5.3, Est 7.2, Sahel 6.6. The page also gives national `AMP` as 30.7 years. |

The statistical table, final-report prose, and final-report figure disagree with one another. These differences were confirmed on rendered pages, not inferred from OCR alone. Do not silently average, overwrite, or treat any one of these as a corrected version. Table II.10 remains pending for adoption until INSD version/date, population basis and errata are checked. Keep its value, unit, page and document version separate in the review ledger. The existing dashboard has no indicator adopted from Table II.10, so no current displayed value was changed by this finding.

The source-page renderings are retained in the ignored country project at `generated/burkina-faso-20260924/evidence/source-page-review/table-ii-10.png` and `final-report-fertility.png`; source PDFs remain outside Git pending redistribution terms.
