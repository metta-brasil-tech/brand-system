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
os.environ.setdefault("ARTIFACTS_DIR", str(ROOT / "render_out" / "artifacts"))

import generate as gen                       # noqa: E402
from _blueprint_render import list_blueprints  # noqa: E402


def _infer_marca(model_id: str) -> str:
    """Mesma regra do pipeline: a marca dona do model_id (default metta)."""
    for marca, ids in list_blueprints().items():
        if model_id in ids:
            return marca
    return "metta"


def _shell_quote(s: str) -> str:
    return "'" + (s or "").replace("'", "'\\''") + "'"


def _modo_b(args, marca: str) -> bool:
    """Propõe a copy a partir de --theme, aplica a escolha em args (vira copy literal).

    Retorna True para seguir gerando; False para parar (--propose-only ou abortado).
    """
    from _copywriter import propose_copy
    print(f"MODO B — propondo copy para o tema (marca={marca})...\n  tema: {args.theme}")
    p = propose_copy(args.theme, marca)
    if not p.get("ok"):
        print("\nERRO ao propor copy:", p.get("reason"))
        sys.exit(1)

    heads = [h for h in (p.get("headlines") or []) if str(h).strip()]
    if not heads:
        print("\nERRO: o copywriter não retornou headlines.")
        sys.exit(1)

    print("\nProposta (ancorada no ICP/voz/método):")
    print("  ângulo    :", p.get("angulo") or "—")
    for i, h in enumerate(heads, 1):
        print(f"  headline {i}: {h}")
    print("  subhead   :", p.get("subhead") or "—")
    print("  cta       :", p.get("cta") or "—")
    print("  fundamento:", p.get("fundamento") or "—")
    if p.get("grounded_in"):
        print("  ancorado em:", ", ".join(str(g) for g in p["grounded_in"]))

    # --propose-only: mostra o comando Modo A equivalente (headline 1) e para.
    if args.propose_only:
        cmd = (f"\npython cli.py --model {args.model} --format {args.format} "
               f"--image {args.image} --preset {args.preset}\n"
               f"    --headline {_shell_quote(heads[0])}")
        if p.get("subhead"):
            cmd += f" --subhead {_shell_quote(p['subhead'])}"
        if p.get("cta"):
            cmd += f" --cta {_shell_quote(p['cta'])}"
        print("\nComando Modo A equivalente (headline 1):", cmd)
        return False

    # Escolha da headline: --pick (não-interativo) > prompt (TTY) > headline 1 (fallback).
    if args.pick and 1 <= args.pick <= len(heads):
        idx = args.pick - 1
    elif args.pick:
        print(f"\n--pick {args.pick} fora de [1..{len(heads)}].")
        sys.exit(1)
    elif sys.stdin.isatty():
        raw = input(f"\nEscolha a headline [1-{len(heads)}], ou 0 p/ abortar: ").strip()
        if not raw.isdigit() or int(raw) == 0:
            print("Abortado.")
            return False
        idx = max(1, min(int(raw), len(heads))) - 1
    else:
        idx = 0
        print("\n(sem TTY e sem --pick) usando headline 1.")

    # A escolha vira copy LITERAL. Subhead/CTA da proposta só preenchem se o user não passou.
    args.headline = heads[idx]
    if not args.subhead.strip():
        args.subhead = p.get("subhead") or ""
    if not args.cta.strip():
        args.cta = p.get("cta") or ""
    print(f"\n✓ Copy aprovada (headline {idx + 1}) → segue no pipeline (Modo A).")
    return True


