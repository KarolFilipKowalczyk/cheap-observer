# C(6) Results Summary

## Rule class

|C(6)| = 516 rules (all binary string rewriting rules with |L| + |R| <= 6).

| |L| | |R| | Count | Type              |
|-----|-----|-------|-------------------|
| 1   | 1   | 4     | length-preserving |
| 1   | 2   | 8     | growing           |
| 1   | 3   | 16    | growing           |
| 1   | 4   | 32    | growing           |
| 1   | 5   | 64    | growing           |
| 2   | 1   | 8     | shrinking         |
| 2   | 2   | 16    | length-preserving |
| 2   | 3   | 32    | growing           |
| 2   | 4   | 64    | growing           |
| 3   | 1   | 16    | shrinking         |
| 3   | 2   | 32    | growing           |
| 3   | 3   | 64    | length-preserving |
| 4   | 1   | 32    | shrinking         |
| 4   | 2   | 64    | growing           |
| 5   | 1   | 64    | shrinking         |

By type: 216 growing, 84 length-preserving, 216 shrinking.


## Sterile vs active

- **Sterile:** 342 rules
- **Active:** 174 rules (all growing: |R| > |L|)
- **Length-preserving active:** 0 (all 84 are sterile)
- **Shrinking active:** 0 (all 216 are sterile)

### Why length-preserving rules are sterile

A length-preserving rule replaces L with R of the same length. For
non-trivial evolution, the result R must contain L as a substring so
that the rule can fire again. Of the 84 length-preserving rules in
C(6), 14 are identity rules (L = R, trivially sterile) and the
remaining 70 have the property that L does not appear in R. The rule
fires once, producing a string that no longer contains L, and reaches
a fixed point immediately. Zero of 84 produce non-trivial evolution.

### Why shrinking rules are sterile

A shrinking rule (|L| > |R|) reduces string length at every step.
Starting from a minimal seed, the string quickly becomes too short to
contain L, reaching a fixed point within a few steps. All 216 shrinking
rules are sterile.

### Implications

Single-rule binary string rewriting cannot produce non-trivial length-
preserving or shrinking dynamics within C(6). Only growing rules
(|L| < |R|) sustain evolution. This is a structural limitation of the
rule class, not a detection issue.


## Observer detection: 0/174, but progress from C(4)

No observers found. No 3/4 near-misses. But the failure pattern has
changed significantly from C(4).

### Entropy pre-filter

168 of 174 active rules are pruned by the entropy pre-filter (all
candidate regions have frozen interiors, H = 0). These are
single-symbol LHS rules (|L| = 1) that produce uniform or periodic
strings, identical to C(4) behavior.

6 rules pass the entropy pre-filter and receive full scoring:

| Rule       | Seed | tau | H      | B      | D      | S | Passed |
|------------|------|-----|--------|--------|--------|---|--------|
| 0 -> 10001 | 0    | 2   | 1.000  | 0.513  | 0.539  | 1 | 1/4    |
| 0 -> 10011 | 0    | 2   | 1.000  | 0.513  | 0.533  | 1 | 1/4    |
| 1 -> 01100 | 1    | 2   | 1.000  | 0.513  | 0.533  | 1 | 1/4    |
| 1 -> 01110 | 1    | 2   | 1.000  | 0.513  | 0.539  | 1 | 1/4    |
| 01 -> 1001 | 01   | 3   | 1.585  | 0.319  | 0.462  | 1 | 2/4    |
| 10 -> 0110 | 10   | 3   | 1.585  | 0.319  | 0.462  | 1 | 2/4    |


### Score distributions (6 scored rules)

| Criterion          | Range         | Threshold | Pass rate | Notes                     |
|--------------------|---------------|-----------|-----------|---------------------------|
| Boundary stability | 0.319–0.513   | < 0.3     | 0/6 (0%)  | Closest: 0.319 (01->1001) |
| Internal entropy   | 1.000–1.585   | > 1.0 bit | 2/6 (33%) | First non-zero H in project|
| Causal decoupling  | 0.462–0.539   | > 0.6     | 0/6 (0%)  | Still below threshold      |
| Self-reference     | 1.0           | >= 1.0    | 6/6 (100%)| Always passes              |


### Best near-misses: 01 -> 1001 and 10 -> 0110

These two rules (mirror images) are the most interesting in C(6).
They produce non-trivial spatial patterns with a repeating `100`/`011`
motif and a growing uniform prefix:

    01 -> 1001:  01 -> 1001 -> 101001 -> 11001001 -> 1101001001 -> ...

The match site (leftmost `01`) shifts rightward as 1s accumulate at
the left. This creates a moving boundary between a uniform region
(all 1s) and a patterned region (`100100100...`).

Scores: H = 1.585 bits (PASS), S = 1.0 (PASS), B = 0.319 (FAIL by
0.019), D = 0.462 (FAIL by 0.138).

Boundary stability fails because the match site moves, shifting the
boundary of any fixed subgraph. Causal decoupling fails because the
uniform prefix dominates external state prediction — the interior is
not sufficiently self-predictive.


## Comparison to C(4)

| Metric                    | C(4)      | C(6)      | Change           |
|---------------------------|-----------|-----------|------------------|
| Total rules               | 68        | 516       |                  |
| Active rules              | 20        | 174       |                  |
| Length-preserving active   | 0         | 0         | No change        |
| Shrinking active           | 0         | 0         | No change        |
| Rules past entropy filter | 0         | 6         | First non-frozen |
| Best near-miss            | 2/4       | 2/4       | Same count...    |
| Best H score              | 0.000     | 1.585     | Entropy now passes |
| Best B score              | 0.014     | 0.319     | Worse (non-trivial)|
| Best D score              | 0.500     | 0.462     | Slightly worse   |

The failure pattern has changed qualitatively:

- **C(4):** Boundary stability and self-reference pass trivially;
  entropy and decoupling fail because strings are uniform.
- **C(6):** Multi-symbol LHS rules (|L| >= 2) produce spatial
  heterogeneity for the first time. Entropy passes in 2 rules.
  But boundary stability now fails because the active site moves,
  and decoupling still fails because internal dynamics are not
  sufficiently self-contained.

The bottleneck has shifted from "no internal dynamics" (C(4)) to
"dynamics exist but are not bounded" (C(6)).


## Length-preserving rules (separate section)

All 84 length-preserving rules in C(6) are sterile. No observer
detection was attempted. This was a key hope for C(6) — length-
preserving dynamics cannot exploit growth artifacts — but the rule
class does not support it. Binary single-rule length-preserving
rewriting always reaches a fixed point within one step because R
never contains L as a substring (for L != R).

This is a fundamental limitation: length-preserving binary string
rewriting with a single rule is too constrained. Multi-rule systems
or larger alphabets may be needed for non-trivial length-preserving
dynamics.


## Conclusion

C(6) produces the first non-trivial internal dynamics (H > 0) but
still no observers. The new bottleneck is boundary stability and
causal decoupling — the active rewrite site moves through the string,
preventing any fixed or tracking subgraph from maintaining a stable
boundary with self-contained dynamics.

Next steps:
1. **C(8)** — larger rules may produce spatially localized dynamics
   where the active site stays within a bounded region.
2. **Longer runs at 5000 steps** for the 6 interesting rules — check
   if boundary stability improves over longer windows.
3. **Multi-rule systems** — if single-rule rewriting is fundamentally
   too simple, the rule class definition may need extension.
