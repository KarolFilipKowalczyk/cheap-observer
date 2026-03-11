"""
Causal invariance measurement for string rewriting rules.

Tests whether the evolution graph is invariant under change of update
order. A rule is causally invariant at step n if k random orderings all
produce isomorphic causal graphs through n steps.

The canonical hash sorts nodes by (time, position), serializes the
labeled edge list, and computes SHA-256. For string rewriting, node
labeling by (position, time, symbol) makes this effectively a complete
invariant.

See definitions.md Section 7.
"""

from __future__ import annotations

import hashlib
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.spark.rule_classes.string_rewriting import StringRewritingRule


# ---------------------------------------------------------------------------
# Core: evolve with random match selection and hash the result
# ---------------------------------------------------------------------------

def _evolve_and_hash(
    rule: StringRewritingRule,
    seed: str,
    n_steps: int,
    rng: random.Random,
) -> tuple[str, int]:
    """Evolve under random match selection, return canonical hash.

    Builds the evolution graph (strings + causal edges) and serializes
    it into a canonical hash per definitions.md Section 7.

    Returns:
        (sha256_hex, actual_steps) where actual_steps <= n_steps.
    """
    len_L = len(rule.L)
    len_R = len(rule.R)
    delta = len_R - len_L

    hasher = hashlib.sha256()
    # Hash the seed (step 0 nodes)
    hasher.update(seed.encode())
    hasher.update(b"|")

    current = seed
    actual_steps = 0

    for _step in range(n_steps):
        occurrences = rule.find_occurrences(current)
        if not occurrences:
            break

        # Random match selection (definitions.md Section 7 step 1)
        match_pos = rng.choice(occurrences)

        # Build new string
        new_string = (
            current[:match_pos]
            + rule.R
            + current[match_pos + len_L:]
        )

        # Build and hash causal edges, sorted by (src, dst)
        # Definitions.md Section 3: matched positions -> all R positions,
        # unmatched positions -> shifted identity
        edges: list[tuple[int, int]] = []
        for i in range(len(current)):
            if match_pos <= i < match_pos + len_L:
                for j in range(match_pos, match_pos + len_R):
                    edges.append((i, j))
            elif i < match_pos:
                edges.append((i, i))
            else:
                edges.append((i, i + delta))

        # Serialize: string (node labels) then sorted edge list
        hasher.update(new_string.encode())
        hasher.update(b"|")
        for src, dst in edges:  # already in src order
            hasher.update(f"{src},{dst};".encode())
        hasher.update(b"#")

        current = new_string
        actual_steps += 1

    return hasher.hexdigest(), actual_steps


# ---------------------------------------------------------------------------
# Vacuous invariance check
# ---------------------------------------------------------------------------

def check_vacuous(
    rule: StringRewritingRule,
    seed: str,
    n_steps: int,
) -> bool:
    """Check if the rule always has exactly one match at each step.

    If true, there is no choice of update order — causal invariance is
    vacuously satisfied. T_rul = 0.

    Runs the canonical (leftmost) evolution and checks match count at
    each step.
    """
    current = seed
    for _ in range(n_steps):
        occurrences = rule.find_occurrences(current)
        if len(occurrences) == 0:
            # Evolution terminates — vacuously invariant up to here
            return True
        if len(occurrences) > 1:
            return False
        # Exactly one match — apply it
        pos = occurrences[0]
        current = (
            current[:pos]
            + rule.R
            + current[pos + len(rule.L):]
        )
    return True


# ---------------------------------------------------------------------------
# Causal invariance test at a given step count
# ---------------------------------------------------------------------------

def test_invariance_at_n(
    rule: StringRewritingRule,
    seed: str,
    n_steps: int,
    k: int = 50,
) -> bool:
    """Test causal invariance at evolution length n with k random orderings.

    See definitions.md Section 7: "The rule exhibits ruliad-like coherence
    at length n if all sampled pairs are isomorphic."

    Uses early exit: as soon as two hashes disagree, returns False.

    Args:
        rule: The rewriting rule.
        seed: The minimal seed.
        n_steps: Evolution length to test.
        k: Number of random orderings to sample. Default 50.

    Returns:
        True if all k orderings produce the same canonical hash.
    """
    reference_hash: str | None = None

    for trial in range(k):
        rng = random.Random(trial * 7919 + 42)
        h, _actual = _evolve_and_hash(rule, seed, n_steps, rng)

        if reference_hash is None:
            reference_hash = h
        elif h != reference_hash:
            return False

    return True


# ---------------------------------------------------------------------------
# T_rul finder
# ---------------------------------------------------------------------------

# Step counts to probe. Sparse at first, denser for precision.
_PROBE_POINTS = [5, 10, 20, 50, 100, 200, 500, 1000]


def find_t_rul(
    rule: StringRewritingRule,
    seed: str,
    max_steps: int = 1000,
    k: int = 50,
) -> tuple[int | None, bool]:
    """Find T_rul: earliest step count n where rule is causally invariant.

    First checks for vacuous invariance (always unique match). If not
    vacuous, probes at increasing step counts and binary-searches for
    the exact earliest invariant length.

    See definitions.md Section 8: "T_rul(r) is the earliest evolution
    length n such that r exhibits ruliad-like coherence at length n."

    Args:
        rule: The rewriting rule.
        seed: The minimal seed.
        max_steps: Maximum evolution length to test.
        k: Number of random orderings per test.

    Returns:
        (t_rul, vacuous) where:
        - t_rul is the earliest invariant step count, or None if infinity.
        - vacuous is True if the rule always has a unique match (T_rul = 0).
    """
    # 1. Check vacuous invariance
    check_len = min(max_steps, 200)
    if check_vacuous(rule, seed, check_len):
        return 0, True

    # 2. Probe at increasing step counts
    probes = [n for n in _PROBE_POINTS if n <= max_steps]
    if not probes or probes[-1] < max_steps:
        probes.append(max_steps)

    first_pass: int | None = None
    for n in probes:
        if test_invariance_at_n(rule, seed, n, k):
            first_pass = n
            break

    if first_pass is None:
        return None, False  # T_rul = infinity

    # 3. Binary search for exact earliest invariant length
    # We know it fails before some lower bound and passes at first_pass
    idx = probes.index(first_pass)
    lo = probes[idx - 1] + 1 if idx > 0 else 1
    hi = first_pass

    while lo < hi:
        mid = (lo + hi) // 2
        if test_invariance_at_n(rule, seed, mid, k):
            hi = mid
        else:
            lo = mid + 1

    return lo, False
