# Canonical Event Schema

## Purpose

Canonical events are append-only JSON records with explicit hash chaining.

They are used for:

- chip evidence
- research provenance
- derived state
- derivation proofs

## Required common fields

Every canonical event ledger entry contains:

- `ledger`
- `run_id`
- `seq`
- `event_id`
- `event_type`
- `pc_before`
- `pc_after`
- `instruction`
- `instruction_class`
- `context`
- `details`
- `ontology_version`
- `prev_event_hash`
- `event_hash`

## Hash-chain rule

`event_hash` is computed over the unsigned payload.

`prev_event_hash` must equal the previous event's `event_hash`.

This makes each ledger:

- append-only
- tamper-evident
- replay-verifiable

## Ledger roles

### `chip-evidence`

Canonicalized events emitted from the trace source boundary.

### `research-provenance`

Pipeline bookkeeping for:

- scope
- program load
- trace capture
- normalization
- ontology load
- rule application
- state derivation
- report generation

### `derived-state`

Deterministic findings derived by ontology rules from chip evidence.

### `derivation-proofs`

Per-finding proof records linking a finding to:

- source event
- rule id
- ontology version
- derivation steps

## Current boundary

The schema is canonical and hashable, but it does not imply that every event type is available from every source.

Renode v0.5 and v0.6 remain architectural evidence sources.
They do not imply microarchitectural visibility.
