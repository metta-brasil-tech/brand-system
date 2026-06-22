#!/usr/bin/env python3
"""E2E real de UM criativo DARK-COLAGEM — valida FASE 2/3 (fidelidade ao modelo).

Confere:
  - 04-image-prompt.json: prompt SEM humano realista; anti-padrão "foto humana
    realista" virou negativo (o diretor converteu via model_dna).
  - vision-qa / evaluator: campo anti_pattern_violated; guardrail rebaixa
    SHIP->REVISAR se a vision-qa reprovar ou se violar anti-padrão.

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_e2e_dark_colagem.py
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
os.environ.setdefault("IMAGE_QUALITY", "low")
os.environ.setdefault("VISION_QA_MAX", "2")            # permite 1 regen p/ exercitar _ad_direct2
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ.setdefault("FINAL_EVAL", "1")               # exercita o evaluator model-aware (Fase 6)
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ROOT / "artifacts")

import generate as gen  # noqa: E402

OUT = ROOT / "render_out" / "_e2e-dark-colagem"
OUT.mkdir(parents=True, exist_ok=True)

MODEL = "DARK-COLAGEM"
HEADLINE = "Sua operação tem método ou tem sorte?"
SUBHEAD = "Quando cada peça tem lugar, a próxima venda deixa de ser aposta."
BODY = ""
CTA = "Conheça a mentoria"
PRESET = "cinematic-dark"
FMT = "feed"


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
    print(f"[e2e] gerando {MODEL} ({FMT}, img={os.environ['IMAGE_QUALITY']})...")
    res = gen._run_pipeline_inline(
        briefing_text="e2e-dark-colagem", mock=False, forced_model_id=MODEL,
        image_source="generate", image_style_preset=PRESET,
        user_headline=HEADLINE, user_subhead=SUBHEAD, user_body=BODY,
        user_cta_text=CTA, user_tag="", wizard_format=FMT,
        render_png=True, art_director=True, vision_qa=True,
    )

    print("\n===== DIAGNOSTICS =====")
    for d in res.get("diagnostics", []):
        print(" ·", d)

    if not res.get("ok"):
        print("\nFALHOU:", res.get("error"))
        (OUT / "ERRO.txt").write_text(str(res.get("error")) + "\n\n"
                                      + "\n".join(res.get("diagnostics", [])), encoding="utf-8")
        return

    run_id = res.get("run_id", "")
    if res.get("png_data_uri"):
        _save_img(res["png_data_uri"], OUT / "criativo.png")
    (OUT / "criativo.html").write_text(res.get("html", ""), encoding="utf-8")
    _save_img(res.get("image_data_uri") or res.get("image_file_url") or "", OUT / "imagem-gerada.png")

    img_prompt = img_neg = ""
    try:
        art = json.loads((ROOT / "artifacts" / run_id / "04-image-prompt.json").read_text())
        p0 = (art.get("prompts") or [{}])[0]
        img_prompt = p0.get("prompt", "")
        img_neg = p0.get("negative_prompt", "")
    except Exception as e:
        print("  (não capturou 04-image-prompt.json:", e, ")")

    vqa = res.get("vision_qa") or {}
    ev = res.get("evaluation") or res.get("eval") or {}

    # checagens automáticas
    pl = img_prompt.lower()
    nl = img_neg.lower()
    human_in_prompt = any(w in pl for w in ["realistic human", "human photo", "homem realista",
                                            "foto humana", "realistic person", "portrait of a"])
    anti_in_neg = any(w in nl for w in ["realistic human", "human photo", "not a realistic",
                                        "homem realista", "foto humana"])

    print("\n===== CHECAGENS FASE 2/3 =====")
    print(f"  prompt cita humano realista?      {'SIM (ruim)' if human_in_prompt else 'não (bom)'}")
    print(f"  anti-padrão humano no negative?   {'sim (bom)' if anti_in_neg else 'NÃO'}")
    print(f"  vision-qa verdict:                {vqa.get('verdict')}")
    print(f"  vision-qa anti_pattern_violated:  {vqa.get('anti_pattern_violated')}")
    print(f"  evaluator anti_pattern_violated:  {ev.get('anti_pattern_violated')}")
    print(f"  evaluator status (pós-guardrail): {ev.get('status') or ev.get('verdict')}")

    (OUT / "RELATORIO.md").write_text(f"""# E2E DARK-COLAGEM — {run_id}

## Prompt de imagem (gpt-image-2)
```
{img_prompt or '(não capturado)'}
```

## Negative prompt
```
{img_neg or '(não capturado)'}
```

## Checagens FASE 2/3
- prompt cita humano realista? **{'SIM (ruim)' if human_in_prompt else 'não (bom)'}**
- anti-padrão humano no negative? **{'sim (bom)' if anti_in_neg else 'NÃO'}**
- vision-qa verdict: **{vqa.get('verdict')}**
- vision-qa anti_pattern_violated: **{vqa.get('anti_pattern_violated')}**
- evaluator anti_pattern_violated: **{ev.get('anti_pattern_violated')}**
- evaluator status (pós-guardrail): **{ev.get('status') or ev.get('verdict')}**

## Diagnostics
""" + "\n".join(f"- {d}" for d in res.get("diagnostics", [])), encoding="utf-8")

    print(f"\nTudo em: {OUT}")


if __name__ == "__main__":
    main()
