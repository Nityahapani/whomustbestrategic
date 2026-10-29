# Reproducibility supplement

**Companion paper:** *Who Must Be Strategic? Target-Specific Access in Deferred Acceptance*  
**Package date:** 29 October 2026

This archive accompanies Appendix B. It contains six validation scripts, one shared Python module, the saved output logs, and the technical supplement in Markdown, editable LaTeX (`technical-supplement.tex`), and compiled PDF (`technical-supplement.pdf`). The supplement documents the reserve-set ledger and full-market efficiency lift. The computations corroborate implementations and finite classes; they do not prove the paper's general results.

## Contents

- `scripts/` — the six scripts listed in Appendix B and their shared dependency, `restricted-da-multicapacity-audit.py`.
- `logs/` — the saved stdout for each check. The unit-capacity block check uses `restricted-da-priority-block-proof-validation.log` rather than the script's default stem.
- `technical-supplement.md` — editable Markdown source.
- `technical-supplement.tex` — editable LaTeX version of the technical supplement.
- `technical-supplement.pdf` — compiled six-page PDF version.
- `MANIFEST.sha256` — SHA-256 checksums for the README, Markdown/LaTeX/PDF supplements, scripts, and saved logs.

All scripts use Python's standard library only. They were validated with Python 3.13.16 and require no input files or network access. Keep all files in `scripts/` together: the two-school `n=2` and incomplete-acceptability `n=4` scripts load the shared module by its adjacent path.

## Run instructions

From the extracted supplement root, run:

```sh
python3 scripts/restricted-da-two-school-target-loss-n2.py
python3 scripts/restricted-da-access-frontier-check.py
python3 scripts/restricted-da-incomplete-acceptability-n4.py
python3 scripts/restricted-da-priority-block-proof.py
python3 scripts/restricted-da-stable-cycle-ergin-lemma-check.py
python3 scripts/restricted-da-three-school-boundary.py
```

Each script writes its result to standard output and exits nonzero if an asserted check fails. To keep the archived logs unchanged when rerunning, redirect output to a temporary file, for example:

```sh
python3 scripts/restricted-da-access-frontier-check.py > /tmp/access-frontier.log 2>&1
```

The saved logs record the outputs bundled with this package. Runtime fields can differ across machines; compare pass status, counts, seeds, and substantive result fields rather than elapsed seconds.

## Build the technical supplement PDF

