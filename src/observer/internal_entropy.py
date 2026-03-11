"""
Internal entropy criterion (definitions.md Section 5.2).

Measures the diversity of a subgraph's internal states over tau-sized
sliding windows. The minimum entropy across all windows must exceed
epsilon_H (default 1.0 bit) to pass.

    H(internal states over tau window) > epsilon_H
"""

from __future__ import annotations

import math
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.spark.evolution_graph import SubgraphView


def _shannon_entropy(strings: list[str]) -> float:
    """Shannon entropy in bits of the empirical distribution."""
    n = len(strings)
    if n == 0:
        return 0.0
    counts = Counter(strings)
    entropy = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def internal_entropy_score(
    subgraph: SubgraphView, t_start: int, t_end: int, tau: int
) -> float:
    """Compute internal entropy per definitions.md Section 5.2.

    Collects the internal state string at each timestep, then slides a
    tau-sized window across [t_start, t_end] and computes Shannon entropy
    of the state distribution within each window. Returns the minimum
    entropy across all windows.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step (inclusive).
        t_end: Last time step (inclusive).
        tau: Characteristic time, used as sliding window length.

    Returns:
        Minimum Shannon entropy (bits) across all tau-windows.
    """
    # Collect all internal states in the full window
    states = [subgraph.internal_state_at_time(t) for t in range(t_start, t_end + 1)]
    n_states = len(states)

    if n_states == 0 or tau <= 0:
        return 0.0

    # If tau exceeds the window, compute entropy of the full window
    if tau >= n_states:
        return _shannon_entropy(states)

    # Slide a window of size tau, track minimum entropy
    min_entropy = float("inf")
    for w_start in range(n_states - tau + 1):
        window_states = states[w_start : w_start + tau]
        h = _shannon_entropy(window_states)
        if h < min_entropy:
            min_entropy = h

    return min_entropy


# ---------------------------------------------------------------------------
# __main__
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.spark.rule_classes.string_rewriting import StringRewritingRule
    from src.spark.seed_search import find_minimal_seed
    from src.spark.evolution_graph import StringEvolutionGraph
    from src.spark.characteristic_time import characteristic_time

    rule = StringRewritingRule("1", "010")
    seed = find_minimal_seed(rule)
    print(f"Rule: {rule}  |  Seed: {seed!r}")

    graph = StringEvolutionGraph(rule, seed)
    graph.evolve(500)
    tau = characteristic_time(graph)
    print(f"Steps: {graph.n_steps_evolved}  |  tau: {tau}")

    configs = [
        ("fixed [2,8) t=[50,150)", 2, 8, 50, 150),
        ("narrow [3,5) t=[50,150)", 3, 5, 50, 150),
        ("wide [0,15) t=[50,150)", 0, 15, 50, 150),
        ("left edge [0,3) t=[10,60)", 0, 3, 10, 60),
    ]

    for label, ps, pe, ts, te in configs:
        sg = graph.get_subgraph(pos_start=ps, pos_end=pe, time_start=ts, time_end=te)
        score = internal_entropy_score(sg, ts, te, tau)
        print(f"  {label}: internal_entropy = {score:.4f} bits"
              f"  {'PASS' if score > 1.0 else 'FAIL'} (> 1.0)")

        # Show a few internal states for the first config
        if ps == 2 and pe == 8:
            print(f"    Sample states: ", end="")
            for t in range(ts, min(ts + 10, te + 1)):
                print(f"{sg.internal_state_at_time(t)!r} ", end="")
            print()
