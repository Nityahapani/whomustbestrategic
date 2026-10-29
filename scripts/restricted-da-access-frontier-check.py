"""Exhaustively validate the two-school complete-acceptability access-frontier formula.

For n=2,3,4, enumerate every strict priority pair, every binary preference-type
profile, and every positive capacity split (a,n-a). Compare (i) the closed-form
cutoff rule to direct stability enumeration, (ii) truthful DA to the r_hi
endpoint, and (iii) the target-loss/baseline-core identities to direct assignments.
This is finite validation; the general claim is proved in the companion memo.
"""
from __future__ import annotations

import itertools
import json
from collections import Counter


def da(reports, priorities, capacities):
    schools = ("A", "B")
    rank = {s: {i: k for k, i in enumerate(priorities[s])} for s in schools}
    next_choice = [0] * len(reports)
    held = {s: set() for s in schools}
    while True:
        proposals = {s: set() for s in schools}
        made = False
        for i, report in enumerate(reports):
            if any(i in held[s] for s in schools):
                continue
            if next_choice[i] < len(report):
                s = report[next_choice[i]]
                next_choice[i] += 1
                proposals[s].add(i)
                made = True
        if not made:
            break
        for s in schools:
            pool = held[s] | proposals[s]
            held[s] = set(sorted(pool, key=rank[s].__getitem__)[:capacities[s]])
    mu = [None] * len(reports)
    for s in schools:
        for i in held[s]:
            mu[i] = s
    return tuple(mu)


def is_stable(mu, pref_types, priorities, capacities):
    rank = {s: {i: k for k, i in enumerate(priorities[s])} for s in ("A", "B")}
    if any(mu.count(s) != capacities[s] for s in ("A", "B")):
        return False
    for i, top in enumerate(pref_types):
        if mu[i] != top:
            assignees = [j for j, x in enumerate(mu) if x == top]
            if any(rank[top][i] < rank[top][j] for j in assignees):
                return False
    return True


def candidate_matching(n, pref_types, priorities, a, r):
    q = sum(t == "B" for t in pref_types)
    p = n - q
    b = n - a
    rank = {s: {i: k for k, i in enumerate(priorities[s])} for s in ("A", "B")}
    A_pref = sorted((i for i, t in enumerate(pref_types) if t == "A"), key=rank["A"].__getitem__)
    B_pref = sorted((i for i, t in enumerate(pref_types) if t == "B"), key=rank["B"].__getitem__)
    s = r - a + q
    assert 0 <= r <= p and 0 <= s <= q
    mu = [None] * n
    for i in A_pref[:r]:
        mu[i] = "A"
    for i in A_pref[r:]:
        mu[i] = "B"
    for i in B_pref[:s]:
        mu[i] = "B"
    for i in B_pref[s:]:
        mu[i] = "A"
    assert mu.count("A") == a and mu.count("B") == b
    return tuple(mu), A_pref, B_pref


def frontier_formula(pref_types, priorities, a):
    n = len(pref_types)
    p = sum(t == "A" for t in pref_types)
    q = n - p
    rank = {s: {i: k for k, i in enumerate(priorities[s])} for s in ("A", "B")}
    A_pref = sorted((i for i, t in enumerate(pref_types) if t == "A"), key=rank["A"].__getitem__)
    B_pref = sorted((i for i, t in enumerate(pref_types) if t == "B"), key=rank["B"].__getitem__)
    incompatible = []
    for k, x in enumerate(A_pref, 1):
        for j, y in enumerate(B_pref, 1):
            if not (rank["A"][y] < rank["A"][x] and rank["B"][x] < rank["B"][y]):
                incompatible.append((k, j))
    rlo, rhi = max(0, a-q), min(p, a)
    rS = max([rlo] + [min(k, j+a-q) for k, j in incompatible])
    return {
        "r_lo": rlo, "r_hi": rhi, "r_student_pessimal": rS,
        "stable_target_count": rhi-rS+1,
        "student_pessimal_roster_burden": p+a-2*rS,
        "baseline_core_size": abs(p-a),
        "incompatible_pairs": incompatible,
    }


