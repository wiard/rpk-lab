# Proof Bundle Schema

Schema version:

- `rpk-proof-bundle-v1`

## Purpose

The proof bundle is a compact, path-neutral summary of a verified run.

It is not the source of truth.
The source of truth remains:

- `chip-evidence.jsonl`
- `research-provenance.jsonl`
- `derived-state.jsonl`
- `derivation-proofs.jsonl`
- `proofs.json`

## Required top-level fields

- `schema_version`
- `run_id`
- `run_path_relative`
- `evidence_root`
- `evidence_level`
- `capture_boundary`
- `unsupported_claims`
- `event_count`
- `finding_count`
- `ontology_version`
- `ontology_hash`
- `chip_event_merkle_root`
- `derived_state_merkle_root`
- `deterministic_state_id`
- `verification_result`
- `verification_errors`
- `findings`
- `provenance`

## Field meanings

### `schema_version`

Identifies the proof bundle contract.

Current value:

- `rpk-proof-bundle-v1`

### `evidence_level`

Declares the strongest honest evidence tier represented by the run.

Current levels:

- `architectural`
- `microarchitectural`

Renode v0.5 and v0.6 runs are architectural.

### `capture_boundary`

Explicitly states what the trace source made visible and what it did not.

Structure:

```json
{
  "visible": ["InstructionStep", "ControlFlowTransfer"],
  "not_visible": ["TransientDataLeakCandidate", "SpeculativeAccessObserved"]
}
```

### `unsupported_claims`

Lists claims or candidate event types that may not be derived from the captured evidence.

This keeps proof bundles honest when the source trace is architectural only.

### `provenance`

PROV-inspired summary of:

- `entities`
- `activities`
- `agents`

This is a compact explanation layer around the evidence pipeline, not a replacement for the ledgers.

## Path discipline

Proof bundles must not contain machine-local absolute paths such as `/Users/...`.

Use repository-relative or neutral external paths instead.

## Claim discipline

Architectural-only evidence must not claim:

- transient data leakage
- speculative execution internals
- cache state
- branch predictor state
- pipeline flush state
- taint propagation that was not explicitly captured
