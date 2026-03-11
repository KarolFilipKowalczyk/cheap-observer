"""
Rule enumeration and minimal spark search.

Takes a rule class and iterates through all rules. For each rule, calls
seed_search to find the minimal spark. Outputs (rule, seed, is_sterile)
tuples.

See definitions.md Sections 1 and 2.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Iterator

from src.spark.rule_classes.string_rewriting import StringRewritingRule
from src.spark.seed_search import find_minimal_seed


@dataclass
class SparkResult:
    """Result of searching for the minimal spark of a rule."""

    rule: StringRewritingRule
    seed: str | None
    is_sterile: bool

    @property
    def description_length(self) -> int:
        return self.rule.description_length


def enumerate_sparks(
    max_description_length: int,
    max_seed_length: int | None = None,
    bootstrap_steps: int = 100,
) -> Iterator[SparkResult]:
    """Enumerate all rules in C(l) and find their minimal sparks.

    Args:
        max_description_length: The bound l on |L| + |R|.
        max_seed_length: Override for maximum seed length per rule.
            Defaults to 2 * description_length per rule.
        bootstrap_steps: Steps to test non-triviality. Default 100.

    Yields:
        SparkResult for each rule in the class.
    """
    for rule in StringRewritingRule.enumerate(max_description_length):
        seed = find_minimal_seed(
            rule,
            max_seed_length=max_seed_length,
            steps=bootstrap_steps,
        )
        yield SparkResult(
            rule=rule,
            seed=seed,
            is_sterile=seed is None,
        )


def print_summary(results: list[SparkResult], max_description_length: int) -> None:
    """Print a summary table of enumeration results."""
    total = len(results)
    active = [r for r in results if not r.is_sterile]
    sterile = [r for r in results if r.is_sterile]

    print(f"\n{'=' * 60}")
    print(f"  C({max_description_length}) Spark Enumeration Summary")
    print(f"{'=' * 60}")
    print(f"  Total rules:   {total}")
    print(f"  Active:        {len(active)}  ({100 * len(active) / total:.1f}%)")
    print(f"  Sterile:       {len(sterile)}  ({100 * len(sterile) / total:.1f}%)")

    # Breakdown by description length
    lengths = sorted(set(r.description_length for r in results))
    print(f"\n  {'|L|+|R|':>7}  {'total':>5}  {'active':>6}  {'sterile':>7}")
    print(f"  {'-' * 33}")
    for dl in lengths:
        at_dl = [r for r in results if r.description_length == dl]
        act = sum(1 for r in at_dl if not r.is_sterile)
        ste = sum(1 for r in at_dl if r.is_sterile)
        print(f"  {dl:>7}  {len(at_dl):>5}  {act:>6}  {ste:>7}")

    # Active rules detail
    print(f"\n  Active rules:")
    print(f"  {'rule':>12}  {'seed':>10}  {'|seed|':>6}")
    print(f"  {'-' * 33}")
    for r in active:
        print(f"  {str(r.rule):>12}  {r.seed:>10}  {len(r.seed):>6}")

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    l = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    print(f"Enumerating C({l}) — all string rewriting rules with |L| + |R| <= {l}")
    print(f"Finding minimal sparks (100-step non-triviality test)...")

    t0 = time.time()
    results = list(enumerate_sparks(l))
    elapsed = time.time() - t0

    print_summary(results, l)
    print(f"  Completed in {elapsed:.2f}s")
