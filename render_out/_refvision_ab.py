#!/usr/bin/env python3
"""A/B — qualidade: baseline (texto) vs REFERENCE-AWARE (pensador olha o PNG campeão).

Prova se a Fase 7 (geração reference-aware) deixa o criativo MELHOR. Para alguns briefs
do golden set: gera baseline e gera com o prompt enriquecido por _ref_vision (que olha a
referência campeã do banco), pontua os dois com o avaliador e compara a nota.

Injeção sem mexer no pipeline: o prompt enriquecido vai em `briefing_image_text` (direção
visual de prioridade máxima → o diretor de arte não sobrescreve).

ISOLADO (ARTIFACTS_DIR + output próprios). Uso: set -a; . engine/.env; set +a;
python3.11 render_out/_refvision_ab.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
OUT = ROOT / "render_out" / "refvision-ab"
ART = OUT / "artifacts"
OUT.mkdir(parents=True, exist_ok=True); ART.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "low")
os.environ["VISION_QA_MAX"] = "1"
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ART)

from generate import _run_pipeline_inline   # noqa: E402
from _evaluator import evaluate             # noqa: E402
from _critic import pick_reference          # noqa: E402
from _ref_vision import enrich_scene        # noqa: E402

# 3 briefs metta com foto (setoriais — onde o craft da referência mais ajuda)
IDS = {"metta-pet", "metta-otica", "metta-farmacia"}


def _png(res):
    uri = res.get("png_data_uri") or ""
    return base64.b64decode(uri.split(",", 1)[1]) if uri.startswith("data:") else None


def _dl(rid):
    try:
        return json.loads((ART / rid / "03-decision-log.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def _gen(brief, briefing_image=None):
    res = _run_pipeline_inline(
        briefing_text="ab", forced_model_id=brief["model"], image_source="generate",
        image_style_preset="fotorrealista", briefing_image_text=briefing_image,
        user_headline=brief.get("headline", ""), user_subhead=brief.get("subhead", ""),
        user_body=brief.get("body", ""), user_cta_text=brief.get("cta", ""),
        wizard_format=brief.get("format", "feed"),
        render_png=True, art_director=True, vision_qa=True)
    png = _png(res) if res.get("ok") else None
    if not png:
        return 0.0, "FAIL", None
    ev = evaluate(png, brief, "metta", res.get("vision_qa"), res.get("critic"),
                  decision_log=_dl(res.get("run_id")))
    return float(ev.get("geral") or 0), ev.get("verdict", "?"), png


def main():
    briefs = [b for b in json.loads((ROOT / "data" / "golden-set.json").read_text())["briefs"]
              if b["id"] in IDS]
    rows = []
    for b in briefs:
        print(f"\n=== {b['id']} ({b['model']}) ===")
        # BASELINE (texto)
        sa, va, pa = _gen(b)
        print(f"  baseline      → {va} nota={sa}")
        # REFERENCE-AWARE
        q = " ".join(filter(None, [b.get("headline"), b.get("subhead"), b.get("body")]))
        ref = pick_reference(q, "metta")
        enr = enrich_scene(ref, b, "", "metta") if ref else {"ok": False}
        if enr.get("ok"):
            sb, vb, pb = _gen(b, briefing_image=enr["enriched_prompt"])
            print(f"  reference-aware→ {vb} nota={sb}  (ref={enr['reference_id']})")
            print(f"     herdou: {enr.get('borrowed','')[:90]}")
        else:
            sb, vb, pb = 0.0, "SKIP", None
            print(f"  reference-aware→ SKIP ({enr.get('reason','sem ref')})")
        fold = OUT / b["id"]; fold.mkdir(exist_ok=True)
        if pa: (fold / "baseline.png").write_bytes(pa)
        if pb: (fold / "refaware.png").write_bytes(pb)
        rows.append((b["id"], sa, va, sb, vb, ref["id"] if ref else "-"))

    print("\n\n===== A/B QUALIDADE — baseline vs reference-aware =====")
    print(f"{'brief':16s} {'base':>6s} {'refaware':>9s} {'Δ':>6s}  ref")
    lifts = []
    for bid, sa, va, sb, vb, rid in rows:
        d = round(sb - sa, 2)
        lifts.append(d)
        print(f"{bid:16s} {sa:6.1f} {sb:9.1f} {d:+6.2f}  {rid}")
    if lifts:
        print(f"\nlift médio: {sum(lifts)/len(lifts):+.2f} nota  ·  output em {OUT}")


if __name__ == "__main__":
    main()
