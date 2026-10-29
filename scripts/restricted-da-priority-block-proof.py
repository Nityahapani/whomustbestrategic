"""Independent checks for the unit-capacity Ergin-priority block proof of H.

This is a finite verification aid, not a proof. It implements DA independently
from restricted-da-hybrid-enumeration.py (round-based proposals rather than its
queue routine), derives the ordered singleton/pair blocks from Ergin acyclicity,
checks blockwise/global DA equivalence, and exactly enumerates a 4x4 market with
two independent stable pair swaps for every K of size two.

Run:
  python research/restricted-da-priority-block-proof.py
"""

from __future__ import annotations

import itertools
import random
import time
from collections import Counter


def ergincycle(priorities, students, schools):
    """Return True iff an Ergin cycle exists (unit capacities)."""
    for a in schools:
        ra = {i: priorities[a].index(i) for i in students}
        for b in schools:
            if a == b:
                continue
            rb = {i: priorities[b].index(i) for i in students}
            for i, j, k in itertools.permutations(students, 3):
                if ra[i] < ra[j] < ra[k] and rb[k] < rb[i]:
                    return True
    return False


def priority_blocks(priorities, students, schools):
    """Recover common ordered blocks of size at most two, or raise ValueError.

    In a reference-school order, Ergin acyclicity forbids every inversion between
    nonadjacent ranks. Inversions in one school cannot overlap, and inversion edges
    from different schools cannot overlap. The union therefore partitions the
    reference order into singleton/pair blocks.
    """
    if not schools:
        return tuple((i,) for i in students)
    reference = tuple(priorities[schools[0]])
    if set(reference) != set(students):
        raise ValueError("priority order must contain each student exactly once")
    pos = {student: k for k, student in enumerate(reference)}
    union_edges = set()

    for school in schools:
        order = tuple(priorities[school])
        if set(order) != set(students):
            raise ValueError("priority order must contain each student exactly once")
        rank = {student: k for k, student in enumerate(order)}
        edges = set()
        for p in range(len(reference)):
            for r in range(p + 1, len(reference)):
                if rank[reference[r]] < rank[reference[p]]:
                    if r != p + 1:
                        raise ValueError("nonadjacent inversion; Ergin cycle")
                    edges.add((p, r))
        endpoints = [x for edge in edges for x in edge]
        if len(endpoints) != len(set(endpoints)):
            raise ValueError("overlapping adjacent inversions; Ergin cycle")
        union_edges.update(edges)

    endpoints = [x for edge in union_edges for x in edge]
    if len(endpoints) != len(set(endpoints)):
        raise ValueError("inversions overlap across schools; Ergin cycle")

    blocks = []
    p = 0
    while p < len(reference):
        if p + 1 < len(reference) and (p, p + 1) in union_edges:
            blocks.append((reference[p], reference[p + 1]))
            p += 2
        else:
            blocks.append((reference[p],))
            p += 1

    block_index = {student: b for b, block in enumerate(blocks) for student in block}
    for school in schools:
        rank = {student: k for k, student in enumerate(priorities[school])}
        for a in range(len(blocks)):
            for b in range(a + 1, len(blocks)):
                if any(rank[i] > rank[j] for i in blocks[a] for j in blocks[b]):
                    raise ValueError("priority rankings do not respect the common block order")
    return tuple(blocks)


def da_rounds(reports, schools, priorities):
    """Round-based student-proposing DA; reports are strict lists with None cutoff."""
    students = tuple(range(len(reports)))
    rank = {s: {i: priorities[s].index(i) for i in students} for s in schools}
    acceptable = []
    for report in reports:
        choices = []
        for x in report:
            if x is None:
                break
            if x in schools:
                choices.append(x)
        acceptable.append(tuple(choices))

    next_index = [0] * len(students)
    held = {s: set() for s in schools}
    rejected = set()
    while True:
        proposals = {s: set() for s in schools}
        made_proposal = False
        for i in students:
            currently_held = any(i in held[s] for s in schools)
            if currently_held or next_index[i] >= len(acceptable[i]):
                continue
            s = acceptable[i][next_index[i]]
            next_index[i] += 1
            proposals[s].add(i)
            made_proposal = True

        if not made_proposal:
            break

        for s in schools:
            pool = held[s] | proposals[s]
            if pool:
                winner = min(pool, key=lambda i: rank[s][i])
                held[s] = {winner}
                rejected.update(pool - {winner})

        # Rejected applicants are free in the next round. The loop naturally
        # advances them to their next acceptable option.

    assignment = [None] * len(students)
    for s in schools:
        for i in held[s]:
            assignment[i] = s
    return tuple(assignment)


