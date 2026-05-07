# Evidence Levels

## Purpose

Evidence levels state how strong the capture boundary really is.

They prevent false equivalence between:

- architectural traces
- microarchitectural traces
- RTL or hardware-level observations

## `architectural`

Architectural evidence exposes committed or explicitly surfaced execution behavior.

Typical examples:

- instruction steps
- explicit control-flow transfers
- explicit traps
- explicit architectural policy events

Architectural evidence does not justify claims about:

- speculative execution internals
- transient data flow
- cache state
- predictor state
- pipeline flushes

## `microarchitectural`

Microarchitectural evidence exposes behavior below the committed architectural boundary.

Typical future examples:

- speculative access observations
- pipeline flush observations
- taint propagation through transient state
- detector output tied to microarchitectural execution

This is a future source tier for:

- gem5
- BOOM
- Verilator

It is not provided by current Renode v0.5 or v0.6 runs.

## Current RPK stance

Current Renode-based runs must be labeled:

- `evidence_level = architectural`

They must not derive:

- `TransientDataLeakCandidate`
- `SpeculativeAccessObserved`
- `PipelineFlushObserved`
- taint-based transient events

## Design consequence

The evidence level belongs in the proof bundle so the boundary travels with the bundle, not just with the code or the paper discussion.
