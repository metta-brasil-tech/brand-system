#!/usr/bin/env python3
"""CLI do ad-generator Metta — gera UM ad pelo pipeline blueprint-driven.

A UI (/criar) está oculta; este CLI é a forma suportada de testar localmente.

Exemplos:
  python cli.py --list
  python cli.py --model A-headline-foto-dark \\
      --headline "Crescer deixou de ser sorte." \\
      --subhead "Quando a operação tem método, a próxima venda é previsível." \\
      --cta "Conheça a Metta" --image generate --preset fotorrealista
  python cli.py --model C-tipografia-pura-dark --headline "Vendedor herói não é estratégia." \\
      --cta "Conheça a mentoria" --image none

Saída: HTML + PNG em ./out/. PNG exige Chromium (Playwright ou Chrome instalado).
Requer OPENAI_API_KEY no ambiente.
"""
import os
import sys
import argparse
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "engine"))

# Defaults sensatos — sobrescreva por variável de ambiente se quiser.
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "low")
os.environ.setdefault("ARTIFACTS_DIR", str(ROOT / "artifacts"))

import generate as gen                       # noqa: E402
from _blueprint_render import list_blueprints  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Gera um ad Metta (pipeline blueprint-driven).")
    ap.add_argument("--list", action="store_true", help="lista os modelos disponíveis e sai")
    ap.add_argument("--model", help="id do modelo (ex: A-headline-foto-dark). Veja --list")
    ap.add_argument("--headline", default="", help="headline (obrigatória)")
    ap.add_argument("--subhead", default="")
    ap.add_argument("--body", default="", help="corpo; use \\n entre linhas pra virar bullets (YELLOW-BLOCO)")
    ap.add_argument("--cta", default="")
    ap.add_argument("--tag", default="", help="eyebrow/label (ex: NEWS-CARD, K)")
    ap.add_argument("--format", default="feed", choices=["feed", "story", "sqr"])
    ap.add_argument("--image", default="generate", choices=["generate", "none"],
                    help="generate = gera foto via IA; none = sem foto (modelos tipográficos)")
    ap.add_argument("--preset", default="fotorrealista",
                    help="tratamento da foto: fotorrealista | cinematic-dark | bw-yellow | surreal-hbr")
    ap.add_argument("--no-art-director", action="store_true", help="desliga composição/direção visual")
    ap.add_argument("--no-vision-qa", action="store_true", help="desliga a checagem final por visão")
    ap.add_argument("--out", default=str(ROOT / "out"), help="pasta de saída (default ./out)")
    args = ap.parse_args()

    if args.list:
        for marca, ids in list_blueprints().items():
            print(f"\n[{marca}]  ({len(ids)} modelos)")
            for i in ids:
                print("   ", i)
        return

    if not args.model:
        ap.error("informe --model (ou use --list pra ver os modelos)")
    if not args.headline.strip():
        ap.error("informe --headline")
    if not os.getenv("OPENAI_API_KEY"):
        ap.error("defina OPENAI_API_KEY no ambiente (export OPENAI_API_KEY=sk-...)")

    print(f"Gerando '{args.model}' ({args.format}, imagem={args.image})...")
    res = gen._run_pipeline_inline(
        briefing_text="cli", mock=False, forced_model_id=args.model,
        image_source=args.image,
        image_style_preset=(None if args.image == "none" else args.preset),
        user_headline=args.headline, user_subhead=args.subhead, user_body=args.body,
        user_cta_text=args.cta, user_tag=args.tag, wizard_format=args.format,
        render_png=True, art_director=not args.no_art_director,
        vision_qa=not args.no_vision_qa,
    )

    if not res.get("ok"):
        print("\nERRO:", res.get("error"))
        for d in res.get("diagnostics", []):
            print("  ·", d)
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = out / args.model
    base.with_suffix(".html").write_text(res["html"], encoding="utf-8")
    if res.get("png_data_uri"):
        base.with_suffix(".png").write_bytes(base64.b64decode(res["png_data_uri"].split(",", 1)[1]))

    print("\nOK")
    print("  modelo :", res.get("model_id"))
    print("  qa     :", (res.get("qa") or {}).get("status"))
    print("  visão  :", (res.get("vision_qa") or {}).get("verdict") or "(sem foto)")
    _cr = res.get("critic") or {}
    if _cr.get("verdict"):
        print(f"  crítico: {_cr.get('verdict')}"
              + (f" (vs {_cr.get('reference_id')})" if _cr.get('reference_id') else "")
              + (f" — {_cr.get('reason')}" if _cr.get('reason') else ""))
    print("  html   :", base.with_suffix(".html"))
    if res.get("png_data_uri"):
        print("  png    :", base.with_suffix(".png"))
    else:
        print("  png    : NÃO gerado (Chromium ausente) — abra o .html no navegador.")
    print("\nDiagnóstico:")
    for d in res.get("diagnostics", []):
        if any(k in d for k in ["art-director", "diretor-visual", "04-image-gen", "vision-qa", "critic", "export-png", "render-html"]):
            print("  ·", d)


if __name__ == "__main__":
    main()
