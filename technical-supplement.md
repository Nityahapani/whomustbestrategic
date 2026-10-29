# Technical supplement: reserve certificates, efficiency lift, and finite checks

**Companion paper:** *Who Must Be Strategic? Target-Specific Access in Deferred Acceptance*  
**Date:** 29 October 2026  
**Scope:** Detailed reserve-set derivations, the full-market efficiency lift, and validation scope for the accompanying reproducibility scripts.

## A. Adjusted-Ergin cycle definition used in the proof

For school capacities `q_s,q_t`, an adjusted-Ergin certificate is a pair of distinct schools `s,t`, three distinct students `p,j,ell`, and disjoint reserve sets `E,F` such that

- at `s`: `p ≻_s j ≻_s ell`;
- at `t`: `ell ≻_t p`;
- `E` contains exactly `q_s-1` students above `j` at `s`, excludes the triple;
- `F` contains exactly `q_t-1` students above `p` at `t`, excludes the triple;
- `E ∩ F = ∅`.

Empty reserve sets are permitted when a school has unit capacity. In the proof, each chosen reserve set is obtained from a full target roster `C_h=μ^{-1}(b_h)` of size `q_h`; fullness and the incumbent-priority comparison follow from stability whenever the cycle's incoming student strictly prefers that school to their target assignment.

## B. Reserve-set certificate ledger for the long-cycle lemma

Assume a stable matching `μ` has a strict improvement cycle with distinct schools `b_1,...,b_m`, distinct students `a_1,...,a_m`, `m≥3`, and indices modulo `m`, with `μ(a_i)=b_i` and `b_i ≻_{a_{i+1}} b_{i+1}`. Write `C_i=μ^{-1}(b_i)` and `q_i=q_{b_i}`. Stability gives `|C_i|=q_i` and every member of `C_i` above incoming `a_{i+1}` at `b_i`.

| Contradiction branch | Certificate triple and schools | Reserve at first school | Reserve at second school | Size, priority, exclusion, and disjointness check |
|---|---|---|---|---|
| Comparison induction, `r=0` | `(p,j,ell)=(a_i,a_{i+1},a_{i-1})`; `(s,t)=(b_i,b_{i-1})` | `C_i \ {a_i}` | `C_{i-1} \ {a_{i-1}}` | First size `q_i−1`; it removes the only triple student in `C_i`. Both other triple members have assignments at `b_{i+1}` and `b_{i-1}`, distinct from `b_i` for all `m≥3`. All first-reserve members outrank `j` by stability. Second size `q_{i-1}−1`; `a_{i-1}=ell` is removed, `p` is assigned to `b_i`, and `j` to `b_{i+1}`, both distinct from `b_{i-1}`. Stability for incoming `p` puts every remaining incumbent above `p`. The school rosters are distinct and disjoint. |
| Comparison induction, `1≤r≤m−3` | `(p,j,ell)=(a_{i-r},a_{i+1},a_{i-r-1})`; `(s,t)=(b_i,b_{i-r-1})` | Any `q_i−1` members of `C_i` | `C_{i-r-1} \ {a_{i-r-1}}` | At `s`, the three students are outside `C_i`: their assigned-school offsets from `i` are `−r`, `+1`, and `−r−1`, none zero modulo `m` over this range. Thus any `q_i−1` incumbents exclude the triple and all outrank `j` by stability. At `t`, `ell` is removed; `p` is assigned to the distinct school `b_{i-r}`. `j` is assigned to `b_{i+1}`; this differs from `b_{i-r-1}` because equality would require `r+2≡0 (mod m)`, whereas `2≤r+2≤m−1`. The second set has exact size and lies above incoming `p` by stability. The schools differ because `1≤r+1≤m−2`; their target rosters are disjoint. |
| Lowest-incumbent contradiction | If `a_{i+2} ≻_{b_i} r_i`, use `(p,j,ell)=(a_{i+2},r_i,a_{i+1})`; `(s,t)=(b_i,b_{i+1})` | `C_i \ {r_i}` | `C_{i+1} \ {a_{i+1}}` | First size `q_i−1`; its members outrank `r_i=j` because `r_i` is the lowest incumbent. `p` and `ell` are assigned to `b_{i+2}` and `b_{i+1}`, not `b_i`. Second size `q_{i+1}−1`; `ell` is removed and stability puts all remaining incumbents above incoming `p`. Neither `p` nor `j` is assigned to `b_{i+1}`. The rosters are distinct/disjoint. When either capacity is one, the corresponding reserve is empty and still has the required size. |
| Final certificate, `m=3` | `(p,j,ell)=(a_i,a_{i+2},a_{i+1})`; `(s,t)=(b_i,b_{i-1})` | `C_i \ {a_i}` | `C_{i-1} \ {a_{i+2}}` | At `s`, size is `q_i−1`; `r_i` is above `a_{i+2}` and is the lowest incumbent, so every reserve is above `j`. The only triple member assigned at `t` is `a_{i+2}`, since `b_{i+2}=b_{i-1}` for `m=3`; remove it. The other two triple members are at `b_i,b_{i+1}`. At `t`, every remaining incumbent is above incoming `a_i` by stability. The school rosters are distinct/disjoint. |
| Final certificate, `m≥4` | Same triple and schools | `C_i \ {a_i}` | Any `q_{i-1}−1` members of `C_{i-1}` | The first set has the same exact size and priority property as above. None of the triple members is assigned to `b_{i-1}`: the assignments are at `b_i,b_{i+1},b_{i+2}`, and these differ from `b_{i-1}` for `m≥4`. Choose any `q_{i-1}−1` incumbents; stability puts them above incoming `a_i`. Distinct target rosters make the sets disjoint. |

