#!/usr/bin/env python3
"""
Inspect the full answer texts of all 9 Quota runs to rigorously check for fabrication.
"""

import json
from pathlib import Path

STATE_BASE = Path("/Users/zhyz/.local/state/notebooklm-skill/persona-effect-20260827")
EVIDENCE_QUOTA = STATE_BASE / "evidence-quota2"

GROUPS = ["g1", "g2", "g3"]
REPS = [1, 2, 3]

def inspect_quotas():
    for g in GROUPS:
        for r in REPS:
            p = EVIDENCE_QUOTA / f"{g}-quota-rep{r}.json"
            if not p.exists() and r == 1:
                p = EVIDENCE_QUOTA / f"{g}-quota.json"
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            ans = d.get("answer", "")
            print(f"\n{'='*70}")
            print(f"GROUP {g.upper()} - REP {r} ({p.name})")
            print(f"{'='*70}")
            print(ans)

if __name__ == "__main__":
    inspect_quotas()
