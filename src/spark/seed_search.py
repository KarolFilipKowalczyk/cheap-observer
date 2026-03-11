"""
Minimal seed finder.

Given a rule, find the shortest seed that produces non-trivial evolution:
the configuration neither halts nor reaches a fixed point within the first
100 steps. Returns None if the rule is sterile.

Supports both string rewriting rules and directed graph rewriting rules.

See definitions.md §2 (abstract), Appendix A.4 (string), Appendix B.4 (graph).
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from src.spark.rule_classes.string_rewriting import StringRewritingRule
    from src.spark.rule_classes.directed_graph import DirectedGraphRule

DEFAULT_BOOTSTRAP_STEPS = 100


# ---------------------------------------------------------------------------
# String rewriting seeds
# ---------------------------------------------------------------------------

def is_non_trivial(rule: StringRewritingRule, seed: str, steps: int = DEFAULT_BOOTSTRAP_STEPS) -> bool:
    """Test whether a spark (rule, seed) produces non-trivial evolution.

    Non-trivial means the string neither vanishes (becomes empty) nor
    reaches a fixed point (stops changing) within the given number of
    steps.

    See definitions.md §2.

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
    """Find the minimal spark for a string rewriting rule.

    Enumerates binary seeds of increasing length and returns the shortest
    one producing non-trivial evolution. Returns None if no such seed
    exists up to the maximum length (the rule is sterile).

    See definitions.md §2 and Appendix A.4.

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


# ---------------------------------------------------------------------------
# Directed graph rewriting seeds
# ---------------------------------------------------------------------------

def _graph_signature(G: nx.DiGraph) -> tuple:
    """A cheap structural signature for fixed-point detection.

    Captures (node_count, edge_count, sorted_label_multiset,
    sorted_degree_sequence). Two isomorphic graphs produce the same
    signature. Non-isomorphic graphs usually produce different ones.
    """
    n = len(G.nodes)
    e = len(G.edges)
    labels = tuple(sorted(G.nodes[v]["label"] for v in G.nodes))
    degrees = tuple(sorted(
        (G.in_degree(v), G.out_degree(v)) for v in G.nodes
    ))
    return (n, e, labels, degrees)


def is_non_trivial_graph(
    rule: DirectedGraphRule,
    seed: nx.DiGraph,
    steps: int = DEFAULT_BOOTSTRAP_STEPS,
) -> bool:
    """Test whether a spark (rule, seed_graph) produces non-trivial evolution.

    Non-trivial means the state graph neither becomes empty (no nodes),
    halts (no match found), nor reaches a structural fixed point (the
    graph's signature stops changing) within the given number of steps.

    See definitions.md §2 and Appendix B.

    Args:
        rule: The directed graph rewriting rule.
        seed: The seed graph.
        steps: Number of steps to test.

    Returns:
        True if the evolution is still changing after the given steps.
    """
    current = seed
    next_id = [max(seed.nodes) + 1 if seed.nodes else 0]
    prev_sig = _graph_signature(current)
    unchanged_count = 0
    # If signature unchanged for 10 consecutive steps, treat as fixed point
    FIXED_POINT_THRESHOLD = 10

    for _ in range(steps):
        new_G, match, _ = rule.apply(current, order="canonical", _next_id=next_id)
        if match is None:
            return False
        if len(new_G.nodes) == 0:
            return False
        sig = _graph_signature(new_G)
        if sig == prev_sig:
            unchanged_count += 1
            if unchanged_count >= FIXED_POINT_THRESHOLD:
                return False
        else:
            unchanged_count = 0
        prev_sig = sig
        current = new_G
    return True


def _enumerate_seed_graphs(
    n_nodes: int, label_alphabet_size: int
) -> list[nx.DiGraph]:
    """Generate all weakly connected labeled directed graphs on exactly
    n_nodes nodes with labels from {0, ..., k-1}. Self-loops allowed.

    Seeds must be weakly connected to ensure a non-degenerate starting
    configuration.
    """
    if n_nodes == 0:
        return []

    labels = list(range(label_alphabet_size))
    nodes = list(range(n_nodes))
    possible_edges = [(i, j) for i in nodes for j in nodes]
    seeds: list[nx.DiGraph] = []

    for label_combo in itertools.product(labels, repeat=n_nodes):
        for edge_mask in range(2 ** len(possible_edges)):
            G = nx.DiGraph()
            for i, lab in zip(nodes, label_combo):
                G.add_node(i, label=lab)
            for bit, (u, v) in enumerate(possible_edges):
                if edge_mask & (1 << bit):
                    G.add_edge(u, v)
            if n_nodes > 1 and not nx.is_weakly_connected(G):
                continue
            seeds.append(G)

    return seeds


def find_minimal_seed_graph(
    rule: DirectedGraphRule,
    max_seed_nodes: int | None = None,
    steps: int = DEFAULT_BOOTSTRAP_STEPS,
) -> nx.DiGraph | None:
    """Find the minimal spark for a directed graph rewriting rule.

    Enumerates weakly connected labeled directed graphs of increasing
    node count. Returns the smallest seed producing non-trivial evolution.
    Returns None if no such seed exists (the rule is sterile).

    See definitions.md §2 and Appendix B.4: "Seed size for minimal spark
    search: number of nodes |V(G_0)|. s_max = n + m."

    Args:
        rule: The directed graph rewriting rule.
        max_seed_nodes: Maximum seed node count. Defaults to
            |V(P)| + |V(Q)| (pattern + replacement size).
        steps: Number of evolution steps to test per seed.

    Returns:
        The smallest seed graph producing non-trivial evolution, or None
        if the rule is sterile.
    """
    if max_seed_nodes is None:
        max_seed_nodes = len(rule.P) + len(rule.Q)
    # Ensure we try at least up to |V(P)| nodes (need enough for a match)
    max_seed_nodes = max(max_seed_nodes, len(rule.P))

    k = max(
        (rule.P.nodes[n]["label"] for n in rule.P.nodes),
        default=0,
    ) + 1
    if rule.Q.nodes:
        k = max(k, max(rule.Q.nodes[n]["label"] for n in rule.Q.nodes) + 1)

    for n_nodes in range(1, max_seed_nodes + 1):
        for seed in _enumerate_seed_graphs(n_nodes, k):
            if is_non_trivial_graph(rule, seed, steps):
                return seed

    return None
