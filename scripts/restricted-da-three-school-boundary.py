"""Independent exact checker for the 3-school failure of the two-school L(mu) rule.

Three students and three unit-capacity schools; every strict preference and
priority order is written explicitly below. This file intentionally contains an
independent round-based DA implementation and direct blocking-pair checker; it
does not import the project's other DA checker.
"""
from __future__ import annotations

import itertools
import json

STUDENTS = ("i", "j", "k")
SCHOOLS = ("A", "B", "C")
CAPACITY = {s: 1 for s in SCHOOLS}
PREFS = {
    "i": ("A", "B", "C", None),
    "j": ("B", "A", "C", None),
    "k": ("A", "B", "C", None),
}
PRIORITIES = {
    "A": ("j", "i", "k"),
    "B": ("i", "j", "k"),
    "C": ("i", "j", "k"),
}
TRUTH = {i: PREFS[i][:3] for i in STUDENTS}
TARGET = {"i": "B", "j": "A", "k": "C"}


def all_reports():
    return tuple(
        seq
        for length in range(len(SCHOOLS) + 1)
        for seq in itertools.permutations(SCHOOLS, length)
    )


REPORTS = all_reports()
PRIORITY_RANK = {
    s: {student: rank for rank, student in enumerate(PRIORITIES[s])}
    for s in SCHOOLS
}


def da_independent(reports):
    """Synchronous student-proposing DA by explicit proposal rounds."""
    next_index = {i: 0 for i in STUDENTS}
    held = {s: set() for s in SCHOOLS}
    while True:
        proposals = {s: set() for s in SCHOOLS}
        any_proposal = False
        for i in STUDENTS:
            if any(i in held[s] for s in SCHOOLS):
                continue
            if next_index[i] < len(reports[i]):
                s = reports[i][next_index[i]]
                next_index[i] += 1
                proposals[s].add(i)
                any_proposal = True
        if not any_proposal:
            break
        for s in SCHOOLS:
            pool = held[s] | proposals[s]
            held[s] = set(sorted(pool, key=PRIORITY_RANK[s].__getitem__)[:CAPACITY[s]])
    assignment = {i: None for i in STUDENTS}
    for s in SCHOOLS:
        for i in held[s]:
            assignment[i] = s
    return assignment


def stable_independent(mu):
    """Check one-to-one feasibility, individual rationality, and all blocks."""
    if any(mu[i] not in PREFS[i][:3] for i in STUDENTS):
        return False
    for s in SCHOOLS:
        if sum(mu[i] == s for i in STUDENTS) > 1:
            return False
    for i in STUDENTS:
        for s in PREFS[i][:3]:
            if PREFS[i].index(s) >= PREFS[i].index(mu[i]):
                continue
            incumbent = next((j for j in STUDENTS if mu[j] == s), None)
            if incumbent is None or PRIORITY_RANK[s][i] < PRIORITY_RANK[s][incumbent]:
                return False
    return True


def ergin_cycle_independent():
    """Directly check the unit-capacity 3-student Ergin cycle definition."""
    for s in SCHOOLS:
        for t in SCHOOLS:
            if s == t:
                continue
            for x, y, z in itertools.permutations(STUDENTS, 3):
                if (PRIORITY_RANK[s][x] < PRIORITY_RANK[s][y]
                        < PRIORITY_RANK[s][z]
                        and PRIORITY_RANK[t][z] < PRIORITY_RANK[t][x]):
                    return (s, t, x, y, z)
    return None


def utility_rank(i, school):
    return PREFS[i].index(school)


def main():
    baseline = da_independent(TRUTH)
    assert baseline == {"i": "A", "j": "B", "k": "C"}
    assert stable_independent(TARGET)
    assert ergin_cycle_independent() is None

    # Target-first reports for D={i,j}; k remains truthful.
    support_profile = {"i": ("B",), "j": ("A",), "k": TRUTH["k"]}
    assert da_independent(support_profile) == TARGET

    counts = {}
    supports_by_mask = {}
    checked_profiles = 0
    checked_deviations = 0
    for mask in range(1 << len(STUDENTS)):
        K = tuple(i for pos, i in enumerate(STUDENTS) if mask & (1 << pos))
        supports = []
        for choices in itertools.product(REPORTS, repeat=len(K)):
            profile = dict(TRUTH)
            for i, report in zip(K, choices):
                profile[i] = report
            outcome = da_independent(profile)
            checked_profiles += 1
            if outcome != TARGET:
                continue
            is_ne = True
            for i in K:
                for alt_report in REPORTS:
                    deviated = dict(profile)
                    deviated[i] = alt_report
                    alt_outcome = da_independent(deviated)
                    checked_deviations += 1
                    if utility_rank(i, alt_outcome[i]) < utility_rank(i, TARGET[i]):
                        is_ne = False
                        break
                if not is_ne:
                    break
            if is_ne:
                supports.append({"reports": {i: profile[i] for i in STUDENTS}, "outcome": outcome})
        supports_by_mask[mask] = supports
        counts[str(K)] = {
            "target_producing_profiles": sum(
                1 for choices in itertools.product(REPORTS, repeat=len(K))
                if da_independent({**TRUTH, **dict(zip(K, choices))}) == TARGET
            ),
            "target_NE_profiles": len(supports),
        }

    support_masks = [m for m, profiles in supports_by_mask.items() if profiles]
    minimal_masks = [
        m for m in support_masks
        if not any(other != m and (other & m) == other for other in support_masks)
    ]
    names = lambda mask: tuple(i for pos, i in enumerate(STUDENTS) if mask & (1 << pos))
    D = {i for i in STUDENTS if TARGET[i] != baseline[i]}
    L = {i for i in STUDENTS if any(
        PREFS[i].index(s) < PREFS[i].index(TARGET[i]) for s in SCHOOLS
    )}
    assert D == {"i", "j"}
    assert L == {"i", "j", "k"}
    assert [names(m) for m in minimal_masks] == [("i", "j")]
    assert supports_by_mask[0b011]

    result = {
        "status": "PASS_INDEPENDENT_EXACT_CHECK",
        "truthful_DA": baseline,
        "target": TARGET,
        "target_stable": stable_independent(TARGET),
        "unit_capacity_Ergin_cycle_witness": ergin_cycle_independent(),
        "all_16_ordered_reports_per_strategic_student": len(REPORTS),
        "report_profiles_checked_across_all_8_rosters": checked_profiles,
        "unilateral_deviations_checked_on_target_profiles": checked_deviations,
        "D": sorted(D),
        "L": sorted(L),
        "support_rosters": [names(m) for m in support_masks],
        "inclusion_minimal_rosters": [names(m) for m in minimal_masks],
        "support_profile_for_D": support_profile,
        "roster_by_roster_counts": counts,
        "note": "Exact only for this fixture; shows MinK(target)=D is strictly smaller than L(target).",
    }
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
