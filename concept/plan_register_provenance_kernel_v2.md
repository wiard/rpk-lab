# Plan van Aanpak — Register Provenance Kernel (v2)

**Versie:** 2 — geconsolideerd. Vervangt v1 (`plan_register_provenance_kernel.md`).
**Werkruimte:** RPK-Lab
**Mantra:** *De chip getuigt; AI redeneert.*
**Status:** onderzoeksvoorstel met werkend prototype als doel. Geen product.

---

## 1. Aanleiding en positionering

Veel AI-cyberdefensie redeneert boven telemetrie waarvan de afkomst niet expliciet vastligt. Conclusies zijn daardoor moeilijk reproduceerbaar en moeilijk auditbaar.

**Centrale these:** AI-cyberdefensie wordt betrouwbaarder als er onder de redeneerlaag een register-nabije, ontologisch geduide en cryptografisch verankerde bewijslaag ligt — én als de onderzoeksstappen die tot conclusies leidden zelf ook bewijsbaar zijn.

**Bestaand werk waar dit naast staat:**

- **Phantom Trails** (USENIX Security 2025, VUSec — De Faveri Tron, Isemann, Ragab, Giuffrida, Von Gleissenthall, Bos): pre-silicon discovery van transient data leaks via fuzzing met software taint tracking. Geëvalueerd op de BOOM RISC-V CPU; vond alle bekende speculatieve kwetsbaarheden binnen 24 uur, plus een nieuwe Spectre-variant specifiek voor BOOM (Spectre-LoopPredictor). Code op `github.com/vusec/phantom-trails`.
- **SpecCheck** (PACT 2023): register-FSM in gem5 voor Spectre v1/v2 detectie.
- **Open Se Cura / CHERIoT** (Google × Antmicro): secure architecturen in Renode.

**Waar RPK boven of naast deze drie staat:**

1. **Breedte.** Niet alleen transient execution. Ook control-flow, memory-safety, privilege-transities.
2. **Bewijslaag, niet detector.** Bestaand werk classificeert. RPK voegt reproduceerbare afleidingsketen toe — events, regels, derived state, allemaal hash-verankerd.
3. **Strikte AI-scheiding.** AI mag uitleggen, niet beslissen of feiten toevoegen.
4. **Onderzoeksprovenance.** Niet alleen het resultaat, maar ook de weg ernaartoe is bewijsbaar (zie §5).

## 2. Architectuur — vijf lagen, twee ledgers

```
            VIRTUAL RISC-V CORE
                    ↓
              raw execution trace
                    ↓
                normalizer
                    ↓
        ┌────────────────────────┐
        │  CHIP EVIDENCE LEDGER  │   ← canoniek, hash-chained
        │  (JSONL)               │
        └────────────────────────┘
                    ↓
            security ontology
                    ↓
        deterministic rule engine
                    ↓
            derived states
                    ↓
        AI commentator (read-only)
```

Parallel hieraan:

```
        YOUR RESEARCH ACTIVITY
                    ↓
        ┌─────────────────────────────┐
        │  RESEARCH PROVENANCE LEDGER │  ← jouw stappen, hash-chained
        │  (JSONL)                    │
        └─────────────────────────────┘
```

**Invariant:**
*same trace + same ontology + same replay engine = same derived state*

**Twee ledgers, beide hash-chained, beide openbaar.** De Chip Evidence Ledger bewijst wat de chip zag. De Research Provenance Ledger bewijst wat de onderzoeker deed. Een externe lezer kan op basis van beide ledgers de hele keten van trace tot AI-uitleg reproduceren.

## 3. Pad — Venus → Spike → Ibex + Verilator

```
Venus / web simulator   →   Spike   →   Ibex + Verilator   →   AI-commentator
   (vocabulaire)        (eventlog)    (RTL-niveau virtueel)    (uitleg)
```

**Waarom Spike als primaire trace-bron, niet Renode:**

- Spike is de gouden RISC-V ISA-referentie. Schoon, klein, bekend gedrag.
- Trace-formaat is uniform en triviaal te parsen. Renode's tracing is rijker maar minder canoniek.
- Voor MINIX-discipline (klein, schoon, veilig, begrijpbaar) wint Spike.
- Renode wordt pas relevant als peripheral- of multi-core-context nodig is. Niet in de eerste cyclus.

**Renode en gem5 zijn satellieten:**

- **Renode** voor SoC-context (peripherals, secure boot, multi-node) als latere fase daarom vraagt.
- **gem5** voor microarchitecturale vragen (cache state, branch predictor) als de overlap met SpecCheck/Phantom Trails expliciet uitgewerkt moet worden.
- **AWS F2 / fysieke hardware** pas overwegen na Fase 5, en alleen als externe review erom vraagt.

