# Definitions

This document reads top to bottom. Each definition depends on those
before it. The final section states the hypothesis as a formal claim
over the preceding definitions.

The core definitions (§1–§9) are rule-class-agnostic: they are stated
in terms of abstract evolution graphs. Each rule class is specified in
an appendix that defines how it produces evolution graphs. A reader who
does not care about a particular rule class can read §1–§9 and skip
the appendices.


## 1. Evolution graph

An **evolution graph** G is a directed acyclic graph encoding the
causal structure of a discrete rewriting process. It is defined as
follows:

- **Nodes.** Each node is a pair (e, t) where e is an element and t
  is a non-negative integer (the timestep). Each node carries a label
  drawn from a finite label set.

- **Edges.** A directed edge from (a, t) to (b, t+1) means element a
  at time t causally influenced element b at time t+1. Edges connect
  only adjacent timesteps.

"Element" is abstract — it could be a string position, a graph node,
a hyperedge, a cell in a grid, or anything else that participates in
rewrites. The label captures the element's state.

A **rule class** must specify:

1. What elements are (the carrier set).
2. What labels are (the label alphabet).
3. How rewrites produce edges (the causal map from matched and
   unmatched elements at time t to elements at time t+1).
4. What **canonical update order** means (a deterministic rule for
   choosing among multiple applicable rewrites at a single step).

The evolution graph is deterministic under the canonical update order:
given a rule and a seed, the graph is uniquely determined. Section 7
explicitly varies the update order to test causal invariance; all
other sections use the canonical order.


## 2. Spark

A **spark** is a pair (r, s_0) where r is a rule (in some rule class)
and s_0 is a seed configuration.

The **minimal spark** for a rule r is the pair (r, s_0*) where s_0*
is the smallest seed configuration such that applying r to s_0*
produces a non-trivial evolution — meaning the configuration neither
halts nor reaches a fixed point within the first 100 steps.

Note: this criterion is deliberately simple and does not depend on
the characteristic time tau (defined in Section 3), which requires
an already-selected spark to compute. The threshold of 100 steps is
a bootstrap parameter, not a deep constant. Sensitivity to this
choice is reported in experiments.

In practice, we search for s_0* by enumerating seeds of increasing
size. A spark that produces no non-trivial evolution for any seed
up to size s_max is classified as **sterile**. Default: s_max = 2l
(twice the rule description length).

"Smallest" and "size" are defined per rule class: for string
rewriting, it is string length; for graph rewriting, it may be node
count. Each appendix specifies this.


## 3. Characteristic time

The **characteristic time** tau(r, s_0) of a spark measures the
natural timescale of the evolution's dynamics.

**Definition.** Compute the normalized distance d(t) between
consecutive configurations at time t and t+1 for each step.
The characteristic time tau is the smallest lag k such that the
autocorrelation of the sequence d(0), d(1), d(2), ... drops below
1/e:

    autocorr(k) = corr(d(t), d(t+k)) < 1/e

If the autocorrelation never drops below 1/e within the evolution
(indicating periodic or highly regular dynamics), tau is set to the
period length.

The distance function d(t) is defined per rule class. For
configurations representable as symbol strings, d(t) is the Hamming
distance between consecutive configurations, normalized by
configuration size. Each appendix specifies the distance function
for its rule class.

This definition is standard in time series analysis. The
characteristic time normalizes all duration-dependent quantities
below. This prevents fast rules from appearing observer-rich and
slow rules from appearing observer-poor for trivial reasons.


## 4. Observer

An **observer** in an evolution graph G is a connected subgraph S of
G satisfying four criteria simultaneously (strict conjunction) over
a persistence window of at least 10 * tau.


### 4.1 Boundary stability

The **boundary** of S at time t is the set of edges crossing between
nodes inside S and nodes outside S at time t.

**Criterion.** The symmetric difference between the boundary at time
t and the boundary at time t+1, averaged over the persistence window,
is small relative to the total boundary size:

    (1 / W) * sum_{t in window} |B(t) △ B(t+1)| / |B(t)| < epsilon_B

where W is the window length and epsilon_B is the boundary stability
threshold. Default: epsilon_B = 0.3.

Interpretation: the boundary changes by less than 30% per step on
average. The structure maintains its shape.


### 4.2 Internal entropy

The **internal state** of S at time t is the multiset of labels of
all nodes in S at time t.

**Criterion.** The Shannon entropy of the internal state distribution,
computed over a sliding window of tau steps, exceeds a minimum:

    H(internal states over tau window) > epsilon_H

