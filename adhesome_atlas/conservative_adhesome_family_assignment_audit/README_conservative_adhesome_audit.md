# Conservative adhesome family-assignment audit

## Environment

- Python 3.10 or newer
- `openpyxl==3.1.5`

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install openpyxl==3.1.5
```

## Run

```bash
python conservative_adhesome_audit.py \
  adhesome_candidates_list.xlsx \
  adhesome_candidates_list_reproduced_audit.xlsx
```

The program refuses to overwrite the input workbook. It writes an audited workbook and a JSON manifest containing the algorithm version and SHA-256 checksums.

## Evidence hierarchy

1. **Domain architecture is the primary gate.** A complete family architecture receives 4 points. Partial domain-type and copy coverage receives at most 2 points.
2. **Orthology is supporting evidence.** Shared-HOG status plus direct orthologues across the five reference species contributes 0–3 points.
3. **Motifs are contextual evidence.** Context-supported/high-confidence motifs contribute 2 points; sequence-only or medium-confidence motifs contribute 1 point.
4. **Localization/topology is a compatibility check.** It contributes at most 1 point.
5. **Competing family labels are resolved conservatively.** A unique complete architecture can resolve a duplicate label. Multiple complete architectures remain ambiguous. If no competing label has a complete architecture, no family-level assignment is made.
6. **Experimental validation is excluded.** It is not read, scored, or used to assign families. It remains a downstream action.

## Grades

- **A:** strong computational support
- **B:** supported family assignment
- **C:** provisional or ambiguous
- **D:** unsupported at the stated family level

## Reproducibility checks

Compare the input SHA-256 against the manifest before interpreting differences between runs. A different input checksum indicates that the source library changed. The output checksum should be compared only when the same Python, `openpyxl`, source workbook, and script version are used.
