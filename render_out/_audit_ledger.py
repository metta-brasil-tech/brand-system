#!/usr/bin/env python3
"""Audita um run no ledger de auto-melhoria.

Lê o manifest do batch atual, calcula as métricas e grava uma entrada comparada à
anterior ("depois dessa alteração, melhorou/piorou isto"). Renderiza o MD legível.

Uso:
    python3.11 render_out/_audit_ledger.py "rótulo da alteração" ["o que mudou em detalhe"]
Ex:
    python3.11 render_out/_audit_ledger.py "baseline" "estado antes de ligar o flywheel"
    python3.11 render_out/_audit_ledger.py "passo 5: flywheel" "peça SHIP entra no banco"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
from _ledger import compute_metrics, record  # noqa: E402

# manifest padrão = o batch atual; pode passar outro caminho via env MANIFEST.
import os  # noqa: E402
MANIFEST = Path(os.getenv("MANIFEST", ROOT / "render_out" / "criativos-atuais" / "manifest.json"))


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    change = sys.argv[2] if len(sys.argv) > 2 else ""
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"manifest indisponível ({MANIFEST}): {e}")
        sys.exit(1)
    m = compute_metrics(manifest)
    entry = record(label, m, change_desc=change)
    print(f"=== {label} → {entry['verdict']} ===")
    print(f"n={m['n']}  SHIP={m['ship_rate']}%  nota={m['avg_score']}  "
          f"REVISAR={m['revisar_rate']}%  regen={m['regen_rate']}%")
    if entry.get("deltas"):
        difs = " · ".join(f"{k} {v:+}" for k, v in entry["deltas"].items()
                          if isinstance(v, (int, float)) and v)
        print(f"Δ vs anterior: {difs or 'sem variação'}")
    print(f"\nLedger: {ROOT/'docs'/'IMPROVEMENT-LEDGER.md'}")


if __name__ == "__main__":
    main()
