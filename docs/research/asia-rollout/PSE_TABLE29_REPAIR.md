# Palestine Table 29: coordinate-based source-cell recovery

Status: extraction aid only, **not adopted, accepted or published**. This repair
uses the official PCBS *PHC 2017 Census Final Results - Summary*, PDF pp.
116-130, Table 29. The source PDF is pinned to SHA-256
`25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f`.
No PDF is committed or redistributed here.

The previous text-line parser counted 585 distinct locality codes but could
read all three count cells on the same physical line for only 529. Visual
checks of pp. 116, 117, 129 and 130 show that long English names wrap while
the printed numeric cells remain in separate fixed columns. The new
`scripts/extract_palestine_pcbs_table29.py` reads Poppler's bounding boxes and
links each source code to one female, male and total count on the *same printed
row*, within an 8-point vertical tolerance. It rejects missing or ambiguous
cells, duplicate codes, sex-sum mismatches and changes in per-page row counts.
Six visually checked codes cover both ordinary and wrapped rows, including
Gaza and the final page. Source code is preserved verbatim; names and legal
geography are **not joined**.

Run against the already-acquired official original:

```powershell
python -X utf8 scripts/extract_palestine_pcbs_table29.py --pdf <official-summary-pdf>
python -X utf8 scripts/extract_palestine_pcbs_table29.py --pdf <official-summary-pdf> --out <unadopted-cells.csv>
python -X utf8 -m unittest discover -s tests -p test_palestine_table29.py -v
```

The 585 extracted locality totals sum to **4,500,085**, not the printed
national final total of **4,781,248**: difference **281,163**. The Table 29
footnote says the final population includes post-enumeration estimates, but
this extraction alone does not establish the precise cause or allocation of
the difference. Do not use an invented balancing row, claim exhaustive local
coverage, or aggregate the locality cells as the national count. Jerusalem
J1/J2 source semantics and dated code/polygon crosswalk also remain open.
These cells are therefore an auditable raw source inventory, not a country
edition import. The existing 19-area Table 2 candidate and independent
acceptance status remain unchanged.