## 4. Ontologie v0

Vijf tiers. Klein beginnen, expliciet uitbreiden.

### Entity
`Core`, `Program`, `Register`, `MemoryRegion`, `ExecutionContext`

### Event
`InstructionStep`, `RegisterWrite`, `CSRWrite`, `MemoryAccess`, `ControlFlowTransfer`, `PrivilegeTransition`, `Trap`, `Exception`

### Property
`writesRegister`, `targetsAddress`, `changesPrivilege`, `accessesRegion`, `causedByInstruction`, `occursInContext`

### DerivedState
`NormalTransition`, `SuspiciousControlFlow`, `UnauthorizedCSRWrite`, `StackOutOfBounds`, `ProtectedMemoryWrite`, `PrivilegeViolationCandidate`, `ViolationConfirmed`

### Decision
`RecordOnly`, `Flag`, `Trap`, `Deny`

In Fase 1 en 2 is Decision altijd `RecordOnly` — geen interventie, alleen observatie. `Trap` wordt mogelijk in Fase 3 via Verilator-instrumentatie. `Deny` is onderzoeksterritorium en vereist core-modificatie.

### Eerste regelset (v0, < 10 regels)

```
R-CF-001:  IF Event = ControlFlowTransfer
           ∧ Property.instruction_class = indirect_jump
           ∧ Property.targetsAddress ∉ allowed_targets
           THEN DerivedState = SuspiciousControlFlow
           THEN Decision = RecordOnly

R-CSR-001: IF Event = CSRWrite
           ∧ Property.changesPrivilege = true
           ∧ Property.occursInContext ≠ machine-mode
           THEN DerivedState = UnauthorizedCSRWrite
           THEN Decision = RecordOnly

R-MEM-001: IF Event = MemoryAccess
           ∧ Property.accessesRegion = protected
           ∧ Property.access_type = write
           THEN DerivedState = ProtectedMemoryWrite
           THEN Decision = RecordOnly

R-SP-001:  IF Event = RegisterWrite
           ∧ Property.writesRegister = sp
           ∧ Property.value ∉ valid_stack_range
           THEN DerivedState = StackOutOfBounds
           THEN Decision = RecordOnly

R-TRAP-001: IF Event = Trap
            ∧ Property.causedByInstruction → previous_event ∈ Suspicious*
            THEN DerivedState = ViolationConfirmed
            THEN Decision = RecordOnly
```

## 5. Twee eventlog-formaten

### Chip Evidence Ledger

```json
{
  "ledger": "chip-evidence",
  "seq": 42,
  "event_type": "ControlFlowTransfer",
  "simulator": "spike",
  "architecture": "riscv32",
  "pc_before": "0x80001020",
  "pc_after": "0x80004000",
  "instruction_class": "indirect_jump",
  "context": "user",
  "ontology_version": "rpk-security-v0.1",
  "prev_event_hash": "sha256:...",
  "event_hash": "sha256:..."
}
```

### Research Provenance Ledger

```json
{
  "ledger": "research-provenance",
  "seq": 7,
  "event_type": "TraceNormalized",
  "input_trace_hash": "sha256:...",
  "normalizer_version": "rpk-normalizer-v0.1",
  "output_eventlog_hash": "sha256:...",
  "ontology_version": "rpk-security-v0.1",
  "timestamp": "2026-05-06T14:00:00Z",
  "prev_event_hash": "sha256:...",
  "event_hash": "sha256:..."
}
```

### Afleidingsbewijs

```json
{
  "finding_id": "F-001",
  "finding": "SuspiciousControlFlow",
  "derived_from": {
    "events": ["E-0042"],
    "rules": ["R-CF-001"],
    "ontology": "rpk-security-v0.1"
  },
  "derivation": [
    "E-0042.event_type = ControlFlowTransfer",
    "E-0042.instruction_class = indirect_jump",
    "E-0042.pc_after ∉ allowed_targets",
    "R-CF-001 derives SuspiciousControlFlow"
  ],
  "proof_hash": "sha256:..."
}
```

De conclusie is niet opgeslagen als waarheid. De conclusie is reproduceerbaar afleidbaar.

## 6. Fasering

### Fase 0 — Concept en literatuur (2–3 weken)
- Concept note van 2–3 pagina’s (Engelstalig).
- Lezen: Phantom Trails (volledig), SpecCheck, Open Se Cura/CHERIoT.
- Drie zinnen scherp: wat bestaat, wat ontbreekt, wat RPK toevoegt.
- **Deliverable:** `concept_note.pdf`, literatuurmap.
- **Go/no-go:** kunt u in één alinea het verschil met Phantom Trails uitleggen?

