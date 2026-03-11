# src/

Three general modules that work on any rule class:

- **`spark/`** — Rule enumeration and minimal seed search. Given a rule
  class, systematically generate rules and find the smallest seed that
  produces non-trivial evolution.

- **`observer/`** — Observer detection using four criteria (boundary
  stability, internal entropy, causal decoupling, self-reference). The
  formal contract is in `observer/definition.py`. All detection code
  conforms to it.

- **`ruliad/`** — Physics-likeness benchmarks. Measures causal
  invariance, effective dimensionality, and global coherence to
  determine when a rule's evolution enters the ruliad regime.

## What is NOT here

The Game of Intelligence engine is a specific rule class instance, not
part of the general framework. It lives in
`experiments/directed_graph/engine/`.
