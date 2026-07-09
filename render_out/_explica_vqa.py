#!/usr/bin/env python3
"""Roda SÓ a vision-qa sobre os criativo.png já gerados (sem regenerar imagem)
e grava 'por-que-vision-qa.md' em cada pasta com a razão textual do juiz.

Uso:
  set -a; . engine/.env; set +a
  python3.11 render_out/_explica_vqa.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
os.environ.setdefault("LLM_PROVIDER", "openai")

from _vision_qa import check as vqa_check  # noqa: E402

LOTE = ROOT / "render_out" / "criativos-novos-21jun"


def _copy_from_info(info_path: Path) -> dict:
    """Lê headline/subhead/body/cta do info.md pra dar contexto ao juiz."""
    c = {"headline": "", "subhead": "", "body": "", "cta": ""}
    if not info_path.exists():
        return c
    for line in info_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"-\s*(headline|subhead|body|cta):\s*(.*)", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            c[k] = "" if v == "—" else v
    return c


def main() -> None:
    folders = sorted(p for p in LOTE.iterdir() if p.is_dir())
    for folder in folders:
        png = folder / "criativo.png"
        if not png.exists():
            print(f"  {folder.name}: SEM criativo.png — pulado")
            continue
        copy = _copy_from_info(folder / "info.md")
        res = vqa_check(png.read_bytes(), copy)
        verdict = res.get("verdict", "?")
        rel = res.get("relevance", "?")
        integ = res.get("integrity", "?")
        reason = res.get("reason", "(sem razão)")

        # tradução do critério pra deixar claro o PORQUÊ
        explic = []
        if rel == "weak":
            explic.append(
                "**RELEVÂNCIA fraca:** a vision-qa exige que a imagem mostre o "
                "ASSUNTO CONCRETO da copy (pra tema de método/gestão ela espera ver "
                "dashboard, gráfico, planilha ou uma cena de decisão sobre números). "
                "A cena gerada ficou genérica/atmosférica e não traz esse elemento "
                "concreto à vista — por isso `relevance=weak`.")
        if integ == "broken":
            explic.append(
                "**INTEGRIDADE quebrada:** algum elemento principal parece cortado, "
                "espremido ou coberto de forma acidental (não direção de arte).")
        if not explic and verdict == "PASS":
            explic.append("Passou: relevância e integridade OK.")

        md = f"""# Por que a vision-qa deu {verdict} — {folder.name}

- **veredito:** {verdict}
- **relevância:** {rel}
- **integridade:** {integ}

## Razão do juiz (texto literal)
> {reason}

## O que isso significa
""" + "\n\n".join(explic) + """

---
*Critério da vision-qa (`api/_vision_qa.py`): PASS só se `relevance=ok` E `integrity=ok`.
RELEVÂNCIA = a foto ilustra o assunto concreto da copy. INTEGRIDADE = nenhum
elemento principal cortado/coberto por acidente. Esta checagem foi rodada sobre o
`criativo.png` já salvo, sem regerar a imagem.*
"""
        (folder / "por-que-vision-qa.md").write_text(md, encoding="utf-8")
        print(f"  {folder.name}: {verdict} (rel={rel} integ={integ}) → por-que-vision-qa.md")


if __name__ == "__main__":
    main()
