#!/usr/bin/env python3
"""Valida a vision-qa MODEL-AWARE sobre PNGs já salvos (sem regerar).
Compara o veredito contra a intenção/anti-padrões do blueprint."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
os.environ.setdefault("LLM_PROVIDER", "openai")

from _vision_qa import check as vqa_check          # noqa: E402
from _blueprint_dna import extract_dna             # noqa: E402

# (pasta do png, model_id, copy) — lote + o e2e do DARK-COLAGEM
TARGETS = [
    (ROOT / "render_out/criativos-novos-21jun/01-A-headline-foto-dark",
     "A-headline-foto-dark"),
    (ROOT / "render_out/criativos-novos-21jun/04-DARK-OBJETO", "DARK-OBJETO"),
    (ROOT / "render_out/criativos-novos-21jun/05-TIAGO-DARK-SURREAL", "TIAGO-DARK-SURREAL"),
    (ROOT / "render_out/_e2e-dark-colagem", "DARK-COLAGEM"),
]


def _copy_from_info(folder: Path) -> dict:
    c = {"headline": "", "subhead": "", "body": "", "cta": ""}
    info = folder / "info.md"
    if not info.exists():
        return c
    for line in info.read_text(encoding="utf-8").splitlines():
        m = re.match(r"-\s*(headline|subhead|body|cta):\s*(.*)", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            c[k] = "" if v == "—" else v
    return c


def main() -> None:
    for folder, model_id in TARGETS:
        png = folder / "criativo.png"
        if not png.exists():
            png = folder / "imagem-gerada.png"   # e2e do dark-colagem pode não ter criativo.png
        if not png.exists():
            print(f"  {model_id}: SEM png — pulado")
            continue
        marca = "tiago" if model_id.upper().startswith("TIAGO") else "metta"
        dna = extract_dna(marca, model_id)
        copy = _copy_from_info(folder)
        res = vqa_check(png.read_bytes(), copy, model_dna=dna)
        print(f"\n  {model_id} ({marca}) — anti-padrões no DNA: {len(dna.get('anti_patterns') or [])}")
        print(f"    verdict={res.get('verdict')} rel={res.get('relevance')} "
              f"integ={res.get('integrity')} anti_pattern_violated={res.get('anti_pattern_violated')}")
        print(f"    razão: {res.get('reason')}")


if __name__ == "__main__":
    main()
