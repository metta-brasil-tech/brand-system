#!/usr/bin/env python3
"""Recria 6 peças do FEED ATUAL quase-idênticas — copy EXATA dos posts + cena casada.

Diferente de criativos-atuais/ (que escreveu copy própria do conhecimento), aqui a copy
e a direção de cena são TRAVADAS no post original (engenharia reversa do print). Fotos
são "cena-fiel gerada" (mesmo enquadramento/clima/pose; rosto novo) — aprovado pelo Nathan.

Cada peça roda o pipeline COMPLETO (ICP/_knowledge, diretor de arte, vision-QA, crítico),
igual aos criativos atuais. Chama o pipeline, não edita.

DRY_RUN=1 (padrão): só mostra o plano (sem custo). DRY_RUN=0: gera de verdade.

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_gen_feed_replica.py            # dry-run
  DRY_RUN=0 python3.11 render_out/_gen_feed_replica.py  # gera
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
OUT = ROOT / "render_out" / "feed-replica"
ART = OUT / "artifacts"
OUT.mkdir(parents=True, exist_ok=True); ART.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "low")   # conserva crédito; sobe nos aprovados depois
os.environ["VISION_QA_MAX"] = "1"
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ART)

PRESET = "cinematic-dark"  # tratamento de foto uniforme do feed

# 6 peças — copy EXATA do post + cena casada. src "none" = tipográfico (custo zero).
PIECES = [
    {
        "ref": "post: xadrez (rei)", "model": "DARK-OBJETO", "src": "generate",
        "headline": "Sabe a diferença entre a empresa que sofre pra bater meta e a que bate a meta todos os meses?",
        "subhead": "", "body": "", "cta": "", "tag": "",
        "scene": ("A single black CHESS KING piece standing isolated and dominant at the center, "
                  "dark moody background, dramatic warm golden rim light from the right edge, long "
                  "dramatic cast shadow, vast empty dark negative space around it, photorealistic "
                  "editorial product photography, no other pieces, no board clutter"),
    },
    {
        "ref": "post: GESTÃO/PRESSÃO", "model": "C-tipografia-pura-dark", "src": "none",
        "headline": "Quem não sabe fazer *GESTÃO* acaba fazendo *PRESSÃO* no time.",
        "subhead": "", "body": "", "cta": "", "tag": "",
        "scene": "",
    },
    {
        "ref": "post: diagnóstico comercial", "model": "B-foto-top-headline-mixed", "src": "generate",
        "headline": "O que um diagnóstico comercial revela que a *cobrança* não mostra.",
        "subhead": "", "body": "", "cta": "", "tag": "Inteligência Comercial",
        "scene": ("Middle-aged Brazilian businessman seen in PROFILE, pensive and serious, looking "
                  "toward a bright window with soft natural side light, modern office softly blurred "
                  "behind him, editorial desaturated documentary photography, subject in the upper "
                  "portion of the frame, calm contemplative mood, warm side light"),
    },
    {
        "ref": "post: quanto mais você cobra", "model": "A-headline-foto-dark", "src": "generate",
        "headline": "Quanto mais você cobra, mais o time *espera você*.",
        "subhead": "Dependência disfarçada de gestão ainda continua sendo dependência.",
        "body": "", "cta": "", "tag": "",
        "scene": ("Close editorial portrait of a serious Brazilian man, dark desaturated high-contrast "
                  "lighting, a bold YELLOW diagonal hazard stripe band entering from the right edge of "
                  "the frame, moody near-black background, gaze slightly off-camera, dramatic shadows"),
    },
    {
        "ref": "post: jornada do desengajamento", "model": "D-foto-fullbleed-overlay", "src": "generate",
        "headline": "A jornada do desengajamento.",
        "subhead": "Por que seu vendedor sai antes de vender?",
        "body": "", "cta": "", "tag": "",
        "scene": ("Cinematic full-bleed photograph of a man seen from BEHIND, back to camera, walking "
                  "away and leaving a dim corporate office, silhouette against low ambient light, moody "
                  "and somber, sense of departure and disengagement, dark tones, lower third kept "
                  "darker as empty space for text overlay"),
    },
    {
        "ref": "post: cultura comercial (tagline)", "model": "K-bold-dourado-urgencia", "src": "none",
        "headline": "Meta batida uma vez é esforço. Meta batida todo mês é *cultura*.",
        "subhead": "", "body": "", "cta": "", "tag": "",
        "scene": "",
    },
]


def main():
    dry = os.getenv("DRY_RUN", "1") == "1"
    print(f"=== FEED-REPLICA · {len(PIECES)} peças · preset={PRESET} · {'DRY-RUN' if dry else 'GERANDO'} ===")
    for i, p in enumerate(PIECES, 1):
        foto = "não" if p["src"] == "none" else "sim"
        print(f"  {i}. {p['model']:30s} foto={foto:3s} «{p['headline'][:46]}»  [{p['ref']}]")
        if p["scene"]:
            print(f"       cena: {p['scene'][:88]}…")
    if dry:
        print("\n(DRY-RUN — nada gerado. DRY_RUN=0 pra gerar.)")
        return

    from generate import _run_pipeline_inline
    manifest = []
    for i, p in enumerate(PIECES, 1):
        src = p["src"]
        brief = p["scene"] or p["headline"]
        print(f"\n[{i}/{len(PIECES)}] {p['model']} (foto={src})…", flush=True)
        try:
            res = _run_pipeline_inline(
                briefing_text=brief, forced_model_id=p["model"], image_source=src,
                image_style_preset=(None if src == "none" else PRESET),
                user_headline=p["headline"], user_subhead=p.get("subhead", ""),
                user_body=p.get("body", ""), user_cta_text=p.get("cta", ""),
                user_tag=p.get("tag", "") or None,
                wizard_format="feed", render_png=True, art_director=True, vision_qa=True)
        except Exception as e:
            print(f"   ERRO {e.__class__.__name__}: {e}", flush=True)
            manifest.append({"n": i, "model": p["model"], "ok": False, "error": str(e)})
            continue
        uri = (res.get("png_data_uri") or "") if res.get("ok") else ""
        if uri.startswith("data:"):
            (OUT / f"{i:02d}-{p['model']}.png").write_bytes(base64.b64decode(uri.split(",", 1)[1]))
        verdict = res.get("critic", {}).get("verdict")
        print(f"   → ok={res.get('ok')} qa={res.get('qa',{}).get('status')} crítico={verdict}", flush=True)
        manifest.append({"n": i, "model": p["model"], "ref": p["ref"], "foto": src == "generate",
                         "headline": p["headline"], "ok": res.get("ok"), "critic": verdict})
    (OUT / "manifest.json").write_text(
        json.dumps({"preset": PRESET, "pieces": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {OUT}/NN-MODELO.png")


if __name__ == "__main__":
    main()
