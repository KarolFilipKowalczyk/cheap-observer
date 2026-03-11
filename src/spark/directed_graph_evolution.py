"""
Evolution graph construction for directed graph rewriting rules.

The evolution graph E(r, G_0) encodes the causal structure of a directed
graph rewriting evolution as a DAG. Nodes are (graph_node, timestep) pairs
with labels. Edges encode causal influence: matched pattern nodes connect
to all replacement nodes, reconnection edges link matched nodes to
reattachment sites, and identity edges link unaffected nodes to their
next-timestep copies.

See definitions.md §1 (abstract protocol) and Appendix B, Section B.3.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import networkx as nx

from src.spark.rule_classes.directed_graph import DirectedGraphRule, STAR


# ---------------------------------------------------------------------------
# Node type
# ---------------------------------------------------------------------------

class EvolutionNode(NamedTuple):
    """A node in the evolution graph: state-graph node v at time t.

    See definitions.md B.3: "Each node (v, t) represents a state graph
    node v at time t. The node's label is the label of v in G_t."
    """

    node_id: int
    time: int
    label: int


# ---------------------------------------------------------------------------
# Evolution graph
# ---------------------------------------------------------------------------

class DirectedGraphEvolution:
    """The causal DAG of a directed graph rewriting evolution.

    Builds the evolution graph incrementally by applying the rule step by
    step, recording causal edges at each step according to the three edge
    types from definitions.md B.3.

    Attributes:
        rule: The directed graph rewriting rule.
        seed: The initial state graph.
        state_graphs: List of state graphs [G_0, G_1, ...].
        matches: List of (match_dict, new_node_ids) per step.
    """

    def __init__(self, rule: DirectedGraphRule, seed: nx.DiGraph) -> None:
        self.rule = rule
        self.seed = seed
        self.state_graphs: list[nx.DiGraph] = [seed]
        # Per-step records: (match P-node->G-node, new node IDs from Q)
        self._matches: list[tuple[dict[int, int], list[int]]] = []
        # Causal edges: lists of (src_node_id, dst_node_id) per step
        self._edge_src: list[list[int]] = []
        self._edge_dst: list[list[int]] = []
        self._next_id = [max(seed.nodes) + 1 if seed.nodes else 0]

    # -- construction -------------------------------------------------------

    def evolve(self, n_steps: int) -> None:
        """Run the evolution for n_steps, building the causal graph.

        Applies the rule under canonical update order. Stops early if
        no match is found in the current state graph.
        """
        for _ in range(n_steps):
            G_t = self.state_graphs[-1]
            new_G, match, new_ids = self.rule.apply(
                G_t, order="canonical", _next_id=self._next_id
            )
            if match is None:
                break

            matched_g_nodes = set(match.values())
            src_list: list[int] = []
            dst_list: list[int] = []

            # 1. Matched-to-replacement edges:
            #    Each matched G-node -> every new Q node
            for g_node in matched_g_nodes:
                for nid in new_ids:
                    src_list.append(g_node)
                    dst_list.append(nid)

            # 2. Reconnection edges:
            #    Matched g_node with phi != STAR -> external neighbors
            for p_node, g_node in match.items():
                target_p = self.rule.phi[p_node]
                if target_p == STAR:
                    continue
                # Find the new node ID that this P-node maps to
                # (via the Q-node that phi maps to)
                q_to_new = {}
                for qi, nid in zip(sorted(self.rule.Q.nodes), new_ids):
                    q_to_new[qi] = nid
                new_target = q_to_new.get(target_p)
                if new_target is None:
                    continue

                # External predecessors of g_node that persist
                for u in G_t.predecessors(g_node):
                    if u not in matched_g_nodes and u in new_G.nodes:
                        src_list.append(g_node)
                        dst_list.append(u)

                # External successors of g_node that persist
                for v in G_t.successors(g_node):
                    if v not in matched_g_nodes and v in new_G.nodes:
                        src_list.append(g_node)
                        dst_list.append(v)

            # 3. Identity edges:
            #    Unmatched nodes that persist -> their next-timestep copy
            for v in G_t.nodes:
                if v not in matched_g_nodes and v in new_G.nodes:
                    src_list.append(v)
                    dst_list.append(v)

            self._edge_src.append(src_list)
            self._edge_dst.append(dst_list)
            self._matches.append((match, new_ids))
            self.state_graphs.append(new_G)

    # -- protocol methods ---------------------------------------------------

    @property
    def max_time(self) -> int:
        return len(self.state_graphs) - 1

    @property
    def n_steps_evolved(self) -> int:
        """Number of rewrite steps actually performed."""
        return len(self._edge_src)

    def state_graph_at_time(self, t: int) -> nx.DiGraph:
        """Return the state graph G_t."""
        return self.state_graphs[t]

    def nodes_at_time(self, t: int) -> list[EvolutionNode]:
        """All evolution nodes at time step t, ordered by node ID."""
        G_t = self.state_graphs[t]
        return [
            EvolutionNode(v, t, G_t.nodes[v]["label"])
            for v in sorted(G_t.nodes)
        ]

    def node_ids_at_time(self, t: int) -> set[int]:
        """Set of state-graph node IDs at time t."""
        return set(self.state_graphs[t].nodes)

    def edges_at_time(self, t: int) -> list[tuple[int, int]]:
        """Causal edges from time t to t+1 as (src_id, dst_id) pairs."""
        if t >= len(self._edge_src):
            return []
        return list(zip(self._edge_src[t], self._edge_dst[t]))

    def match_at_time(self, t: int) -> tuple[dict[int, int], list[int]] | None:
        """Return (match_dict, new_node_ids) for step t, or None."""
        if t >= len(self._matches):
            return None
        return self._matches[t]

    # -- distance function --------------------------------------------------

    def normalized_distances(self) -> np.ndarray:
        """Compute d(t): fraction of nodes whose label or 1-hop neighborhood
        changed between G_t and G_{t+1}.

        See definitions.md B.4: "the fraction of nodes whose label or
        local neighborhood (1-hop degree sequence) changed between G_t
        and G_{t+1}, computed over nodes present in both timesteps."
        """
        n = self.n_steps_evolved
        if n == 0:
            return np.array([], dtype=np.float64)

        d = np.empty(n, dtype=np.float64)
        for t in range(n):
            G_t = self.state_graphs[t]
            G_t1 = self.state_graphs[t + 1]

            nodes_t = set(G_t.nodes)
            nodes_t1 = set(G_t1.nodes)
            common = nodes_t & nodes_t1
            max_size = max(len(nodes_t), len(nodes_t1))

            if max_size == 0:
                d[t] = 0.0
                continue

            # Count nodes only in one timestep as changed
            changed = (len(nodes_t) - len(common)) + (len(nodes_t1) - len(common))

            # Count common nodes whose label or neighborhood changed
            for v in common:
                if G_t.nodes[v]["label"] != G_t1.nodes[v]["label"]:
                    changed += 1
                    continue
                # 1-hop degree signature: (in-degree, out-degree)
                in_t = G_t.in_degree(v)
                out_t = G_t.out_degree(v)
                in_t1 = G_t1.in_degree(v)
                out_t1 = G_t1.out_degree(v)
                if in_t != in_t1 or out_t != out_t1:
                    changed += 1

            d[t] = min(changed / max_size, 1.0)

        return d

    # -- subgraph view (for observer detection) -----------------------------

    def get_boundary_edges(
        self, inside_t: set[int], inside_t1: set[int], t: int
    ) -> set[tuple[tuple[int, int], tuple[int, int]]]:
        """Return boundary edges at time t.

        A boundary edge is a causal edge from t to t+1 where exactly one
        endpoint is inside the subgraph.
        """
        if t >= len(self._edge_src):
            return set()

        boundary = set()
        for src, dst in zip(self._edge_src[t], self._edge_dst[t]):
            src_in = src in inside_t
            dst_in = dst in inside_t1
            if src_in != dst_in:
                boundary.add(((src, t), (dst, t + 1)))

        return boundary


# ---------------------------------------------------------------------------
# __main__: quick sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from src.spark.rule_classes.directed_graph import DirectedGraphRule

    # Simple test: single node with label 0, self-loop -> two nodes
    P = nx.DiGraph()
    P.add_node(0, label=0)
    P.add_edge(0, 0)

    Q = nx.DiGraph()
    Q.add_node(0, label=0)
    Q.add_node(1, label=1)
    Q.add_edge(0, 1)

    phi = {0: 0}
    rule = DirectedGraphRule(P=P, Q=Q, phi=phi)

    seed = nx.DiGraph()
    seed.add_node(0, label=0)
    seed.add_edge(0, 0)

    evo = DirectedGraphEvolution(rule, seed)
    evo.evolve(10)

    print(f"Rule: {rule}")
    print(f"Steps evolved: {evo.n_steps_evolved}")
    for t in range(min(evo.n_steps_evolved + 1, 11)):
        G_t = evo.state_graph_at_time(t)
        print(f"  t={t}: |V|={len(G_t.nodes)}, |E|={len(G_t.edges)}, "
              f"nodes={sorted(G_t.nodes)}")

    distances = evo.normalized_distances()
    print(f"\nDistances: {distances}")
