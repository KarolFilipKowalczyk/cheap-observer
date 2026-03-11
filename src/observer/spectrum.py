"""
Proto-observer spectrum classification.

Classifies structures by how many of the four observer criteria they
satisfy:
    4/4 = observer
    3/4 = proto-observer (reports which criterion failed)
    2/4 or less = not an observer

This feeds experiments/counterexamples/false_positives.py — structures
that pass 3 of 4 criteria test whether each criterion is doing real
work.

See definitions.md Section 5.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.observer.definition import ObserverCriteria, DEFAULT_CRITERIA
from src.observer.boundary_stability import boundary_stability_score
from src.observer.internal_entropy import internal_entropy_score
from src.observer.causal_decoupling import causal_decoupling_score
from src.observer.self_reference import self_reference_score

if TYPE_CHECKING:
    from src.spark.evolution_graph import SubgraphView


CRITERION_NAMES = [
    "boundary_stability",
    "internal_entropy",
    "causal_decoupling",
    "self_reference",
]


@dataclass
class SpectrumResult:
    """Full classification of a subgraph against the four criteria."""

    boundary_score: float
    entropy_score: float
    decoupling_score: float
    self_ref_score: float

    boundary_pass: bool
    entropy_pass: bool
    decoupling_pass: bool
    self_ref_pass: bool

    @property
    def n_passed(self) -> int:
        return (
            self.boundary_pass
            + self.entropy_pass
            + self.decoupling_pass
            + self.self_ref_pass
        )

    @property
    def is_observer(self) -> bool:
        return self.n_passed == 4

    @property
    def is_proto_observer(self) -> bool:
        return self.n_passed == 3

    @property
    def classification(self) -> str:
        if self.n_passed == 4:
            return "observer"
        elif self.n_passed == 3:
            return f"proto-observer (failed: {self.failed_criteria[0]})"
        else:
            return f"not observer ({self.n_passed}/4)"

    @property
    def failed_criteria(self) -> list[str]:
        failed = []
        if not self.boundary_pass:
            failed.append("boundary_stability")
        if not self.entropy_pass:
            failed.append("internal_entropy")
        if not self.decoupling_pass:
            failed.append("causal_decoupling")
        if not self.self_ref_pass:
            failed.append("self_reference")
        return failed

    @property
    def passed_criteria(self) -> list[str]:
        passed = []
        if self.boundary_pass:
            passed.append("boundary_stability")
        if self.entropy_pass:
            passed.append("internal_entropy")
        if self.decoupling_pass:
            passed.append("causal_decoupling")
        if self.self_ref_pass:
            passed.append("self_reference")
        return passed

    def summary(self) -> str:
        lines = [
            f"  Classification: {self.classification}",
            f"  Criteria passed: {self.n_passed}/4",
            f"    boundary_stability: {self.boundary_score:.4f}"
            f"  {'PASS' if self.boundary_pass else 'FAIL'}",
            f"    internal_entropy:   {self.entropy_score:.4f} bits"
            f"  {'PASS' if self.entropy_pass else 'FAIL'}",
            f"    causal_decoupling:  {self.decoupling_score:.4f}"
            f"  {'PASS' if self.decoupling_pass else 'FAIL'}",
            f"    self_reference:     {self.self_ref_score:.1f}"
            f"  {'PASS' if self.self_ref_pass else 'FAIL'}",
        ]
        return "\n".join(lines)


def classify_subgraph(
    subgraph: SubgraphView,
    t_start: int,
    t_end: int,
    tau: int,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
) -> SpectrumResult:
    """Classify a subgraph against all four observer criteria.

    Computes all four scores and reports which pass and which fail.
    Unlike is_observer, this always computes all four scores regardless
    of early failures.

    Args:
        subgraph: The candidate subgraph.
        t_start: Window start (inclusive).
        t_end: Window end (inclusive).
        tau: Characteristic time.
        criteria: Observer thresholds.

    Returns:
        SpectrumResult with all scores and pass/fail status.
    """
    b = boundary_stability_score(subgraph, t_start, t_end)
    h = internal_entropy_score(subgraph, t_start, t_end, tau)

    # Skip expensive MI if entropy is zero (constant state)
    if h < 0.01:
        d = 0.5
    else:
        d = causal_decoupling_score(subgraph, t_start, t_end, tau)

    s = self_reference_score(subgraph, t_start, t_end)

    return SpectrumResult(
        boundary_score=b,
        entropy_score=h,
        decoupling_score=d,
        self_ref_score=s,
        boundary_pass=b < criteria.epsilon_B,
        entropy_pass=h > criteria.epsilon_H,
        decoupling_pass=d > criteria.epsilon_D,
        self_ref_pass=s >= 1.0,
    )


def spectrum_summary(results: list[SpectrumResult]) -> str:
    """Summarize a collection of spectrum results.

    Reports how many structures fall into each classification bucket
    and which criteria are most commonly failed.
    """
    if not results:
        return "  No candidates scored."

    n_total = len(results)
    n_observer = sum(1 for r in results if r.is_observer)
    n_proto = sum(1 for r in results if r.is_proto_observer)
    n_other = n_total - n_observer - n_proto

    # Count how often each criterion fails
    fail_counts = {name: 0 for name in CRITERION_NAMES}
    for r in results:
        for name in r.failed_criteria:
            fail_counts[name] += 1

    lines = [
        f"  Spectrum summary ({n_total} candidates):",
        f"    observers (4/4):       {n_observer}",
        f"    proto-observers (3/4): {n_proto}",
        f"    other (<=2/4):         {n_other}",
        f"  Failure rates:",
    ]
    for name in CRITERION_NAMES:
        pct = 100 * fail_counts[name] / n_total if n_total > 0 else 0
        lines.append(f"    {name}: {fail_counts[name]}/{n_total} ({pct:.0f}%)")

    # Best near-miss
    best = max(results, key=lambda r: r.n_passed)
    if not best.is_observer:
        lines.append(f"  Best near-miss: {best.classification}")
        lines.append(best.summary())

    return "\n".join(lines)
