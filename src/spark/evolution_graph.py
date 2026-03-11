"""
Evolution graph construction for string rewriting rules.

The evolution graph G(r, s_0) encodes the causal structure of a spark's
evolution as a directed acyclic graph. Nodes are (position, time) pairs
with symbol labels. Edges encode causal influence between consecutive
time steps.

See definitions.md Section 3.
"""

from __future__ import annotations

from typing import NamedTuple, Sequence

import numpy as np

from src.spark.rule_classes.string_rewriting import StringRewritingRule


# ---------------------------------------------------------------------------
# Node type
# ---------------------------------------------------------------------------

class EvolutionNode(NamedTuple):
    """A node in the evolution graph: position i in the string at time t.

    See definitions.md Section 3: "Each node (i, t) represents position i
    in the string at time t. The node's label is the symbol s_t[i]."
    """

    position: int
    time: int
    label: str


# ---------------------------------------------------------------------------
# Evolution graph
# ---------------------------------------------------------------------------

class StringEvolutionGraph:
    """The causal DAG of a string rewriting evolution.

    Builds the evolution graph incrementally by applying the rule step by
    step under leftmost-match canonical order, recording the causal edges
    at each step.

    See definitions.md Section 3.

    Internal storage (numpy-backed for later CUDA portability):
        strings: list of the string at each time step.
        _edge_src[t]: int32 array of source positions at time t.
        _edge_dst[t]: int32 array of destination positions at time t+1.
        _match_pos[t]: position of the leftmost L-match at step t, or -1.
    """

    def __init__(self, rule: StringRewritingRule, seed: str) -> None:
        self.rule = rule
        self.seed = seed
        self.strings: list[str] = [seed]
        self._edge_src: list[np.ndarray] = []
        self._edge_dst: list[np.ndarray] = []
        self._match_pos: list[int] = []

    # -- construction -------------------------------------------------------

    def evolve(self, n_steps: int) -> None:
        """Run the evolution for n_steps, building the causal graph.

        Applies the rule under leftmost-match canonical order. Stops early
        if the string becomes empty or reaches a fixed point (L not found).

        See definitions.md Section 3: "the leftmost match is rewritten
        first."
        """
        len_L = len(self.rule.L)
        len_R = len(self.rule.R)
        delta = len_R - len_L

        for _ in range(n_steps):
            current = self.strings[-1]
            match_pos = current.find(self.rule.L)

            if match_pos == -1:
                self._match_pos.append(-1)
                break

            # Build new string
            new_string = (
                current[:match_pos]
                + self.rule.R
                + current[match_pos + len_L:]
            )

            # Build causal edges per definitions.md Section 3:
            # - Matched positions -> all positions in inserted R
            # - Unmatched positions -> shifted identity
            src_list = []
            dst_list = []
            cur_len = len(current)

            for i in range(cur_len):
                if match_pos <= i < match_pos + len_L:
                    # Matched: edges to all positions in R
                    for j in range(match_pos, match_pos + len_R):
                        src_list.append(i)
                        dst_list.append(j)
                elif i < match_pos:
                    # Before match: identity propagation
                    src_list.append(i)
                    dst_list.append(i)
                else:
                    # After match: shifted by delta
                    src_list.append(i)
                    dst_list.append(i + delta)

            self._edge_src.append(np.array(src_list, dtype=np.int32))
            self._edge_dst.append(np.array(dst_list, dtype=np.int32))
            self._match_pos.append(match_pos)
            self.strings.append(new_string)

    # -- protocol methods ---------------------------------------------------

    @property
    def max_time(self) -> int:
        return len(self.strings) - 1

    @property
    def n_steps_evolved(self) -> int:
        """Number of rewrite steps actually performed."""
        return len(self._edge_src)

    def nodes_at_time(self, t: int) -> list[EvolutionNode]:
        """All nodes at time step t, ordered by position."""
        s = self.strings[t]
        return [EvolutionNode(i, t, s[i]) for i in range(len(s))]

    def string_at_time(self, t: int) -> str:
        return self.strings[t]

    def string_length_at_time(self, t: int) -> int:
        return len(self.strings[t])

    def successors(self, node: EvolutionNode) -> list[EvolutionNode]:
        """Nodes at time t+1 causally influenced by this node."""
        t = node.time
        if t >= self.n_steps_evolved:
            return []
        mask = self._edge_src[t] == node.position
        dst_positions = self._edge_dst[t][mask]
        next_str = self.strings[t + 1]
        return [
            EvolutionNode(int(j), t + 1, next_str[int(j)])
            for j in dst_positions
        ]

    def predecessors(self, node: EvolutionNode) -> list[EvolutionNode]:
        """Nodes at time t-1 that causally influenced this node."""
        t = node.time
        if t == 0 or t - 1 >= len(self._edge_src):
            return []
        mask = self._edge_dst[t - 1] == node.position
        src_positions = self._edge_src[t - 1][mask]
        prev_str = self.strings[t - 1]
        return [
            EvolutionNode(int(i), t - 1, prev_str[int(i)])
            for i in src_positions
        ]

    def edges_at_time(self, t: int) -> np.ndarray:
        """Return (n, 2) array of (src_pos, dst_pos) edges from t to t+1."""
        if t >= len(self._edge_src):
            return np.empty((0, 2), dtype=np.int32)
        return np.column_stack((self._edge_src[t], self._edge_dst[t]))

    def match_position_at_time(self, t: int) -> int:
        """Position of the leftmost L-match at step t, or -1 if none."""
        if t >= len(self._match_pos):
            return -1
        return self._match_pos[t]

    # -- subgraph extraction ------------------------------------------------

    def get_subgraph(
        self,
        positions_by_time: dict[int, set[int]] | None = None,
        pos_start: int | None = None,
        pos_end: int | None = None,
        time_start: int = 0,
        time_end: int | None = None,
    ) -> SubgraphView:
        """Extract a spatiotemporal region as a SubgraphView.

        Either provide positions_by_time (a dict mapping time -> set of
        positions) for arbitrary subgraphs, or provide pos_start/pos_end
        for a rectangular region.

        Args:
            positions_by_time: Explicit node membership per timestep.
            pos_start: Left boundary of rectangular region (inclusive).
            pos_end: Right boundary of rectangular region (exclusive).
            time_start: First timestep (inclusive).
            time_end: Last timestep (inclusive). Defaults to max_time.

        Returns:
            A SubgraphView over this evolution graph.
        """
        if time_end is None:
            time_end = self.max_time

        if positions_by_time is not None:
            return SubgraphView(self, positions_by_time)

        if pos_start is None or pos_end is None:
            raise ValueError(
                "Provide either positions_by_time or pos_start/pos_end"
            )

        pbt: dict[int, set[int]] = {}
        for t in range(time_start, time_end + 1):
            s_len = len(self.strings[t])
            actual_end = min(pos_end, s_len)
            actual_start = max(pos_start, 0)
            if actual_start < actual_end:
                pbt[t] = set(range(actual_start, actual_end))
        return SubgraphView(self, pbt)

    def get_boundary_edges(
        self, subgraph: SubgraphView, t: int
    ) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        """Return boundary edges at time t.

        A boundary edge is an edge from t to t+1 where exactly one
        endpoint is inside the subgraph.

        See definitions.md Section 5.1: "The boundary of S at time t is
        the set of edges crossing between nodes inside S and nodes
        outside S at time t."

        Returns:
            Set of ((src_pos, t), (dst_pos, t+1)) tuples.
        """
        if t >= len(self._edge_src):
            return set()

        inside_t = subgraph.position_set_at_time(t)
        inside_t1 = subgraph.position_set_at_time(t + 1)
        src = self._edge_src[t]
        dst = self._edge_dst[t]
        boundary = set()

        for idx in range(len(src)):
            s, d = int(src[idx]), int(dst[idx])
            src_in = s in inside_t
            dst_in = d in inside_t1
            if src_in != dst_in:
                boundary.add(((s, t), (d, t + 1)))

        return boundary


