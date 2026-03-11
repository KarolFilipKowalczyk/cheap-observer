# C(8) T_rul Results

Causal invariance measurement for all 1026 active C(8) rules.
k=50 random update orderings per rule, max 1000 evolution steps.

See definitions.md Sections 7–8.


## Summary

| Metric                        | Count | Fraction |
|-------------------------------|-------|----------|
| Active rules tested           | 1026  |          |
| Vacuous T_rul = 0             | 314   | 30.6%    |
| Genuine finite T_rul          | 0     | 0%       |
| T_rul = infinity              | 712   | 69.4%    |

**No rule in C(8) exhibits genuine causal invariance.** Every rule
with finite T_rul is vacuously invariant (always has exactly one match
per step, so there is no choice of update order).


## Breakdown by |L|

| |L| | Active | Vacuous (T_rul=0) | Infinite | % vacuous |
|-----|--------|-------------------|----------|-----------|
| 1   | 492    | 54                | 438      | 11%       |
| 2   | 370    | 156               | 214      | 42%       |
| 3   | 164    | 104               | 60       | 63%       |

Longer LHS patterns are more likely to be vacuously invariant because
they produce fewer matches per step. A 3-character pattern is harder to
find in the string than a 1-character pattern, so many |L|=3 rules
have at most one match at each step throughout the 1000-step evolution.

Note: the initial expectation that all |L|=1 rules would be vacuously
invariant was wrong. Only 54 of 492 |L|=1 rules (11%) always have a
unique match. The majority of |L|=1 rules produce multiple matches as
the string grows (e.g., L="0", R="010" creates two "0"s per step).


## The two observer rules

| Rule        | T_obs | T_rul | Notes                        |
|-------------|-------|-------|------------------------------|
| 01 -> 10001 | 310   | inf   | Observer exists, no coherence|
| 10 -> 01110 | 310   | inf   | Mirror of above              |

Both observer rules have |L|=2 and are NOT vacuously invariant (they
produce multiple matches per step). Their causal graphs diverge under
different update orders. T_obs = 310, T_rul = infinity.

**T_obs < T_rul for both observer rules.** Observers appear; physics
does not.


## The eight 3/4 near-misses

| Rule          | T_obs | T_rul | Notes                      |
|---------------|-------|-------|----------------------------|
| 01 -> 100111  | inf   | inf   | Neither observer nor phys.  |
| 01 -> 100010  | inf   | inf   |                            |
| 01 -> 100001  | inf   | inf   |                            |
| 01 -> 100011  | inf   | inf   |                            |
| 10 -> 011000  | inf   | inf   |                            |
| 10 -> 011101  | inf   | inf   |                            |
| 10 -> 011110  | inf   | inf   |                            |
| 10 -> 011100  | inf   | inf   |                            |

All near-misses have both T_obs = infinity and T_rul = infinity.
They come close to being observers (3/4 criteria) but fail on
decoupling. They are not causally invariant either.


## P_obs vs P_rul

| Metric                              | Value         |
|-------------------------------------|---------------|
| P_obs (any)                         | 2/1026 = 0.2% |
| P_obs (unique, excl. mirrors)       | 1/1026 = 0.1% |
| P_rul (vacuous, T_rul = 0)          | 314/1026 = 30.6% |
| P_rul (genuine, T_rul > 0 & finite) | 0/1026 = 0%   |
| Rules with both finite              | 0             |

The sets of observer-producing rules and causally-invariant rules are
**completely disjoint** in C(8). No rule has both finite T_obs and
finite T_rul.


## Interpretation

### The prevalence gap (definitions.md Claim 10.1)

The formal claim states P_obs >> P_rul. In C(8):

- If we count vacuous T_rul: P_rul = 30.6% >> P_obs = 0.2%.
  This REVERSES the claim — more rules have T_rul finite than T_obs.
  But vacuous invariance is not physics. It is the absence of
  ambiguity, not the presence of confluence.

- If we exclude vacuous T_rul: P_rul = 0% < P_obs = 0.2%.
  Observers exist. Genuine physics does not. The claim holds.

The correct comparison uses P_rul(genuine). Vacuously invariant rules
have no choice point — they are deterministic by construction, not
confluent by structure. Definitions.md Section 7 tests confluence:
"the result is independent of the order in which rewrites are applied."
When there is only one possible rewrite, the test is undefined, not
passed.

### The ordering claim (definitions.md Claim 10.2)

"Among rules where both T_obs and T_rul are finite, T_obs < T_rul."

In C(8): zero rules have both finite. The claim is vacuously true.
This is not evidence for the hypothesis — it is the absence of a
test. C(8) is below the complexity threshold for genuine causal
invariance, so the ordering question has no data points.

### What this means

C(8) establishes one half of the argument: observers are cheap
(P_obs > 0). The other half — that physics is expensive relative to
observers — cannot be tested in C(8) because genuine physics does
not appear at all.

The hypothesis predicts that at larger class sizes (C(10)+), some
rules will exhibit genuine causal invariance, and for those rules,
T_obs < T_rul. C(8) is consistent with this prediction (observers
appear at a lower complexity threshold than genuine invariance) but
does not confirm the ordering on individual rules.


## Scatter data

The file `c8_scatter.json` contains all 316 rules where at least
one of T_obs or T_rul is finite:
- 2 rules with finite T_obs only (the observers)
- 314 rules with finite T_rul only (all vacuous)
- 0 rules with both finite

The "scatter plot" is degenerate in C(8): points lie on the axes
only, never in the interior. The first non-trivial scatter plot
requires a rule class where genuine causal invariance appears.
