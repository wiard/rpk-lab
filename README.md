# RPK-Lab

**Register Provenance Kernel Lab.**

This project investigates whether AI-assisted cyberdefense can reason over
reproducible chip-level evidence instead of mutable telemetry.

A virtual RISC-V core produces execution events. These events are normalized
into a canonical eventlog, interpreted through an explicit security ontology,
and replayed deterministically to derive security state.

AI is not the source of truth. AI may explain derived findings, but every
finding must trace back to verifiable events, public rules, and a replayable
proof chain.

**Invariant:** *same trace + same ontology + same replay engine = same derived state*

See `concept/plan_register_provenance_kernel_v2.md` for the full plan.

---

**Repository:** `github.com/wiard/rpk-lab`
**License:** Apache License 2.0 (see `LICENSE`)
**Status:** Fase 0 — concept and literature review.

*De chip getuigt; AI redeneert.*

## Repository relationship

This is the canonical repository for reviewed Register Provenance Kernel work.

The exploration repository is:

https://github.com/wiard/register-provenance-kernel

Nothing is adopted here without a seq-numbered ledger entry in:

ledgers/research-provenance.jsonl

Modules, design decisions and experiments from the exploration repository
enter this repository only through explicit adoption events such as
ModuleAdopted, DesignDecisionAdopted or ExperimentAdopted.
