# Counterexample Notes

Running commentary on what counterexamples and edge cases teach us
about the observer definitions.


## 1. Trivial boundary stability in uniform-growth rules

**Source:** C(4) sweep (all 20 active rules).

**Observation:** Boundary stability scores 0.01–0.05 for every active
C(4) rule, well below the 0.3 threshold. This is not because the
candidates have genuinely stable boundaries — it is because the
string grows uniformly, so the boundary set barely changes between
timesteps by construction. Any fixed rectangular subgraph in a
uniformly growing string will trivially pass boundary stability.

**Concern for larger rule classes:** When observers are found in C(6)+,
verify that boundary stability passes for non-trivial reasons — meaning
the boundary is stable despite nearby rewrites that could disrupt it,
not merely because no rewrites occur near the boundary.

**Possible tightening:** Require that the boundary region contain at
least one rewrite event within the persistence window. This would
exclude candidates whose stability is due to spatial isolation from
dynamics rather than genuine structural persistence.


## 2. Trivial self-reference in fixed-match-site rules

**Source:** C(4) sweep (all 20 active rules).

**Observation:** Self-reference scores 1.0 for every active C(4) rule.
All these rules have |L| = 1, so the leftmost match is always at or
near position 0. Causal paths from the match site trivially return to
the same spatial region because the match site never moves.

**Concern for larger rule classes:** In rules where the match site
shifts across the string (|L| >= 2 with non-trivial overlap), self-
reference becomes a real test. But for any rule where the match site
is spatially anchored, self-reference is free.

**No tightening recommended yet.** Self-reference is correctly defined
as a spatial return, and a fixed match site does satisfy it. The
criterion will become discriminating in rule classes with mobile
rewrite sites. Monitor in C(6).