where epsilon_H is the internal entropy threshold.
Default: epsilon_H = 1.0 bit.

Interpretation: the interior is not frozen. It undergoes non-trivial
state transitions. A structure with constant internal state is not an
observer — it is a crystal.


### 4.3 Causal decoupling

For a window of tau steps, compute:
- I_int: the mutual information between the internal state of S at
  time t and the internal state at time t + tau.
- I_ext: the mutual information between the internal state of S at
  time t and the external state (the complement of S) at time t + tau.

**Criterion.**

    I_int / (I_int + I_ext) > epsilon_D

where epsilon_D is the decoupling threshold. Default: epsilon_D = 0.6.

**Estimator.** Mutual information between discrete state-valued
variables is estimated using the plug-in estimator with Miller-Madow
bias correction when the internal state has at most 20 elements.
For larger internal states, where sample counts are insufficient for
reliable MI estimation, we use normalized compression distance (NCD)
as a proxy: NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))
where C denotes the compressed length. The decoupling ratio is then
computed as (1 - NCD_int) / ((1 - NCD_int) + (1 - NCD_ext)), which
preserves the same semantics: higher values indicate greater internal
predictability relative to external influence.

Interpretation: at least 60% of the predictive information about the
structure's future comes from its own past, not from the environment.
The interior is partly its own business.


### 4.4 Self-reference

The evolution graph is a DAG — it has no topological cycles. The
"cycle" in self-reference is spatial, not temporal: the structure's
output causally returns to its own spatial region.

A **self-referential return** in S is a pair of directed paths in the
evolution graph such that:

