#!/usr/bin/env python3
"""Regenera os 4 criativos que deram vision-qa FAIL, AGORA com o loop de regen
ligado (VISION_QA_MAX=3 → até 2 retentativas de cena melhor). Sobrescreve as
pastas existentes no lote."""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "medium")
os.environ["VISION_QA_MAX"] = "3"          # <<< regen LIGADO (até 2 retentativas)
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ROOT / "artifacts")

import generate as gen  # noqa: E402

OUT = ROOT / "render_out" / "criativos-novos-21jun"

# (n da pasta, model, headline, subhead, body, cta, preset, fmt) — só os 4 que falharam
BRIEFS = [
    (1, "A-headline-foto-dark",
     "Sua operação tem método ou tem sorte?",
     "Quando o processo é claro, a próxima venda deixa de ser aposta.",
     "", "Conheça a Metta", "cinematic-dark", "feed"),
    (2, "D-foto-fullbleed-overlay",
     "Crescer deixou de ser sorte.",
     "Método transforma operação em resultado previsível.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
    (4, "DARK-OBJETO",
     "Vendedor herói não é estratégia.",
     "Método transforma esforço em previsibilidade.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
    (5, "TIAGO-DARK-SURREAL",
     "O silêncio também é decisão.",
     "Liderar é escolher o que não fazer.",
     "", "Siga @tiagoalves", "surreal-hbr", "feed"),
]


def _save_img(uri: str, dest: Path) -> bool:
    if not uri:
        return False
    if uri.startswith("data:"):
        dest.write_bytes(base64.b64decode(uri.split(",", 1)[1]))
        return True
    try:
        import requests
        r = requests.get(uri, timeout=60); r.raise_for_status()
        dest.write_bytes(r.content); return True
    except Exception:
        return False


def main() -> None:
    for n, model, h, s, body, cta, preset, fmt in BRIEFS:
        folder = OUT / f"{n:02d}-{model}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{n:02d} {model}] regenerando (max={os.environ['VISION_QA_MAX']})...")
        res = gen._run_pipeline_inline(
            briefing_text="regen-fails", mock=False, forced_model_id=model,
            image_source="generate", image_style_preset=preset,
            user_headline=h, user_subhead=s, user_body=body,
            user_cta_text=cta, user_tag="", wizard_format=fmt,
            render_png=True, art_director=True, vision_qa=True,
        )
        # quantas tentativas de visão rodaram
        tries = [d for d in res.get("diagnostics", []) if d.startswith("vision-qa (try")]
        regen = [d for d in res.get("diagnostics", []) if "REGENEROU" in d]
        if not res.get("ok"):
            print(f"   FALHOU: {res.get('error')}")
            continue
        if res.get("png_data_uri"):
            _save_img(res["png_data_uri"], folder / "criativo.png")
        (folder / "criativo.html").write_text(res.get("html", ""), encoding="utf-8")
        _save_img(res.get("image_data_uri") or res.get("image_file_url") or "", folder / "imagem-gerada.png")
        vqa = res.get("vision_qa") or {}
        cr = res.get("critic") or {}
        (folder / "info.md").write_text(f"""# {model}
- headline: {h}
- subhead: {s or '—'}
- cta: {cta}
- preset: {preset} · formato: {fmt}
- qa: {(res.get('qa') or {}).get('status')}
- vision-qa: {vqa.get('verdict')} (rel={vqa.get('relevance')} integ={vqa.get('integrity')})
- crítico: {cr.get('verdict')} {cr.get('reason','')}
- tentativas de visão: {len(tries)} · regen de imagem: {len(regen)}
""", encoding="utf-8")
        print(f"   final · visão={vqa.get('verdict')} (rel={vqa.get('relevance')}) "
              f"crítico={cr.get('verdict')} · tentativas={len(tries)} regen-img={len(regen)}")


if __name__ == "__main__":
    main()