### Boundary checks

- **Smallest cycle:** When `m=3`, the induction range `0≤r≤m−3` contains the single step `r=0`. If its comparison failed, the certificate triple is `(a_i,a_{i+1},a_{i+2})` at the distinct schools `(b_i,b_{i-1})`; if no certificate exists, that step yields the comparison `a_{i+2}≻_{b_i}a_{i+1}` used later. The lowest-incumbent step uses `b_i,b_{i+1}`, also distinct. In the final branch, exactly one triple student, `a_{i+2}`, is assigned to the second school `b_{i-1}` and is removed from its reserve roster.
- **Longer cycles:** For `m≥4`, the final second-school roster contains none of the three certificate students, so no deletion is needed there. The modular inequalities in the induction ensure the second roster also excludes `p,j` at every endpoint `r=m−3`.
- **Capacity one:** Every reserve set has cardinality exactly `q_s−1`. If `q_s=1`, its prescribed set is empty. All priority claims about an empty set are vacuous; no branch presumes a positive reserve count.
- **Disjointness:** In every branch, the reserve sets are subsets of `C_h` and `C_k` for distinct target schools. Since `μ` is a matching, distinct school rosters are disjoint. The explicitly deleted triple member is the only triple student in that roster; the index checks above establish that no other triple member enters the set.
- **Priority thresholds:** At a school with a reserve roster, the incoming cycle student strictly prefers that school to their `μ`-assignment. Stability therefore makes the school full and ranks every incumbent above that incoming student. The one exception to this general source of a priority inequality is the first-school reserve in the lowest-incumbent step: `C_i\{r_i}` lies above `r_i` because `r_i` is the lowest-priority incumbent.

## C. Exact application of Ergin efficiency in the residual-efficiency lemma

For each `J⊆K`, the residual market `M_J` removes students in `J` and exactly their target seats; its DA outcome is `λ^J`. The efficiency argument is deliberately **not** an application of Ergin's theorem to `M_J`.

1. Return to the **original full market**, with the original priorities, capacities, and adjusted-Ergin-acyclicity condition.
2. Construct a full strict report profile `P^J`: students in `J` rank a matched target first and all omitted schools below the outside option; an unmatched target reporter ranks the outside option above every school; all active students report true preferences.
3. The target-lock decomposition proves that full-market DA at `P^J` yields `μ_J ∪ λ^J`.
4. If a feasible residual matching `ω` Pareto-dominated `λ^J`, lift it to `μ_J ∪ ω`. At each school `s`, feasibility is exactly
   `|J∩μ^{-1}(s)| + |ω^{-1}(s)| ≤ |J∩μ^{-1}(s)| + q_s^J = q_s`.
   The lift leaves each target-locked reporter unchanged under their completed report, weakly improves every active student at their true preference, and strictly improves at least one.
5. Ergin (2002), Theorem 1, gives Pareto efficiency of the extended DA rule under the original adjusted-acyclic priority-capacity profile, for every strict preference profile. It applies to the full profile `P^J`, contradicting the full-market Pareto improvement. Thus `λ^J` is Pareto efficient among feasible residual matchings, evaluated at active students' true preferences.

