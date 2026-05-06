"""Hash helper voor ledger-entries.

Een ledger-entry is een JSON-object. event_hash is sha256 over de
canonieke JSON van de entry met event_hash zelf weggelaten.

Standaardbibliotheek alleen. Geen externe dependencies.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_json(obj: dict) -> str:
    """Canonieke JSON: gesorteerde keys, geen whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def compute_event_hash(entry: dict) -> str:
    """Bereken event_hash voor een entry.

    De entry mag prev_event_hash bevatten maar event_hash wordt
    weggelaten voor de berekening.
    """
    payload = {k: v for k, v in entry.items() if k != "event_hash"}
    digest = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
    return f"sha256:{digest}"


def tail_entry(ledger_path: str) -> dict | None:
    """Lees de laatste entry uit een ledger, of None als leeg."""
    p = Path(ledger_path)
    if not p.exists():
        return None
    last = None
    with p.open("r") as f:
        for line in f:
            if line.strip():
                last = line
    return json.loads(last) if last else None


def append_entry(ledger_path: str, entry: dict) -> dict:
    """Append entry aan ledger, met chained prev_event_hash en event_hash.

    Bij lege ledger is prev_event_hash 'sha256:0'.
    Geeft de definitieve entry (incl. hashes) terug.
    """
    prev = tail_entry(ledger_path)
    entry["prev_event_hash"] = prev["event_hash"] if prev else "sha256:0"
    entry["event_hash"] = compute_event_hash(entry)

    p = Path(ledger_path)
    with p.open("a") as f:
        f.write(canonical_json(entry) + "\n")

    return entry


def verify_chain(ledger_path: str) -> bool:
    """Verifieer hash-chain van een ledger. Geeft True als alles klopt."""
    p = Path(ledger_path)
    if not p.exists():
        return True

    prev_hash = "sha256:0"
    with p.open("r") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("prev_event_hash") != prev_hash:
                print(f"Chain break at line {lineno}: prev mismatch")
                return False
            expected = compute_event_hash(entry)
            if entry.get("event_hash") != expected:
                print(f"Chain break at line {lineno}: hash mismatch")
                return False
            prev_hash = entry["event_hash"]
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: hash_ledger.py verify <ledger_path>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "verify":
        ok = verify_chain(sys.argv[2])
        print("OK" if ok else "BROKEN")
        sys.exit(0 if ok else 1)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
