#!/usr/bin/env python3
"""A/B do Briefer A↔B (Fase 12): controle (BRIEFER=0) × tratamento (BRIEFER=1).

Roda o MESMO brief duas vezes e compara o que o refino mudou:
  - prompt de imagem (antes × depois, lido do artefato 04-image-prompt.json)
  - log do briefer (rodadas / aprovação) extraído dos diagnostics
  - vision_qa (relevância copy↔imagem + integridade) e nota do avaliador (FINAL_EVAL)
  - qa + critic

Saída: render_out/ab-briefer/REPORT.md  +  control.png / treatment.png (+ .html).

Precisa das chaves no ambiente (gera imagem de verdade — custa $):
    export OPENAI_API_KEY=sk-...        # gpt-image + (texto, se LLM_PROVIDER=openai)
    # se LLM_PROVIDER=claude (default): export ANTHROPIC_API_KEY=sk-ant-...

Uso:
    python3.11 scripts/ab_briefer.py \
        --model A-headline-foto-dark --preset bw-yellow --format feed \
        --headline "Crescer deixou de ser sorte." \
        --subhead "Quando a operação tem método, a próxima venda é previsível." \
        --cta "Conheça a Metta"
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "engine"))

# Artefatos no mesmo lugar que o CLI usa, pra reler o prompt final de cada run.
ARTIFACTS_DIR = ROOT / "render_out" / "artifacts"
os.environ.setdefault("ARTIFACTS_DIR", str(ARTIFACTS_DIR))
# Local não tem o teto de 60s do Vercel — relaxa o guard pré-image-gen pro briefer
# (1-2 chamadas LLM extras) não disparar abort-timeout.
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "600000")
# Queremos a nota final do avaliador nos dois lados pra comparar.
os.environ.setdefault("FINAL_EVAL", "1")

import generate as gen  # noqa: E402


def _read_prompt(run_id: str) -> str:
    f = ARTIFACTS_DIR / (run_id or "") / "04-image-prompt.json"
    if not f.exists():
        return "(artefato 04-image-prompt.json não encontrado)"
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        prompts = data.get("prompts") or []
        return (prompts[0].get("prompt") if prompts else "") or "(sem prompt)"
    except Exception as e:  # noqa: BLE001
        return f"(erro lendo artefato: {e})"


def _run(brief: dict, briefer_on: bool) -> dict:
    os.environ["BRIEFER"] = "1" if briefer_on else "0"
    res = gen._run_pipeline_inline(**brief)
    res["_prompt_used"] = _read_prompt(res.get("run_id", ""))
    res["_briefer_log"] = [d for d in res.get("diagnostics", []) if d.startswith("briefer")]
    return res


def _save(res: dict, out_dir: Path, label: str) -> str:
    base = out_dir / label
    note = ""
    if res.get("html"):
        base.with_suffix(".html").write_text(res["html"], encoding="utf-8")
    if res.get("png_data_uri"):
        try:
            base.with_suffix(".png").write_bytes(
                base64.b64decode(res["png_data_uri"].split(",", 1)[1]))
            note = f"{label}.png"
        except Exception as e:  # noqa: BLE001
            note = f"(falha ao salvar png: {e})"
    return note


def _score(res: dict) -> str:
    ev = res.get("evaluation") or {}
    sc = ev.get("score") if isinstance(ev, dict) else None
    verdict = ev.get("verdict") if isinstance(ev, dict) else None
    return f"{sc if sc is not None else '—'} ({verdict or 'sem FINAL_EVAL'})"


def _vision(res: dict) -> str:
    v = res.get("vision_qa") or {}
    return f"{v.get('verdict', '—')}" + (f" · {v.get('reason', '')[:120]}" if v.get("reason") else "")


def main():
    ap = argparse.ArgumentParser(description="A/B do Briefer A↔B (Fase 12).")
    ap.add_argument("--model", default="A-headline-foto-dark")
    ap.add_argument("--preset", default="bw-yellow",
                    help="bw-yellow exercita o erro 'amarelo ausente'")
    ap.add_argument("--format", default="feed", choices=["feed", "story", "sqr"])
    ap.add_argument("--headline", default="Crescer deixou de ser sorte.")
    ap.add_argument("--subhead",
                    default="Quando a operação tem método, a próxima venda é previsível.")
    ap.add_argument("--body", default="")
    ap.add_argument("--cta", default="Conheça a Metta")
    ap.add_argument("--avatar-segment", default="",
                    help="ex: varejo-farmacia (exercita o erro 'ICP genérico')")
    ap.add_argument("--rounds", type=int, default=1, help="BRIEFER_ROUNDS no tratamento")
    ap.add_argument("--out", default=str(ROOT / "render_out" / "ab-briefer"))
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        ap.error("defina OPENAI_API_KEY (e ANTHROPIC_API_KEY se LLM_PROVIDER=claude). "
                 "O A/B gera imagem de verdade.")

    os.environ["BRIEFER_ROUNDS"] = str(max(1, args.rounds))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    brief = dict(
        briefing_text="ab-briefer", mock=False, forced_model_id=args.model,
        image_source="generate", image_style_preset=args.preset,
        user_headline=args.headline, user_subhead=args.subhead, user_body=args.body,
        user_cta_text=args.cta, user_tag="", wizard_format=args.format,
        avatar_segment=args.avatar_segment or None, avatar_variant=None,
        render_png=True, art_director=True, vision_qa=True,
    )

    print(f"[A/B] modelo={args.model} preset={args.preset} formato={args.format} rounds={args.rounds}")
    print("[A/B] (1/2) CONTROLE  — BRIEFER=0 ...")
    ctrl = _run(dict(brief), briefer_on=False)
    print(f"        ok={ctrl.get('ok')} run_id={ctrl.get('run_id')}")
    print("[A/B] (2/2) TRATAMENTO — BRIEFER=1 ...")
    trt = _run(dict(brief), briefer_on=True)
    print(f"        ok={trt.get('ok')} run_id={trt.get('run_id')}")

    png_c = _save(ctrl, out_dir, "control")
    png_t = _save(trt, out_dir, "treatment")

    def block(res, label):
        return (
            f"### {label}\n"
            f"- ok: `{res.get('ok')}` · run_id: `{res.get('run_id')}`\n"
            f"- qa: `{(res.get('qa') or {}).get('status', '—')}`\n"
            f"- vision_qa: {_vision(res)}\n"
            f"- nota avaliador: **{_score(res)}**\n"
            f"- critic: `{(res.get('critic') or {}).get('verdict', '—')}`\n"
            + (f"- erro: `{res.get('error')}`\n" if not res.get("ok") else "")
            + f"\n**prompt de imagem usado:**\n```\n{res['_prompt_used']}\n```\n"
            + (("**log do briefer:**\n" + "\n".join(f"- {x}" for x in res["_briefer_log"]) + "\n")
               if res["_briefer_log"] else "")
        )

    report = (
        "# A/B — Briefer A↔B (Fase 12)\n\n"
        f"`model={args.model}` · `preset={args.preset}` · `format={args.format}` · "
        f"`rounds={args.rounds}` · `avatar_segment={args.avatar_segment or '(auto)'}`\n\n"
        "> Imagem é não-determinística — 1 amostra/lado é leitura rápida, não verdade "
        "estatística. Pra decidir ligar em prod, rode N≥3/lado e olhe a média.\n\n"
        "## Comparativo\n\n"
        "| métrica | CONTROLE (off) | TRATAMENTO (on) |\n"
        "|---|---|---|\n"
        f"| nota avaliador | {_score(ctrl)} | {_score(trt)} |\n"
        f"| vision_qa | {_vision(ctrl)} | {_vision(trt)} |\n"
        f"| qa | {(ctrl.get('qa') or {}).get('status','—')} | {(trt.get('qa') or {}).get('status','—')} |\n"
        f"| png | {png_c or '—'} | {png_t or '—'} |\n\n"
        + block(ctrl, "CONTROLE — BRIEFER=0")
        + "\n"
        + block(trt, "TRATAMENTO — BRIEFER=1")
    )
    report_path = out_dir / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print("\n[A/B] PRONTO")
    print(f"  relatório : {report_path}")
    print(f"  imagens   : {out_dir/'control.png'}  ×  {out_dir/'treatment.png'}")
    print(f"  prompt off: {ctrl['_prompt_used'][:90]}...")
    print(f"  prompt on : {trt['_prompt_used'][:90]}...")
    if trt["_briefer_log"]:
        print("  briefer   : " + " | ".join(trt["_briefer_log"]))


if __name__ == "__main__":
    main()