No residual acyclicity is assumed or needed. The point of lifting is precisely to use the established efficiency theorem where its verified acyclicity hypothesis applies: the original market.

## D. Unit-capacity ordered blocks: role in the roster theorem

The paper now states the common ordered-block representation as a separate lemma (`lem:orderedblocks`) and the DA/stability decomposition as a separate lemma (`lem:blockdecomp`). Their proof works for every finite number of students and schools. In brief:

- Relative to a reference school's ranking, any nonadjacent inversion creates an Ergin cycle.
- Adjacent reversals cannot overlap at one school, by transitivity and the preceding nonadjacent result.
- Adjacent reversals cannot overlap across schools: the induced three-student priority comparisons themselves form an Ergin cycle.
- The union of reversals is therefore a matching on the reference-order path, which yields common ordered singleton/pair blocks; conversely, the shared block order precludes a cycle.
- Asynchronous DA can clear those blocks in order because earlier-block students outrank later-block students at every school. Stable-match restrictions within each residual block market satisfy Rural Hospitals, so each block uses the same school set across stable matchings. A changed pair is a whole swap; a singleton cannot change.
- This makes `D(μ)⊆K` necessary and sufficient for the unit-capacity theorem. The block representation reformulates the established acyclicity condition and is used to derive the fixed-roster outcome correspondence.

## E. Finite validation scope and saved logs

The analytic proofs in the manuscript establish the general results. The checks below validate small enumerated classes or the implementation of the written certificate construction; they do not replace those proofs. The companion `README.md` gives exact run commands, class definitions, dependencies, and the explicit separation between exhaustive enumeration and seeded sampling.

### Exhaustive enumerations and fixed-fixture checks

| Check | Scope and validation | Saved log |
|---|---|---|
| Two-school `n=2` target-loss regression | All four priority profiles, four complete preference profiles per priority, and all four rosters; 64 market-roster cells and 576 strategic report profiles. Checks the exact roster/outcome correspondence over all five ordered two-school reports. | `logs/restricted-da-two-school-target-loss-n2.log` |
| Two-school access frontier | Exact `n=2,3,4` complete-acceptability class; 28,240 markets, 447,040 candidate assignments, and 33,906 stable outcomes. Checks the cutoff formula and target-loss/core identities against direct stability. | `logs/restricted-da-access-frontier-check.log` |
| Incomplete-acceptability two-school scan | Exact canonical `n=4`, `(2,2)` class; 31,104 markets and 324 non-DA stable targets, including 224 incomplete-acceptability targets. Checks the target-loss formula over all target-roster cases. | `logs/restricted-da-incomplete-acceptability-n4.log` |
| Unit-capacity block check | All four-student/three-school priority profiles classified (456 acyclic); an exact four-by-four fixture enumerates all six size-two rosters and 25,350 report profiles. Checks the block classification and the fixed-roster equality in that fixture. | `logs/restricted-da-priority-block-proof-validation.log` |
| Reserve certificates, exact classes | All 13,824 profiles for `m=3`, `q=(2,1,1)`, and all 331,776 profiles for `m=4`, `q=(1,1,1,1)`; only profiles satisfying the stable-cycle comparisons enter the certificate checks. | `logs/restricted-da-stable-cycle-ergin-lemma-check.log` |
| Three-school boundary fixture | One explicitly specified three-student, three-school unit-capacity market; all 4,913 report-profile/roster combinations and 16,820 unilateral deviations. Independently checks the stable target and `MinK(target)=D(target)⊊L(target)` for this fixture only. | `logs/restricted-da-three-school-boundary.log` |

### Seeded checks — not exhaustive

| Check | Sample and seed | Validation |
|---|---|---|
| Unit-capacity DA/block comparison | 2,000 random profiles; seed `20261026`. | Cross-checks blockwise and independent round-based DA. |
| Reserve-certificate samples | 20,000 profiles for each of `q=(2,2,2)`, `q=(2,2,2,2)`, and `q=(3,2,1,2)`; seeds `20261028`, `20261029`, and `20261030`, respectively. | Verifies the reserve construction on qualifying stable-cycle profiles found in each sample; counts are sample outcomes. |

The exact profile counts and per-sample certificate-branch counts appear in the saved logs. A seeded sample is not treated as exhaustive. The three-school fixture is a single counterexample illustration, not a class-wide theorem check.
