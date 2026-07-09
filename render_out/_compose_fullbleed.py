#!/usr/bin/env python3
"""Re-compõe peças do feed em FULL-BLEED + overlay (igual aos posts), REUSANDO as fotos
cruas já geradas — zero crédito de imagem. Só render HTML→PNG.

Problema que resolve: os templates de ZONAS (object-center=card, photo-side=painel)
não batem com a composição dos posts (foto full-bleed + texto por cima). Aqui forço o
layout `photo-full` (o do D, que foi o único que chegou perto) nas fotos boas.

Uso:  python3.11 render_out/_compose_fullbleed.py
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
IMG = ROOT / "render_out" / "feed-replica" / "artifacts" / "images"
OUT = ROOT / "render_out" / "feed-replica" / "fullbleed"
OUT.mkdir(parents=True, exist_ok=True)

from _blueprint_render import render as bp_render  # noqa: E402
from _render_png import render_format              # noqa: E402

FULLBLEED_MODEL = "D-foto-fullbleed-overlay"  # archetype photo-full = foto full-bleed + grad + texto

# fotos cruas boas (a do "cobra" saiu bege/corpo-inteiro → fora; vai regerar dark/close)
ITEMS = [
    {"out": "01-xadrez", "photo": "openai_1782079564.png",
     "headline": "Sabe a *diferença* entre a empresa que sofre pra bater meta e a que bate a *meta* todos os meses?",
     "subhead": "", "body": "", "cta": ""},
    {"out": "03-diagnostico", "photo": "openai_1782079599.png",
     "headline": "O que um *diagnóstico* comercial revela que a *cobrança* não mostra.",
     "subhead": "", "body": "", "cta": ""},
    {"out": "05-desengajamento", "photo": "openai_1782079658.png",
     "headline": "A *jornada* do desengajamento.",
     "subhead": "Por que seu vendedor sai antes de vender?", "body": "", "cta": ""},
]


def data_uri(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def main():
    print(f"=== FULL-BLEED recompose · {len(ITEMS)} peças · modelo={FULLBLEED_MODEL} (reusa foto, sem custo) ===")
    for it in ITEMS:
        photo = IMG / it["photo"]
        if not photo.exists():
            print(f"  ⚠️  foto não encontrada: {photo}"); continue
        copy = {k: it.get(k, "") for k in ("headline", "subhead", "body", "cta")}
        res = bp_render("metta", FULLBLEED_MODEL, copy, image_url=data_uri(photo), format="feed")
        if not res.get("html"):
            print(f"  ⚠️  render falhou ({it['out']})"); continue
        png = render_format(res["html"], "feed")
        (OUT / f"{it['out']}.png").write_bytes(png)
        print(f"  ✓ {it['out']:18s} ← {it['photo']}  «{it['headline'][:46]}»")
    print(f"\nSalvo em {OUT}/")


if __name__ == "__main__":
    main()