1. A node (a, t) inside S has a forward causal path, passing only
   through nodes inside S, to a node (b, t') inside S at a later
   time t' > t.

2. The rewrite at time t' that produces content at element b is
   causally downstream of element a at time t.

3. Element b at time t' in turn has a forward causal path, again
   through nodes inside S, to a node (a', t'') where a' occupies
   the same spatial region as the original element a (meaning a' is
   within the spatial extent of S at time t).

The graph path is acyclic — it moves forward in time at every edge.
But the spatial trajectory returns to where it started. The
structure's dynamics feed back into their own spatial region.

"Same spatial region" is defined per rule class: for linear
configurations it means positional proximity; for graph-based
configurations it means graph-theoretic proximity (e.g., within the
subgraph boundary). Each appendix specifies the spatial proximity
criterion.

**Criterion.** At least one self-referential return exists within
the persistence window.

Interpretation: this criterion distinguishes an observer from a mere
persistent pattern. A glider that propagates without internal feedback
is not an observer — its causal paths exit the spatial region and
never return. A structure whose rewrites produce content that causally
re-enters its own region is.


### 4.5 Conjunction

A connected subgraph S is an **observer** if and only if all four
criteria (4.1 through 4.4) are satisfied simultaneously over a
contiguous window of at least 10 * tau steps.

There is no partial credit. No weighting. No scoring function. A
structure either is or is not an observer under this definition.
This strictness is deliberate — see `falsification.md` for what
would motivate relaxing it.


## 5. T_obs

**T_obs(r)** is the earliest time step t such that the evolution
graph G(r, s_0*) contains an observer (as defined in Section 4)
whose persistence window begins at or before t.

If no observer appears within the maximum evolution length N_max,
then T_obs(r) = infinity. Default: N_max = 10000 steps.

For the prevalence study, we report:
- P_obs(C): the fraction of rules in class C where T_obs is finite.
- The distribution of T_obs values over rules where it is finite.


## 6. Ruliad-like coherence

A rule r exhibits **ruliad-like coherence** at evolution length n if
its evolution graph is invariant under change of update order.

**Operational test.** Given a spark (r, s_0*) and evolution length n:

1. Sample k distinct update orders uniformly at random. At each step
   where multiple rewrites are applicable, randomly choose which to
   apply first. Default: k = 50.

2. For each update order, construct the evolution graph G_j up to
   step n.

3. For all pairs (G_j, G_k), test whether the causal graphs are
   isomorphic as labeled DAGs. Since full DAG isomorphism is
   GI-complete, we use a canonical hash: sort nodes by (time,
   element-index), serialize the labeled edge list, and compute a
   cryptographic hash. For evolution graphs where the node labeling
   by (element, time, label) is rich enough, this hash is effectively
   a complete invariant — non-isomorphic graphs produce distinct
   hashes with overwhelming probability. Two graphs are deemed
   isomorphic if and only if their canonical hashes match.

4. The rule exhibits ruliad-like coherence at length n if all
   sampled pairs are isomorphic.

This is a statistical test, not a proof. It can produce false
positives (a rule that appears invariant under 50 samples but fails
under the 51st). It cannot produce false negatives. We report the
sample size k alongside all results.

**Note.** Causal invariance is Wolfram's primary criterion for
physics-like behavior. It corresponds to confluence in rewriting
theory — the property that the result is independent of the order
in which rewrites are applied. Most rewriting systems are not
confluent. This is the expensive property.


## 7. T_rul

**T_rul(r)** is the earliest evolution length n such that r exhibits
ruliad-like coherence (as defined in Section 6) at length n.

If no coherence is detected within N_max steps under k sampled
orderings, then T_rul(r) = infinity.

For the prevalence study, we report:
- P_rul(C): the fraction of rules in class C where T_rul is finite.
- The distribution of T_rul values over rules where it is finite.


## 8. Null model

To verify that the observer criteria are not trivially satisfied by
arbitrary graph structure, we define a **null model**:

For each evolution graph G(r, s_0*) that produces an observer,
generate a random DAG using the **configuration model**: matched
node count, edge count, and degree sequence. This is the stronger
null — it preserves local connectivity structure, making it more
likely to accidentally satisfy observer criteria than an Erdos-Renyi
graph would. If the observer criteria still separate rewriting
graphs from configuration model nulls, the criteria detect rewriting
dynamics specifically, not just degree-regular subgraph structure.

Apply the observer detection algorithm to each random graph.

Report **P_null**: the fraction of random graphs that contain a
structure satisfying all four observer criteria.

If P_null is comparable to P_obs, the observer definition is too
loose and must be tightened. If P_null is negligible compared to
P_obs, the definition captures genuine structure produced by the
rewriting dynamics, not graph-theoretic accidents.

The null model comparison is reported alongside every prevalence
result. It is not optional.


## 9. The formal claim

**Cheap Observer Hypothesis.** For a rule class C with sufficient
description length:

1. **Prevalence.** P_obs(C) >> P_rul(C). The fraction of rules
   producing observers vastly exceeds the fraction producing
   ruliad-like coherence.

2. **Ordering.** Among rules where both T_obs and T_rul are finite,
   P(T_obs < T_rul) > 1 - delta for small delta. Observers appear
   first in almost all cases.

3. **Non-triviality.** P_obs(C) >> P_null. The observer prevalence
   is not an artifact of loose definitions.

4. **Robustness.** Claims (1) and (2) hold under reasonable
   variation of the thresholds epsilon_B, epsilon_H, epsilon_D, and
   the persistence window multiplier.

**Current status.** Tested on binary string rewriting C(8), where
P_obs = 0.097% (unique) and P_rul(genuine) = 0%. The sets are
completely disjoint — no rule has both finite T_obs and finite
T_rul. The ordering claim (2) is vacuously true. The full test
requires a rule class where both properties can be finite. See
Appendix A for complete string rewriting results and Appendix B for
the next planned rule class.


---


## Appendix A: String rewriting

This appendix defines binary string rewriting as a rule class and
specifies how it produces evolution graphs in the framework of §1–§9.
Results are final.


### A.1 Rule class

A **string rewriting rule** r is a pair (L, R) where L and R are
non-empty strings over the alphabet {0, 1}. At each step, the rule
replaces one occurrence of L in the current string with R.

A **rule class** C(l) is the set of all string rewriting rules where
|L| + |R| <= l. The parameter l controls the description length of
the rule — its Kolmogorov cost.

For l = 4 (e.g., L and R are each at most 2 symbols), C(4) contains
a finite, enumerable set of rules. Its exact cardinality is computed
as follows: for each pair of lengths (|L|, |R|) with |L| >= 1,
|R| >= 1, and |L| + |R| <= 4, we count all binary strings of those
lengths. The six (|L|, |R|) bins are (1,1), (1,2), (1,3), (2,1),
(2,2), (3,1), contributing 4 + 8 + 16 + 8 + 16 + 16 = 68 rules.
The cardinality |C(4)| = 68.


### A.2 Elements, labels, and canonical order

- **Elements** are string positions: element e = i means position i
  in the string.
- **Labels** are drawn from the binary alphabet {0, 1}. The label of
  node (i, t) is the symbol s_t[i].
- **Canonical update order** is leftmost-match: when multiple
  occurrences of L exist at some step, the leftmost occurrence is
  rewritten first.


### A.3 Evolution graph construction

Given a spark (r, s_0), the evolution is the sequence of strings
s_0, s_1, s_2, ... produced by repeatedly applying r under
leftmost-match ordering.

The **evolution graph** G(r, s_0) is a directed acyclic graph:

- **Nodes.** Each node (i, t) represents position i in the string at
  time t. The node's label is the symbol s_t[i].

- **Edges.** A directed edge connects (i, t) to (j, t+1) if position
  i at time t causally influenced position j at time t+1. Specifically:
  - If position i was part of the matched occurrence of L at time t,
    it has edges to all positions in the inserted R at time t+1.
  - If position i was not part of the match, it has an edge to its
    shifted position at time t+1 (identity propagation).

This graph encodes both temporal and spatial structure. A contiguous
region of the graph corresponds to a spatiotemporal region of the
string's evolution. Locality, influence, and boundedness are all
readable from the graph.


### A.4 Rule-class-specific definitions

- **Seed size** for minimal spark search: string length. s_max = 2l.
- **Distance function** for characteristic time: Hamming distance
  between consecutive strings, normalized by string length.
- **Internal state** ordering: labels of nodes in S at time t, read
  left to right (positional order).
- **Spatial proximity** for self-reference: |i' - i| < the width of
  S at time t.
- **Canonical hash node ordering** for causal invariance: sort by
  (time, position). Node labeling by (position, time, symbol).


### A.5 Results summary

| Class | Rules | Active | Observers | Near-miss (3/4) | P_obs  |
|-------|-------|--------|-----------|-----------------|--------|
| C(4)  | 68    | 20     | 0         | 0               | 0%     |
| C(6)  | 516   | 174    | 0         | 0               | 0%     |
| C(8)  | 3076  | 1026   | 2         | 8               | 0.195% |

Corrected prevalence (unique structures): P_obs = 1/1026 = 0.097%.
The two observers are 01->10001 and 10->01110 — a single distinct
structure and its 0<->1 bit-flip mirror.

Observer properties:
- |L| = 2, |R| = 5 (growth +3 per step)
- T_obs = 310 (observer appears after 310 evolution steps)
- tau = 4 (characteristic time)
- Sawtooth match dynamics: period-3 oscillation, net drift +1/3

Causal invariance:

| Metric                        | Count | Fraction |
|-------------------------------|-------|----------|
| Vacuous T_rul = 0             | 314   | 30.6%    |
| Genuine finite T_rul          | 0     | 0%       |
| T_rul = infinity              | 712   | 69.4%    |

No rule in C(8) has both finite T_obs and finite T_rul. The sets are
completely disjoint. The T_obs vs T_rul scatter plot is degenerate.

Sensitivity analysis:

| Parameter       | Default | Observer range | Assessment       |
|-----------------|---------|----------------|------------------|
| epsilon_D       | 0.60    | 0.52 – >0.70   | Most robust      |
| epsilon_B       | 0.30    | 0.25 – 0.30+   | 17% margin       |
| epsilon_H       | 1.00    | <0.50 – 1.25   | 50% margin       |
| persistence     | 10      | 5 – 10         | Tightest axis    |

Full results: `experiments/string_rewriting/results/`.

**Appendix A is COMPLETE. These results are final.**


### A.6 Structural limitation

Single-rule binary string rewriting cannot test the full Cheap
Observer Hypothesis. Rules complex enough for observers inevitably
produce multiple matches per step, making causal invariance
non-trivial. Rules simple enough for confluence are too simple for
observers. In 1D string rewriting with a single rule, these demands
are irreconcilable. See
`experiments/string_rewriting/results/conclusion.md` for full
analysis.


## Appendix B: Directed graph rewriting (placeholder)

This appendix will define directed graph rewriting as the second
rule class. The Game of Intelligence engine
(`experiments/directed_graph/engine/`) implements this rule class.

The `src/observer/` and `src/ruliad/` modules are rule-class-agnostic
and operate on evolution graphs. A new rule class needs only to
implement the evolution graph protocol defined in §1:

1. Specify the element type and label alphabet.
2. Define how rewrites produce causal edges.
3. Define a canonical update order.
4. Implement the distance function for characteristic time (§3).
5. Define spatial proximity for self-reference (§4.4).

The remaining definitions (observer criteria, T_obs, causal
invariance, T_rul, null model, formal claim) apply without
modification.

Content forthcoming.
