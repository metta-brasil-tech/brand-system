#!/usr/bin/env python3
"""Roda o avaliador FINAL sobre os criativos já gerados em criativos-teste/.

Reusa os PNGs prontos (não regera imagem) → só chamadas de visão. Lê a copy e os
vereditos de cada prompts.md, chama _evaluator.evaluate(), grava avaliacao.md em
cada pasta e um AVALIACAO.md rankeado no topo.

Uso: set -a; . engine/.env; set +a; python3.11 render_out/_avaliar_criativos.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
os.environ.setdefault("VISION_QA_MODEL", "gpt-4.1")

from _evaluator import evaluate  # noqa: E402

OUT = ROOT / "criativos-teste"


def _field(md: str, label: str) -> str:
    m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.*)", md)
    return (m.group(1).strip() if m else "").replace("—", "").strip()


def main() -> None:
    rows = []
    for folder in sorted(OUT.glob("modelo-*")):
        png = folder / "criativo.png"
        meta = folder / "prompts.md"
        if not png.is_file() or not meta.is_file():
            continue
        md = meta.read_text(encoding="utf-8")
        marca = "tiago" if "TIAGO" in folder.name.upper() else "metta"
        copy = {"headline": _field(md, "headline"), "subhead": _field(md, "subhead"),
                "body": _field(md, "body"), "cta": _field(md, "cta")}
        # reconstrói os sinais já computados (pro guardrail)
        vqa = {}
        cr = {}
        mv = re.search(r"vision-qa.*?:\*\*\s*(\w+).*?integ=(\w+)", md)
        if mv:
            vqa = {"verdict": mv.group(1), "integrity": mv.group(2)}
        mc = re.search(r"crítico.*?:\*\*\s*(\w+)", md)
        if mc:
            cr = {"verdict": mc.group(1)}

        print(f"avaliando {folder.name} ...")
        ev = evaluate(png.read_bytes(), copy, marca, vqa, cr)
        sc = ev.get("scores", {}) or {}
        geral = ev.get("geral", 0)
        (folder / "avaliacao.md").write_text(
            f"# Avaliação final — {folder.name}\n\n"
            f"- **Veredito:** {ev.get('verdict')}\n"
            f"- **Nota geral:** {geral}/10\n"
            f"- **relevância:** {sc.get('relevancia','?')} · **marca:** {sc.get('marca','?')} · "
            f"**hierarquia:** {sc.get('hierarquia','?')} · **acabamento:** {sc.get('acabamento','?')}\n"
            f"- **Por quê:** {ev.get('reason','')}\n"
            + (f"- **Guardrail (defeito objetivo):** {', '.join(ev.get('guardrail', []))}\n" if ev.get("guardrail") else "")
            + "\n## Ajustes que elevam a nota\n"
            + ("\n".join(f"- {fx}" for fx in ev.get("fixes", [])) or "- (nenhum)") + "\n",
            encoding="utf-8")
        rows.append((folder.name, ev.get("verdict", "?"), float(geral or 0), sc, ev.get("reason", "")))

    rows.sort(key=lambda r: r[2], reverse=True)
    lines = ["# Avaliação final do lote — rankeado por nota geral\n",
             "| # | Modelo | Veredito | Geral | rel | marca | hier | acab |",
             "|---|---|---|---|---|---|---|---|"]
    for name, verd, geral, sc, _ in rows:
        lines.append(f"| | {name} | **{verd}** | {geral:.1f} | "
                     f"{sc.get('relevancia','?')} | {sc.get('marca','?')} | "
                     f"{sc.get('hierarquia','?')} | {sc.get('acabamento','?')} |")
    lines.append("\n## Resumo")
    for v in ("SHIP", "REVISAR", "DESCARTAR"):
        names = [n for n, verd, *_ in rows if verd == v]
        lines.append(f"- **{v}** ({len(names)}): {', '.join(names) or '—'}")
    (OUT / "AVALIACAO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n===== RANKING =====")
    for name, verd, geral, sc, reason in rows:
        print(f" {geral:4.1f}  {verd:9s} {name:40s} {reason[:50]}")
    print(f"\nRelatório: {OUT/'AVALIACAO.md'}")


if __name__ == "__main__":
    main()