### Fase 1 — Vocabulaire op Venus (1–2 weken)
- RISC-V assembly draaien in browser-simulator.
- Eventtypes destilleren uit register- en memory-veranderingen.
- Ontologie v0.1 vastleggen: vijf tiers, tien regels, ontologieversie hash-bevroren.
- Research Provenance Ledger begint hier: `HypothesisDeclared`, `OntologyInitialized`.
- **Deliverable:** `ontology/rpk-security-v0.1.yaml`, `ontology/rpk-security-v0.1.rules`.
- **Go/no-go:** kan een externe lezer uit de ontologie alleen reproduceren wat een gegeven event betekent?

### Fase 2 — Spike-pipeline + twee ledgers (3–4 weken)
- Spike compileren met logging-flags voor PC, register writes, CSR writes, memory access, exceptions, privilege transitions.
- Trace-normalizer in Python: log → canonical events → JSONL met hash-chain.
- Rule engine: ontologie-regels deterministisch toepassen, derivation proofs schrijven.
- Research Provenance Ledger volledig actief: elke configuratie, elke run, elke versiekeuze gelogd.
- Klein corpus: vijf toy-binaries (zie §7).
- **Deliverable:** `rpk-lab/` repo met de structuur uit §10.
- **Go/no-go:** levert dezelfde binary altijd dezelfde event-keten en dezelfde derivation proofs op? Twee externe lezers, onafhankelijk.

### Fase 3 — Ibex + Verilator (6–8 weken)
- Ibex Simple System bouwen volgens upstream documentatie.
- Verilator-build met instructie- en wave-tracing.
- RTL-signalen tappen: program counter, register file writes, CSR writes, branch decisions, exceptions, privilege state, memory interface.
- Mapping op dezelfde ontologie als in Fase 2 — ledger-formaat ongewijzigd, alleen `simulator`-veld is `ibex-verilator`.
- Vergelijking Spike vs. Ibex per scenario: welke events ziet alleen één van beide?
- Eerste experiment met `Decision = Trap`: Verilator instrumenteren om bij specifieke derived states te halten.
- **Deliverable:** `rpk-lab/ibex/` met patch op Ibex Simple System, host-side parser, vergelijkingstabel.
- **Go/no-go:** kunt u op RTL-niveau minstens twee classificaties afleiden die op Spike onzichtbaar bleven?

### Fase 4 — AI-commentator (2–3 weken)
- AI-laag krijgt alleen-lezen toegang tot beide ledgers en derivation proofs.
- Drie functies, niet meer:
  - welke events zijn relevant
  - welke regel ging af
  - waarom dit verdacht is
- AI-output verplicht ankeren aan: `event_id`, `rule_id`, `ontology_version`, `proof_hash`.
- AI mag **nooit** zeggen "er was een aanval". Wel: "volgens R-CF-001 volgt uit E-0042 de classificatie SuspiciousControlFlow."
- **Deliverable:** demo-script dat een aanvalsscenario doorloopt en zowel het bewijs als de uitleg toont.

### Fase 5 — Validatie en falsificatie (4 weken)
- Toy attack scenarios door de pipeline (zie §7).
- Welke aanvalsklassen vallen aantoonbaar buiten? Eerlijk documenteren.
- Adversarial test: aanval die opzettelijk de ontologie probeert te omzeilen.
- Twee onafhankelijke lezers de pipeline laten reproduceren.
- **Deliverable:** falsification report met expliciete lijst van wat het model mist.

## 7. Toy attack scenarios

Synthetische binaries, geen malware. Veilig te delen.

| # | Vraag | Event | Verwachte DerivedState |
|---|-------|-------|------------------------|
| 1 | Indirecte sprong naar niet-toegestaan doel | `ControlFlowTransfer` | `SuspiciousControlFlow` |
| 2 | CSR-write vanuit user-mode naar privilege-register | `CSRWrite` | `UnauthorizedCSRWrite` |
| 3 | Stack pointer onder geldige range | `RegisterWrite(sp)` | `StackOutOfBounds` |
| 4 | Memory write in beschermd gebied | `MemoryAccess(write)` | `ProtectedMemoryWrite` |
| 5 | Trap volgend op een verdachte transitie | `Trap` | `ViolationConfirmed` |

Eerste publieke demo: laat zien dat scenario #1 op Spike-trace en Ibex-trace dezelfde derived state oplevert via verschillende onderliggende events maar dezelfde proof chain.

## 8. Onderzoeksvragen

Drie, samen genoeg voor een eerste paper.

1. Kunnen register- en control-flow-events uit een virtuele RISC-V core worden omgezet in een canoniek, hashbaar eventlog?
2. Kan een expliciete veiligheidsontologie deterministisch security-state afleiden uit zulke events?
3. Kan AI zinvol redeneren over deze afgeleide state zonder zelf bron van waarheid te worden?

