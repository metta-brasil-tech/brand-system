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
  python cli.py --serie slides.json --plan-only     # só o plano da série (sem custo)
  python cli.py --serie slides.json --format feed   # gera o carrossel inteiro

Saída: HTML + PNG em ./out/. PNG exige Chromium (Playwright ou Chrome instalado).
Requer OPENAI_API_KEY no ambiente.
"""
import json
import os
import re
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


def run_serie(args):
    """Modo carrossel: planeja a série (regras C1-C8 mecânicas), gera N slides.

    O plano vem de api/_serie.py (porta das serie-rules do plugin-metta-ads):
    classificação copy→tratamento, ponte tratamento→blueprint, família travada
    no slide 1. Coerência visual (motivos, marca) segue sendo olho do critic.
    """
    from _serie import plan_serie, validate_serie, familia_hint_from

    raw = json.loads(Path(args.serie).read_text(encoding="utf-8"))
    slides = raw.get("slides") if isinstance(raw, dict) else raw
    if not isinstance(slides, list) or not slides:
        sys.exit(f"--serie: {args.serie} precisa ser lista de slides ou {{\"slides\":[...]}}")
    for i, sl in enumerate(slides, 1):
        if not str(sl.get("headline", "")).strip():
            sys.exit(f"--serie: slide {i} sem headline")

    if args.panorama and not (2 <= len(slides) <= 4):
        sys.exit("--panorama: a cena contínua só funciona com 2-4 slides")

    if args.panorama:
        # Panorama: UMA cena atravessa a série — todos os slides são foto-fullbleed
        # com a fatia como fundo. continued marca a repetição legítima (C3) e o
        # último slide leva o CTA sobre a última fatia (C2 via T-CTA-FINAL).
        n = len(slides)
        plan = {"n_slides": n, "familia": "DARK", "panorama": True, "slides": [{
            "slide": i + 1,
            "position": "capa" if i == 0 else ("fim" if i == n - 1 else "meio"),
            "treatment": "T-CTA-FINAL" if i == n - 1 else "T-FOTO-CENA",
            "model": "D-foto-fullbleed-overlay", "familia": "DARK",
            "needs_image": False,  # a imagem vem da fatia, não do gerador por slide
            "continued": i > 0,
        } for i in range(n)]}
        avoid = None
    else:
        avoid = familia_hint_from(ROOT / "render_out")
        if avoid:
            print(f"anti-monotonia: últimas 2 séries foram {avoid} — preferindo outra família na capa")
        plan = plan_serie(slides, avoid_familia=avoid)
    issues = validate_serie(plan)
    print(f"Série de {plan['n_slides']} slides · família travada: {plan['familia']} · formato: {args.format}"
          + (" · PANORAMA" if args.panorama else ""))
    for s in plan["slides"]:
        print(f"  {s['slide']} {s['position']:<5} {s['treatment']:<20} {s['model']:<28} "
              f"{s['familia']:<6} img={'sim' if s['needs_image'] else 'não'}")
    for x in issues:
        print("  ⚠", x)
    if args.plan_only:
        return
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("defina OPENAI_API_KEY no ambiente (export OPENAI_API_KEY=sk-...)")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Panorama: gera a cena contínua UMA vez e fatia — cada slide recebe a sua
    # fatia como foto (data URI). 1 chamada de imagem pra série toda.
    pano_slices: list[str] = []
    if args.panorama:
        from _nano_pipeline import generate_panorama
        print(f"\nGerando panorama ({plan['n_slides']} fatias)...")
        raws, pmeta = generate_panorama(args.panorama, n_slides=plan["n_slides"])
        pano_slices = ["data:image/png;base64," + base64.b64encode(b).decode("ascii")
                       for b in raws]
        print(f"  panorama ok · {pmeta['size'][0]}×{pmeta['size'][1]} · ref={pmeta.get('ref_id')} "
              f"· {pmeta['ms']}ms")

    def _gen_slide(s, sl):
        gen_img = s["needs_image"] and args.image != "none" and not pano_slices
        slice_uri = pano_slices[s["slide"] - 1] if pano_slices else None
        return gen._run_pipeline_inline(
            briefing_text="cli-serie", mock=False, forced_model_id=s["model"],
            image_source="upload" if slice_uri else ("generate" if gen_img else "none"),
            image_url=slice_uri,
            image_style_preset=(args.preset if gen_img else None),
            user_headline=str(sl.get("headline", "")),
            user_subhead=str(sl.get("subhead", "")),
            # marcador de lista ("- ", "• ") serviu pra classificação; o
            # blueprint de bullets põe o próprio marcador — tira o duplicado
            user_body=re.sub(r"(?m)^\s*[-•*]\s+", "", str(sl.get("body", ""))),
            user_cta_text=str(sl.get("cta", "")), user_tag=str(sl.get("tag", "")),
            wizard_format=args.format,
            avatar_segment=args.avatar_segment or None,
            avatar_variant=args.avatar_variant or None,
            render_png=True, art_director=not args.no_art_director,
            vision_qa=not args.no_vision_qa,
        )

    failed = []
    status_por_slide = {}
    for s, sl in zip(plan["slides"], slides):
        gen_img = (s["needs_image"] and args.image != "none") or bool(pano_slices)
        print(f"\n[{s['slide']}/{plan['n_slides']}] '{s['model']}' "
              f"({s['treatment']}, imagem={'fatia' if pano_slices else ('sim' if gen_img else 'não')})...")
        res = _gen_slide(s, sl)
        if not res.get("ok"):
            # slide ruim trava o conjunto (regra do plugin): 1 retry automático
            print("  falhou (%s) — retry 1/1..." % str(res.get("error"))[:60])
            res = _gen_slide(s, sl)
        base = out / f"ad-slide-{s['slide']}"
        if not res.get("ok"):
            failed.append(s["slide"])
            status_por_slide[s["slide"]] = {"ok": False, "error": str(res.get("error"))[:200]}
            print("  ERRO:", res.get("error"))
            continue
        base.with_suffix(".html").write_text(res["html"], encoding="utf-8")
        if res.get("png_data_uri"):
            base.with_suffix(".png").write_bytes(
                base64.b64decode(res["png_data_uri"].split(",", 1)[1]))
        status_por_slide[s["slide"]] = {
            "ok": True, "qa": (res.get("qa") or {}).get("status"),
            "visao": (res.get("vision_qa") or {}).get("verdict"),
            "png": bool(res.get("png_data_uri")),
        }
        print(f"  ok · qa={((res.get('qa') or {}).get('status'))} "
              f"visão={(res.get('vision_qa') or {}).get('verdict') or '(sem foto)'} "
              f"→ {base.with_suffix('.png' if res.get('png_data_uri') else '.html')}")

    # Pós-check: plano ↔ arquivos no disco + status por slide vão pro config —
    # é o registro que o critic de série e a galeria leem depois.
    missing = [s["slide"] for s in plan["slides"]
               if s["slide"] not in failed and not (out / f"ad-slide-{s['slide']}.png").exists()]
    (out / "serie-config.json").write_text(json.dumps({
        "familia": plan["familia"], "format": args.format,
        "panorama": bool(args.panorama),
        "slides": [{**{k: s[k] for k in ("slide", "position", "treatment", "model", "familia")},
                    **({"continued": True} if s.get("continued") else {}),
                    "status": status_por_slide.get(s["slide"], {})}
                   for s in plan["slides"]],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSérie concluída: {plan['n_slides'] - len(failed)}/{plan['n_slides']} slides em {out}")
    print("  config :", out / "serie-config.json")
    if missing:
        print("  SEM PNG (Chromium ausente?):", missing, "— use os .html")
    if failed:
        print("  FALHARAM:", failed, "— re-rode só esses com --model/--headline (slide ruim trava o conjunto)")
        sys.exit(1)


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
    ap.add_argument("--avatar-segment", default="", help="segmento do ICP (avatars.json) — ancora quem aparece na cena no diretor de arte")
    ap.add_argument("--avatar-variant", default="", help="variante do avatar (mood/pose) — ver engine/brand-knowledge/audience/avatars.json")
    ap.add_argument("--auto-improve", action="store_true",
                    help="FASE 6: loop gera→avalia→regera até SHIP (ou --max-attempts). Só com --image generate")
    ap.add_argument("--max-attempts", type=int, default=3, help="teto de tentativas do --auto-improve")
    ap.add_argument("--no-art-director", action="store_true", help="desliga composição/direção visual")
    ap.add_argument("--no-vision-qa", action="store_true", help="desliga a checagem final por visão")
    ap.add_argument("--serie", default="", metavar="SLIDES_JSON",
                    help="modo carrossel: JSON com os slides ([{headline,subhead,body,cta},...]). "
                         "UM formato por série (--format). Ver content/direcao-arte/serie-carrossel.md")
    ap.add_argument("--plan-only", action="store_true",
                    help="com --serie: só imprime o plano (tratamento/modelo/família por slide) e sai, sem gerar")
    ap.add_argument("--panorama", default="", metavar="CENA",
                    help="com --serie (2-4 slides): UMA cena contínua descrita aqui vira UMA imagem "
                         "panorâmica (Nano Banana) fatiada entre os slides — fundo que se completa no "
                         "swipe. Requer GEMINI_API_KEY. Todos os slides saem em foto-fullbleed.")
    ap.add_argument("--out", default=str(ROOT / "render_out" / "out"), help="pasta de saída (default ./render_out/out)")
    args = ap.parse_args()

    if args.list:
        for marca, ids in list_blueprints().items():
            print(f"\n[{marca}]  ({len(ids)} modelos)")
            for i in ids:
                print("   ", i)
        return

    if args.serie:
        return run_serie(args)

    if not args.model:
        ap.error("informe --model (ou use --list pra ver os modelos)")
    if not args.headline.strip():
        ap.error("informe --headline")
    if not os.getenv("OPENAI_API_KEY"):
        ap.error("defina OPENAI_API_KEY no ambiente (export OPENAI_API_KEY=sk-...)")

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
