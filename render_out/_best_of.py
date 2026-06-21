#!/usr/bin/env python3
"""'Best of' — os melhores criativos via AUTO-MELHORIA (autogen), qualidade média.

O lever validado de qualidade: gera → avalia → regera com feedback → guarda a melhor
(_autogen). Roda um conjunto selecionado em IMAGE_QUALITY=medium (não low/one-shot dos
testes) pra produzir criativos bons de verdade. Usa o pipeline ATUAL (com inferência de
ICP ligada). ISOLADO. Grava o resultado no ledger.

Uso: set -a; . engine/.env; set +a; python3.11 render_out/_best_of.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
OUT = ROOT / "render_out" / "best-of"
ART = OUT / "artifacts"
OUT.mkdir(parents=True, exist_ok=True); ART.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ["IMAGE_QUALITY"] = "medium"     # caprichado (não o low dos testes)
os.environ["VISION_QA_MAX"] = "1"          # o autogen faz a regeneração (loop externo)
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "180000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ART)

from _autogen import generate_until_approved   # noqa: E402
import _ledger                                 # noqa: E402

# Seleção: mix Metta + Tiago, fortes pra polir + alguns pra puxar pra cima.
PICK = {"metta-inflexao-1", "metta-inflexao-2", "metta-otica", "metta-pet",
        "tiago-surreal", "tiago-noir"}


def main():
    briefs = [b for b in json.loads((ROOT / "data" / "golden-set.json").read_text())["briefs"]
              if b["id"] in PICK]
    manifest = []
    for i, b in enumerate(briefs, 1):
        marca = b["marca"]
        img = "none" if b.get("image") == "none" else "generate"
        preset = "fotorrealista" if marca != "tiago" else "cinematic-dark"
        print(f"\n[{i}/{len(briefs)}] {b['id']} ({b['model']}) — autogen…")
        brief_kwargs = {
            "briefing_text": "best-of", "forced_model_id": b["model"],
            "image_source": img, "image_style_preset": (None if img == "none" else preset),
            "user_headline": b.get("headline", ""), "user_subhead": b.get("subhead", ""),
            "user_body": b.get("body", ""), "user_cta_text": b.get("cta", ""),
            "wizard_format": b.get("format", "feed"),
            "render_png": True, "art_director": True, "vision_qa": True,
        }
        try:
            best, hist = generate_until_approved(brief_kwargs, max_attempts=2, target="SHIP", verbose=False)
        except Exception as e:
            print(f"   ERRO {e.__class__.__name__}: {e}")
            manifest.append({"id": b["id"], "model": b["model"], "score": 0, "verdict": "EXC", "foto": img == "generate"})
            continue
        ev = best.get("eval", {}) if best else {}
        res = best.get("result", {}) if best else {}
        uri = res.get("png_data_uri") or ""
        if uri.startswith("data:"):
            fold = OUT / b["id"]; fold.mkdir(exist_ok=True)
            (fold / "final.png").write_bytes(base64.b64decode(uri.split(",", 1)[1]))
        score = float(ev.get("geral") or 0)
        manifest.append({"id": b["id"], "model": b["model"], "marca": marca,
                         "foto": img == "generate", "score": score,
                         "verdict": ev.get("verdict", "?"),
                         "attempts": len(hist), "headline": b.get("headline", "")})
        print(f"   → {manifest[-1]['verdict']} nota={score} (tentativas={len(hist)})")

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics = _ledger.compute_metrics(manifest)
    _ledger.record("best-of (autogen, qualidade média)", metrics,
                   change_desc="auto-melhoria nos melhores briefs, qualidade média (não comparável 1:1 ao golden baseline low)")
    print("\n===== BEST OF =====")
    for m in sorted(manifest, key=lambda x: -x["score"]):
        print(f"  {m['score']:4.1f} {m['verdict']:8s} {m['id']}")
    print(f"\nnota média={metrics['avg_score']} SHIP={metrics['ship_rate']}%  ·  pngs em {OUT}/<id>/final.png")


if __name__ == "__main__":
    main()
