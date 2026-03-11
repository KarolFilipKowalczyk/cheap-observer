"""
Boundary stability criterion (definitions.md Section 5.1).

Measures how much the boundary of a subgraph changes per step.
Lower values mean greater stability.

    score = (1/W) * sum_{t} |B(t) △ B(t+1)| / |B(t)|

where B(t) is the set of boundary edges at time t and △ is symmetric
difference. The score must be below epsilon_B (default 0.3) to pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.spark.evolution_graph import SubgraphView


def boundary_stability_score(
    subgraph: SubgraphView, t_start: int, t_end: int
) -> float:
    """Compute boundary stability per definitions.md Section 5.1.

    For each step in [t_start, t_end), compute the boundary edge set
    B(t) as position-pairs (src_pos, dst_pos), take the symmetric
    difference with B(t+1), and average the fractional change over the
    window.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step (inclusive).
        t_end: Last time step (inclusive).

    Returns:
        Average fractional boundary change, in [0, 1].
    """
    W = t_end - t_start
    if W <= 0:
        return 0.0

    def _boundary_pos_set(t: int) -> set[tuple[int, int]]:
        """Boundary edges at time t as (src_pos, dst_pos) pairs."""
        raw = subgraph.boundary_edges_at_time(t)
        return {(src_pos, dst_pos) for (src_pos, _), (dst_pos, _) in raw}

    total = 0.0
    prev_boundary = _boundary_pos_set(t_start)

    for t in range(t_start, t_end):
        curr_boundary = prev_boundary
        next_boundary = _boundary_pos_set(t + 1)

        if len(curr_boundary) > 0:
            sym_diff = curr_boundary.symmetric_difference(next_boundary)
            total += len(sym_diff) / len(curr_boundary)
        # else: no boundary => contributes 0.0

        prev_boundary = next_boundary

    return total / W


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

    # Test several subgraph widths and positions
    configs = [
        ("fixed [2,8) t=[50,150)", 2, 8, 50, 150),
        ("narrow [3,5) t=[50,150)", 3, 5, 50, 150),
        ("wide [0,15) t=[50,150)", 0, 15, 50, 150),
        ("left edge [0,3) t=[10,60)", 0, 3, 10, 60),
    ]

    for label, ps, pe, ts, te in configs:
        sg = graph.get_subgraph(pos_start=ps, pos_end=pe, time_start=ts, time_end=te)
        score = boundary_stability_score(sg, ts, te)
        print(f"  {label}: boundary_stability = {score:.4f}"
              f"  {'PASS' if score < 0.3 else 'FAIL'} (< 0.3)")
