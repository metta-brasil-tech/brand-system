#!/usr/bin/env python3
"""Smoke test do _nano_pipeline: gera 1 criativo pronto ponta a ponta.
Rodar: GEMINI_API_KEY=... .venv/bin/python scripts/nano_smoke.py"""
import sys, pathlib
WT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT / "api"))

from _nano_pipeline import generate_creative, pick_reference

COPY = {"tag": "GESTÃO COMERCIAL", "headline": "Seu processo *morre* em 30 dias?",
        "subhead": "O que não é sistema vira improviso.", "cta": "APLICAR PARA A MENTORIA"}
SCENE = ("a surreal metaphor: a potted plant shaped like an upward business growth arrow, "
         "wilting and dying on an office desk, symbol of a process that dies without a system; "
         "bottom third clean for a headline.")

ref = pick_reference("LIGHT-SURREAL", COPY)
print("referência escolhida:", ref)
png, meta = generate_creative("metta", "LIGHT-SURREAL", COPY, SCENE, format="feed")
out = WT / "scripts" / "_smoke-out.png"
out.write_bytes(png)
print("meta:", meta)
print("criativo pronto salvo em:", out, f"({len(png)//1024}KB)")
