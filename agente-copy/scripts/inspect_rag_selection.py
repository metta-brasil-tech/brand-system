"""Mostra quais trechos da base o RAG lexical seleciona pra um briefing.

Ferramenta de auditoria offline, custo zero: roda briefings representativos
e imprime os títulos das seções escolhidas por documento, com a pontuação.
Use antes de confiar em qualquer mudança no retrieval (orçamento, stopwords,
peso de título) e sempre que a base de conhecimento mudar de forma relevante.

Uso:
    python3 scripts/inspect_rag_selection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import retrieval
from src.generator import _BRAND_FILES, _REPO_ROOT, _brief_query
from src.icp_catalog import icp_knowledge_file
from src.interview import build_brief_from_answers

BRIEFS = {
    "post único / mentoria / institucional": {
        "brand": "metta", "copy_type": "post_unico",
        "objective": "autoridade institucional, tom reflexivo sobre progresso e método",
        "icp": "mentoria-estrategica",
        "angle_choice": "progresso operacional que só aparece olhando pra trás",
        "emotional_axis": "necessidade", "cta": "", "platform": "instagram",
        "subtype": "frase de autor", "signature": "não",
    },
    "carrossel / varejo moda / conversão": {
        "brand": "metta", "copy_type": "carrossel",
        "objective": "conversão, dor do dono que é o melhor vendedor da loja",
        "icp": "varejo-moda-calcados",
        "angle_choice": "spread de performance entre vendedores",
        "emotional_axis": "dor", "cta": "Comenta DIAGNÓSTICO",
        "platform": "instagram", "input_mode": "ideia solta", "reading_time": "1min",
    },
    "reels / serviços saúde / autoridade": {
        "brand": "metta", "copy_type": "reels",
        "objective": "autoridade, clínica cheia que não vira lucro previsível",
        "icp": "servicos-saude",
        "angle_choice": "agenda cheia, caixa imprevisível",
        "emotional_axis": "dor", "cta": "link na bio", "platform": "instagram",
        "subtype": "longo de conteúdo", "input_mode": "ideia",
        "duration": "1 minuto", "opening_hook": "sim",
    },
    "criativo / mentoria / lead": {
        "brand": "metta", "copy_type": "criativos",
        "objective": "aquisição, lead qualificado de dono sobrecarregado",
        "icp": "mentoria-estrategica",
        "angle_choice": "a empresa para se o dono tira férias",
        "emotional_axis": "dor", "cta": "Agendar diagnóstico",
        "platform": "instagram", "media": "estático", "winner_or_new": "novo",
        "cta_goal": "lead", "attack_axis": "dor",
    },
}


def main() -> None:
    pool_files = [f for f in _BRAND_FILES["metta"]
                  if f not in ("tom-de-voz-metta.md", "SKILLMETTACOPY.md")]
    docs = {f: (_REPO_ROOT / f).read_text(encoding="utf-8") for f in pool_files}

    for label, answers in BRIEFS.items():
        brief = build_brief_from_answers(answers)
        query = _brief_query(brief)
        print("=" * 72)
        print(f"BRIEFING: {label}")
        print(f"termos: {sorted(set(query))}")

        print("\n-- pool de referência (orçamento "
              f"{retrieval.POOL_BUDGET_CHARS} chars) --")
        for name, text in docs.items():
            chunks = retrieval.split_markdown_sections(name, text)
            scored = sorted(
                ((retrieval.score_chunk(c, query), c) for c in chunks),
                key=lambda p: p[0], reverse=True,
            )
            top = [(round(s, 2), c.heading) for s, c in scored[:3] if s > 0]
            print(f"  {name}: {top if top else 'NADA relevante (iria completo)'}")

        icp_file = icp_knowledge_file(brief.icp)
        if icp_file:
            icp_text = (_REPO_ROOT / icp_file).read_text(encoding="utf-8")
            selecionado = retrieval.select_sections(
                icp_file, icp_text, query, retrieval.ICP_BUDGET_CHARS
            )
            print(f"\n-- ICP {icp_file}: {len(icp_text)} -> "
                  f"{len(selecionado)} chars --")
            for line in selecionado.split("\n"):
                if line.startswith("#"):
                    print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
