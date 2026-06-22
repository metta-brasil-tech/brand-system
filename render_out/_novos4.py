#!/usr/bin/env python3
"""Gera 4 criativos novos (padrões de sempre) — cada um na sua pasta.

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_novos4.py
"""
from __future__ import annotations

import base64
import json
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

# (model, headline, subhead, body, cta, preset, formato) — padrões de sempre
BRIEFS = [
    ("A-headline-foto-dark",
     "Sua operação tem método ou tem sorte?",
     "Quando o processo é claro, a próxima venda deixa de ser aposta.",
     "", "Conheça a Metta", "cinematic-dark", "feed"),
    ("D-foto-fullbleed-overlay",
     "Crescer deixou de ser sorte.",
     "Método transforma operação em resultado previsível.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
    ("YELLOW-BLOCO",
     "Sua operação tem método ou tem sorte?",
     "",
     "Processo estruturado\nIndicadores que orientam\nRitmo de gestão semanal",
     "Aplique para a mentoria", "fotorrealista", "feed"),
    ("DARK-OBJETO",
     "Vendedor herói não é estratégia.",
     "Método transforma esforço em previsibilidade.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
]


def _save_img(data_uri_or_url: str, dest: Path) -> bool:
    if not data_uri_or_url:
        return False
    if data_uri_or_url.startswith("data:"):
        dest.write_bytes(base64.b64decode(data_uri_or_url.split(",", 1)[1]))
        return True
    try:
        import requests
        r = requests.get(data_uri_or_url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception:
        return False


def main() -> None:
    summary = []
    for i, (model, h, s, body, cta, preset, fmt) in enumerate(BRIEFS, start=1):
        folder = OUT / f"{i:02d}-{model}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{i}/{len(BRIEFS)}] {model} — gerando...")
        try:
            res = gen._run_pipeline_inline(
                briefing_text="lote-novos", mock=False, forced_model_id=model,
                image_source="generate", image_style_preset=preset,
                user_headline=h, user_subhead=s, user_body=body,
                user_cta_text=cta, user_tag="", wizard_format=fmt,
                render_png=True, art_director=True, vision_qa=True,
            )
        except Exception as e:
            print(f"   ERRO: {e.__class__.__name__}: {e}")
            (folder / "ERRO.txt").write_text(f"{e.__class__.__name__}: {e}", encoding="utf-8")
            summary.append((i, model, "EXC", "?"))
            continue

        if not res.get("ok"):
            print(f"   FALHOU: {res.get('error')}")
            (folder / "ERRO.txt").write_text(str(res.get("error")) + "\n\n"
                                             + "\n".join(res.get("diagnostics", [])), encoding="utf-8")
            summary.append((i, model, "FAIL", "?"))
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
- body: {body.replace(chr(10), ' · ') or '—'}
- cta: {cta}
- preset: {preset} · formato: {fmt}
- qa: {(res.get('qa') or {}).get('status')}
- vision-qa: {vqa.get('verdict')} (rel={vqa.get('relevance')} integ={vqa.get('integrity')})
- crítico: {cr.get('verdict')} {cr.get('reason','')}
""", encoding="utf-8")
        print(f"   OK · qa={(res.get('qa') or {}).get('status')} visão={vqa.get('verdict')} crítico={cr.get('verdict')}")
        summary.append((i, model, "OK", vqa.get("verdict", "?")))

    print("\n===== RESUMO =====")
    for i, model, st, v in summary:
        print(f" {i}. {model:28s} {st:5s} visão={v}")
    print(f"\nTudo em: {OUT}")


if __name__ == "__main__":
    main()
