"""Certificate-level checks for the stable-improvement-cycle lemma.

This is an implementation audit of the reserve-set construction in
restricted-da-residual-local-global-proof.md, not a proof and not a broad
priority-class search. For each tested simple cycle, it filters priority
profiles satisfying the stability comparisons at the cycle schools, then builds
one of the proof's three adjusted-Ergin-cycle certificates (induction, reserve
minimum, or final cycle) and verifies every comparison, reserve size, exclusion,
and disjointness condition.

Run:
  python research/restricted-da-stable-cycle-ergin-lemma-check.py
"""
from __future__ import annotations

import itertools
import random


def above(priorities, school, x, y):
    return priorities[school].index(x) < priorities[school].index(y)


def stable_cycle_condition(priorities, capacities, rosters, movers, schools):
    """At each school, all mu-incumbents outrank its incoming cycle mover."""
    m = len(movers)
    return all(
        all(above(priorities, s, c, movers[(i + 1) % m]) for c in rosters[s])
        for i, s in enumerate(schools)
    )


def build_certificate(priorities, capacities, rosters, movers, schools):
    """Return a concrete adjusted-Ergin cycle using the proof's case split."""
    m = len(movers)
    assert m >= 3 and len(set(movers)) == m and len(set(schools)) == m
    assert stable_cycle_condition(priorities, capacities, rosters, movers, schools)

    # Stage 1: if a cycle mover is not above the incoming mover at some school,
    # the induction step itself is an adjusted Ergin cycle.
    for i, s in enumerate(schools):
        for r in range(m - 2):  # r = 0,...,m-3
            p = movers[(i - r) % m]
            j = movers[(i + 1) % m]
            ell = movers[(i - r - 1) % m]
            assert above(priorities, s, p, j)
            if above(priorities, s, j, ell):
                t = schools[(i - r - 1) % m]
                A = list(rosters[s])
                if r == 0:
                    A.remove(movers[i])
                else:
                    A = A[: capacities[s] - 1]
                B = list(rosters[t])
                B.remove(ell)
                return (s, t, p, j, ell, tuple(A), tuple(B), "induction")

    # Stage 2: a capacity-minimum incumbent above the incoming mover.
    for i, s in enumerate(schools):
        t = schools[(i + 1) % m]
        worst = max(rosters[s], key=lambda x: priorities[s].index(x))
        p = movers[(i + 2) % m]
        j = worst
        ell = movers[(i + 1) % m]
        if above(priorities, s, p, worst):
            A = list(rosters[s])
            A.remove(worst)
            B = list(rosters[t])
            B.remove(ell)
            return (s, t, p, j, ell, tuple(A), tuple(B), "minimum-incumbent")

    # Final cycle. At school b_i use (a_i,a_{i+2},a_{i+1}); at b_{i-1},
    # a_{i+1} outranks the incoming a_i. For m=3, remove a_{i+2} from C_{i-1};
    # for m>=4 no student in the triple is assigned to b_{i-1}.
    i = 0
    s, t = schools[i], schools[(i - 1) % m]
    p = movers[i]
    j = movers[(i + 2) % m]
    ell = movers[(i + 1) % m]
    A = list(rosters[s])
    A.remove(p)
    B = [x for x in rosters[t] if x not in {p, j, ell}]
    B = B[: capacities[t] - 1]
    return (s, t, p, j, ell, tuple(A), tuple(B), "final")


def verify_certificate(priorities, capacities, cert):
    s, t, p, j, ell, A, B, _branch = cert
    triple = {p, j, ell}
    return (
        s != t
        and len(triple) == 3
        and above(priorities, s, p, j)
        and above(priorities, s, j, ell)
        and above(priorities, t, ell, p)
        and len(A) == capacities[s] - 1
        and len(B) == capacities[t] - 1
        and triple.isdisjoint(A)
        and triple.isdisjoint(B)
        and set(A).isdisjoint(B)
        and all(above(priorities, s, x, j) for x in A)
        and all(above(priorities, t, x, p) for x in B)
    )


def run_exact(name, capacities, rosters, movers):
    schools = tuple(capacities)
    students = tuple(range(sum(capacities.values())))
    orders = list(itertools.permutations(students))
    checked = 0
    branches = {"induction": 0, "minimum-incumbent": 0, "final": 0}
    for profile in itertools.product(orders, repeat=len(schools)):
        priorities = dict(zip(schools, profile))
        if not stable_cycle_condition(priorities, capacities, rosters, movers, schools):
            continue
        checked += 1
        cert = build_certificate(priorities, capacities, rosters, movers, schools)
        assert verify_certificate(priorities, capacities, cert), (name, priorities, cert)
        branches[cert[-1]] += 1
    print(
        f"{name}: total_priority_profiles={len(orders) ** len(schools)}; "
        f"stable_cycle_profiles={checked}; valid_certificates={sum(branches.values())}; "
        f"branches={branches}"
    )


def run_random(name, capacities, rosters, movers, trials, seed):
    schools = tuple(capacities)
    students = tuple(range(sum(capacities.values())))
    rng = random.Random(seed)
    checked = 0
    branches = {"induction": 0, "minimum-incumbent": 0, "final": 0}
    for _ in range(trials):
        priorities = {s: tuple(rng.sample(students, len(students))) for s in schools}
        if not stable_cycle_condition(priorities, capacities, rosters, movers, schools):
            continue
        checked += 1
        cert = build_certificate(priorities, capacities, rosters, movers, schools)
        assert verify_certificate(priorities, capacities, cert), (name, priorities, cert)
        branches[cert[-1]] += 1
    print(
        f"{name}: sampled_profiles={trials}; stable_cycle_profiles={checked}; "
        f"valid_certificates={sum(branches.values())}; branches={branches}; seed={seed}"
    )


def main():
    run_exact(
        "exact m=3, q=(2,1,1), n=4",
        {0: 2, 1: 1, 2: 1},
        {0: (0, 3), 1: (1,), 2: (2,)},
        (0, 1, 2),
    )
    run_exact(
        "exact m=4, q=(1,1,1,1), n=4",
        {0: 1, 1: 1, 2: 1, 3: 1},
        {0: (0,), 1: (1,), 2: (2,), 3: (3,)},
        (0, 1, 2, 3),
    )
    run_random(
        "random m=3, q=(2,2,2), n=6",
        {0: 2, 1: 2, 2: 2},
        {0: (0, 3), 1: (1, 4), 2: (2, 5)},
        (0, 1, 2),
        trials=20_000,
        seed=20261028,
    )
    run_random(
        "random m=4, q=(2,2,2,2), n=8",
        {0: 2, 1: 2, 2: 2, 3: 2},
        {0: (0, 4), 1: (1, 5), 2: (2, 6), 3: (3, 7)},
        (0, 1, 2, 3),
        trials=20_000,
        seed=20261029,
    )
    run_random(
        "random m=4, q=(3,2,1,2), n=8",
        {0: 3, 1: 2, 2: 1, 3: 2},
        {0: (0, 4, 5), 1: (1, 6), 2: (2,), 3: (3, 7)},
        (0, 1, 2, 3),
        trials=20_000,
        seed=20261030,
    )
    print("PASS: every tested stable-cycle priority profile has a verified Ergin-cycle certificate")


if __name__ == "__main__":
    main()
