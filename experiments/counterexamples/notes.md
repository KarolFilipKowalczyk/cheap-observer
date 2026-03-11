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


## 3. Drift-limited persistence in C(8) observers

**Source:** C(8) sensitivity check (experiments/string_rewriting/results/c8_sensitivity.md).

**Observation:** The C(8) observers (01->10001 / 10->01110) pass all
four criteria at persistence_multiplier=10 (window=40 steps) but fail
at persistence_multiplier=12 (window=48 steps). The sawtooth match
dynamics drift the active zone by +1/3 per step, covering ~13
positions per 40-step window and ~16 per 48-step window. The subgraph
eventually cannot contain the drifting match site.

At persistence_multiplier=8 (window=32 steps), 6 observers exist —
three times the default count. The structures have genuine internal
dynamics but limited spatial persistence.

**Concern for the claim:** Persistence_multiplier is the tightest axis
in the sensitivity analysis. If the default multiplier of 10 is set
even slightly higher (12), C(8) produces zero observers. This is not a
threshold-tuning artifact — it reflects a real physical property: the
sawtooth dynamics drift faster than the structure can sustain itself.

**Implication:** C(10)+ rules with slower drift (lower net match-site
velocity) should produce observers with longer persistence. The
persistence bottleneck is a property of C(8)'s limited rule complexity,
not of the definitions. Monitor whether larger rule classes break this
bottleneck.


## 4. Mirror symmetry double-counting

**Source:** C(8) sweep and sensitivity check.

**Observation:** The two C(8) observers (01->10001, 10->01110) are
0<->1 bit-flip mirrors with identical scores, tau, and T_obs. The
eight 3/4 near-misses also form four mirror pairs. Binary string
rewriting is symmetric under bit flip, so every observer automatically
has a mirror partner.

**Concern for prevalence:** Reporting P_obs = 2/1026 double-counts.
The true number of distinct observer structures is 1, giving
P_obs = 1/1026 = 0.097% unique. Both values should be reported
alongside each other: 2/1026 (with mirrors) or 1/1026 (unique).

**No tightening needed.** This is a reporting correction, not a
definition issue. The bit-flip symmetry is a feature of the rule class,
not an artifact of the criteria.