def da_blockwise(reports, schools, priorities, blocks):
    """Sequentially clear ordered priority blocks; remove already-held schools."""
    n = len(reports)
    assignment = [None] * n
    remaining = set(schools)
    for block in blocks:
        local_students = tuple(block)
        local_schools = tuple(s for s in schools if s in remaining)
        local_reports = []
        for i in local_students:
            prefix = []
            for x in reports[i]:
                if x is None:
                    break
                if x in remaining:
                    prefix.append(x)
            local_reports.append(tuple(prefix) + (None,))
        local_position = {student: pos for pos, student in enumerate(local_students)}
        local_priorities = {
            s: tuple(local_position[i] for i in priorities[s] if i in local_position)
            for s in local_schools
        }
        local_assignment = da_rounds(local_reports, local_schools, local_priorities)
        for pos, i in enumerate(local_students):
            assignment[i] = local_assignment[pos]
            if local_assignment[pos] is not None:
                remaining.remove(local_assignment[pos])
    return tuple(assignment)


def stable(assignment, true_preferences, schools, priorities):
    if len([s for s in assignment if s is not None]) != len(set(s for s in assignment if s is not None)):
        return False
    rank = {s: {i: priorities[s].index(i) for i in range(len(assignment))} for s in schools}
    for i, pref in enumerate(true_preferences):
        if assignment[i] is not None and pref.index(assignment[i]) > pref.index(None):
            return False
        for s in schools:
            if pref.index(s) >= pref.index(assignment[i]):
                continue
            incumbent = next((j for j, x in enumerate(assignment) if x == s), None)
            if incumbent is None or rank[s][i] < rank[s][incumbent]:
                return False
    return True


def canonical_reports(schools):
    out = []
    for length in range(len(schools) + 1):
        for prefix in itertools.permutations(schools, length):
            out.append(prefix + (None,) + tuple(s for s in schools if s not in prefix))
    return tuple(out)


def exact_two_pair_fixture():
    students = (0, 1, 2, 3)
    schools = ("a", "b", "c", "d")
    priorities = {
        "a": (0, 1, 2, 3),
        "b": (1, 0, 2, 3),
        "c": (0, 1, 3, 2),
        "d": (1, 0, 3, 2),
    }
    blocks = priority_blocks(priorities, students, schools)
    assert blocks == ((0, 1), (2, 3)), blocks
    assert not ergincycle(priorities, students, schools)
    true_preferences = (
        ("b", "c", "a", "d", None),
        ("c", "b", None, "a", "d"),
        ("d", "b", "c", "a", None),
        ("a", "b", "d", None, "c"),
    )
    baseline = da_rounds(true_preferences, schools, priorities)
    all_assignments = tuple(itertools.product(schools + (None,), repeat=len(students)))
    stable_set = {
        x for x in all_assignments if stable(x, true_preferences, schools, priorities)
    }
    assert len(stable_set) == 4, stable_set
    expected_blocks = {
        x for x in stable_set
        if x[0] in (baseline[0], baseline[1])
    }
    assert expected_blocks == stable_set

    reports = canonical_reports(schools)
    total_profiles = 0
    started = time.time()
    for K in itertools.combinations(students, 2):
        expected = {
            x for x in stable_set
            if all(x[i] == baseline[i] for i in students if i not in K)
        }
        outcomes = {}
        for r_i in reports:
            for r_j in reports:
                p = list(true_preferences)
                p[K[0]], p[K[1]] = r_i, r_j
                outcomes[(r_i, r_j)] = da_rounds(tuple(p), schools, priorities)
        ne = set()
        for r_i in reports:
            for r_j in reports:
                outcome = outcomes[(r_i, r_j)]
                best = True
                for pos, i in enumerate(K):
                    current_rank = true_preferences[i].index(outcome[i])
                    for deviation in reports:
                        alternative = outcomes[(deviation, r_j)] if pos == 0 else outcomes[(r_i, deviation)]
                        if true_preferences[i].index(alternative[i]) < current_rank:
                            best = False
                            break
                    if not best:
                        break
                if best:
                    ne.add(outcome)
        total_profiles += len(reports) ** 2
        if ne != expected:
            raise AssertionError((K, expected, ne))
        print(f"PASS exact 4x4 K={K}: expected={len(expected)}, NE={len(ne)}")

    print("fixture priorities:", priorities)
    print("priority blocks:", blocks)
    print("truthful DA:", baseline)
    print("true stable matchings:", stable_set)
    print("all K size 2 exactly enumerated profiles:", f"{total_profiles:,}")
    print("exact-enumeration seconds:", f"{time.time()-started:.2f}")


