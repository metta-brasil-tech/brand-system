#!/usr/bin/env python3
"""Roda o GOLDEN SET (data/golden-set.json) no pipeline e grava o baseline no ledger.

É a régua fixa do flywheel: roda os 12 briefs → pontua com o avaliador → calcula
métricas → registra no docs/IMPROVEMENT-LEDGER.md. A cada mudança grande, roda de novo
e compara (antes→depois).

ISOLADO de propósito (ARTIFACTS_DIR + output próprios) pra rodar em paralelo com outro
batch sem colidir o concept_memory. Compartilha só a chave OpenAI.

Uso: set -a; . engine/.env; set +a; python3.11 render_out/_golden_run.py ["rótulo"]
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))

OUT = ROOT / "render_out" / "golden"
ART = OUT / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "low")          # baseline barato/rápido
os.environ["VISION_QA_MAX"] = "1"                       # one-shot (baseline, sem auto-melhoria)
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ART)                 # ISOLADO (não colide concept_memory)

from generate import _run_pipeline_inline  # noqa: E402
from _evaluator import evaluate            # noqa: E402
import _ledger                             # noqa: E402


def _png(res):
    uri = res.get("png_data_uri") or ""
    return base64.b64decode(uri.split(",", 1)[1]) if uri.startswith("data:") else None


def _decision_log(run_id):
    try:
        return json.loads((ART / run_id / "03-decision-log.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline golden set (pós-fix ICP)"
    briefs = json.loads((ROOT / "data" / "golden-set.json").read_text(encoding="utf-8"))["briefs"]
    manifest = []
    print(f"Golden set: {len(briefs)} briefs → {OUT}\n")
    for i, b in enumerate(briefs, 1):
        marca = b["marca"]
        img_src = "none" if b.get("image") == "none" else "generate"
        preset = "fotorrealista" if marca != "tiago" else "cinematic-dark"
        print(f"[{i:02d}/{len(briefs)}] {b['id']} ({b['model']})…")
        try:
            res = _run_pipeline_inline(
                briefing_text="golden", forced_model_id=b["model"],
                image_source=img_src, image_style_preset=(None if img_src == "none" else preset),
                user_headline=b.get("headline", ""), user_subhead=b.get("subhead", ""),
                user_body=b.get("body", ""), user_cta_text=b.get("cta", ""),
                wizard_format=b.get("format", "feed"),
                render_png=True, art_director=True, vision_qa=True)
        except Exception as e:
            print(f"   ERRO {e.__class__.__name__}: {e}")
            manifest.append({"id": b["id"], "model": b["model"], "score": 0, "verdict": "EXC", "foto": img_src == "generate"})
            continue
        png = _png(res) if res.get("ok") else None
        ev = {}
        if png:
            dl = _decision_log(res.get("run_id"))
            ev = evaluate(png, b, marca, res.get("vision_qa"), res.get("critic"), decision_log=dl)
            fold = OUT / b["id"]; fold.mkdir(exist_ok=True)
            (fold / "final.png").write_bytes(png)
            inf = ((dl or {}).get("avatar") or {}).get("segment") if dl else None
        else:
            inf = None
        manifest.append({
            "id": b["id"], "model": b["model"], "marca": marca,
            "foto": img_src == "generate",
            "score": ev.get("geral", 0) if ev else 0,
            "verdict": ev.get("verdict", "FAIL") if ev else ("SKIPPED" if not res.get("ok") else "NOPNG"),
            "headline": b.get("headline", ""),
            "expected_segment": b.get("expected_segment"),
            "inferred_segment": inf,
        })
        m = manifest[-1]
        print(f"   → {m['verdict']} nota={m['score']} seg(esp/inf)={m['expected_segment']}/{m['inferred_segment']}")

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # baseline limpo: o ledger passa a medir o GOLDEN SET (régua fixa), não o batch.
    _ledger._save([])
    metrics = _ledger.compute_metrics(manifest)
    entry = _ledger.record(label, metrics, change_desc="golden set como régua fixa; pipeline já com inferência de ICP ligada")
    # auditoria da inferência (esperado vs inferido)
    seg_ok = sum(1 for m in manifest if m.get("marca") == "metta" and m.get("inferred_segment") == m.get("expected_segment"))
    seg_tot = sum(1 for m in manifest if m.get("marca") == "metta")
    print(f"\n===== BASELINE GRAVADO ({entry['verdict']}) =====")
    print(f"n={metrics['n']} SHIP={metrics['ship_rate']}% nota={metrics['avg_score']} REVISAR={metrics['revisar_rate']}%")
    print(f"inferência de ICP: {seg_ok}/{seg_tot} corretas")
    print(f"Ledger: {ROOT/'docs'/'IMPROVEMENT-LEDGER.md'}")


if __name__ == "__main__":
    main()