def main():
    ap = argparse.ArgumentParser(description="Gera um ad Metta (pipeline blueprint-driven).")
    ap.add_argument("--list", action="store_true", help="lista os modelos disponíveis e sai")
    ap.add_argument("--model", help="id do modelo (ex: A-headline-foto-dark). Veja --list")
    ap.add_argument("--headline", default="", help="headline (obrigatória)")
    ap.add_argument("--subhead", default="")
    ap.add_argument("--body", default="", help="corpo; use \\n entre linhas pra virar bullets (YELLOW-BLOCO)")
    ap.add_argument("--cta", default="")
    ap.add_argument("--tag", default="", help="eyebrow/label (ex: NEWS-CARD, K)")
    # MODO B (ideia→copy): em vez de --headline literal, dá um tema; o sistema PROPÕE
    # a copy ancorada no ICP/voz/método (api/_copywriter) → você aprova → vira literal.
    ap.add_argument("--theme", default="",
                    help="MODO B: tema/ângulo → propõe copy ancorada no ICP. Dispensa --headline")
    ap.add_argument("--marca", default="", choices=["", "metta", "tiago"],
                    help="marca p/ o copywriter do --theme (default: inferida do --model)")
    ap.add_argument("--pick", type=int, default=0,
                    help="MODO B: usa a headline N (1-based) sem perguntar. 0 = pergunta (se TTY)")
    ap.add_argument("--propose-only", action="store_true",
                    help="MODO B: só propõe a copy e mostra o comando Modo A equivalente; não gera")
    ap.add_argument("--format", default="feed", choices=["feed", "story", "sqr"])
    ap.add_argument("--image", default="generate", choices=["generate", "none"],
                    help="generate = gera foto via IA; none = sem foto (modelos tipográficos)")
    ap.add_argument("--preset", default="fotorrealista",
                    help="tratamento da foto: fotorrealista | cinematic-dark | bw-yellow | surreal-hbr")
    ap.add_argument("--avatar-segment", default="", help="segmento do ICP (avatars.json) — ancora quem aparece na cena no diretor de arte")
    ap.add_argument("--avatar-variant", default="", help="variante do avatar (mood/pose) — ver engine/brand-knowledge/audience/avatars.json")
    ap.add_argument("--auto-improve", action="store_true",
                    help="FASE 6: loop gera→avalia→regera até SHIP (ou --max-attempts). Só com --image generate")
    ap.add_argument("--max-attempts", type=int, default=3, help="teto de tentativas do --auto-improve")
    ap.add_argument("--no-art-director", action="store_true", help="desliga composição/direção visual")
    ap.add_argument("--no-vision-qa", action="store_true", help="desliga a checagem final por visão")
    ap.add_argument("--out", default=str(ROOT / "render_out" / "out"), help="pasta de saída (default ./render_out/out)")
    args = ap.parse_args()

    if args.list:
        for marca, ids in list_blueprints().items():
            print(f"\n[{marca}]  ({len(ids)} modelos)")
            for i in ids:
                print("   ", i)
        return

    if not args.model:
        ap.error("informe --model (ou use --list pra ver os modelos)")
    if not args.theme.strip() and not args.headline.strip():
        ap.error("informe --headline (Modo A) ou --theme (Modo B: propõe a copy)")
    if not os.getenv("OPENAI_API_KEY"):
        ap.error("defina OPENAI_API_KEY no ambiente (export OPENAI_API_KEY=sk-...)")

    # MODO B — tema → proposta de copy ancorada no ICP → aprovação → vira literal (Modo A).
    if args.theme.strip():
        marca = args.marca or _infer_marca(args.model)
        if not _modo_b(args, marca):
            return  # --propose-only ou abortado

    print(f"Gerando '{args.model}' ({args.format}, imagem={args.image})...")
    brief = dict(
        briefing_text="cli", mock=False, forced_model_id=args.model,
        image_source=args.image,
        image_style_preset=(None if args.image == "none" else args.preset),
        user_headline=args.headline, user_subhead=args.subhead, user_body=args.body,
        user_cta_text=args.cta, user_tag=args.tag, wizard_format=args.format,
        avatar_segment=args.avatar_segment or None,
        avatar_variant=args.avatar_variant or None,
        render_png=True, art_director=not args.no_art_director,
        vision_qa=not args.no_vision_qa,
    )
    if args.auto_improve and args.image == "generate":
        from _autogen import generate_until_approved
        best, hist = generate_until_approved(brief, max_attempts=max(1, args.max_attempts))
        res = best.get("result") or {}
        if res.get("ok"):
            res["evaluation"] = best.get("eval") or res.get("evaluation") or {}
            print(f"  auto-improve: {len(hist)} tentativa(s) · melhor=#{best.get('attempt')} "
                  f"nota={best.get('score')}")
    else:
        res = gen._run_pipeline_inline(**brief)

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
    _ev = res.get("evaluation") or {}
    if _ev.get("verdict") or _ev.get("geral") is not None:
        _anc = (_ev.get("scores") or {}).get("ancoragem")
        print(f"  avaliação: {_ev.get('verdict')} nota={_ev.get('geral')}"
              + (f" · ancoragem={_anc}" if _anc is not None else "")
              + "  (FASE 6 / FINAL_EVAL)")
    print("  html   :", base.with_suffix(".html"))
    if res.get("png_data_uri"):
        print("  png    :", base.with_suffix(".png"))
    else:
        print("  png    : NÃO gerado (Chromium ausente) — abra o .html no navegador.")
    print("\nDiagnóstico:")
    for d in res.get("diagnostics", []):
        if any(k in d for k in ["art-director", "diretor-visual", "knowledge", "decision-log", "04-avatar", "04-image-gen", "vision-qa", "critic", "final-eval", "export-png", "render-html"]):
            print("  ·", d)


if __name__ == "__main__":
    main()