# ---------------------------------------------------------------------------
# Subgraph view
# ---------------------------------------------------------------------------

class SubgraphView:
    """A view into a spatiotemporal region of the evolution graph.

    Implements the operations needed by the observer detection contract
    in src/observer/definition.py.

    The subgraph is defined by a dict mapping timesteps to sets of
    positions that are "inside."
    """

    def __init__(
        self,
        parent: StringEvolutionGraph,
        positions_by_time: dict[int, set[int]],
    ) -> None:
        self._parent = parent
        self._positions_by_time = positions_by_time

    @property
    def parent_graph(self) -> StringEvolutionGraph:
        return self._parent

    @property
    def time_span(self) -> tuple[int, int]:
        """(earliest time, latest time) covered by this subgraph."""
        times = self._positions_by_time.keys()
        return (min(times), max(times))

    def contains(self, node: EvolutionNode) -> bool:
        positions = self._positions_by_time.get(node.time)
        if positions is None:
            return False
        return node.position in positions

    def position_set_at_time(self, t: int) -> set[int]:
        """Raw set of positions inside the subgraph at time t."""
        return self._positions_by_time.get(t, set())

    def nodes_at_time(self, t: int) -> list[EvolutionNode]:
        """All nodes inside this subgraph at time t, ordered by position."""
        positions = sorted(self._positions_by_time.get(t, set()))
        s = self._parent.strings[t]
        return [EvolutionNode(i, t, s[i]) for i in positions if i < len(s)]

    def boundary_edges_at_time(
        self, t: int
    ) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        """Boundary edges at time t. Delegates to parent graph."""
        return self._parent.get_boundary_edges(self, t)

    def internal_state_at_time(self, t: int) -> str:
        """String of labels of nodes inside S at time t, left to right.

        See definitions.md Section 5.2.
        """
        positions = sorted(self._positions_by_time.get(t, set()))
        s = self._parent.strings[t]
        return "".join(s[i] for i in positions if i < len(s))

    def width_at_time(self, t: int) -> int:
        """Spatial extent at time t (max pos - min pos).

        See definitions.md Section 5.4.
        """
        positions = self._positions_by_time.get(t, set())
        if not positions:
            return 0
        return max(positions) - min(positions)


