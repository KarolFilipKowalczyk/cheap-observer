# Counterexamples

Counterexamples are first-class citizens. They are as valuable as
positive results because they stress-test the definitions and reveal
where the claim is weakest.

## Taxonomy

- **`obs_without_rul.py`** — Rules that produce observers but never
  produce ruliad-like coherence. These are expected to be common and
  support the claim, but extreme cases may reveal that our observer
  criteria are too loose.

- **`rul_without_obs.py`** — Rules that produce coherence but no
  observers. These are the most dangerous counterexamples. If a natural
  rule class is dominated by such rules, the claim is refuted.

- **`false_positives.py`** — Structures that pass 3 of 4 observer
  criteria but fail the fourth. These test whether each criterion is
  doing real work and whether the conjunction requirement is too strict
  or too permissive.

- **`borderline/`** — Cases that sit at the boundary of the definitions.
  Structures where small parameter changes flip the classification.
  These inform how robust the claim is to definitional choices.

- **`notes.md`** — What counterexamples teach us about the definitions.
  Running commentary on how failures reshape our understanding.
