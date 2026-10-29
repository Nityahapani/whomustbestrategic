"""Exact audit of the fixed-truthful-subset DA conjecture with capacities > 1.

This is a separate, round-based checker (not a proof). It implements the
capacity-adjusted Ergin-cycle condition stated by Ergin (2002) / Haeringer–Klijn
(2009), checks its unit-capacity reduction, discovers interesting (2,1)-capacity
priority profiles, and can exactly enumerate every true-preference profile and
strategic set for selected 4-student/2-school markets.

Reports are ordered lists of acceptable schools. This is outcome-equivalent to a
strict school/outside-option ranking: keep the prefix above the outside option.

Commands:
  python research/restricted-da-multicapacity-audit.py --validate-acyclicity
  python research/restricted-da-multicapacity-audit.py --discover
  python research/restricted-da-multicapacity-audit.py --exact --limit 3

The exact all-K test is exhaustive over (1) all six strict true rankings of two
schools plus the outside option for each of four students, (2) every K subset,
(3) all ordered acceptable lists for students in K, and (4) every unilateral
deviation. It tests only the listed priority profiles, not all possible markets.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import time
from collections import deque
from pathlib import Path


def rank_maps(priorities):
    return {s: {i: k for k, i in enumerate(order)} for s, order in priorities.items()}


def da_rounds(reports, schools, capacities, ranks):
    """Independent round-based student-proposing DA for responsive school choice."""
    n = len(reports)
    next_choice = [0] * n
    held = {s: set() for s in schools}
    while True:
        proposals = {s: set() for s in schools}
        made = False
        for i in range(n):
            if any(i in held[s] for s in schools):
                continue
            if next_choice[i] >= len(reports[i]):
                continue
            s = reports[i][next_choice[i]]
            next_choice[i] += 1
            proposals[s].add(i)
            made = True
        if not made:
            break
        for s in schools:
            pool = held[s] | proposals[s]
            if len(pool) > capacities[s]:
                chosen = set(sorted(pool, key=lambda i: ranks[s][i])[:capacities[s]])
            else:
                chosen = pool
            held[s] = chosen
    ans = [None] * n
    for s, members in held.items():
        for i in members:
            ans[i] = s
    return tuple(ans)


def da_queue(reports, schools, capacities, ranks):
    """Queue-order DA implementation used only as a cross-check."""
    n = len(reports)
    next_choice = [0] * n
    held = {s: set() for s in schools}
    free = deque(range(n))
    while free:
        i = free.popleft()
        if next_choice[i] >= len(reports[i]):
            continue
        s = reports[i][next_choice[i]]
        next_choice[i] += 1
        held[s].add(i)
        chosen = set(sorted(held[s], key=lambda j: ranks[s][j])[:capacities[s]])
        rejected = held[s] - chosen
        held[s] = chosen
        free.extend(sorted(rejected))
    ans = [None] * n
    for s, members in held.items():
        for i in members:
            ans[i] = s
    return tuple(ans)


def stable(assignment, true_preferences, schools, capacities, ranks):
    """Feasibility, individual rationality, nonwastefulness, and no justified envy."""
    for s in schools:
        if sum(x == s for x in assignment) > capacities[s]:
            return False
    for i, pref in enumerate(true_preferences):
        assigned = assignment[i]
        if assigned is not None and pref.index(assigned) > pref.index(None):
            return False
        for s in schools:
            if pref.index(s) >= pref.index(assigned):
                continue
            incumbents = [j for j, x in enumerate(assignment) if x == s]
            if len(incumbents) < capacities[s]:
                return False
            worst = max(incumbents, key=lambda j: ranks[s][j])
            if ranks[s][i] < ranks[s][worst]:
                return False
    return True


def capacity_ergin_cycle(priorities, capacities, students=None):
    """Exact Ergin cycle test including the capacity-dependent scarcity sets.

    There is a cycle at distinct schools s,t and students i,j,l if
    i >_s j >_s l, l >_t i, and there are disjoint sets outside the triple
    A subset of U_s(j), B subset of U_t(i), with |A|=q_s-1 and |B|=q_t-1.
    """
    schools = tuple(priorities)
    if students is None:
        students = tuple(priorities[schools[0]]) if schools else ()
    rank = rank_maps(priorities)
    for s in schools:
        for t in schools:
            if s == t:
                continue
            for i, j, ell in itertools.permutations(students, 3):
                if not (rank[s][i] < rank[s][j] < rank[s][ell]):
                    continue
                if not (rank[t][ell] < rank[t][i]):
                    continue
                excluded = {i, j, ell}
                a_pool = [x for x in students if x not in excluded and rank[s][x] < rank[s][j]]
                b_pool = [x for x in students if x not in excluded and rank[t][x] < rank[t][i]]
                qa = capacities[s] - 1
                qb = capacities[t] - 1
                if qa < 0 or qb < 0 or qa > len(a_pool) or qb > len(b_pool):
                    continue
                for a_set in itertools.combinations(a_pool, qa):
                    a_set = set(a_set)
                    for b_set in itertools.combinations(b_pool, qb):
                        if a_set.isdisjoint(b_set):
                            return True
    return False


def unit_ergin_cycle(priorities, students=None):
    """Simplified capacity-one cycle test, independent of scarcity sets."""
    schools = tuple(priorities)
    if students is None:
        students = tuple(priorities[schools[0]]) if schools else ()
    rank = rank_maps(priorities)
    for s in schools:
        for t in schools:
            if s == t:
                continue
            for i, j, ell in itertools.permutations(students, 3):
                if rank[s][i] < rank[s][j] < rank[s][ell] and rank[t][ell] < rank[t][i]:
                    return True
    return False


def ordered_reports(schools):
    return tuple(
        prefix
        for length in range(len(schools) + 1)
        for prefix in itertools.permutations(schools, length)
    )


def preference_prefix(pref):
    return pref[:pref.index(None)]


def all_assignments(students, schools):
    return itertools.product(tuple(schools) + (None,), repeat=len(students))


def validate_acyclicity():
    """Check generalized cycle code reduces exactly to classic cycles at q=1."""
    n = 4
    students = tuple(range(n))
    schools = ("a", "b", "c")
    orders = tuple(itertools.permutations(students))
    caps = {s: 1 for s in schools}
    count = 0
    start = time.time()
    for profile in itertools.product(orders, repeat=len(schools)):
        priorities = dict(zip(schools, profile))
        generalized = capacity_ergin_cycle(priorities, caps, students)
        classic = unit_ergin_cycle(priorities, students)
        if generalized != classic:
            raise AssertionError((priorities, generalized, classic))
        count += not generalized
    print(f"PASS unit-capacity reduction: {count:,} acyclic profiles among 13,824; {time.time()-start:.2f}s")


def capacity_priority_profiles(n=4):
    students = tuple(range(n))
    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    orders = tuple(itertools.permutations(students))
    out = []
    for oa, ob in itertools.product(orders, repeat=2):
        p = {"A": oa, "B": ob}
        if not capacity_ergin_cycle(p, capacities, students):
            out.append(p)
    return students, schools, capacities, out


def find_interesting_profiles(sample_per_priority=160, seed=20261026):
    students, schools, capacities, acyclic = capacity_priority_profiles(4)
    individual_preferences = tuple(itertools.permutations(schools + (None,)))
    true_profiles = tuple(itertools.product(individual_preferences, repeat=len(students)))
    assignments = tuple(all_assignments(students, schools))
    rng = random.Random(seed)
    report = []
    for idx, priorities in enumerate(acyclic):
        ranks = rank_maps(priorities)
        best = None
        sampled = rng.sample(true_profiles, min(sample_per_priority, len(true_profiles)))
        for prefs in sampled:
            stable_set = tuple(x for x in assignments if stable(x, prefs, schools, capacities, ranks))
            if len(stable_set) > 1 and (best is None or len(stable_set) > best[0]):
                baseline = da_rounds(tuple(preference_prefix(p) for p in prefs), schools, capacities, ranks)
                best = (len(stable_set), prefs, baseline, stable_set)
        if best is not None:
            # Kendall distance between the two school's orders measures nontriviality.
            oa, ob = priorities["A"], priorities["B"]
            pos_a = {x: i for i, x in enumerate(oa)}
            inversion_distance = sum(pos_a[x] > pos_a[y] for x, y in itertools.combinations(ob, 2))
            report.append((best[0], inversion_distance, idx, priorities, best[1], best[2], best[3]))
    report.sort(key=lambda z: (z[0], z[1]), reverse=True)
    print(f"Capacity vector (2,1), n=4: {len(acyclic)} acyclic priority pairs out of 576.")
    print(f"Profiles with sampled stable multiplicity: {len(report)} (sample={sample_per_priority} per priority pair, seed={seed}).")
    for count, distance, idx, p, prefs, baseline, stable_set in report[:10]:
        print({
            "acyclic_index": idx,
            "stable_count_in_sample": count,
            "priority_disagreement": distance,
            "priorities": p,
            "preferences": prefs,
            "truthful_DA": baseline,
            "stable_set": stable_set,
        })
    return [x[3] for x in report[:10]]


def exact_all_preferences(priorities, label="market", max_profiles=None):
    """Enumerate H, all K and all unilateral deviations for one priority profile."""
    students = tuple(range(4))
    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    ranks = rank_maps(priorities)
    individual_preferences = tuple(itertools.permutations(schools + (None,)))
    true_preferences_all = tuple(itertools.product(individual_preferences, repeat=len(students)))
    reports = ordered_reports(schools)
    report_id = {r: k for k, r in enumerate(reports)}
    nreport = len(reports)
    full_report_profiles = tuple(itertools.product(range(nreport), repeat=len(students)))
    da_table = {
        rp: da_rounds(tuple(reports[x] for x in rp), schools, capacities, ranks)
        for rp in full_report_profiles
    }
    assignments = tuple(all_assignments(students, schools))
    all_k = tuple(tuple(i for i in students if mask & (1 << i)) for mask in range(1 << len(students)))
    run_profiles = true_preferences_all if max_profiles is None else true_preferences_all[:max_profiles]
    report_profiles_checked = 0
    market_k_cells = 0
    stable_outcomes_seen = 0
    nontrivial_stable_cells = 0
    total_expected_outcomes = 0
    total_ne_outcomes = 0
    target_only_tested = 0
    target_only_passed = 0
    first_target_only_failure = None
    started = time.time()

    for pidx, true_prefs in enumerate(run_profiles):
        true_report_ids = tuple(report_id[preference_prefix(p)] for p in true_prefs)
        baseline = da_table[true_report_ids]
        stable_set = tuple(x for x in assignments if stable(x, true_prefs, schools, capacities, ranks))
        stable_outcomes_seen += len(stable_set)
        if len(stable_set) > 1:
            nontrivial_stable_cells += 1
        for K in all_k:
            Kset = set(K)
            frozen = set(students) - Kset
            expected = {
                mu for mu in stable_set
                if all(mu[i] == baseline[i] for i in frozen)
            }
            total_expected_outcomes += len(expected)
            actual = set()
            # Enumerate all reports of K; outsiders use their true acceptable prefixes.
            for strategic_choice in itertools.product(range(nreport), repeat=len(K)):
                q = list(true_report_ids)
                for i, r_id in zip(K, strategic_choice):
                    q[i] = r_id
                q = tuple(q)
                outcome = da_table[q]
                report_profiles_checked += 1
                is_ne = True
                for i in K:
                    current_rank = true_prefs[i].index(outcome[i])
                    for dev in range(nreport):
                        q_dev = list(q)
                        q_dev[i] = dev
                        alternate = da_table[tuple(q_dev)][i]
                        if true_prefs[i].index(alternate) < current_rank:
                            is_ne = False
                            break
                    if not is_ne:
                        break
                if is_ne:
                    actual.add(outcome)
            market_k_cells += 1
            total_ne_outcomes += len(actual)
            if actual != expected:
                mismatch = {
                    "profile_index": pidx,
                    "priorities": priorities,
                    "preferences": true_prefs,
                    "K": K,
                    "truthful_DA": baseline,
                    "stable_set": stable_set,
                    "expected": expected,
                    "actual": actual,
                }
                print("H MISMATCH:", mismatch)
                return {
                    "status": "COUNTEREXAMPLE_TO_H",
                    "mismatch": str(mismatch),
                    "priorities": priorities,
                    "cells_checked": market_k_cells,
                    "report_profiles_checked": report_profiles_checked,
                }

            # Test the natural capacity-generalized support: changed K students
            # report only their target school; other strategic students report truth.
            for mu in expected:
                q = list(true_report_ids)
                for i in K:
                    if mu[i] != baseline[i]:
                        q[i] = report_id[(mu[i],)] if mu[i] is not None else report_id[()]
                q = tuple(q)
                target_only_tested += 1
                supported = da_table[q]
                good = supported == mu
                if good:
                    for i in K:
                        current_rank = true_prefs[i].index(supported[i])
                        for dev in range(nreport):
                            q_dev = list(q)
                            q_dev[i] = dev
                            if true_prefs[i].index(da_table[tuple(q_dev)][i]) < current_rank:
                                good = False
                                break
                        if not good:
                            break
                if good:
                    target_only_passed += 1
                elif first_target_only_failure is None:
                    first_target_only_failure = {
                        "profile_index": pidx,
                        "preferences": true_prefs,
                        "K": K,
                        "target": mu,
                        "truthful_DA": baseline,
                        "support_reports": tuple(reports[r] for r in q),
                        "outcome": supported,
                    }
        if (pidx + 1) % 128 == 0:
            print(f"{label}: preferences={pidx+1}/{len(run_profiles)}; report profiles={report_profiles_checked:,}; elapsed={time.time()-started:.1f}s", flush=True)

    result = {
        "status": "PASS_H" if max_profiles is None else "PARTIAL_H_PASS",
        "label": label,
        "priorities": {s: list(o) for s, o in priorities.items()},
        "capacity": capacities,
        "true_preference_profiles": len(run_profiles),
        "market_K_cells": market_k_cells,
        "report_profiles_checked": report_profiles_checked,
        "stable_outcomes_sum_across_preferences": stable_outcomes_seen,
        "preference_profiles_with_stable_multiplicity": nontrivial_stable_cells,
        "predicted_hybrid_outcomes_sum": total_expected_outcomes,
        "exact_NE_outcomes_sum": total_ne_outcomes,
        "target_only_supports_passed": target_only_passed,
        "target_only_supports_tested": target_only_tested,
        "first_target_only_failure": first_target_only_failure,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    print(json.dumps(result, indent=2, default=str))
    return result


def capacity_cycle_candidates(priorities, capacities, students=None):
    """List cycle-condition triples, marking whether scarcity can be filled."""
    schools = tuple(priorities)
    if students is None:
        students = tuple(priorities[schools[0]]) if schools else ()
    rank = rank_maps(priorities)
    candidates = []
    for s in schools:
        for t in schools:
            if s == t:
                continue
            for i, j, ell in itertools.permutations(students, 3):
                if not (rank[s][i] < rank[s][j] < rank[s][ell]):
                    continue
                if not (rank[t][ell] < rank[t][i]):
                    continue
                excluded = {i, j, ell}
                a_pool = [x for x in students if x not in excluded and rank[s][x] < rank[s][j]]
                b_pool = [x for x in students if x not in excluded and rank[t][x] < rank[t][i]]
                qa, qb = capacities[s] - 1, capacities[t] - 1
                witness = None
                if 0 <= qa <= len(a_pool) and 0 <= qb <= len(b_pool):
                    for a_set in itertools.combinations(a_pool, qa):
                        for b_set in itertools.combinations(b_pool, qb):
                            if set(a_set).isdisjoint(b_set):
                                witness = (a_set, b_set)
                                break
                        if witness is not None:
                            break
                candidates.append({
                    "schools": (s, t), "triple": (i, j, ell),
                    "A_pool": tuple(a_pool), "B_pool": tuple(b_pool),
                    "required_sizes": (qa, qb), "scarcity_witness": witness,
                })
    return candidates


def exact_fixed_market(priorities, true_preferences, label="fixed-market"):
    """Exact all-K game enumeration for one many-to-one market."""
    students = tuple(range(len(true_preferences)))
    schools = tuple(priorities)
    capacities = {"A": 2, "B": 1}
    ranks = rank_maps(priorities)
    reports = ordered_reports(schools)
    report_id = {r: x for x, r in enumerate(reports)}
    true_report_ids = tuple(report_id[preference_prefix(p)] for p in true_preferences)
    baseline = da_rounds(tuple(preference_prefix(p) for p in true_preferences), schools, capacities, ranks)
    stable_set = tuple(
        mu for mu in all_assignments(students, schools)
        if stable(mu, true_preferences, schools, capacities, ranks)
    )
    cycle_candidates = capacity_cycle_candidates(priorities, capacities, students)
    acyclic = not any(c["scarcity_witness"] is not None for c in cycle_candidates)
    expected_table = {}
    actual_table = {}
    ne_profiles_table = {}
    report_count_total = 0
    for mask in range(1 << len(students)):
        K = tuple(i for i in students if mask & (1 << i))
        frozen = set(students) - set(K)
        expected = {
            mu for mu in stable_set
            if all(mu[i] == baseline[i] for i in frozen)
        }
        actual = set()
        ne_profiles = []
        for strategic_choice in itertools.product(range(len(reports)), repeat=len(K)):
            q = list(true_report_ids)
            for i, rid in zip(K, strategic_choice):
                q[i] = rid
            q = tuple(q)
            outcome = da_rounds(tuple(reports[r] for r in q), schools, capacities, ranks)
            report_count_total += 1
            ne = True
            for i in K:
                current = true_preferences[i].index(outcome[i])
                for dev in range(len(reports)):
                    qd = list(q)
                    qd[i] = dev
                    alternate = da_rounds(tuple(reports[r] for r in qd), schools, capacities, ranks)[i]
                    if true_preferences[i].index(alternate) < current:
                        ne = False
                        break
                if not ne:
                    break
            if ne:
                actual.add(outcome)
                ne_profiles.append((tuple(reports[r] for r in q), outcome))
        expected_table[K] = expected
        actual_table[K] = actual
        ne_profiles_table[K] = ne_profiles

    result = {
        "label": label,
        "capacities": capacities,
        "priorities": {s: tuple(priorities[s]) for s in schools},
        "true_preferences": tuple(true_preferences),
        "capacity_adjusted_ergin_acyclic": acyclic,
        "cycle_condition_candidates": cycle_candidates,
        "truthful_DA": baseline,
        "stable_set": stable_set,
        "expected_H_outcomes_by_K": {K: v for K, v in expected_table.items()},
        "exact_NE_outcomes_by_K": {K: v for K, v in actual_table.items()},
        "NE_report_profiles_by_K": {K: v for K, v in ne_profiles_table.items()},
        "report_profiles_enumerated_across_all_K": report_count_total,
        "mismatching_K": tuple(K for K in expected_table if expected_table[K] != actual_table[K]),
    }
    printable = {k: v for k, v in result.items() if k not in {
        "expected_H_outcomes_by_K", "exact_NE_outcomes_by_K", "NE_report_profiles_by_K"
    }}
    printable["by_K"] = [
        {
            "K": K,
            "expected_H": expected_table[K],
            "exact_NE": actual_table[K],
            "NE_report_profile_count": len(ne_profiles_table[K]),
            "mismatch": expected_table[K] != actual_table[K],
        }
        for K in expected_table
    ]
    print(json.dumps(printable, indent=2, default=str))
    return result


def counterexample_fixture():
    """Verify and explain a 4-student (2,1)-capacity counterexample to H."""
    priorities = {
        "A": (0, 1, 2, 3),
        "B": (2, 1, 0, 3),
    }
    preferences = (
        ("B", "A", None),
        ("B", "A", None),
        ("A", "B", None),
        ("A", "B", None),
    )
    result = exact_fixed_market(priorities, preferences, "capacity-(2,1)-counterexample")
    assert result["capacity_adjusted_ergin_acyclic"]
    baseline = ("A", "B", "A", None)
    target = ("A", "A", "B", None)
    assert result["truthful_DA"] == baseline
    assert set(result["stable_set"]) == {baseline, target}
    assert result["mismatching_K"] == ((1, 2), (1, 2, 3)), result["mismatching_K"]
    assert target in result["expected_H_outcomes_by_K"][(1, 2)]
    assert target not in result["exact_NE_outcomes_by_K"][(1, 2)]

    # Check all target-supporting reports for K={1,2}; student 2 can switch to A alone.
    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    ranks = rank_maps(priorities)
    reports = ordered_reports(schools)
    target_supports = []
    dev_outcomes = []
    for r1, r2 in itertools.product(reports, repeat=2):
        q = [("B", "A"), r1, r2, ("A", "B")]
        outcome = da_rounds(tuple(q), schools, capacities, ranks)
        if outcome == target:
            target_supports.append((r1, r2))
            qd = [q[0], q[1], ("A",), q[3]]
            deviated = da_rounds(tuple(qd), schools, capacities, ranks)
            assert deviated[2] == "A" and preferences[2].index("A") < preferences[2].index("B")
            dev_outcomes.append((r1, r2, deviated))
    assert target_supports
    assert all(row[2][2] == "A" for row in dev_outcomes)
    gatekeeper_support = (("A",), ("A",), ("B",), ("A", "B"))
    assert da_rounds(gatekeeper_support, schools, capacities, ranks) == target
    gatekeeper_deviations = []
    for i in (0, 1, 2):
        for deviation in reports:
            qd = list(gatekeeper_support)
            qd[i] = deviation
            outcome = da_rounds(tuple(qd), schools, capacities, ranks)
            assert preferences[i].index(outcome[i]) >= preferences[i].index(target[i])
            gatekeeper_deviations.append((i, deviation, outcome))
    print("\nTarget-supporting reports for students 1,2:", target_supports)
    print("Student 2's unilateral A-only deviation outcomes:", dev_outcomes)
    print("With student 0 strategic, (A),(A),(B),(AB) support the target; all 15 deviations:", gatekeeper_deviations)
    print("PASS: exact capacity-adjusted acyclicity certificate and H counterexample.")
    return result


def minimal_counterexample_fixture():
    """The smallest exact (2,1)-capacity counterexample found: n=3, two schools."""
    priorities = {
        "A": (0, 1, 2),
        "B": (2, 0, 1),
    }
    preferences = (
        ("B", "A", None),
        ("B", "A", None),
        ("A", "B", None),
    )
    result = exact_fixed_market(priorities, preferences, "minimal-capacity-counterexample")
    baseline = ("B", "A", "A")
    target = ("A", "A", "B")
    assert result["capacity_adjusted_ergin_acyclic"]
    assert result["truthful_DA"] == baseline
    assert set(result["stable_set"]) == {baseline, target}
    assert target in result["expected_H_outcomes_by_K"][(0, 2)]
    assert target not in result["exact_NE_outcomes_by_K"][(0, 2)]

    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    ranks = rank_maps(priorities)
    reports = ordered_reports(schools)
    for profile in itertools.product(reports, repeat=3):
        assert da_rounds(profile, schools, capacities, ranks) == da_queue(profile, schools, capacities, ranks)
    target_supports = []
    for r0, r2 in itertools.product(reports, repeat=2):
        q = [r0, ("B", "A"), r2]
        if da_rounds(tuple(q), schools, capacities, ranks) == target:
            qd = [r0, ("B", "A"), ("A",)]
            deviated = da_rounds(tuple(qd), schools, capacities, ranks)
            assert deviated[2] == "A"
            assert preferences[2].index("A") < preferences[2].index("B")
            target_supports.append((r0, r2, deviated))
    assert target_supports
    full_support = (("A",), ("A",), ("B",))
    all_strategic_support = da_rounds(full_support, schools, capacities, ranks)
    assert all_strategic_support == target
    equilibrium_deviations = []
    for i in range(3):
        for deviation in reports:
            qd = list(full_support)
            qd[i] = deviation
            outcome = da_rounds(tuple(qd), schools, capacities, ranks)
            assert preferences[i].index(outcome[i]) >= preferences[i].index(target[i])
            equilibrium_deviations.append((i, deviation, outcome))
    print("Target-support profiles with K={0,2} and student-2's A-only deviation:", target_supports)
    print("When student 1 is also strategic, reports (A),(A),(B) yield target:", all_strategic_support)
    print("Verified all 15 unilateral report deviations from that full-K profile:", equilibrium_deviations)
    return result


def validate_da_implementations(seed=381026, trials=10000):
    rng = random.Random(seed)
    students = tuple(range(4))
    schools = ("A", "B", "C")
    capacities = {"A": 2, "B": 1, "C": 2}
    orders = tuple(itertools.permutations(students))
    reports = ordered_reports(schools)
    for _ in range(trials):
        priorities = {s: rng.choice(orders) for s in schools}
        ranks = rank_maps(priorities)
        profile = tuple(rng.choice(reports) for _ in students)
        by_round = da_rounds(profile, schools, capacities, ranks)
        by_queue = da_queue(profile, schools, capacities, ranks)
        if by_round != by_queue:
            raise AssertionError((priorities, profile, by_round, by_queue))
    print(f"PASS DA implementation cross-check: {trials:,} random profiles, seed={seed}")


def exact_small_class(n, capacities):
    """Fully enumerate all priorities, preferences, K, reports, and deviations."""
    students = tuple(range(n))
    schools = ("A", "B")
    orders = tuple(itertools.permutations(students))
    individual_preferences = tuple(itertools.permutations(schools + (None,)))
    true_profiles = tuple(itertools.product(individual_preferences, repeat=n))
    reports = ordered_reports(schools)
    report_profiles = tuple(itertools.product(range(len(reports)), repeat=n))
    assignments = tuple(all_assignments(students, schools))
    total_priority_profiles = 0
    total_acyclic_profiles = 0
    total_market_K_cells = 0
    total_reports = 0
    mismatches = []
    started = time.time()
    for order_a, order_b in itertools.product(orders, repeat=2):
        priorities = {"A": order_a, "B": order_b}
        total_priority_profiles += 1
        if capacity_ergin_cycle(priorities, capacities, students):
            continue
        total_acyclic_profiles += 1
        ranks = rank_maps(priorities)
        da_table = {
            rp: da_rounds(tuple(reports[r] for r in rp), schools, capacities, ranks)
            for rp in report_profiles
        }
        report_id = {r: j for j, r in enumerate(reports)}
        for true_prefs in true_profiles:
            true_ids = tuple(report_id[preference_prefix(p)] for p in true_prefs)
            baseline = da_table[true_ids]
            stable_set = tuple(
                mu for mu in assignments
                if stable(mu, true_prefs, schools, capacities, ranks)
            )
            for mask in range(1 << n):
                K = tuple(i for i in students if mask & (1 << i))
                frozen = set(students) - set(K)
                expected = {
                    mu for mu in stable_set
                    if all(mu[i] == baseline[i] for i in frozen)
                }
                actual = set()
                for strategic_choice in itertools.product(range(len(reports)), repeat=len(K)):
                    q = list(true_ids)
                    for i, rid in zip(K, strategic_choice):
                        q[i] = rid
                    q = tuple(q)
                    outcome = da_table[q]
                    total_reports += 1
                    ne = True
                    for i in K:
                        current = true_prefs[i].index(outcome[i])
                        for dev in range(len(reports)):
                            qd = list(q)
                            qd[i] = dev
                            if true_prefs[i].index(da_table[tuple(qd)][i]) < current:
                                ne = False
                                break
                        if not ne:
                            break
                    if ne:
                        actual.add(outcome)
                total_market_K_cells += 1
                if actual != expected:
                    if len(mismatches) < 10:
                        mismatches.append({
                            "priorities": priorities,
                            "preferences": true_prefs,
                            "K": K,
                            "truthful_DA": baseline,
                            "stable": stable_set,
                            "expected": expected,
                            "actual": actual,
                        })
                    # No need to enumerate the remainder once a counterexample exists.
                    print("N3 CLASS COUNTEREXAMPLE:", mismatches[-1])
                    return {
                        "n": n, "capacities": capacities,
                        "priority_profiles": total_priority_profiles,
                        "acyclic_priority_profiles": total_acyclic_profiles,
                        "market_K_cells_checked": total_market_K_cells,
                        "report_profiles_checked": total_reports,
                        "mismatch": mismatches[-1],
                        "elapsed_seconds": round(time.time()-started, 2),
                    }
    result = {
        "n": n, "capacities": capacities,
        "priority_profiles": total_priority_profiles,
        "acyclic_priority_profiles": total_acyclic_profiles,
        "market_K_cells_checked": total_market_K_cells,
        "report_profiles_checked": total_reports,
        "mismatches": mismatches,
        "status": "PASS_EXHAUSTIVE_CLASS",
        "elapsed_seconds": round(time.time()-started, 2),
    }
    print(json.dumps(result, indent=2, default=str))
    return result


def minimality_n3():
    """Find an exact three-student (2,1)-capacity counterexample."""
    return exact_small_class(3, {"A": 2, "B": 1})


def exhaustive_n3_capacity_class():
    """Fully scan all n=3, two-school, (2,1)-capacity priorities/preferences/K."""
    n = 3
    students = tuple(range(n))
    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    orders = tuple(itertools.permutations(students))
    individual_preferences = tuple(itertools.permutations(schools + (None,)))
    true_profiles = tuple(itertools.product(individual_preferences, repeat=n))
    reports = ordered_reports(schools)
    report_profiles = tuple(itertools.product(range(len(reports)), repeat=n))
    report_id = {r: idx for idx, r in enumerate(reports)}
    assignments = tuple(all_assignments(students, schools))
    counters = {
        "priority_profiles": 0, "acyclic_priority_profiles": 0,
        "market_K_cells": 0, "report_profiles": 0,
        "sufficiency_mismatch_cells": 0, "necessity_mismatch_cells": 0,
        "both_direction_mismatch_cells": 0, "unstable_NE_cells": 0,
        "preference_profiles_with_stable_multiplicity": 0,
    }
    examples = {"sufficiency": [], "necessity": [], "both": [], "unstable": []}
    started = time.time()
    for order_a, order_b in itertools.product(orders, repeat=2):
        priorities = {"A": order_a, "B": order_b}
        counters["priority_profiles"] += 1
        if capacity_ergin_cycle(priorities, capacities, students):
            continue
        counters["acyclic_priority_profiles"] += 1
        ranks = rank_maps(priorities)
        da_table = {
            rp: da_rounds(tuple(reports[r] for r in rp), schools, capacities, ranks)
            for rp in report_profiles
        }
        for true_prefs in true_profiles:
            true_ids = tuple(report_id[preference_prefix(p)] for p in true_prefs)
            baseline = da_table[true_ids]
            stable_set = tuple(
                mu for mu in assignments
                if stable(mu, true_prefs, schools, capacities, ranks)
            )
            if len(stable_set) > 1:
                counters["preference_profiles_with_stable_multiplicity"] += 1
            for mask in range(1 << n):
                K = tuple(i for i in students if mask & (1 << i))
                frozen = set(students) - set(K)
                expected = {
                    mu for mu in stable_set
                    if all(mu[i] == baseline[i] for i in frozen)
                }
                actual = set()
                for strategic_choice in itertools.product(range(len(reports)), repeat=len(K)):
                    q = list(true_ids)
                    for i, rid in zip(K, strategic_choice):
                        q[i] = rid
                    q = tuple(q)
                    outcome = da_table[q]
                    counters["report_profiles"] += 1
                    ne = True
                    for i in K:
                        current = true_prefs[i].index(outcome[i])
                        for dev in range(len(reports)):
                            qd = list(q)
                            qd[i] = dev
                            if true_prefs[i].index(da_table[tuple(qd)][i]) < current:
                                ne = False
                                break
                        if not ne:
                            break
                    if ne:
                        actual.add(outcome)
                counters["market_K_cells"] += 1
                missing, extra = expected - actual, actual - expected
                if missing or extra:
                    category = "both" if missing and extra else ("sufficiency" if missing else "necessity")
                    key = f"{category}_mismatch_cells"
                    counters[key] += 1
                    examples[category].append({
                            "priorities": priorities,
                            "preferences": true_prefs,
                            "K": K,
                            "truthful_DA": baseline,
                            "stable": stable_set,
                            "expected": expected,
                            "actual": actual,
                            "missing_expected": missing,
                            "extra_actual": extra,
                        })
                unstable = actual - set(stable_set)
                if unstable:
                    counters["unstable_NE_cells"] += 1
                    if len(examples["unstable"]) < 5:
                        examples["unstable"].append({
                            "priorities": priorities, "preferences": true_prefs,
                            "K": K, "unstable_NE_outcomes": unstable,
                        })
    failure_classes = set()
    for example in examples["sufficiency"]:
        canonical = None
        for relabel in itertools.permutations(students):
            mapped_priorities = tuple(
                tuple(relabel[i] for i in example["priorities"][s]) for s in schools
            )
            mapped_prefs = [None] * n
            for i, pref in enumerate(example["preferences"]):
                mapped_prefs[relabel[i]] = tuple(pref)
            mapped_K = tuple(sorted(relabel[i] for i in example["K"]))
            key = (mapped_priorities, tuple(mapped_prefs), mapped_K)
            if canonical is None or key < canonical:
                canonical = key
        failure_classes.add(canonical)
    result = {
        "status": "COMPLETE_EXHAUSTIVE_CLASS_SCAN",
        "n": n, "capacities": capacities,
        **counters,
        "expected_report_profiles_if_all_priorities_acyclic": 36 * (6 ** (2*n)),
        "student_relabeling_failure_isomorphism_classes": len(failure_classes),
        "canonical_failure_classes": [str(key) for key in sorted(failure_classes)],
        "examples": examples,
        "elapsed_seconds": round(time.time()-started, 2),
    }
    print(json.dumps(result, indent=2, default=str))
    return result


def exhaustive_fixed_n4_priority_class():
    """Enumerate all preferences, K, reports for one acyclic n=4 q=(2,1) profile."""
    n = 4
    students = tuple(range(n))
    schools = ("A", "B")
    capacities = {"A": 2, "B": 1}
    priorities = {"A": (0, 1, 2, 3), "B": (2, 1, 0, 3)}
    assert not capacity_ergin_cycle(priorities, capacities, students)
    individual_preferences = tuple(itertools.permutations(schools + (None,)))
    true_profiles = tuple(itertools.product(individual_preferences, repeat=n))
    reports = ordered_reports(schools)
    report_profiles = tuple(itertools.product(range(len(reports)), repeat=n))
    report_id = {r: idx for idx, r in enumerate(reports)}
    assignments = tuple(all_assignments(students, schools))
    ranks = rank_maps(priorities)
    da_table = {
        rp: da_rounds(tuple(reports[r] for r in rp), schools, capacities, ranks)
        for rp in report_profiles
    }
    counts = {
        "preference_profiles": 0, "market_K_cells": 0, "report_profiles": 0,
        "sufficiency_mismatch_cells": 0, "necessity_mismatch_cells": 0,
        "both_direction_mismatch_cells": 0, "unstable_NE_cells": 0,
    }
    examples = {"sufficiency": None, "necessity": None, "both": None, "unstable": None}
    started = time.time()
    for true_prefs in true_profiles:
        counts["preference_profiles"] += 1
        true_ids = tuple(report_id[preference_prefix(p)] for p in true_prefs)
        baseline = da_table[true_ids]
        stable_set = {
            mu for mu in assignments
            if stable(mu, true_prefs, schools, capacities, ranks)
        }
        for mask in range(1 << n):
            K = tuple(i for i in students if mask & (1 << i))
            frozen = set(students) - set(K)
            expected = {
                mu for mu in stable_set
                if all(mu[i] == baseline[i] for i in frozen)
            }
            actual = set()
            for strategic_choice in itertools.product(range(len(reports)), repeat=len(K)):
                q = list(true_ids)
                for i, rid in zip(K, strategic_choice):
                    q[i] = rid
                q = tuple(q)
                counts["report_profiles"] += 1
                outcome = da_table[q]
                ne = True
                for i in K:
                    current = true_prefs[i].index(outcome[i])
                    for dev in range(len(reports)):
                        qd = list(q)
                        qd[i] = dev
                        if true_prefs[i].index(da_table[tuple(qd)][i]) < current:
                            ne = False
                            break
                    if not ne:
                        break
                if ne:
                    actual.add(outcome)
            counts["market_K_cells"] += 1
            missing, extra = expected - actual, actual - expected
            category = "both" if missing and extra else ("sufficiency" if missing else ("necessity" if extra else None))
            if category:
                key = {
                    "sufficiency": "sufficiency_mismatch_cells",
                    "necessity": "necessity_mismatch_cells",
                    "both": "both_direction_mismatch_cells",
                }[category]
                counts[key] += 1
                if examples[category] is None:
                    examples[category] = {
                        "preferences": true_prefs, "K": K, "truthful_DA": baseline,
                        "stable": stable_set, "expected": expected, "actual": actual,
                        "missing_expected": missing, "extra_actual": extra,
                    }
            unstable = actual - stable_set
            if unstable:
                counts["unstable_NE_cells"] += 1
                if examples["unstable"] is None:
                    examples["unstable"] = {"preferences": true_prefs, "K": K, "unstable": unstable}
    result = {
        "status": "COMPLETE_FIXED_PRIORITY_CLASS_SCAN",
        "n": n, "capacities": capacities, "priorities": priorities,
        **counts,
        "expected_report_profiles": (6 ** n) * (6 ** n),
        "examples": examples,
        "elapsed_seconds": round(time.time()-started, 2),
    }
    print(json.dumps(result, indent=2, default=str))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-acyclicity", action="store_true")
    parser.add_argument("--validate-da", action="store_true")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--counterexample", action="store_true")
    parser.add_argument("--minimal-counterexample", action="store_true")
    parser.add_argument("--minimality-n3", action="store_true")
    parser.add_argument("--exhaustive-n3", action="store_true")
    parser.add_argument("--exhaustive-n4-fixed", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--partial-preferences", type=int, default=None,
                        help="debug only: cap true preference profiles per priority fixture")
    args = parser.parse_args()
    if args.validate_acyclicity:
        validate_acyclicity()
    if args.validate_da:
        validate_da_implementations()
    if args.discover:
        find_interesting_profiles()
    if args.exact:
        candidates = find_interesting_profiles()
        for k, priorities in enumerate(candidates[:args.limit]):
            label = f"acyclic-candidate-{k+1}"
            print(f"\n=== EXACT {label}: {priorities} ===")
            exact_all_preferences(priorities, label, args.partial_preferences)
    if args.counterexample:
        counterexample_fixture()
    if args.minimal_counterexample:
        minimal_counterexample_fixture()
    if args.minimality_n3:
        minimality_n3()
    if args.exhaustive_n3:
        exhaustive_n3_capacity_class()
    if args.exhaustive_n4_fixed:
        exhaustive_fixed_n4_priority_class()
    if not (args.validate_acyclicity or args.validate_da or args.discover or args.exact or args.counterexample or args.minimal_counterexample or args.minimality_n3 or args.exhaustive_n3 or args.exhaustive_n4_fixed):
        parser.print_help()


if __name__ == "__main__":
    main()