The PDF is compiled from `technical-supplement.tex` with pdfLaTeX. From the supplement root, run:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error technical-supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error technical-supplement.tex
```

The Markdown file is retained as the source record; the LaTeX and PDF versions are included for submission.

## Scope and class definitions

The scripts are standalone finite checks. “Exact” below means all elements of the stated finite class were enumerated; it does not mean the class covers the theorem's full domain.

### Exhaustive enumerations and fixed-fixture checks

| Script | Enumerated class | What the check validates | Saved log |
|---|---|---|---|
| `restricted-da-two-school-target-loss-n2.py` | Two students, two unit-capacity schools; all four strict priority pairs; the four complete true-preference profiles in which each student ranks both schools acceptable; all four strategic rosters. It checks 64 market-roster cells and 576 restricted strategic-report profiles over the five lists `()`, `(A)`, `(B)`, `(A,B)`, `(B,A)`. | Compares the hybrid-NE outcome set for each roster with the exact two-school target-loss formula. Every strategic report profile is enumerated; truthful unilateral deviations suffice for best-response checks by DA strategy-proofness. | `logs/restricted-da-two-school-target-loss-n2.log` |
| `restricted-da-access-frontier-check.py` | Complete-acceptability two-school markets for `n=2,3,4`: every strict priority pair, every preference-type profile (`A>B` or `B>A`), and every positive capacity split `(a,n-a)`. Totals: 28,240 markets, 447,040 candidate assignments, and 33,906 stable outcomes. | Compares the closed-form cutoff rule with direct stability enumeration; checks the truthful-DA endpoint and target-loss/baseline-core identities; includes explicit capacity-direction witnesses. | `logs/restricted-da-access-frontier-check.log` |
| `restricted-da-incomplete-acceptability-n4.py` | Canonical `n=4`, capacities `(2,2)` class. Student labels fix school A's priority; school B ranges over all 24 strict orders. Each student's true preference is any of the six orders of A, B, and the outside option, giving 31,104 markets. The scan covers 324 non-DA stable-target instances (224 with incomplete acceptability) and 414,720 hybrid report profiles. | Checks the target-loss roster formula over every non-DA stable target and roster in this exact class; reports no mismatch or sufficiency failure. This finite scan is not a general theorem. | `logs/restricted-da-incomplete-acceptability-n4.log` |
| `restricted-da-three-school-boundary.py` | One explicitly specified three-student, three-school, unit-capacity fixture. Preferences: `i: A>B>C>outside`, `j: B>A>C>outside`, `k: A>B>C>outside`; priorities: `A: j>i>k`, `B: i>j>k`, `C: i>j>k`. All 16 ordered lists per strategic student are allowed, including the empty list. The script checks all 4,913 profile-roster combinations across the eight rosters and 16,820 unilateral deviations. | Independently checks DA, stability, target support, and minimum-roster identities in this fixture: truthful DA is `(A,B,C)`, the stable target is `(B,A,C)`, and the minimum roster is `D={i,j}`, strictly smaller than `L={i,j,k}`. | `logs/restricted-da-three-school-boundary.log` |
| `restricted-da-priority-block-proof.py` (exact components) | Exhaustively classifies all strict priority profiles for four students and three unit-capacity schools; 456 profiles are Ergin-acyclic. It also exactly enumerates all six two-student rosters in one four-student/four-school fixture, for 25,350 report profiles total. | Checks the acyclic block classification and, in the selected fixture, the exact fixed-roster stable-slice equality. It also preserves a cross-block stability caveat; the fixture is not a proof of the general theorem. | `logs/restricted-da-priority-block-proof-validation.log` |
| `restricted-da-stable-cycle-ergin-lemma-check.py` (exact components) | Exhaustive priority-profile classes for four students with three schools and quotas `(2,1,1)` (13,824 profiles), and four schools with unit quotas `(1,1,1,1)` (331,776 profiles). The checker first selects profiles meeting the stable-cycle comparisons, then tests the reserve certificate. | Verifies each certificate's priority comparisons, reserve sizes, triple exclusions, and disjointness for every qualifying profile in those classes. | `logs/restricted-da-stable-cycle-ergin-lemma-check.log` |

### Seeded samples — not exhaustive

| Script | Sample | What the check validates | Saved log |
|---|---|---|---|
| `restricted-da-priority-block-proof.py` | 2,000 random DA/blockwise profiles; seed `20261026`. | Cross-checks blockwise DA against an independent round-based DA implementation. It is a seeded regression sample, not a classification of all market profiles. | `logs/restricted-da-priority-block-proof-validation.log` |
| `restricted-da-stable-cycle-ergin-lemma-check.py` | 20,000 random priority profiles for each quota vector `(2,2,2)`, `(2,2,2,2)`, `(3,2,1,2)`; seeds `20261028`, `20261029`, `20261030`, respectively. | Checks the reserve-certificate construction on qualifying stable-cycle profiles found in each sample. The logged counts are sample outcomes and are not exhaustive bounds. | `logs/restricted-da-stable-cycle-ergin-lemma-check.log` |

The seed, quota vector, and per-sample counts are also printed in the corresponding saved log. Exact finite checks and seeded samples are separated both here and in Appendix B; no sampled count is presented as an exhaustive result.

## Interpretation

These are implementation and finite-class checks, not independent proofs and not an algorithm for finding a minimum-cost roster. The arbitrary-capacity theorem gives an exact test for a proposed roster; it does not establish a tractability or hardness result for minimum-roster selection. The analytic proofs in the manuscript carry the general theorem claims.