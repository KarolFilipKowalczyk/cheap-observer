"""
Self-reference criterion (definitions.md Section 5.4).

Searches for self-referential returns: forward causal paths through
interior nodes whose spatial trajectory returns to the originating
region. The path is acyclic in time but cyclic in space.

At least one such return must exist within the window to pass.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.spark.evolution_graph import SubgraphView


def _has_self_referential_return(
    subgraph: SubgraphView,
    start_pos: int,
    start_time: int,
    t_end: int,
    width: int,
) -> bool:
    """BFS forward from (start_pos, start_time) through internal edges.

    Returns True if any reached node (pos', t') with t' > start_time
    satisfies |pos' - start_pos| < width.

    The BFS only follows edges where both source and destination are
    inside the subgraph, ensuring the causal path stays internal.
    """
    graph = subgraph.parent_graph

    # BFS frontier: set of positions reachable at each timestep
    # We track reachable positions layer-by-layer (timestep by timestep)
    frontier = {start_pos}
    inside_start = subgraph.position_set_at_time(start_time)

    for t in range(start_time, min(t_end, graph.n_steps_evolved)):
        if not frontier:
            return False

        inside_now = subgraph.position_set_at_time(t)
        inside_next = subgraph.position_set_at_time(t + 1)

        if t >= len(graph._edge_src):
            return False

        src = graph._edge_src[t]
        dst = graph._edge_dst[t]

        next_frontier = set()
        for idx in range(len(src)):
            s, d = int(src[idx]), int(dst[idx])
            if s in frontier and s in inside_now and d in inside_next:
                next_frontier.add(d)

        # Check for spatial return (must be at least 2 steps later to
        # distinguish from trivial identity propagation)
        if t + 1 > start_time + 1:
            for pos in next_frontier:
                if abs(pos - start_pos) < max(width, 1):
                    return True

        frontier = next_frontier

    return False


def self_reference_score(
    subgraph: SubgraphView, t_start: int, t_end: int
) -> float:
    """Compute self-reference score per definitions.md Section 5.4.

    Searches for at least one self-referential return within the window.
    A return is a forward causal path through internal nodes that starts
    at (i, t) and reaches (i', t'') where |i' - i| < width(S, t).

    For efficiency, tests nodes at rewrite positions first (they produce
    the fan-out edges that are most likely to create returns), then
    samples other internal nodes.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step (inclusive).
        t_end: Last time step (inclusive).

    Returns:
        Count of self-referential returns found (as float).
        >= 1.0 means the criterion is satisfied.
    """
    graph = subgraph.parent_graph
    count = 0.0

    # Collect candidate starting nodes, prioritizing rewrite positions
    candidates: list[tuple[int, int]] = []  # (position, time)
    other_candidates: list[tuple[int, int]] = []

    for t in range(t_start, t_end):
        inside = subgraph.position_set_at_time(t)
        if not inside:
            continue

        match_pos = graph.match_position_at_time(t)
        width = subgraph.width_at_time(t)

        if match_pos >= 0 and match_pos in inside:
            candidates.append((match_pos, t))
        else:
            # Sample one non-match node per timestep
            for pos in sorted(inside):
                other_candidates.append((pos, t))
                break

    # Test rewrite-position candidates first
    for pos, t in candidates:
        width = subgraph.width_at_time(t)
        if _has_self_referential_return(subgraph, pos, t, t_end, width):
            count += 1.0
            return count  # Early exit: one is enough

    # If no match-position returns, sample other nodes
    # Limit to avoid excessive computation
    MAX_SAMPLES = 50
    for pos, t in other_candidates[:MAX_SAMPLES]:
        width = subgraph.width_at_time(t)
        if _has_self_referential_return(subgraph, pos, t, t_end, width):
            count += 1.0
            return count

    return count


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
        score = self_reference_score(sg, ts, te)
        print(f"  {label}: self_reference = {score:.1f}"
              f"  {'PASS' if score >= 1.0 else 'FAIL'} (>= 1.0)")

    # Also test a rule where match stays at position 0
    print(f"\n--- Testing rule with fixed match position ---")
    rule2 = StringRewritingRule("0", "011")
    seed2 = find_minimal_seed(rule2)
    print(f"Rule: {rule2}  |  Seed: {seed2!r}")

    graph2 = StringEvolutionGraph(rule2, seed2)
    graph2.evolve(500)
    tau2 = characteristic_time(graph2)
    print(f"Steps: {graph2.n_steps_evolved}  |  tau: {tau2}")

    configs2 = [
        ("around match [0,5) t=[10,100)", 0, 5, 10, 100),
        ("wide [0,10) t=[10,100)", 0, 10, 10, 100),
        ("offset [3,8) t=[10,100)", 3, 8, 10, 100),
    ]

    for label, ps, pe, ts, te in configs2:
        sg = graph2.get_subgraph(pos_start=ps, pos_end=pe, time_start=ts, time_end=te)
        score = self_reference_score(sg, ts, te)
        print(f"  {label}: self_reference = {score:.1f}"
              f"  {'PASS' if score >= 1.0 else 'FAIL'} (>= 1.0)")