def random_blockwise_crosscheck(seed=20261026, trials=2000):
    rng = random.Random(seed)
    total_reports = 0
    for trial in range(trials):
        n = rng.randint(3, 8)
        m = rng.randint(2, 5)
        students = tuple(range(n))
        schools = tuple(range(m))
        base = list(students)
        rng.shuffle(base)
        # Choose disjoint blocks in the reference order.
        blocks = []
        p = 0
        while p < n:
            if p + 1 < n and rng.random() < 0.38:
                blocks.append((base[p], base[p + 1]))
                p += 2
            else:
                blocks.append((base[p],))
                p += 1
        priorities = {}
        for s in schools:
            order = []
            for block in blocks:
                if len(block) == 2 and rng.random() < 0.5:
                    order.extend(reversed(block))
                else:
                    order.extend(block)
            priorities[s] = tuple(order)
        assert not ergincycle(priorities, students, schools)
        derived = priority_blocks(priorities, students, schools)
        reports = []
        for _ in students:
            order = list(schools + (None,))
            rng.shuffle(order)
            reports.append(tuple(order))
        reports = tuple(reports)
        global_outcome = da_rounds(reports, schools, priorities)
        block_outcome = da_blockwise(reports, schools, priorities, derived)
        if global_outcome != block_outcome:
            raise AssertionError((priorities, reports, global_outcome, block_outcome))
        total_reports += 1
    print(f"PASS blockwise/global DA cross-check: {trials:,} random profiles; seed={seed}")


def exhaustive_small_priority_classification():
    """Check the block characterization against direct Ergin-cycle tests."""
    students = tuple(range(4))
    schools = (0, 1, 2)
    orders = tuple(itertools.permutations(students))
    count_acyclic = 0
    for profile in itertools.product(orders, repeat=len(schools)):
        priorities = dict(zip(schools, profile))
        acyclic = not ergincycle(priorities, students, schools)
        try:
            priority_blocks(priorities, students, schools)
            blockable = True
        except ValueError:
            blockable = False
        if acyclic != blockable:
            raise AssertionError((priorities, acyclic, blockable))
        count_acyclic += acyclic
    assert count_acyclic == 456, count_acyclic
    print("PASS exhaustive priority classification: n=4, m=3; acyclic triples=456")


def cross_block_stability_caveat():
    """Show that stable pair-block choices need not form an independent product."""
    students = (0, 1, 2)  # i, j, k
    schools = ("a", "b", "c")
    priorities = {
        "a": (1, 0, 2),
        "b": (0, 1, 2),
        "c": (0, 1, 2),
    }
    blocks = priority_blocks(priorities, students, schools)
    assert blocks == ((1, 0), (2,)), blocks
    assert not ergincycle(priorities, students, schools)
    prefs = (
        ("a", "c", "b", None),
        ("b", "a", "c", None),
        ("c", "a", "b", None),
    )
    baseline = da_rounds(prefs, schools, priorities)
    assert baseline == ("a", "b", "c"), baseline

    # The swap is stable inside the two-school residual submarket.
    local_stable = stable(
        ("b", "a"),
        (("a", "b", None), ("b", "a", None)),
        ("a", "b"),
        {"a": (1, 0), "b": (0, 1)},
    )
    assert local_stable
    # But i prefers c to b and outranks k at c, so the same swap is globally blocked.
    assert not stable(("b", "a", "c"), prefs, schools, priorities)
    stable_set = {
        x for x in itertools.product(schools + (None,), repeat=len(students))
        if stable(x, prefs, schools, priorities)
    }
    assert stable_set == {baseline}, stable_set
    print("PASS cross-block stability caveat: pair-local swap stable, globally blocked")


def main():
    exhaustive_small_priority_classification()
    random_blockwise_crosscheck()
    cross_block_stability_caveat()
    exact_two_pair_fixture()


if __name__ == "__main__":
    main()
