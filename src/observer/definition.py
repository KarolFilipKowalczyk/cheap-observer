"""
The formal contract for observer detection.

This file defines what an observer is. All detection code in src/observer/
implements against these types, thresholds, and conjunction rules. The
definitions here translate definitions.md Sections 5.1-5.5 into code.

An observer is a connected subgraph of the evolution graph satisfying
four criteria simultaneously (strict conjunction) over a persistence
window of at least persistence_multiplier * tau steps. There is no
partial credit. No weighting. No scoring function.

See: definitions.md Section 5.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Sequence, runtime_checkable


# ---------------------------------------------------------------------------
# Evolution graph types (placeholder protocols)
#
# The concrete implementations depend on the evolution graph format from
# definitions.md Section 3. A node (i, t) represents position i in the
# string at time t, labeled with symbol s_t[i]. A directed edge connects
# (i, t) to (j, t+1) if position i causally influenced position j.
# ---------------------------------------------------------------------------

@runtime_checkable
class Node(Protocol):
    """A node in the evolution graph.

    Represents position i in the string at time t with label s_t[i].
    See definitions.md Section 3: "Each node (i, t) represents position i
    in the string at time t. The node's label is the symbol s_t[i]."
    """

    @property
    def position(self) -> int:
        """Spatial position i in the string."""
        ...

    @property
    def time(self) -> int:
        """Time step t in the evolution."""
        ...

    @property
    def label(self) -> str:
        """Symbol s_t[i] at this position and time."""
        ...


@runtime_checkable
class EvolutionGraph(Protocol):
    """The causal structure of a spark's evolution.

    A directed acyclic graph where nodes are (position, time) pairs and
    edges encode causal influence between consecutive time steps.

    See definitions.md Section 3: "The evolution graph G(r, s_0) encodes
    the causal structure of this evolution. It is a directed acyclic graph."
    """

    def nodes_at_time(self, t: int) -> Sequence[Node]:
        """All nodes at time step t, ordered by position."""
        ...

    def successors(self, node: Node) -> Sequence[Node]:
        """Nodes at time t+1 causally influenced by this node."""
        ...

    def predecessors(self, node: Node) -> Sequence[Node]:
        """Nodes at time t-1 that causally influenced this node."""
        ...

    @property
    def max_time(self) -> int:
        """The latest time step in the graph."""
        ...


@runtime_checkable
class Subgraph(Protocol):
    """A connected subgraph of the evolution graph.

    Represents a spatiotemporal region — a candidate observer. Must be
    connected in the underlying undirected graph. The subgraph knows
    which nodes are inside it and can identify its boundary edges at
    each time step.

    See definitions.md Section 5: "An observer in an evolution graph G
    is a connected subgraph S of G."
    """

    def contains(self, node: Node) -> bool:
        """Whether the given node is inside this subgraph."""
        ...

    def nodes_at_time(self, t: int) -> Sequence[Node]:
        """All nodes inside this subgraph at time step t, ordered by position."""
        ...

    def boundary_edges_at_time(self, t: int) -> set[tuple[Node, Node]]:
        """Edges crossing between inside and outside at time t.

        See definitions.md Section 5.1: "The boundary of S at time t is
        the set of edges crossing between nodes inside S and nodes
        outside S at time t."
        """
        ...

    def internal_state_at_time(self, t: int) -> str:
        """The string of labels of all nodes inside S at time t, left to right.

        See definitions.md Section 5.2: "The internal state of S at time t
        is the string of labels of all nodes in S at time t, read left to
        right."
        """
        ...

    def width_at_time(self, t: int) -> int:
        """Spatial extent of the subgraph at time t (max position - min position).

        Used by the self-reference criterion to determine whether a causal
        path returns to the same spatial region. See definitions.md
        Section 5.4: "|i' - i| < the width of S at time t".
        """
        ...

    @property
    def time_span(self) -> tuple[int, int]:
        """(earliest time, latest time) covered by this subgraph."""
        ...

    @property
    def parent_graph(self) -> EvolutionGraph:
        """The evolution graph this subgraph belongs to."""
        ...


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObserverCriteria:
    """Thresholds for the four observer criteria and the persistence window.

    All defaults match definitions.md Sections 5.1-5.5.

    The persistence_multiplier controls the minimum window length: a
    subgraph must satisfy all four criteria simultaneously over a
    contiguous window of at least persistence_multiplier * tau steps.

    See definitions.md Section 5.5: "A connected subgraph S is an observer
    if and only if all four criteria (5.1 through 5.4) are satisfied
    simultaneously over a contiguous window of at least 10 * tau steps."
    """

    epsilon_B: float = 0.3
    """Boundary stability threshold (definitions.md Section 5.1).
    The average fractional boundary change per step must be below this."""

    epsilon_H: float = 1.0
    """Internal entropy threshold in bits (definitions.md Section 5.2).
    Shannon entropy of internal states over a tau-window must exceed this."""

    epsilon_D: float = 0.6
    """Causal decoupling threshold (definitions.md Section 5.3).
    I_int / (I_int + I_ext) must exceed this."""

    persistence_multiplier: int = 10
    """Minimum persistence window is persistence_multiplier * tau steps
    (definitions.md Section 5.5). Default: 10."""


DEFAULT_CRITERIA = ObserverCriteria()


# ---------------------------------------------------------------------------
# Scoring functions (stubs)
#
# Each function takes a subgraph and a time window and returns a score.
# The actual implementations live in the four metric files:
#   boundary_stability.py, internal_entropy.py,
#   causal_decoupling.py, self_reference.py
#
# These stubs define the contract: signature, return semantics, and the
# precise mathematical definition from definitions.md.
# ---------------------------------------------------------------------------

def boundary_stability_score(subgraph: Subgraph, t_start: int, t_end: int) -> float:
    """Compute the boundary stability score for a subgraph over a time window.

    Returns the average fractional boundary change per step:

        (1 / W) * sum_{t=t_start}^{t_end-1} |B(t) △ B(t+1)| / |B(t)|

    where W = t_end - t_start is the window length, B(t) is the set of
    boundary edges at time t, and △ denotes symmetric difference.

    Lower values indicate greater stability. The subgraph passes the
    boundary stability criterion if this score is below epsilon_B.

    A score of 0.0 means the boundary is perfectly static.
    A score of 1.0 means the boundary is completely replaced each step.

    If |B(t)| = 0 for any step in the window (the subgraph has no
    boundary, meaning it spans the entire string), that step contributes
    0.0 to the average.

    See definitions.md Section 5.1.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step of the window (inclusive).
        t_end: Last time step of the window (inclusive).

    Returns:
        The average fractional boundary change. Lower is more stable.
    """
    raise NotImplementedError(
        "Implemented in src/observer/boundary_stability.py"
    )


def internal_entropy_score(
    subgraph: Subgraph, t_start: int, t_end: int, tau: int
) -> float:
    """Compute the internal entropy score for a subgraph over a time window.

    Returns the minimum Shannon entropy of the internal state distribution
    over all tau-length sliding windows within [t_start, t_end]:

        min over w in sliding_windows:
            H({internal_state(t) : t in w})

    where H is Shannon entropy in bits and each sliding window w contains
    tau consecutive time steps.

    The internal state at time t is the string of labels of all nodes
    inside S at time t, read left to right. The entropy is computed over
    the distribution of these strings within the window — that is, over
    the empirical frequency of distinct internal state strings.

    Higher values indicate more dynamic internals. The subgraph passes
    the internal entropy criterion if this score exceeds epsilon_H.

    A score of 0.0 means the internal state is constant (a crystal).
    The maximum depends on the number of distinct states in the window.

    See definitions.md Section 5.2.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step of the window (inclusive).
        t_end: Last time step of the window (inclusive).
        tau: Characteristic time of the evolution, used as the sliding
            window length for entropy computation.

    Returns:
        The minimum Shannon entropy (in bits) across all tau-windows.
    """
    raise NotImplementedError(
        "Implemented in src/observer/internal_entropy.py"
    )


def causal_decoupling_score(
    subgraph: Subgraph, t_start: int, t_end: int, tau: int
) -> float:
    """Compute the causal decoupling score for a subgraph over a time window.

    Returns the decoupling ratio:

        I_int / (I_int + I_ext)

    averaged over all valid time offsets within the window, where:
    - I_int is the mutual information between the internal state of S at
      time t and the internal state at time t + tau.
    - I_ext is the mutual information between the internal state of S at
      time t and the external state (complement of S) at time t + tau.

    The estimator depends on internal state length:
    - If the internal state is at most 20 symbols, use the plug-in
      estimator with Miller-Madow bias correction.
    - For longer states, use normalized compression distance (NCD) as a
      proxy: the ratio becomes (1 - NCD_int) / ((1 - NCD_int) + (1 - NCD_ext)).

    Higher values indicate greater self-determination. The subgraph passes
    the causal decoupling criterion if this score exceeds epsilon_D.

    A score of 1.0 means the structure's future is entirely self-determined.
    A score of 0.5 means internal and external influence are equal.
    A score of 0.0 means the structure is entirely externally driven.

    See definitions.md Section 5.3.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step of the window (inclusive).
        t_end: Last time step of the window (inclusive).
        tau: Characteristic time, used as the temporal offset for MI
            computation and to select the estimator.

    Returns:
        The decoupling ratio I_int / (I_int + I_ext), averaged over
        the window.
    """
    raise NotImplementedError(
        "Implemented in src/observer/causal_decoupling.py"
    )


def self_reference_score(subgraph: Subgraph, t_start: int, t_end: int) -> float:
    """Compute the self-reference score for a subgraph over a time window.

    Returns the number of self-referential returns found within the window.

    A self-referential return is a pair of directed paths in the evolution
    graph such that:

    1. A node (i, t) inside S has a forward causal path, passing only
       through nodes inside S, to a node (j, t') inside S at a later
       time t' > t.

    2. The rewrite at time t' that produces content at position j is
       causally downstream of position i at time t.

    3. Position j at time t' has a forward causal path, again through
       nodes inside S, to a node (i', t'') where i' occupies the same
       spatial region as position i: |i' - i| < width of S at time t.

    The graph paths are acyclic (forward in time at every edge). The
    spatial trajectory returns to where it started. The structure's
    dynamics feed back into their own spatial region.

    The subgraph passes the self-reference criterion if this score is
    >= 1.0 (at least one self-referential return exists).

    See definitions.md Section 5.4.

    Args:
        subgraph: The candidate observer subgraph.
        t_start: First time step of the window (inclusive).
        t_end: Last time step of the window (inclusive).

    Returns:
        The count of distinct self-referential returns (as a float).
        A value >= 1.0 means the criterion is satisfied.
    """
    raise NotImplementedError(
        "Implemented in src/observer/self_reference.py"
    )


# ---------------------------------------------------------------------------
# Conjunction logic
# ---------------------------------------------------------------------------

def is_observer(
    subgraph: Subgraph,
    tau: int,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
) -> bool:
    """Test whether a subgraph qualifies as an observer.

    A connected subgraph S is an observer if and only if all four criteria
    are satisfied simultaneously over a contiguous window of at least
    persistence_multiplier * tau steps. Strict conjunction. No partial
    credit.

    The function searches for any contiguous window of the required length
    within the subgraph's time span where all four scores pass their
    thresholds. If at least one such window exists, the subgraph is an
    observer.

    See definitions.md Section 5.5: "A connected subgraph S is an observer
    if and only if all four criteria (5.1 through 5.4) are satisfied
    simultaneously over a contiguous window of at least 10 * tau steps."

    Args:
        subgraph: A connected subgraph of the evolution graph.
        tau: Characteristic time of the evolution (definitions.md Section 4).
        criteria: Threshold values for the four criteria.

    Returns:
        True if all four criteria are satisfied simultaneously over at
        least one contiguous window of persistence_multiplier * tau steps.
        False otherwise.
    """
    min_window = criteria.persistence_multiplier * tau
    t_first, t_last = subgraph.time_span

    if t_last - t_first < min_window:
        return False

    # Slide a window of length min_window across the subgraph's time span.
    # Return True as soon as we find a window where all four criteria pass.
    for t_start in range(t_first, t_last - min_window + 1):
        t_end = t_start + min_window

        b_score = boundary_stability_score(subgraph, t_start, t_end)
        if b_score >= criteria.epsilon_B:
            continue

        h_score = internal_entropy_score(subgraph, t_start, t_end, tau)
        if h_score <= criteria.epsilon_H:
            continue

        d_score = causal_decoupling_score(subgraph, t_start, t_end, tau)
        if d_score <= criteria.epsilon_D:
            continue

        s_score = self_reference_score(subgraph, t_start, t_end)
        if s_score < 1.0:
            continue

        return True

    return False


def detect_observers(
    evolution_graph: EvolutionGraph,
    tau: int,
    criteria: ObserverCriteria = DEFAULT_CRITERIA,
) -> list[Subgraph]:
    """Find all observers in an evolution graph.

    Scans the evolution graph for connected subgraphs satisfying
    is_observer. Returns them sorted by earliest appearance time
    (the start of their first qualifying persistence window).

    This is the entry point for computing T_obs: the earliest time step
    at which the evolution contains an observer.

    See definitions.md Section 6: "T_obs(r) is the earliest time step t
    such that the evolution graph G(r, s_0*) contains an observer whose
    persistence window begins at or before t."

    The candidate enumeration strategy is not specified by this contract.
    Implementations may use spatial clustering, sliding windows, or
    exhaustive search. The only requirement is correctness: every returned
    subgraph must satisfy is_observer, and no observer present in the
    graph should be missed within the search resolution.

    Args:
        evolution_graph: The full evolution graph G(r, s_0).
        tau: Characteristic time of the evolution (definitions.md Section 4).
        criteria: Threshold values for the four criteria.

    Returns:
        List of Subgraph objects satisfying all four observer criteria,
        sorted by the earliest time step of their first qualifying
        persistence window. Empty list if no observers are found.
    """
    raise NotImplementedError(
        "Implemented in src/observer/detect.py. "
        "The enumeration strategy for candidate subgraphs is defined there, "
        "not here. This contract only specifies what must be returned."
    )