## 9. Wat dit niet probeert te bewijzen

Expliciet, om scope-creep te voorkomen:

- **Niet:** dat alle aanvallen vindbaar zijn.
- **Niet:** dat Spectre beter detecteerbaar is dan in Phantom Trails.
- **Niet:** dat AI betrouwbaar is.
- **Niet:** dat register-state genoeg is voor alle chipaanvallen.
- **Niet:** dat dit silicon vervangt.

**Wel:**

- Dat chip-events canoniek vastlegbaar zijn.
- Dat een ontologie betekenis kan geven aan die events.
- Dat security-state deterministisch kan worden afgeleid.
- Dat iedere afleiding reproduceerbaar is — door derden, zonder de bouwer.
- Dat AI boven deze laag kan redeneren zonder zelf de feitenbasis te zijn.
- Dat het onderzoeksproces zelf bewijsbaar gemaakt kan worden.

## 10. Repository-structuur

```
rpk-lab/
  README.md
  ontology/
    rpk-security-v0.1.yaml
    rpk-security-v0.1.rules
  programs/
    safe-control-flow-test/
    safe-csr-write-test/
    safe-stack-range-test/
    safe-memory-write-test/
    safe-trap-test/
  traces/
    raw/
    normalized/
  ledgers/
    chip-evidence.jsonl
    research-provenance.jsonl
  replay/
    normalize_trace.py
    hash_ledger.py
    replay_rules.py
    derive_state.py
  proofs/
    merkle_roots.json
    derivation_proofs.jsonl
  reports/
    experiment-001.md
    experiment-002.md
  ibex/                 # vanaf Fase 3
  spike/
  concept/
    concept_note.md
```

De repo is de bewijsruimte. Iedere claim in `README.md` of `concept_note.md` koppelt aan een artefact elders in de repo.

## 11. Risico’s

| Risico | Mitigatie |
|--------|-----------|
| Overlap met Phantom Trails niet helder | Drie zinnen in concept note, expliciet citerend, tegen volledige paper. |
| Verilator-builds traag | Klein begin: Ibex Simple System, korte programma’s. MMU pas later. |
| Ontologie groeit ongecontroleerd | Strikt klein in Fase 1–2. Uitbreiden vereist explicit `OntologyVersionIncremented` event in Research Provenance Ledger. |
| AI-laag groeit voorbij commentator-rol | Strikte read-only API; output verplicht ankeren aan event/rule/proof. |
| Spike-trace en Ibex-trace incompatibel | Acceptabel — een onderzoeksresultaat op zich. Eerlijk documenteren. |
| Twee ledgers worden onhanteerbaar | Klein houden in formaat; iedere ledgerregel < 1 KB. Schema versioning. |
| Sequence-creep | Vaste go/no-go's, geen Fase n+1 zonder afgesloten Fase n. |

## 12. Werkprincipes

- Klein, schoon, veilig, begrijpbaar.
- Geen claim zonder artefact.
- Geen artefact zonder reproductiepad.
- Geen reproductiepad dat de bouwer nodig heeft.
- Browser → ISA-simulator → RTL — niet andersom.
- Ontologie expliciet en versioneerd.
- Twee ledgers, beide gehasht, beide open.
- AI mag uitleggen, niet beslissen.
- Falsificatie is eerste klas.
- *De chip getuigt; AI redeneert.*

## 13. Eerste concrete stap

Vandaag, in één middag:

1. `mkdir -p ~/rpk-lab/{ontology,programs,traces,ledgers,replay,proofs,reports,concept}`
2. In `concept/concept_note.md` drie kopjes neerzetten — *wat bestaat*, *wat ontbreekt*, *wat RPK toevoegt* — met onder elk kopje één zin. Eén zin, niet meer.
3. Phantom Trails-paper downloaden naar `concept/references/`.
4. Eerste regel van de Research Provenance Ledger schrijven, met de hand:
   ```json
   {
     "ledger": "research-provenance",
     "seq": 1,
     "event_type": "HypothesisDeclared",
     "hypothesis": "Chip events kunnen canoniek vastgelegd en deterministisch geclassificeerd worden",
     "ontology_version": "rpk-security-v0.0",
     "timestamp": "2026-05-06T...",
     "prev_event_hash": "sha256:0",
     "event_hash": "sha256:..."
   }
   ```
5. `git init`, `git add`, `git commit -m "RPK-Lab seq 1: HypothesisDeclared"`.

Het verschil tussen een plan en een project is een eerste commit. Stap 5 is die eerste commit. Vanaf daar wordt iedere volgende stap zelf een entry in de Research Provenance Ledger.
