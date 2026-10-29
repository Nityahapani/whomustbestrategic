"""Exact n=2 regression check for the two-school target-loss theorem.

Enumerates all strict priorities, true preference profiles, strategic rosters,
and all strategic report profiles over the five two-school lists (empty, A, B,
AB, BA), with arbitrary order, plus truthful unilateral deviations. DA
strategy-proofness makes truthful deviations sufficient for the NE check.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path

CORE_PATH = Path(__file__).with_name("restricted-da-multicapacity-audit.py")
SPEC = importlib.util.spec_from_file_location("da_core_loss_n2", CORE_PATH)
CORE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CORE)


def main():
    n = 2
    students = tuple(range(n))
    schools = ("A", "B")
    capacities = {"A": 1, "B": 1}
    priorities = tuple(itertools.permutations(students))
    preference_types = (("A", "B", None), ("B", "A", None))
    preference_profiles = tuple(itertools.product(preference_types, repeat=n))
    reports = CORE.ordered_reports(schools)
    report_id = {r: i for i, r in enumerate(reports)}
    report_profiles = tuple(itertools.product(range(len(reports)), repeat=n))
    assignments = tuple(CORE.all_assignments(students, schools))

    cells = 0
    restricted_profiles_checked = 0
    mismatches = []
    for oa, ob in itertools.product(priorities, repeat=2):
        priority_profile = {"A": oa, "B": ob}
        ranks = CORE.rank_maps(priority_profile)
        da_table = {
            rp: CORE.da_rounds(
                tuple(reports[r] for r in rp), schools, capacities, ranks
            )
            for rp in report_profiles
        }
        for prefs in preference_profiles:
            truth = tuple(
                report_id[CORE.preference_prefix(pref)] for pref in prefs
            )
            baseline = da_table[truth]
            stable_set = {
                mu
                for mu in assignments
                if CORE.stable(mu, prefs, schools, capacities, ranks)
            }
            for mask in range(1 << n):
                K = tuple(i for i in students if mask & (1 << i))
                actual = set()
                for choices in itertools.product(range(len(reports)), repeat=len(K)):
                    profile = list(truth)
                    for i, rid in zip(K, choices):
                        profile[i] = rid
                    profile = tuple(profile)
                    outcome = da_table[profile]
                    restricted_profiles_checked += 1
                    is_ne = True
                    for i in K:
                        deviation = list(profile)
                        deviation[i] = truth[i]
                        truth_outcome = da_table[tuple(deviation)]
                        if prefs[i].index(truth_outcome[i]) < prefs[i].index(outcome[i]):
                            is_ne = False
                            break
                    if is_ne:
                        actual.add(outcome)

                expected = {baseline}
                for mu in stable_set - {baseline}:
                    loss = {
                        i for i in students
                        if prefs[i].index(mu[i]) > prefs[i].index(prefs[i][0])
                    }
                    if loss <= set(K):
                        expected.add(mu)
                cells += 1
                if actual != expected and len(mismatches) < 5:
                    mismatches.append({
                        "priorities": priority_profile,
                        "preferences": prefs,
                        "K": K,
                        "baseline": baseline,
                        "expected": sorted(expected),
                        "actual": sorted(actual),
                    })

    result = {
        "status": "PASS_EXHAUSTIVE_N2" if not mismatches else "FAIL",
        "n": n,
        "capacities": capacities,
        "priority_profiles": len(priorities) ** 2,
        "preference_profiles_per_priority": len(preference_profiles),
        "strategic_rosters_per_market": 1 << n,
        "equilibrium_cells_checked": cells,
        "restricted_report_profiles_checked": restricted_profiles_checked,
        "mismatches": mismatches,
        "note": (
            "All strategic profiles were enumerated over Q={empty,A,B,AB,BA}; "
            "order is unrestricted. Unilateral best-response checks use truthful "
            "deviations by DA strategy-proofness."
        ),
    }
    print(json.dumps(result, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