# ---------------------------------------------------------------------------
# __main__: first look at the dynamics
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.spark.seed_search import find_minimal_seed

    # Pick a few interesting active rules from C(4)
    test_rules = [
        StringRewritingRule("0", "01"),
        StringRewritingRule("0", "10"),
        StringRewritingRule("0", "011"),
        StringRewritingRule("1", "010"),
    ]

    N_STEPS = 500

    for rule in test_rules:
        seed = find_minimal_seed(rule)
        if seed is None:
            print(f"Rule {rule}: sterile, skipping")
            continue

        graph = StringEvolutionGraph(rule, seed)
        graph.evolve(N_STEPS)

        actual_steps = graph.n_steps_evolved
        lengths = [graph.string_length_at_time(t) for t in range(actual_steps + 1)]

        print(f"\nRule: {rule}  |  Seed: {seed!r}  |  Steps evolved: {actual_steps}")
        print(f"  String length: {lengths[0]} -> {lengths[-1]}"
              f"  (growth: +{lengths[-1] - lengths[0]} over {actual_steps} steps)")

        # Show a few edge counts
        for t in [0, 1, 2, actual_steps - 1]:
            if t < actual_steps:
                edges = graph.edges_at_time(t)
                mp = graph.match_position_at_time(t)
                print(f"  t={t}: |string|={lengths[t]}, "
                      f"match_pos={mp}, edges={len(edges)}")

        # Quick subgraph test: extract a small region
        if actual_steps >= 10:
            sg = graph.get_subgraph(pos_start=0, pos_end=3, time_start=0, time_end=9)
            t_first, t_last = sg.time_span
            print(f"  Subgraph [0:3, 0:9]: time_span=({t_first}, {t_last})")
            for t in range(t_first, min(t_first + 5, t_last + 1)):
                state = sg.internal_state_at_time(t)
                boundary = sg.boundary_edges_at_time(t)
                print(f"    t={t}: internal={state!r}, |boundary|={len(boundary)}")
