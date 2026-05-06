# Boundary

register-provenance-kernel is the exploration repository.
rpk-lab is the canonical deposit.

Modules cross only through ModuleAdopted events.
Design decisions cross only through DesignDecisionAdopted events.
Rejected work is recorded as ModuleConsideredRejected if relevant.
AI-agent work happens in exploration, not directly in canonical.

Every adoption event records:
- source_repo
- source_commit
- source_path
- source_sha256
- target_path
- review_notes
- deviations_from_source
- deviations_from_plan_v2
- ontology_version
- prev_event_hash
- event_hash

If verification fails for any canonical artifact, work stops until
the inconsistency is resolved through a documented ledger event.