def main():
    checked_markets = 0
    checked_assignments = 0
    stable_outcomes = 0
    direct_r_histogram = Counter()
    first_r = None
    for n in (2, 3, 4):
        students = tuple(range(n))
        orders = tuple(itertools.permutations(students))
        for order_a, order_b in itertools.product(orders, repeat=2):
            priorities = {"A": order_a, "B": order_b}
            rank = {s: {i: k for k, i in enumerate(priorities[s])} for s in ("A", "B")}
            for pref_types in itertools.product(("A", "B"), repeat=n):
                p = sum(t == "A" for t in pref_types)
                q = n - p
                reports = tuple(("A", "B") if t == "A" else ("B", "A") for t in pref_types)
                for a in range(1, n):
                    b = n - a
                    checked_markets += 1
                    rlo = max(0, a - q)
                    rhi = min(p, a)
                    A_pref = sorted((i for i, t in enumerate(pref_types) if t == "A"), key=rank["A"].__getitem__)
                    B_pref = sorted((i for i, t in enumerate(pref_types) if t == "B"), key=rank["B"].__getitem__)
                    incompatible = []
                    for k, x in enumerate(A_pref, 1):
                        for j, y in enumerate(B_pref, 1):
                            compatible = rank["A"][y] < rank["A"][x] and rank["B"][x] < rank["B"][y]
                            if not compatible:
                                incompatible.append((k, j))
                    cutoffs = [min(k, j + a - q) for k, j in incompatible]
                    rS = max([rlo] + cutoffs)
                    assert rlo <= rS <= rhi
                    expected = {}
                    for r in range(rS, rhi + 1):
                        mu, _, _ = candidate_matching(n, pref_types, priorities, a, r)
                        expected[mu] = r
                        assert is_stable(mu, pref_types, priorities, {"A": a, "B": b})

                    direct = {}
                    for mu in itertools.product(("A", "B"), repeat=n):
                        checked_assignments += 1
                        if is_stable(mu, pref_types, priorities, {"A": a, "B": b}):
                            r = sum(pref_types[i] == "A" and mu[i] == "A" for i in students)
                            if r in direct:
                                raise AssertionError(("nonunique r", n, priorities, pref_types, a, r))
                            direct[mu] = r
                    if direct != expected:
                        raise AssertionError(("frontier mismatch", n, priorities, pref_types, a, direct, expected))

                    baseline = da(reports, priorities, {"A": a, "B": b})
                    if baseline != candidate_matching(n, pref_types, priorities, a, rhi)[0]:
                        raise AssertionError(("DA endpoint mismatch", n, priorities, pref_types, a, baseline, rhi))
                    L0 = {i for i in students if baseline[i] != pref_types[i]}
                    if len(L0) != abs(p - a):
                        raise AssertionError(("baseline core size", n, priorities, pref_types, a, L0))
                    for mu, r in direct.items():
                        L = {i for i in students if mu[i] != pref_types[i]}
                        D = {i for i in students if mu[i] != baseline[i]}
                        if L != L0 | D or len(D) != 2 * (rhi - r) or len(L) != p + a - 2 * r:
                            raise AssertionError(("loss identity", n, priorities, pref_types, a, mu, L0, L, D, r, rhi))
                        if not L0 <= L:
                            raise AssertionError(("core nesting", n, priorities, pref_types, a, mu, L0, L))
                    stable_outcomes += len(direct)
                    direct_r_histogram[len(direct)] += 1
                    if first_r is None and rS < rhi:
                        first_r = {
                            "n": n, "priorities": priorities, "preferences": pref_types,
                            "capacity_A": a, "r_S": rS, "r_hi": rhi,
                            "incompatible_pairs": incompatible,
                        }
    # Exact local capacity witnesses: increasing A capacity can either remove
    # or add a stable target, and the pessimal roster burden moves by -1 or +1.
    cap_down_priorities = {"A": (1, 0, 2), "B": (0, 2, 1)}
    cap_down_prefs = ("A", "B", "B")  # u: A>B; v,w: B>A
    cap_down = {
        "a=1": frontier_formula(cap_down_prefs, cap_down_priorities, 1),
        "a=2": frontier_formula(cap_down_prefs, cap_down_priorities, 2),
    }
    assert cap_down["a=1"]["stable_target_count"] == 2
    assert cap_down["a=2"]["stable_target_count"] == 1
    assert cap_down["a=1"]["student_pessimal_roster_burden"] == 2
    assert cap_down["a=2"]["student_pessimal_roster_burden"] == 1

    cap_up_priorities = {"A": (0, 2, 1), "B": (0, 1, 2)}
    cap_up_prefs = ("A", "A", "B")  # u,v: A>B; w: B>A
    cap_up = {
        "a=1": frontier_formula(cap_up_prefs, cap_up_priorities, 1),
        "a=2": frontier_formula(cap_up_prefs, cap_up_priorities, 2),
    }
    assert cap_up["a=1"]["stable_target_count"] == 1
    assert cap_up["a=2"]["stable_target_count"] == 2
    assert cap_up["a=1"]["student_pessimal_roster_burden"] == 1
    assert cap_up["a=2"]["student_pessimal_roster_burden"] == 2

    # With p=1, q=2, a=1 and within-type priority order fixed, removing an
    # incompatible cross pair opens the frontier; adding it closes it.
    priority_alignment = {
        "compatible_all": frontier_formula(
            ("A", "B", "B"), {"A": (1, 2, 0), "B": (0, 1, 2)}, 1
        ),
        "one_incompatible": frontier_formula(
            ("A", "B", "B"), {"A": (1, 0, 2), "B": (0, 1, 2)}, 1
        ),
    }
    assert priority_alignment["compatible_all"]["stable_target_count"] == 2
    assert priority_alignment["one_incompatible"]["stable_target_count"] == 1

    result = {
        "status": "PASS_EXHAUSTIVE_FORMULA_CHECK",
        "n_range": [2, 4],
        "markets_checked": checked_markets,
        "candidate_assignments_checked": checked_assignments,
        "stable_outcomes_checked": stable_outcomes,
        "stable_target_count_histogram_over_markets": dict(sorted(direct_r_histogram.items())),
        "example_with_multiple_stable_targets": first_r,
        "capacity_increase_witnesses": {
            "target_count_and_burden_decrease": cap_down,
            "target_count_and_burden_increase": cap_up,
        },
        "priority_alignment_witness": priority_alignment,
        "note": "Finite validation only; general cutoff and comparative statics are proved in the memo.",
    }
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
