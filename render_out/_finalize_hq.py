#!/usr/bin/env python3
"""Topo do funil — regenera os VENCEDORES em qualidade HIGH (prontos pra publicar).

Lê o manifest do best-of, pega os SHIP de nota alta (>=8.5) e regenera a imagem em
IMAGE_QUALITY=high, salvando em best-of/<id>/final-hq.png. Avalia o resultado high pra
confirmar que continua bom. A versão medium (final.png) fica preservada pra comparação.

Nota honesta: gpt-image-2 é estocástico — o high é uma geração NOVA do mesmo brief/copy/
ICP (não um upscale do medium). Direção, copy e ICP são os mesmos; a cena pode variar.
Por isso guardamos as duas (final.png medium vs final-hq.png high).

RODAR só com a máquina livre (sem outro batch) — high é o tier mais pesado.
Uso: set -a; . engine/.env; set +a; python3.11 render_out/_finalize_hq.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
BESTOF = ROOT / "render_out" / "best-of"
ART = BESTOF / "artifacts-hq"
ART.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ["IMAGE_QUALITY"] = "high"       # topo do funil — só vencedores
os.environ["VISION_QA_MAX"] = "1"
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "240000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ART)

from generate import _run_pipeline_inline   # noqa: E402
from _evaluator import evaluate             # noqa: E402

MIN_SCORE = 8.5


def _dl(rid):
    try:
        return json.loads((ART / rid / "03-decision-log.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def main():
    manifest = json.loads((BESTOF / "manifest.json").read_text(encoding="utf-8"))
    golden = {b["id"]: b for b in json.loads((ROOT / "data" / "golden-set.json").read_text())["briefs"]}
    winners = [m for m in manifest if str(m.get("verdict")).upper() == "SHIP"
               and float(m.get("score") or 0) >= MIN_SCORE]
    winners.sort(key=lambda m: -float(m.get("score") or 0))
    winners = winners[:3]  # bounded — só o topo
    print(f"Vencedores p/ HIGH (SHIP>={MIN_SCORE}): {[w['id'] for w in winners]}\n")
    out = []
    for w in winners:
        b = golden.get(w["id"])
        if not b:
            continue
        marca = b["marca"]
        img = "none" if b.get("image") == "none" else "generate"
        preset = "fotorrealista" if marca != "tiago" else "cinematic-dark"
        print(f"[{w['id']}] medium={w['score']} → regerando em HIGH…")
        try:
            res = _run_pipeline_inline(
                briefing_text="hq", forced_model_id=b["model"], image_source=img,
                image_style_preset=(None if img == "none" else preset),
                user_headline=b.get("headline", ""), user_subhead=b.get("subhead", ""),
                user_body=b.get("body", ""), user_cta_text=b.get("cta", ""),
                wizard_format=b.get("format", "feed"),
                render_png=True, art_director=True, vision_qa=True)
        except Exception as e:
            print(f"   ERRO {e.__class__.__name__}: {e}")
            continue
        uri = res.get("png_data_uri") or "" if res.get("ok") else ""
        if not uri.startswith("data:"):
            print("   sem PNG high — mantém o medium")
            continue
        png = base64.b64decode(uri.split(",", 1)[1])
        (BESTOF / w["id"] / "final-hq.png").write_bytes(png)
        ev = evaluate(png, b, marca, res.get("vision_qa"), res.get("critic"), decision_log=_dl(res.get("run_id")))
        hq = float(ev.get("geral") or 0)
        out.append((w["id"], w["score"], hq, ev.get("verdict")))
        print(f"   high → {ev.get('verdict')} nota={hq}  (medium era {w['score']})")

    print("\n===== HIGH (topo do funil) =====")
    for bid, med, hq, v in out:
        print(f"  {bid:20s} medium={med}  high={hq} {v}  → final-hq.png")
    print(f"\nComparar: render_out/best-of/<id>/final.png (medium) vs final-hq.png (high)")


if __name__ == "__main__":
    main()
