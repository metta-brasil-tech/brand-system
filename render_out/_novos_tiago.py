#!/usr/bin/env python3
"""Gera 2 criativos abstratos do Tiago — mesma pasta do lote."""
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
os.environ.setdefault("VISION_QA_MAX", "1")
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ROOT / "artifacts")

import generate as gen  # noqa: E402

OUT = ROOT / "render_out" / "criativos-novos-21jun"
OUT.mkdir(parents=True, exist_ok=True)

BRIEFS = [
    ("TIAGO-DARK-SURREAL",
     "O silêncio também é decisão.",
     "Liderar é escolher o que não fazer.",
     "", "Siga @tiagoalves", "surreal-hbr", "feed"),
    ("TIAGO-EDITORIAL-HERO",
     "Você virou refém da própria empresa.",
     "Dono não devia trabalhar como funcionário.",
     "", "Saiba mais", "surreal-hbr", "feed"),
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
    for i, (model, h, s, body, cta, preset, fmt) in enumerate(BRIEFS, start=5):
        folder = OUT / f"{i:02d}-{model}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{model}] gerando...")
        try:
            res = gen._run_pipeline_inline(
                briefing_text="lote-tiago", mock=False, forced_model_id=model,
                image_source="generate", image_style_preset=preset,
                user_headline=h, user_subhead=s, user_body=body,
                user_cta_text=cta, user_tag="", wizard_format=fmt,
                render_png=True, art_director=True, vision_qa=True,
            )
        except Exception as e:
            print(f"   ERRO: {e.__class__.__name__}: {e}")
            (folder / "ERRO.txt").write_text(f"{e.__class__.__name__}: {e}", encoding="utf-8")
            continue
        if not res.get("ok"):
            print(f"   FALHOU: {res.get('error')}")
            (folder / "ERRO.txt").write_text(str(res.get("error")), encoding="utf-8")
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
""", encoding="utf-8")
        print(f"   OK · qa={(res.get('qa') or {}).get('status')} visão={vqa.get('verdict')} crítico={cr.get('verdict')}")


if __name__ == "__main__":
    main()
