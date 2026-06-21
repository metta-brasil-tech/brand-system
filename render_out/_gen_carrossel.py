#!/usr/bin/env python3
"""Gera um CARROSSEL coerente — usa _serie.py (Fase 9/10) + o pipeline (chamando, não editando).

Resolve o problema que o Nathan apontou: hoje cada slide é gerado independente (sem
coesão). Aqui: plan_serie trava a família + escolhe capa visual / miolo variado /
fecho CTA (sem repetir) → gera cada slide pelo pipeline → valida C1–C8 → salva.

DRY_RUN=1 (padrão): só mostra o plano + validação, NÃO gera imagem (sem custo).
DRY_RUN=0: gera de verdade.

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_gen_carrossel.py            # dry-run (plano só)
  DRY_RUN=0 python3.11 render_out/_gen_carrossel.py  # gera
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
OUT = ROOT / "render_out" / "carrossel"
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

from _serie import plan_serie, validate_serie, model_info  # noqa: E402

MARCA = "metta"
# Narrativa de carrossel (hook → desenvolve → reframe → fecho CTA)
SLIDES = [
    {"headline": "Meta batida num mês, furada no outro.", "subhead": "", "body": "", "cta": ""},
    {"headline": "Quando o resultado depende do humor do time, ele é do acaso.", "subhead": "", "body": "", "cta": ""},
    {"headline": "Previsibilidade não é sorte — é método rodando todo dia.", "subhead": "", "body": "", "cta": ""},
    {"headline": "Pare de torcer pela meta. Construa ela.", "subhead": "", "body": "", "cta": "Conheça a Metta"},
]


def main():
    dry = os.getenv("DRY_RUN", "1") == "1"
    plan = plan_serie([s["headline"] for s in SLIDES], MARCA)
    seq = plan["treatments_por_slide"]
    print(f"=== CARROSSEL {MARCA} · {len(SLIDES)} slides · família={plan['family']} · {'DRY-RUN' if dry else 'GERANDO'} ===")
    print("Direção de série (plan_serie):")
    for i, (m, s) in enumerate(zip(seq, SLIDES), 1):
        info = model_info(m)
        src = "none" if info["typographic"] else "generate"
        print(f"  slide {i}: {m:30s} família={info['family']:5s} foto={'não' if src=='none' else 'sim'}  «{s['headline'][:42]}»")
    print(f"motivos: {plan['motivos']}")
    v = validate_serie([{"style": m, "cta": SLIDES[i].get('cta', '')} for i, m in enumerate(seq)])
    print(f"\nvalidação C1–C8: ok={v['ok']}")
    for x in v["issues"]:
        print("  ❌", x)
    for x in v["warnings"]:
        print("  ⚠️ ", x)

    if dry:
        print("\n(DRY-RUN — nada gerado. Rode com DRY_RUN=0 pra gerar de verdade.)")
        return

    from generate import _run_pipeline_inline
    manifest = []
    for i, (m, slide) in enumerate(zip(seq, SLIDES), 1):
        info = model_info(m)
        src = "none" if info["typographic"] else "generate"
        print(f"\n[slide {i}/{len(SLIDES)}] {m} (foto={src})…")
        try:
            res = _run_pipeline_inline(
                briefing_text="carrossel", forced_model_id=m, image_source=src,
                image_style_preset=(None if src == "none" else "fotorrealista"),
                user_headline=slide["headline"], user_subhead=slide.get("subhead", ""),
                user_body=slide.get("body", ""), user_cta_text=slide.get("cta", ""),
                wizard_format="feed", render_png=True, art_director=True, vision_qa=True)
        except Exception as e:
            print(f"   ERRO {e.__class__.__name__}: {e}")
            manifest.append({"slide": i, "model": m, "ok": False})
            continue
        uri = res.get("png_data_uri") or "" if res.get("ok") else ""
        if uri.startswith("data:"):
            (OUT / f"slide-{i}.png").write_bytes(base64.b64decode(uri.split(",", 1)[1]))
        print(f"   → ok={res.get('ok')} qa={res.get('qa',{}).get('status')} crítico={res.get('critic',{}).get('verdict')}")
        manifest.append({"slide": i, "model": m, "foto": src == "generate",
                         "ok": res.get("ok"), "critic": res.get("critic", {}).get("verdict")})
    (OUT / "manifest.json").write_text(json.dumps({"marca": MARCA, "plan": plan, "slides": manifest},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nCarrossel salvo em {OUT}/slide-N.png  (validação C1–C8: ok={v['ok']})")


if __name__ == "__main__":
    main()
