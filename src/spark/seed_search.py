"""
Minimal seed finder.

Given a rule, find the shortest seed that produces non-trivial evolution:
the string neither vanishes nor reaches a fixed point within the first
100 steps. Max seed length is 2 * description_length. Returns None if
the rule is sterile.

See definitions.md Section 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.spark.rule_classes.string_rewriting import StringRewritingRule

DEFAULT_BOOTSTRAP_STEPS = 100


def is_non_trivial(rule: StringRewritingRule, seed: str, steps: int = DEFAULT_BOOTSTRAP_STEPS) -> bool:
    """Test whether a spark (rule, seed) produces non-trivial evolution.

    Non-trivial means the string neither vanishes (becomes empty) nor
    reaches a fixed point (stops changing) within the given number of
    steps.

    See definitions.md Section 2: "the shortest seed string such that
    applying r to s_0* produces a non-trivial evolution — meaning the
    string neither vanishes nor reaches a fixed point within the first
    100 steps."

    Args:
        rule: The rewriting rule.
        seed: The seed string.
        steps: Number of steps to test. Default 100 per definitions.md.

    Returns:
        True if the evolution is still changing after the given steps.
    """
    current = seed
    for _ in range(steps):
        next_str = rule.apply(current)
        if not next_str or next_str == current:
            return False
        current = next_str
    return True


def find_minimal_seed(
    rule: StringRewritingRule,
    max_seed_length: int | None = None,
    steps: int = DEFAULT_BOOTSTRAP_STEPS,
) -> str | None:
    """Find the minimal spark for a rule.

    Enumerates binary seeds of increasing length and returns the shortest
    one producing non-trivial evolution. Returns None if no such seed
    exists up to the maximum length (the rule is sterile).

    See definitions.md Section 2: "we search for s_0* by enumerating seeds
    of increasing length. A spark that produces no non-trivial evolution
    for any seed up to length l_max is classified as sterile. Default:
    l_max = 2l (twice the rule description length)."

    Args:
        rule: The rewriting rule.
        max_seed_length: Maximum seed length to try. Defaults to
            2 * rule.description_length.
        steps: Number of evolution steps to test per seed.

    Returns:
        The shortest seed producing non-trivial evolution, or None if
        the rule is sterile.
    """
    if max_seed_length is None:
        max_seed_length = 2 * rule.description_length

    for length in range(1, max_seed_length + 1):
        for seed_int in range(2**length):
            seed = format(seed_int, f"0{length}b")
            if is_non_trivial(rule, seed, steps):
                return seed

    return None
