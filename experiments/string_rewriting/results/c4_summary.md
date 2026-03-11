# C(4) Results Summary

## Rule class

|C(4)| = 68 rules (all binary string rewriting rules with |L| + |R| <= 4).

| |L| | |R| | Count |
|-----|-----|-------|
| 1   | 1   | 4     |
| 1   | 2   | 8     |
| 1   | 3   | 16    |
| 2   | 1   | 8     |
| 2   | 2   | 16    |
| 3   | 1   | 16    |


## Sterile vs active

- **Sterile:** 48 rules (reach fixed point or vanish for all seeds up to length 8)
- **Active:** 20 rules (all growing: |R| > |L|)
- **Length-preserving or shrinking with non-trivial dynamics:** 0

All active C(4) rules have |L| = 1, meaning they match a single symbol
and replace it with a longer string. The match always exists (there is
always a 0 or a 1), so the string grows by exactly |R| - 1 symbols per
step.


## Observer detection: uniform 2/4 failure

Every active rule produces the same failure pattern. No rule in C(4)
has T_obs finite.

| Criterion           | Score range | Threshold | Result | Reason                         |
|---------------------|-------------|-----------|--------|--------------------------------|
| Boundary stability  | 0.01–0.05   | < 0.3     | PASS   | Trivial: uniform growth        |
| Self-reference      | 1.0         | >= 1.0    | PASS   | Trivial: match site is fixed   |
| Internal entropy    | 0.000       | > 1.0 bit | FAIL   | Interior is frozen             |
| Causal decoupling   | 0.500       | > 0.6     | FAIL   | No self-predictability (50/50) |


## Why the criteria fail

All active C(4) rules produce one of three string patterns:

1. **Uniform:** all-zeros or all-ones (e.g., `0 -> 00`, `1 -> 11`)
2. **One-boundary:** one symbol type grows, the other stays at one
   position (e.g., `0 -> 01` produces `01111...1`)
3. **Periodic:** perfectly alternating (e.g., `0 -> 010` produces
   `010101...01`)

In all cases, any rectangular subgraph has a constant or periodic
internal state over time. Shannon entropy over a tau-length window is
zero because the same internal string repeats at every timestep. With
zero entropy, causal decoupling defaults to 0.5 (uninformative).

Boundary stability and self-reference pass trivially: boundaries don't
change because the string grows uniformly, and causal paths return to
their spatial region because the match site stays near position 0.


## Conclusion

C(4) is below the complexity threshold for observers. The rules are too
simple to produce spatially heterogeneous dynamics. Increasing evolution
length will not help — the string patterns are structurally uniform at
every timescale.

The experiment is not wasted: it establishes that the detection pipeline
works correctly and that the criteria correctly reject trivial dynamics.
The failing criteria (internal entropy, causal decoupling) are the ones
that should fail for uniform strings, confirming the definitions are not
vacuously satisfied.

Next step: C(6), which includes multi-symbol matches (|L| >= 2) that
can produce spatially heterogeneous rewrites.
