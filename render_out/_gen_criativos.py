#!/usr/bin/env python3
"""Gera um lote de criativos de teste, cada um na sua pasta.

Cada pasta criativos-teste/modelo-NN-<id>/ recebe:
  - criativo.png        peça final renderizada (foto + texto por cima)
  - criativo.html       fonte HTML da peça final
  - imagem-gerada.png   a imagem crua do gpt-image-2 (antes do overlay)
  - prompts.md          modelo, copy (texto), prompt de imagem, negative, vereditos

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_gen_criativos.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))

# Mesmos defaults do cli.py + ajustes pra rodar local em lote.
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL_OPENAI", "gpt-4.1")
os.environ.setdefault("IMAGE_GEN_PROVIDER", "gpt-image-2")
os.environ.setdefault("IMAGE_QUALITY", "low")          # lote de teste; bump pra 'medium'/'high' nos favoritos
os.environ.setdefault("VISION_QA_MAX", "1")            # 1 imagem por criativo (sem regen)
os.environ.setdefault("CRITIC_COMPARE", "1")           # same-designer test ligado
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")  # local não tem o teto de 60s do Vercel
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ROOT / "artifacts")

import generate as gen  # noqa: E402

OUT = ROOT / "criativos-teste"
OUT.mkdir(exist_ok=True)

# (modelo, headline, subhead, body, cta, preset, formato)
BRIEFS = [
    ("A-headline-foto-dark",
     "Sua operação tem método ou tem sorte?",
     "Quando o processo é claro, a próxima venda deixa de ser aposta.",
     "", "Conheça a Metta", "fotorrealista", "feed"),
    ("B-foto-top-headline-mixed",
     "O time bate meta sem depender de você?",
     "Gestão é o que separa esforço de previsibilidade.",
     "", "Fale com a Metta", "fotorrealista", "feed"),
    ("D-foto-fullbleed-overlay",
     "Crescer deixou de ser sorte.",
     "Método transforma operação em resultado previsível.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
    ("I-retrato-editorial-pb",
     "Liderança não é apagar incêndio.",
     "É construir um time que decide sem você.",
     "", "Conheça a Metta", "fotorrealista", "feed"),
    ("FOTO-PILL-CASUAL",
     "Você fatura alto e ainda vive no operacional?",
     "Tem método pra sair disso.",
     "", "Agende um diagnóstico", "fotorrealista", "feed"),
    ("DARK-OBJETO",
     "Vendedor herói não é estratégia.",
     "Método transforma esforço em previsibilidade.",
     "", "Conheça a mentoria", "cinematic-dark", "feed"),
    ("YELLOW-BLOCO",
     "Sua operação tem método ou tem sorte?",
     "",
     "Processo estruturado\nIndicadores que orientam\nRitmo de gestão semanal",
     "Aplique para a mentoria", "fotorrealista", "feed"),
    ("TIAGO-EDITORIAL-DARK",
     "O silêncio também é decisão.",
     "Liderar é escolher o que não fazer.",
     "", "Siga @tiagoalves", "cinematic-dark", "feed"),
    ("TIAGO-EDITORIAL-HERO",
     "Você virou refém da própria empresa.",
     "Dono não devia trabalhar como funcionário.",
     "", "Saiba mais", "surreal-hbr", "feed"),
    ("TIAGO-STORY-YELLOW-BLOCK",
     "Meta não se bate no improviso.",
     "Se constrói com método.",
     "", "Arrasta pra cima", "bw-yellow", "story"),
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
        folder = OUT / f"modelo-{i:02d}-{model}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{i:02d}/{len(BRIEFS)}] {model} ({fmt}) — gerando...")
        try:
            res = gen._run_pipeline_inline(
                briefing_text="lote-teste", mock=False, forced_model_id=model,
                image_source="generate", image_style_preset=preset,
                user_headline=h, user_subhead=s, user_body=body,
                user_cta_text=cta, user_tag="", wizard_format=fmt,
                render_png=True, art_director=True, vision_qa=True,
            )
        except Exception as e:
            print(f"   ERRO: {e.__class__.__name__}: {e}")
            summary.append((i, model, "EXC", "", ""))
            continue

        if not res.get("ok"):
            print(f"   FALHOU: {res.get('error')}")
            (folder / "ERRO.txt").write_text(str(res.get("error")) + "\n\n"
                                             + "\n".join(res.get("diagnostics", [])), encoding="utf-8")
            summary.append((i, model, "FAIL", "", ""))
            continue

        # criativo final
        if res.get("png_data_uri"):
            _save_img(res["png_data_uri"], folder / "criativo.png")
        (folder / "criativo.html").write_text(res.get("html", ""), encoding="utf-8")
        # imagem crua do gpt-image-2
        got_img = _save_img(res.get("image_data_uri") or res.get("image_file_url") or "",
                            folder / "imagem-gerada.png")

        # prompt de imagem + negative (do artefato salvo pelo run)
        img_prompt = img_neg = ""
        try:
            art = json.loads((ROOT / "artifacts" / res["run_id"] / "04-image-prompt.json").read_text())
            p0 = (art.get("prompts") or [{}])[0]
            img_prompt = p0.get("prompt", "")
            img_neg = p0.get("negative_prompt", "")
        except Exception:
            pass

        vqa = res.get("vision_qa") or {}
        cr = res.get("critic") or {}
        body_md = body.replace("\n", " · ")
        (folder / "prompts.md").write_text(f"""# Criativo {i:02d} — {model}

## Modelo
- **model_id:** `{model}`
- **marca:** {'tiago' if model.upper().startswith('TIAGO') else 'metta'}
- **formato:** {fmt}
- **preset de imagem:** {preset}

## Texto (copy literal — fornecida pelo usuário, não gerada)
- **headline:** {h}
- **subhead:** {s or '—'}
- **body:** {body_md or '—'}
- **cta:** {cta}

## Prompt de imagem (gpt-image-2)
```
{img_prompt or '(não capturado)'}
```

## Negative prompt
```
{img_neg or '(não capturado)'}
```

## Vereditos do pipeline
- **QA estático:** {(res.get('qa') or {}).get('status')}
- **vision-qa (ilustra a copy?):** {vqa.get('verdict')} — rel={vqa.get('relevance')} integ={vqa.get('integrity')}
- **crítico (same-designer test):** {cr.get('verdict')} {f"(vs {cr.get('reference_id')})" if cr.get('reference_id') else ''} — {cr.get('reason','')}
""", encoding="utf-8")

        print(f"   OK · qa={res.get('qa',{}).get('status')} "
              f"visão={vqa.get('verdict')} crítico={cr.get('verdict')} "
              f"img={'sim' if got_img else 'NÃO'}")
        summary.append((i, model, "OK", vqa.get("verdict", "?"), cr.get("verdict", "?")))

    print("\n\n===== RESUMO =====")
    for i, model, st, v, c in summary:
        print(f" {i:02d}. {model:32s} {st:5s} visão={v:8s} crítico={c}")
    print(f"\nTudo em: {OUT}")


if __name__ == "__main__":
    main()
