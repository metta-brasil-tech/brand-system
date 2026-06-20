#!/usr/bin/env python3
"""Demo do loop de auto-melhoria — gera, avalia, regera com feedback até aprovar.

Roda generate_until_approved() num criativo fraco e salva cada tentativa em
criativos-auto/<modelo>/tentativa-NN/ + um RESUMO.md com a trajetória da nota e a
versão vencedora.

Uso: set -a; . engine/.env; set +a; python3.11 render_out/_autogen_demo.py
"""
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
os.environ.setdefault("IMAGE_QUALITY", "low")
os.environ["VISION_QA_MAX"] = "1"          # o loop EXTERNO (auto-melhoria) controla a regeneração
os.environ.setdefault("CRITIC_COMPARE", "1")
os.environ.setdefault("PRE_IMAGE_GUARD_MS", "120000")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(ROOT / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(ROOT / "artifacts")

from _autogen import generate_until_approved  # noqa: E402

OUT = ROOT / "criativos-auto"
OUT.mkdir(exist_ok=True)

# Criativo fraco do lote anterior (tirou 6.0 — foto genérica, problema de imagem).
BRIEF = {
    "briefing_text": "auto-melhoria", "mock": False,
    "forced_model_id": "FOTO-PILL-CASUAL",
    "image_source": "generate", "image_style_preset": "fotorrealista",
    "user_headline": "Você fatura alto e ainda vive no operacional?",
    "user_subhead": "Tem método pra sair disso.",
    "user_body": "", "user_cta_text": "Agende um diagnóstico",
    "user_tag": "", "wizard_format": "feed",
    "render_png": True, "art_director": True, "vision_qa": True,
}


def _save(uri: str, dest: Path):
    if uri and uri.startswith("data:"):
        dest.write_bytes(base64.b64decode(uri.split(",", 1)[1]))


def main():
    model = BRIEF["forced_model_id"]
    folder = OUT / model
    folder.mkdir(parents=True, exist_ok=True)
    print(f"AUTO-MELHORIA · {model} · até 3 tentativas\n")

    best, history = generate_until_approved(BRIEF, max_attempts=3, target="SHIP")

    traj = []
    for it in history:
        n = it["attempt"]
        sub = folder / f"tentativa-{n:02d}"
        sub.mkdir(exist_ok=True)
        res, ev = it["result"], it["eval"]
        _save(res.get("png_data_uri", ""), sub / "criativo.png")
        _save(res.get("image_data_uri", ""), sub / "imagem-gerada.png")
        sc = ev.get("scores", {}) or {}
        (sub / "eval.md").write_text(
            f"# Tentativa {n} — {model}\n\n"
            f"- **Veredito:** {ev.get('verdict')} · **Nota:** {ev.get('geral')}/10\n"
            f"- rel={sc.get('relevancia','?')} marca={sc.get('marca','?')} "
            f"hier={sc.get('hierarquia','?')} acab={sc.get('acabamento','?')}\n"
            f"- **image_fixable:** {ev.get('image_fixable')}\n"
            f"- **Por quê:** {ev.get('reason','')}\n"
            f"- **Feedback usado nesta tentativa:** {it.get('visual_feedback') or '(direção original)'}\n"
            f"- **Próxima imagem deve:** {ev.get('image_feedback','')}\n\n"
            + "## Ajustes\n" + ("\n".join(f"- {x}" for x in ev.get('fixes', [])) or "- —") + "\n",
            encoding="utf-8")
        traj.append((n, ev.get("verdict"), ev.get("geral")))

    # vencedora
    if best:
        _save(best["result"].get("png_data_uri", ""), folder / "VENCEDORA.png")

    lines = [f"# Auto-melhoria — {model}\n", "## Trajetória da nota", ""]
    for n, v, g in traj:
        lines.append(f"- tentativa {n}: **{v}** · {g}/10")
    bn = best.get("attempt") if best else "-"
    lines += ["", f"**Vencedora:** tentativa {bn} "
              f"({best['eval'].get('verdict')} · {best['eval'].get('geral')}/10) → `VENCEDORA.png`",
              "", "Cada tentativa em `tentativa-NN/` (criativo + imagem + eval.md com o feedback usado)."]
    (folder / "RESUMO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n===== TRAJETÓRIA =====")
    for n, v, g in traj:
        print(f"  tentativa {n}: {v:9s} {g}/10")
    print(f"  VENCEDORA: tentativa {bn}")
    print(f"\nTudo em: {folder}")


if __name__ == "__main__":
    main()
