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
# Tema do carrossel (usado no COPY_MODE=auto, que escreve a copy ancorada no acervo)
THEME = os.getenv("CARROSSEL_THEME",
                  "previsibilidade de meta deixa de ser sorte quando vira método rodando todo dia")

# Narrativa manual (fallback p/ DRY-RUN offline ou COPY_MODE=manual). Agora cada slide
# carrega `role` + `visual` (direção de cena) — é o que torna a seleção ciente da copy.
SLIDES = [
    {"role": "hook", "headline": "Meta batida num mês, furada no outro.", "subhead": "", "body": "", "cta": "",
     "visual": "calendário/painel de metas com um mês verde e o seguinte vermelho, objeto-conceito sobre dark moody"},
    {"role": "desenvolve", "headline": "Quando o resultado depende do humor do time, ele é do acaso.", "subhead": "", "body": "", "cta": "",
     "visual": "cena humana de equipe comercial tensa numa sala, luz editorial, foco no clima instável"},
    {"role": "reframe", "headline": "Previsibilidade não é sorte — é método rodando todo dia.", "subhead": "", "body": "", "cta": "",
     "visual": "statement tipográfico sobre o conceito de método/sistema; engrenagem/dado como âncora discreta"},
    {"role": "cta", "headline": "Pare de torcer pela meta. Construa ela.", "subhead": "", "body": "", "cta": "Conheça a Metta",
     "visual": "fechamento com peso de convite oficial; selo/moldura, dourado cirúrgico"},
]


def _load_slides():
    """COPY_MODE=auto escreve a copy do carrossel ancorada no acervo (precisa de chave LLM).
    Senão usa a narrativa manual acima. Retorna (slides, origem)."""
    mode = os.getenv("COPY_MODE", "manual").lower()
    if mode == "auto" and (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")):
        from _copywriter import propose_carousel_copy
        n = int(os.getenv("CARROSSEL_N", "4"))
        prop = propose_carousel_copy(THEME, MARCA, n_slides=n)
        if prop.get("ok") and prop.get("slides"):
            print(f"[copy] COPY_MODE=auto — ângulo: {prop.get('angulo','')[:80]}")
            return prop["slides"], "auto"
        print(f"[copy] auto falhou ({prop.get('reason','?')}) — usando narrativa manual")
    return SLIDES, "manual"


def main():
    dry = os.getenv("DRY_RUN", "1") == "1"
    slides, origem = _load_slides()
    plan = plan_serie(slides, MARCA)                # ciente da copy (passa os dicts inteiros)
    seq = plan["treatments_por_slide"]
    preset = plan.get("preset", "fotorrealista")    # tratamento de foto uniforme da série
    print(f"=== CARROSSEL {MARCA} · {len(slides)} slides · copy={origem} · família={plan['family']} · preset(foto uniforme)={preset} · {'DRY-RUN' if dry else 'GERANDO'} ===")
    print("Direção de série (plan_serie · seleção CIENTE DA COPY):")
    for r, s in zip(plan["selecao"], slides):
        m = r["model"]
        foto = "sim" if r["foto"] else "não"
        print(f"  slide {r['slide']}: {m:30s} [{r['role']:11s}] família={model_info(m)['family']:5s} foto={foto} score={r['score']:>4}  «{(s.get('headline') or '')[:40]}»")
    print(f"capa (direção de cena forte): «{plan.get('cover_direction','')[:80]}»")
    print(f"motivos: {plan['motivos']}")
    v = validate_serie([{"style": m, "cta": slides[i].get('cta', '')} for i, m in enumerate(seq)])
    print(f"\nvalidação C1–C8: ok={v['ok']}")
    for x in v["issues"]:
        print("  ❌", x)
    for x in v["warnings"]:
        print("  ⚠️ ", x)

    if dry:
        print("\n(DRY-RUN — nada gerado. Rode com DRY_RUN=0 pra gerar de verdade.)")
        return

    from generate import _run_pipeline_inline
    briefs = plan.get("briefs_por_slide") or [s.get("visual", "") for s in slides]
    manifest = []
    for i, (m, slide) in enumerate(zip(seq, slides), 1):
        info = model_info(m)
        src = "none" if info["typographic"] else "generate"
        # briefing_text = direção visual do slide (capa mais forte) — NÃO mais "carrossel"
        brief = (briefs[i - 1] if i - 1 < len(briefs) else "") or slide.get("headline", "") or "carrossel"
        print(f"\n[slide {i}/{len(slides)}] {m} (foto={src}) cena: «{brief[:60]}»…")
        try:
            res = _run_pipeline_inline(
                briefing_text=brief, forced_model_id=m, image_source=src,
                image_style_preset=(None if src == "none" else preset),
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
