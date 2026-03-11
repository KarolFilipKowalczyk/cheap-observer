"""
Observer detection: scanning evolution graphs for observer subgraphs.

Generates candidate connected subgraphs and tests them against all four
criteria in strict conjunction over a contiguous persistence window.
Returns observers sorted by earliest appearance time. The first one's
timestep is T_obs.

See definitions.md Sections 5.5 and 6.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.observer.definition import ObserverCriteria, DEFAULT_CRITERIA
from src.observer.boundary_stability import boundary_stability_score
from src.observer.internal_entropy import internal_entropy_score
from src.observer.causal_decoupling import causal_decoupling_score
from src.observer.self_reference import self_reference_score

if TYPE_CHECKING:
    from src.spark.evolution_graph import StringEvolutionGraph, SubgraphView


# ---------------------------------------------------------------------------
# Scored result for a candidate
# ---------------------------------------------------------------------------

@dataclass
class ScoredCandidate:
    """A candidate subgraph with its four criterion scores."""

    subgraph: SubgraphView
    t_window_start: int
    t_window_end: int
    boundary: float
    entropy: float
    decoupling: float
    self_ref: float

    def passes(self, criteria: ObserverCriteria) -> bool:
        return (
            self.boundary < criteria.epsilon_B
            and self.entropy > criteria.epsilon_H
            and self.decoupling > criteria.epsilon_D
            and self.self_ref >= 1.0
        )

    def n_criteria_passed(self, criteria: ObserverCriteria) -> int:
        return (
            (self.boundary < criteria.epsilon_B)
            + (self.entropy > criteria.epsilon_H)
            + (self.decoupling > criteria.epsilon_D)
            + (self.self_ref >= 1.0)
        )

    def criteria_report(self, criteria: ObserverCriteria) -> dict[str, tuple[float, bool]]:
        return {
            "boundary_stability": (self.boundary, self.boundary < criteria.epsilon_B),
            "internal_entropy": (self.entropy, self.entropy > criteria.epsilon_H),
            "causal_decoupling": (self.decoupling, self.decoupling > criteria.epsilon_D),
            "self_reference": (self.self_ref, self.self_ref >= 1.0),
        }


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

def _generate_fixed_candidates(
    graph: StringEvolutionGraph,
    tau: int,
    min_window: int,
    widths: list[int] | None = None,
    time_stride: int = 1,
) -> list[tuple[SubgraphView, int, int]]:
    """Generate fixed rectangular subgraph candidates.

    For each time window start, for each candidate width, center a
    subgraph on the match position at that timestep. This ensures
    candidates include the active rewrite site.

    Returns:
        List of (subgraph, t_start, t_end) tuples.
    """
    max_t = graph.n_steps_evolved

    if widths is None:
        # Try widths from small to moderate
        max_width = min(30, max(5, graph.string_length_at_time(max_t // 2) // 4))
        widths = [w for w in [3, 5, 8, 12, 18, 25] if w <= max_width]

    candidates = []

    for t_start in range(0, max_t - min_window + 1, time_stride):
        t_end = t_start + min_window

        # Find the match position at t_start to center candidates
        match_pos = graph.match_position_at_time(t_start)
        if match_pos < 0:
            continue

        for width in widths:
            half = width // 2
            pos_start = max(0, match_pos - half)
            pos_end = pos_start + width

            sg = graph.get_subgraph(
                pos_start=pos_start,
                pos_end=pos_end,
                time_start=t_start,
                time_end=t_end,
            )
            candidates.append((sg, t_start, t_end))

    return candidates


def _generate_tracking_candidates(
    graph: StringEvolutionGraph,
    tau: int,
    min_window: int,
    widths: list[int] | None = None,
    time_stride: int = 1,
) -> list[tuple[SubgraphView, int, int]]:
    """Generate match-tracking subgraph candidates.

    Builds subgraphs whose spatial extent follows the match position at
    each timestep. This captures the active dynamics even when the match
    site moves.

    Returns:
        List of (subgraph, t_start, t_end) tuples.
    """
    max_t = graph.n_steps_evolved

    if widths is None:
        max_width = min(20, max(5, graph.string_length_at_time(max_t // 2) // 4))
        widths = [w for w in [3, 5, 8, 12] if w <= max_width]

    candidates = []

    for t_start in range(0, max_t - min_window + 1, time_stride):
        t_end = t_start + min_window

        for width in widths:
            half = width // 2
            pbt: dict[int, set[int]] = {}
            valid = True

            for t in range(t_start, t_end + 1):
                match_pos = graph.match_position_at_time(t)
                if match_pos < 0:
                    # No match at this step — use last known position
                    if t > t_start and t - 1 in pbt:
                        pbt[t] = pbt[t - 1].copy()
                    else:
                        valid = False
                        break
                    continue

                ps = max(0, match_pos - half)
                pe = min(graph.string_length_at_time(t), ps + width)
                if pe > ps:
                    pbt[t] = set(range(ps, pe))

            if valid and pbt:
                sg = graph.get_subgraph(positions_by_time=pbt)
                candidates.append((sg, t_start, t_end))

    return candidates


# ---------------------------------------------------------------------------
# Scoring with early pruning
# ---------------------------------------------------------------------------

def _score_candidate(
    sg: SubgraphView,
    t_start: int,
    t_end: int,
    tau: int,
    criteria: ObserverCriteria,
) -> ScoredCandidate | None:
    """Score a candidate, pruning early if any criterion fails.

    Evaluates criteria in order of increasing cost:
    1. Boundary stability (cheap: set operations)
    2. Internal entropy (moderate: string collection + counter)
    3. Self-reference (moderate: BFS)
    4. Causal decoupling (expensive: MI or NCD computation)

    Returns None if boundary stability already clearly fails (score > 2x
    threshold), allowing fast skip of hopeless candidates. Otherwise
    returns full scores for spectrum analysis even if the candidate fails.
    """
    # 1. Boundary stability (cheapest)
    b_score = boundary_stability_score(sg, t_start, t_end)
    # Hard prune: if boundary is wildly unstable, skip entirely
    if b_score > criteria.epsilon_B * 3:
        return None

    # 2. Internal entropy
    h_score = internal_entropy_score(sg, t_start, t_end, tau)

    # 3. Self-reference (before decoupling — cheaper than MI)
    s_score = self_reference_score(sg, t_start, t_end)

    # 4. Causal decoupling (most expensive)
    # Skip if entropy is zero — constant state means MI will be degenerate
    if h_score < 0.01:
        d_score = 0.5  # No variation, default to uninformative
    else:
        d_score = causal_decoupling_score(sg, t_start, t_end, tau)

    return ScoredCandidate(
        subgraph=sg,
        t_window_start=t_start,
        t_window_end=t_end,
        boundary=b_score,
        entropy=h_score,
        decoupling=d_score,
        self_ref=s_score,
    )


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------

def detect_observers(
    graph: StringEvolutionGraph,
    tau: int,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
    verbose: bool = False,
) -> list[ScoredCandidate]:
    """Find all observers in an evolution graph.

    Generates candidate subgraphs using two strategies:
    1. Fixed rectangular regions centered on match positions
    2. Match-tracking regions that follow the rewrite site

    Tests each against all four criteria in strict conjunction.
    Returns observers sorted by earliest appearance time.

    See definitions.md Section 6: "T_obs(r) is the earliest time step t
    such that the evolution graph contains an observer whose persistence
    window begins at or before t."

    Args:
        graph: The evolved StringEvolutionGraph.
        tau: Characteristic time.
        criteria: Observer criteria thresholds.
        verbose: Print progress information.

    Returns:
        List of ScoredCandidate objects that pass all four criteria,
        sorted by t_window_start.
    """
    min_window = criteria.persistence_multiplier * tau
    max_t = graph.n_steps_evolved

    if max_t < min_window:
        if verbose:
            print(f"  Evolution too short ({max_t} steps) for "
                  f"minimum window ({min_window} steps)")
        return []

    # Adaptive stride: for long evolutions, don't check every timestep
    time_stride = max(1, min_window // 4)

    if verbose:
        print(f"  Generating candidates: min_window={min_window}, "
              f"stride={time_stride}, max_t={max_t}")

    # Generate candidates from both strategies
    candidates = []
    candidates.extend(
        _generate_fixed_candidates(graph, tau, min_window, time_stride=time_stride)
    )
    candidates.extend(
        _generate_tracking_candidates(graph, tau, min_window, time_stride=time_stride)
    )

    if verbose:
        print(f"  Testing {len(candidates)} candidates...")

    # Score all candidates, collecting observers
    observers: list[ScoredCandidate] = []
    seen_windows: set[tuple[int, int, int, int]] = set()  # dedup

    for sg, t_start, t_end in candidates:
        # Dedup by (pos_range, time_range)
        ts = sg.time_span
        positions = sg.position_set_at_time(t_start)
        if not positions:
            continue
        key = (min(positions), max(positions), t_start, t_end)
        if key in seen_windows:
            continue
        seen_windows.add(key)

        scored = _score_candidate(sg, t_start, t_end, tau, criteria)
        if scored is None:
            continue

        if scored.passes(criteria):
            observers.append(scored)
            if verbose:
                print(f"  OBSERVER FOUND at t={t_start}, "
                      f"positions [{min(positions)}, {max(positions)}]")

    # Sort by earliest window start
    observers.sort(key=lambda o: o.t_window_start)
    return observers


def scan_all_candidates(
    graph: StringEvolutionGraph,
    tau: int,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
    verbose: bool = False,
) -> list[ScoredCandidate]:
    """Score ALL candidates (not just observers) for spectrum analysis.

    Returns all scored candidates sorted by number of criteria passed
    (descending), then by earliest time. Useful for finding near-misses
    and proto-observers.
    """
    min_window = criteria.persistence_multiplier * tau
    max_t = graph.n_steps_evolved

    if max_t < min_window:
        return []

    time_stride = max(1, min_window // 4)

    candidates = []
    candidates.extend(
        _generate_fixed_candidates(graph, tau, min_window, time_stride=time_stride)
    )
    candidates.extend(
        _generate_tracking_candidates(graph, tau, min_window, time_stride=time_stride)
    )

    if verbose:
        print(f"  Scoring {len(candidates)} candidates for spectrum...")

    scored: list[ScoredCandidate] = []
    seen: set[tuple[int, int, int, int]] = set()

    for sg, t_start, t_end in candidates:
        positions = sg.position_set_at_time(t_start)
        if not positions:
            continue
        key = (min(positions), max(positions), t_start, t_end)
        if key in seen:
            continue
        seen.add(key)

        result = _score_candidate(sg, t_start, t_end, tau, criteria)
        if result is not None:
            scored.append(result)

    # Sort: most criteria passed first, then earliest time
    scored.sort(key=lambda s: (-s.n_criteria_passed(criteria), s.t_window_start))
    return scored
