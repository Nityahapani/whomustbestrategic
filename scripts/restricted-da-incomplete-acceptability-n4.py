"""Exhaustive n=4 test of the two-school target-loss roster formula with
incomplete acceptability and total capacity n.

Capacities are (2,2). By relabeling students, every strict-priority pair is
represented by fixing A's order to 0>1>2>3 and letting B range over all 24
permutations. Each student's true order is any permutation of A, B, and the
outside option, so the 6^4 profiles include every acceptance pattern. Strategic
reports are all five ordered lists (including empty and both orders).

For each non-truthful stable target, the program checks every roster and every
strategic report profile, with best responses reduced to truthful deviations by
strategy-proofness of student-proposing DA. It tests whether the inclusion-minimal
roster is exactly L(mu). This is a finite classification, not a theorem.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import time
from collections import Counter
from pathlib import Path

CORE_PATH = Path(__file__).with_name("restricted-da-multicapacity-audit.py")
SPEC = importlib.util.spec_from_file_location("da_core_incomplete_n4", CORE_PATH)
CORE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CORE)


def is_better(pref, x, y):
    return pref.index(x) < pref.index(y)


def main():
    students = tuple(range(4))
    schools = ("A", "B")
    capacities = {"A": 2, "B": 2}
    ranks_all = tuple(itertools.permutations(students))
    pref_orders = tuple(itertools.permutations(schools + (None,)))
    pref_profiles = tuple(itertools.product(pref_orders, repeat=4))
    reports = CORE.ordered_reports(schools)
    report_id = {r: j for j, r in enumerate(reports)}
    report_profiles = tuple(itertools.product(range(len(reports)), repeat=4))
    profile_index = {profile: j for j, profile in enumerate(report_profiles)}
    assignments = tuple(CORE.all_assignments(students, schools))
    masks = range(1 << 4)

    counters = Counter()
    first_mismatch = None
    first_sufficiency_failure = None
    start = time.time()

    # Canonicalize the first priority order; relabeling preserves the complete class.
    order_a = tuple(students)
    for order_b in ranks_all:
        priorities = {"A": order_a, "B": order_b}
        ranks = CORE.rank_maps(priorities)
        table = tuple(
            CORE.da_rounds(tuple(reports[x] for x in rp), schools, capacities, ranks)
            for rp in report_profiles
        )

        for prefs in pref_profiles:
            counters["markets"] += 1
            truth = tuple(report_id[CORE.preference_prefix(pref)] for pref in prefs)
            baseline = table[profile_index[truth]]
            stable_set = {
                mu for mu in assignments
                if CORE.stable(mu, prefs, schools, capacities, ranks)
            }
            targets = stable_set - {baseline}
            if not targets:
                continue
            counters["markets_with_nonDA_stable_target"] += 1
            counters["nonDA_stable_targets"] += len(targets)
            if all(pref.index("A") < pref.index(None) and pref.index("B") < pref.index(None)
                   for pref in prefs):
                counters["complete_acceptability_target_markets"] += 1
                counters["complete_acceptability_targets"] += len(targets)
            else:
                counters["incomplete_acceptability_target_markets"] += 1
                counters["incomplete_acceptability_targets"] += len(targets)

            loss_mask = {}
            support = {mu: [] for mu in targets}
            for mu in targets:
                lm = 0
                for i in students:
                    if any(is_better(prefs[i], s, mu[i]) for s in schools):
                        lm |= 1 << i
                loss_mask[mu] = lm
                # The target-only construction should support L(mu).
                q = list(truth)
                for i in students:
                    if lm & (1 << i):
                        q[i] = report_id[(mu[i],)] if mu[i] is not None else report_id[()]
                out = table[profile_index[tuple(q)]]
                ok = out == mu
                if ok:
                    for i in students:
                        if lm & (1 << i):
                            qd = list(q)
                            qd[i] = truth[i]
                            alt = table[profile_index[tuple(qd)]][i]
                            if is_better(prefs[i], alt, mu[i]):
                                ok = False
                                break
                if not ok and first_sufficiency_failure is None:
                    first_sufficiency_failure = {
                        "priorities": priorities, "preferences": prefs,
                        "truthful_DA": baseline, "target": mu,
                        "L_mask": lm, "target_only_reports": tuple(reports[x] for x in q),
                        "outcome": out,
                    }
                    raise AssertionError(first_sufficiency_failure)
                counters["target_only_supports_checked"] += 1

            # Enumerate every hybrid report profile for every K. A support by any
            # K not containing L(mu) refutes the conjectured exact minimum roster.
            for mask in masks:
                K = tuple(i for i in students if mask & (1 << i))
                strategic_products = itertools.product(range(len(reports)), repeat=len(K))
                for choices in strategic_products:
                    q = list(truth)
                    for i, rid in zip(K, choices):
                        q[i] = rid
                    q = tuple(q)
                    out = table[profile_index[q]]
                    counters["hybrid_report_profiles_checked"] += 1
                    if out not in support:
                        continue
                    is_ne = True
                    for i in K:
                        qd = list(q)
                        qd[i] = truth[i]
                        alt = table[profile_index[tuple(qd)]][i]
                        if is_better(prefs[i], alt, out[i]):
                            is_ne = False
                            break
                    if not is_ne:
                        continue
                    support[out].append(mask)
                    lm = loss_mask[out]
                    if (mask & lm) != lm and first_mismatch is None:
                        first_mismatch = {
                            "priorities": priorities, "preferences": prefs,
                            "truthful_DA": baseline, "target": out,
                            "L_mask": lm,
                            "supporting_K": K,
                            "reports": tuple(reports[x] for x in q),
                        }
                        raise AssertionError(first_mismatch)

            for mu in targets:
                if not support[mu]:
                    raise AssertionError(("L roster failed to support target", priorities, prefs, baseline, mu))
                counters["formula_targets_verified"] += 1
                counters["supporting_roster_cells_checked"] += 1

        if (len(counters) and (ranks_all.index(order_b) + 1) % 4 == 0):
            print(f"priorities={ranks_all.index(order_b)+1}/24; markets={counters['markets']:,}; "
                  f"targets={counters['nonDA_stable_targets']:,}; "
                  f"elapsed={time.time()-start:.1f}s", flush=True)

    result = {
        "status": "PASS_COMPLETE_EXACT_CLASS" if first_mismatch is None else "COUNTEREXAMPLE",
        "n": 4,
        "capacities": capacities,
        "canonical_priority_profiles": 24,
        "strict_preference_profiles_per_priority": 6**4,
        "ordered_report_profiles_per_roster_game_sum": 6**4,
        "all_markets": counters["markets"],
        "markets_with_nonDA_stable_target": counters["markets_with_nonDA_stable_target"],
        "nonDA_stable_targets": counters["nonDA_stable_targets"],
        "complete_acceptability_target_markets": counters["complete_acceptability_target_markets"],
        "complete_acceptability_targets": counters["complete_acceptability_targets"],
        "incomplete_acceptability_target_markets": counters["incomplete_acceptability_target_markets"],
        "incomplete_acceptability_targets": counters["incomplete_acceptability_targets"],
        "target_only_supports_checked": counters["target_only_supports_checked"],
        "hybrid_report_profiles_checked": counters["hybrid_report_profiles_checked"],
        "formula_targets_verified": counters["formula_targets_verified"],
        "first_mismatch": first_mismatch,
        "first_sufficiency_failure": first_sufficiency_failure,
        "elapsed_seconds": round(time.time() - start, 2),
        "interpretation": "Exact only for the canonical n=4, q=(2,2) class; not a general theorem.",
    }
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
