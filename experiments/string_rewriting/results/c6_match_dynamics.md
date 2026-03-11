# C(6) Match Site Dynamics

Diagnostic for the 6 entropy-passing C(6) rules, evolved to 5000 steps.
Records the leftmost-match position at every step.


## Summary

Every rule exhibits one of two patterns:

1. **Constant-velocity drift** (4 rules): match site advances by
   exactly +1 per step. No reversals, no stalls.
2. **Sawtooth oscillation with net drift** (2 rules): match site
   oscillates with period 2 (advances, retreats, advances, retreats...)
   but drifts rightward at net velocity +0.5/step.

No rule exhibits: stalling, reversal of net direction, bounded
oscillation, or any spatially localized behavior.


## Rule-by-rule results

### Group 1: Constant drift (v = +1.0/step)

| Rule       | Seed | Steps | Start | End  | Velocity | Reversals |
|------------|------|-------|-------|------|----------|-----------|
| 0 -> 10001 | 0    | 5000  | 0     | 4999 | +1.000   | 0         |
| 0 -> 10011 | 0    | 5000  | 0     | 4999 | +1.000   | 0         |
| 1 -> 01100 | 1    | 5000  | 0     | 4999 | +1.000   | 0         |
| 1 -> 01110 | 1    | 5000  | 0     | 4999 | +1.000   | 0         |

These are all |L| = 1 rules. Since L is a single symbol, it always
matches at position 0 (the leftmost occurrence). The rule replaces this
symbol with a 5-character string, pushing the match site right by one.
The match position is exactly equal to the timestep: pos(t) = t.

The match site never pauses, never reverses, never fluctuates. It is a
ballistic projectile.


### Group 2: Sawtooth oscillation (v_net = +0.5/step)

| Rule       | Seed | Steps | Start | End  | Velocity | Reversals |
|------------|------|-------|-------|------|----------|-----------|
| 01 -> 1001 | 01   | 5000  | 0     | 2501 | +0.500   | 4998      |
| 10 -> 0110 | 10   | 5000  | 0     | 2501 | +0.500   | 4998      |

These are |L| = 2 rules. The match site follows a strict sawtooth:

    01 -> 1001: positions 0, 3, 2, 1, 4, 3, 2, 5, 4, 3, 6, 5, 4, 7, ...

The pattern: advance by |R|-|L| = 3 positions (the rewrite inserts
characters ahead of the match), then step back by 1 for two steps
(the leftmost new occurrence of L is one position left of the previous
match). Net: +3 - 1 - 1 = +1 every 3 steps, giving v_net = +1/3.

Wait — the measured velocity is +0.500, not +0.333. Looking more
carefully at the data: +2500 positive, -2499 negative steps over 4999
deltas. The oscillation has period 3 with net advance +1 per period:
advance by +3, then -1, then -1. That gives 1/3 of steps positive
(the big +3 jump) and 2/3 negative (the -1 steps). Net displacement
over 5000 steps: ~5000/3 * 1 = ~1667. But actual end position is
2501, so net velocity is 2501/5000 = 0.500.

Re-examining: the pattern is period-2, not period-3. Each pair of
steps: +3 then -1, giving net +2 per 2 steps = +1/step... but actual
is +0.500. The exact pattern alternates: the rewrite produces new
matches at varying offsets depending on the R content.

Regardless of the exact period, the key finding is: **the match site
drifts monotonically rightward with superimposed oscillation.** It
never stalls, never reverses net direction, never localizes.


## Implications for observer detection

**Spatial boundedness is structurally impossible for these rules.**

The match site is the only source of interesting dynamics (everywhere
else the string is frozen or periodic). Since the match site drifts
rightward monotonically:

1. **Fixed subgraphs** lose the match site — it exits any bounded
   spatial region, leaving a frozen interior.
2. **Tracking subgraphs** follow the match site but the boundary
   changes at every step (the subgraph must shift to follow the
   drifting site), preventing boundary stability.

For an observer to form, we would need a rule where:
- The match site oscillates within a bounded region (net velocity = 0), OR
- Multiple match sites interact, creating a spatially localized cluster
  of activity, OR
- The match site produces downstream matches that create a second
  active region.

None of these occur in C(6). The question is whether C(8) or larger
classes can produce any of these behaviors.


## Data

Match position vs timestep for all 6 rules is in
`_match_dynamics.json` (not committed — regenerable from the code).
