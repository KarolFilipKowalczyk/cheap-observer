"""
Directed graph rewriting rule class.

A directed graph rewriting rule r is a triple (P, Q, phi) where P is a
non-empty weakly connected labeled directed graph (the pattern), Q is a
labeled directed graph (the replacement, may be empty), and phi maps each
node of P to a node of Q or to * (delete external edges).

The rule class D(n, m, k) is the set of all such rules where |V(P)| <= n,
|V(Q)| <= m, and labels are drawn from an alphabet of size k.

See definitions.md Appendix B.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Iterator, Literal

import networkx as nx


# Sentinel for "delete external edges" in the reconnection map.
STAR = "*"


@dataclass(frozen=True)
class DirectedGraphRule:
    """A directed graph rewriting rule (P, Q, phi).

    P and Q are stored as nx.DiGraph with integer node IDs and a 'label'
    attribute on each node. phi maps P-node IDs to Q-node IDs or STAR.

    See definitions.md Appendix B, Section B.1.
    """

    P: nx.DiGraph
    Q: nx.DiGraph
    phi: dict[int, int | str]  # P-node -> Q-node or STAR

    def __post_init__(self) -> None:
        if len(self.P) == 0:
            raise ValueError("Pattern P must be non-empty")
        if not nx.is_weakly_connected(self.P):
            raise ValueError("Pattern P must be weakly connected")
        for n in self.P.nodes:
            if "label" not in self.P.nodes[n]:
                raise ValueError(f"P node {n} missing 'label' attribute")
        for n in self.Q.nodes:
            if "label" not in self.Q.nodes[n]:
                raise ValueError(f"Q node {n} missing 'label' attribute")
        for p_node in self.P.nodes:
            if p_node not in self.phi:
                raise ValueError(f"phi missing mapping for P node {p_node}")
            target = self.phi[p_node]
            if target != STAR and target not in self.Q.nodes:
                raise ValueError(
                    f"phi[{p_node}] = {target} not in Q nodes or STAR"
                )

    def __hash__(self) -> int:
        return hash(self._canonical_key())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DirectedGraphRule):
            return NotImplemented
        return self._canonical_key() == other._canonical_key()

    def _canonical_key(self) -> tuple:
        """A hashable canonical representation for equality/hashing."""
        p_nodes = tuple(
            (n, self.P.nodes[n]["label"]) for n in sorted(self.P.nodes)
        )
        p_edges = tuple(sorted(self.P.edges))
        q_nodes = tuple(
            (n, self.Q.nodes[n]["label"]) for n in sorted(self.Q.nodes)
        )
        q_edges = tuple(sorted(self.Q.edges))
        phi_t = tuple(
            (k, self.phi[k]) for k in sorted(self.phi)
        )
        return (p_nodes, p_edges, q_nodes, q_edges, phi_t)

    @property
    def description_length(self) -> int:
        """Total node count |V(P)| + |V(Q)| as a complexity measure."""
        return len(self.P) + len(self.Q)

    # -- matching -----------------------------------------------------------

    def find_matches(self, G: nx.DiGraph) -> list[dict[int, int]]:
        """Find all subgraph isomorphisms of P in G.

        Returns a list of dicts mapping P-node -> G-node, respecting
        labels and edge structure.

        Uses networkx DiGraphMatcher with a node label constraint.
        """
        def node_match(n1_attrs: dict, n2_attrs: dict) -> bool:
            return n1_attrs["label"] == n2_attrs["label"]

        matcher = nx.algorithms.isomorphism.DiGraphMatcher(
            G, self.P, node_match=node_match
        )
        matches = []
        for iso in matcher.subgraph_isomorphisms_iter():
            # iso maps G-node -> P-node; invert to P-node -> G-node
            inv = {p: g for g, p in iso.items()}
            matches.append(inv)
        return matches

    def _select_match(
        self,
        matches: list[dict[int, int]],
        order: Literal["canonical", "random"] = "canonical",
    ) -> dict[int, int]:
        """Select which match to apply.

        Canonical order: choose the match whose sorted tuple of G-node
        identifiers is lexicographically smallest.

        See definitions.md B.2: "choose the match involving the
        lowest-labeled node (comparing node identifiers lexicographically
        across the match)."
        """
        if order == "canonical":
            return min(matches, key=lambda m: tuple(sorted(m.values())))
        elif order == "random":
            return random.choice(matches)
        else:
            raise ValueError(f"Unknown order: {order!r}")

    # -- application --------------------------------------------------------

    def apply(
        self,
        G: nx.DiGraph,
        order: Literal["canonical", "random"] = "canonical",
        _next_id: list[int] | None = None,
    ) -> tuple[nx.DiGraph, dict[int, int] | None, list[int] | None]:
        """Apply the rule once to state graph G.

        Returns (new_graph, match_used, new_node_ids) where:
          - new_graph: the state graph after one rewrite step
          - match_used: the P-node -> G-node mapping that was applied,
            or None if no match was found
          - new_node_ids: list of fresh node IDs introduced by Q,
            or None if no match

        Args:
            G: Current state graph.
            order: 'canonical' or 'random'.
            _next_id: Mutable list [next_id] for fresh node ID generation.
                      If None, uses max(G.nodes) + 1 as starting point.
        """
        matches = self.find_matches(G)
        if not matches:
            return G, None, None

        match = self._select_match(matches, order)
        matched_g_nodes = set(match.values())

        # Fresh node IDs for Q
        if _next_id is None:
            _next_id = [max(G.nodes) + 1 if G.nodes else 0]
        new_ids: list[int] = []
        q_to_new: dict[int, int] = {}
        for q_node in sorted(self.Q.nodes):
            q_to_new[q_node] = _next_id[0]
            new_ids.append(_next_id[0])
            _next_id[0] += 1

        # Build the reconnection: P-node -> new G-node or STAR
        p_to_new: dict[int, int | str] = {}
        for p_node, target in self.phi.items():
            if target == STAR:
                p_to_new[p_node] = STAR
            else:
                p_to_new[p_node] = q_to_new[target]

        # Build new graph
        new_G = nx.DiGraph()

        # Copy unmatched nodes
        for v in G.nodes:
            if v not in matched_g_nodes:
                new_G.add_node(v, **G.nodes[v])

        # Copy edges among unmatched nodes
        for u, v in G.edges:
            if u not in matched_g_nodes and v not in matched_g_nodes:
                new_G.add_edge(u, v)

        # Insert Q nodes
        for q_node in self.Q.nodes:
            nid = q_to_new[q_node]
            new_G.add_node(nid, label=self.Q.nodes[q_node]["label"])

        # Insert Q internal edges
        for u, v in self.Q.edges:
            new_G.add_edge(q_to_new[u], q_to_new[v])

        # Reconnect dangling edges
        for p_node, g_node in match.items():
            target = p_to_new[p_node]
            if target == STAR:
                continue

            # Incoming external edges: u -> g_node where u not matched
            for u in G.predecessors(g_node):
                if u not in matched_g_nodes:
                    new_G.add_edge(u, target)

            # Outgoing external edges: g_node -> v where v not matched
            for v in G.successors(g_node):
                if v not in matched_g_nodes:
                    new_G.add_edge(target, v)

        return new_G, match, new_ids

    # -- evolution ----------------------------------------------------------

    def evolve(
        self,
        seed: nx.DiGraph,
        steps: int,
        order: Literal["canonical", "random"] = "canonical",
    ) -> list[nx.DiGraph]:
        """Evolve the seed graph for the given number of steps.

        Returns [G_0, G_1, ..., G_n]. Stops early if no match is found.
        """
        history = [seed]
        current = seed
        next_id = [max(seed.nodes) + 1 if seed.nodes else 0]
        for _ in range(steps):
            new_G, match, _ = self.apply(current, order=order, _next_id=next_id)
            if match is None:
                break
            history.append(new_G)
            current = new_G
        return history

    # -- enumeration --------------------------------------------------------

    @classmethod
    def enumerate(
        cls,
        max_pattern_nodes: int,
        max_replacement_nodes: int,
        label_alphabet_size: int,
    ) -> Iterator[DirectedGraphRule]:
        """Yield all rules in D(n, m, k).

        See definitions.md B.1: patterns are non-empty weakly connected
        labeled directed graphs. Replacements may be empty and need not
        be connected. Labels from {0, ..., k-1}.

        Args:
            max_pattern_nodes: n, max nodes in P.
            max_replacement_nodes: m, max nodes in Q.
            label_alphabet_size: k, size of label alphabet.
        """
        labels = list(range(label_alphabet_size))
        patterns = list(
            _enumerate_labeled_digraphs(
                max_nodes=max_pattern_nodes,
                labels=labels,
                require_weakly_connected=True,
                require_nonempty=True,
            )
        )
        replacements = list(
            _enumerate_labeled_digraphs(
                max_nodes=max_replacement_nodes,
                labels=labels,
                require_weakly_connected=False,
                require_nonempty=False,
            )
        )

        for P in patterns:
            p_nodes = sorted(P.nodes)
            for Q in replacements:
                q_nodes = sorted(Q.nodes)
                # Reconnection maps: each P-node -> Q-node or STAR
                # (n_q + 1)^|V(P)| possibilities
                targets = q_nodes + [STAR]
                for mapping in itertools.product(targets, repeat=len(p_nodes)):
                    phi = dict(zip(p_nodes, mapping))
                    yield cls(P=P, Q=Q, phi=phi)

    @classmethod
    def enumerate_count(
        cls,
        max_pattern_nodes: int,
        max_replacement_nodes: int,
        label_alphabet_size: int,
    ) -> int:
        """Count |D(n, m, k)| without materializing all rules."""
        total = 0
        for p_size in range(1, max_pattern_nodes + 1):
            n_patterns = _count_labeled_digraphs(
                p_size, label_alphabet_size, weakly_connected=True
            )
            for q_size in range(0, max_replacement_nodes + 1):
                n_replacements = _count_labeled_digraphs(
                    q_size, label_alphabet_size, weakly_connected=False
                )
                n_maps = (q_size + 1) ** p_size
                total += n_patterns * n_replacements * n_maps
        return total

    def __str__(self) -> str:
        p_labels = [self.P.nodes[n]["label"] for n in sorted(self.P.nodes)]
        p_edges = list(self.P.edges)
        q_labels = [self.Q.nodes[n]["label"] for n in sorted(self.Q.nodes)]
        q_edges = list(self.Q.edges)
        phi_str = {k: v for k, v in sorted(self.phi.items())}
        return (
            f"P(labels={p_labels}, edges={p_edges}) -> "
            f"Q(labels={q_labels}, edges={q_edges}), phi={phi_str}"
        )

    def __repr__(self) -> str:
        return f"DirectedGraphRule(|P|={len(self.P)}, |Q|={len(self.Q)})"


# ---------------------------------------------------------------------------
# Graph enumeration helpers
# ---------------------------------------------------------------------------

def _enumerate_labeled_digraphs(
    max_nodes: int,
    labels: list[int],
    require_weakly_connected: bool,
    require_nonempty: bool,
) -> Iterator[nx.DiGraph]:
    """Yield all labeled directed graphs up to max_nodes nodes.

    Nodes are integers 0..n-1. Each node has a 'label' attribute.
    Self-loops are allowed.
    """
    start = 1 if require_nonempty else 0
    for n in range(start, max_nodes + 1):
        if n == 0:
            yield nx.DiGraph()
            continue
        nodes = list(range(n))
        possible_edges = [(i, j) for i in nodes for j in nodes]

        for label_combo in itertools.product(labels, repeat=n):
            for edge_mask in range(2 ** len(possible_edges)):
                G = nx.DiGraph()
                for i, lab in zip(nodes, label_combo):
                    G.add_node(i, label=lab)
                for bit, (u, v) in enumerate(possible_edges):
                    if edge_mask & (1 << bit):
                        G.add_edge(u, v)
                if require_weakly_connected and n > 1:
                    if not nx.is_weakly_connected(G):
                        continue
                yield G


def _count_labeled_digraphs(
    n: int, k: int, weakly_connected: bool
) -> int:
    """Count labeled directed graphs on exactly n nodes with k labels.

    For n=0: returns 1 (the empty graph).
    For n=1: k * 2^1 (label x self-loop option).
    For n=2 weakly connected: k^2 * (2^4 - 2^2) = k^2 * 12.
    For larger n, falls back to enumeration.
    """
    if n == 0:
        return 1
    if n == 1:
        return k * (2 ** 1)

    total_edges = n * n
    total_graphs = (k ** n) * (2 ** total_edges)

    if not weakly_connected:
        return total_graphs

    if n == 2:
        # Disconnected = no inter-node edges (both (0,1) and (1,0) absent).
        # Self-loop configs: 2^2 = 4. Label configs: k^2.
        disconnected = (k ** 2) * (2 ** 2)
        return total_graphs - disconnected

    # For n >= 3, count by enumeration
    labels = list(range(k))
    count = 0
    nodes = list(range(n))
    possible_edges = [(i, j) for i in nodes for j in nodes]
    for label_combo in itertools.product(labels, repeat=n):
        for edge_mask in range(2 ** len(possible_edges)):
            G = nx.DiGraph()
            for i, lab in zip(nodes, label_combo):
                G.add_node(i, label=lab)
            for bit, (u, v) in enumerate(possible_edges):
                if edge_mask & (1 << bit):
                    G.add_edge(u, v)
            if nx.is_weakly_connected(G):
                count += 1
    return count


# ---------------------------------------------------------------------------
# __main__: first contact with directed graph dynamics
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import time

    sys.path.insert(0, ".")

    from src.spark.seed_search import find_minimal_seed_graph
    from src.spark.directed_graph_evolution import DirectedGraphEvolution

    MAX_P = 2
    MAX_Q = 3
    K = 2

    print(f"Directed graph rewriting: D({MAX_P},{MAX_Q},{K})")
    print(f"Computing cardinality...")

    count = DirectedGraphRule.enumerate_count(MAX_P, MAX_Q, K)
    print(f"|D({MAX_P},{MAX_Q},{K})| = {count:,}")

    # Use D(2,2,2) for actual enumeration — D(2,3,2) is 3.2M rules
    MAX_Q_ENUM = 2
    count_small = DirectedGraphRule.enumerate_count(MAX_P, MAX_Q_ENUM, K)
    print(f"\n|D({MAX_P},{MAX_Q_ENUM},{K})| = {count_small:,}")
    print(f"Searching for non-sterile rules in D({MAX_P},{MAX_Q_ENUM},{K})...")

    t0 = time.time()
    n_checked = 0
    n_sterile = 0
    n_active = 0
    first_active = None

    for rule in DirectedGraphRule.enumerate(MAX_P, MAX_Q_ENUM, K):
        n_checked += 1
        seed = find_minimal_seed_graph(rule)
        if seed is None:
            n_sterile += 1
            continue

        n_active += 1

        # Look for a rule that produces edges (not just node growth)
        test_history = rule.evolve(seed, 20)
        has_edges = any(len(G.edges) > 0 for G in test_history[1:])
        grows = len(test_history[-1].nodes) > len(seed.nodes)
        if has_edges and grows and first_active is None:
            first_active = (rule, seed)
            print(f"\nInteresting rule found after checking {n_checked} rules "
                  f"({n_active} active)")
            print(f"  Rule: {rule}")

        if first_active is not None and n_checked >= 200:
            break
        if n_checked >= 2000:
            break

        if n_checked % 500 == 0:
            elapsed = time.time() - t0
            print(f"  Checked {n_checked} rules ({n_active} active, "
                  f"{n_sterile} sterile) [{elapsed:.1f}s]")

    # Fall back to first active rule if no interesting one found
    if first_active is None:
        print("\nNo rule with edge dynamics found. Re-scanning for any active rule...")
        for rule in DirectedGraphRule.enumerate(MAX_P, MAX_Q_ENUM, K):
            seed = find_minimal_seed_graph(rule)
            if seed is not None:
                first_active = (rule, seed)
                print(f"  Rule: {rule}")
                break

    if first_active is None:
        print("No non-sterile rules found!")
        sys.exit(1)

    rule, seed = first_active
    print(f"\nEvolving for 500 steps...")
    evo = DirectedGraphEvolution(rule, seed)
    evo.evolve(500)

    steps = evo.n_steps_evolved
    print(f"  Steps evolved: {steps}")
    print(f"\n  Graph size over time:")
    checkpoints = [0, 1, 2, 5, 10, 50, 100, 200, 500]
    for t in checkpoints:
        if t <= steps:
            G_t = evo.state_graph_at_time(t)
            print(f"    t={t:>4}: |V|={len(G_t.nodes):>4}, |E|={len(G_t.edges):>4}")

    # Compute tau using the distance series
    distances = evo.normalized_distances()
    if len(distances) >= 2:
        from src.spark.characteristic_time import autocorrelation
        import math
        ac = autocorrelation(distances)
        threshold = 1.0 / math.e
        tau = 1
        for k_lag in range(1, len(ac)):
            if ac[k_lag] < threshold:
                tau = max(k_lag, 1)
                break
        print(f"\n  tau = {tau}")
    else:
        print(f"\n  tau: insufficient data (only {len(distances)} steps)")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")
