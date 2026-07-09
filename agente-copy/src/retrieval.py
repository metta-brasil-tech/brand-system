"""Seleção lexical de trechos da base de conhecimento (RAG sem serviço externo).

Contexto: a base de conhecimento inteira (~155 mil caracteres + documento de
ICP de até 72 mil) era enviada por completo em toda chamada de rascunho, e o
documento de ICP inteiro também no julgamento. Esse é o maior custo real do
sistema (entrada domina a conta, medido em produção). A decisão original "sem
RAG" valia para a orquestração antiga em n8n; em código próprio o cliente
liberou a seleção de trechos.

Por que busca LEXICAL e não embeddings: a Anthropic não tem API de embeddings.
Usar vetores exigiria contratar um segundo provedor (OpenAI/Voyage), mais uma
chave na Vercel e mais um ponto de falha. A seleção aqui é por pontuação de
palavras (estilo BM25 simplificado): determinística, zero chamada de rede,
zero dependência nova, e auditável (scripts/inspect_rag_selection.py mostra
exatamente o que cada briefing puxa).

Regras de segurança:
- tom-de-voz-metta.md e SKILLMETTACOPY.md NUNCA são fatiados: são a voz e as
  regras de escrita, o modelo escreve a partir deles. A seleção só se aplica
  aos documentos de REFERÊNCIA (avatar, posicionamento, oferta, provas,
  glossário) e ao documento de ICP.
- Fallback total: qualquer erro, ou seleção que vier vazia, devolve o
  documento completo, comportamento idêntico ao de antes. No pior caso o
  sistema fica caro como era, nunca sem contexto.
- Interruptor: env var COPY_AGENT_RAG=0 desliga tudo sem mudança de código
  (setável na Vercel, vale no próximo deploy/cold start).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Orçamento de caracteres por grupo de documentos selecionados. Calibrado pra
# cortar ~55-60% do prompt de rascunho mantendo folga: os trechos mais
# relevantes de 5 documentos de referência cabem confortavelmente em 30k, e
# um recorte útil de ICP em 12k (o doc de mentoria inteiro tem 72k).
POOL_BUDGET_CHARS = 30_000
ICP_BUDGET_CHARS = 12_000

def _normalize(text: str) -> str:
    """minúsculas + sem acento, pra 'calçados' casar com 'calcados'."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


# Normalizadas na construção: os tokens saem sem acento, então a lista
# também precisa estar ("não" vira "nao", senão a stopword nunca casa --
# pego na primeira auditoria com scripts/inspect_rag_selection.py).
_STOPWORDS = frozenset(
    _normalize(w)
    for w in (
        "a o as os e é em um uma uns umas de da do das dos para pra com sem "
        "que se no na nos nas por ao à aos às mais menos como ou seu sua "
        "seus suas este esta isso esse essa aquele aquela não sim qual quais "
        "quando onde sobre entre também já só tem têm ser são foi era ele "
        "ela eles elas você vocês nós eu me te lhe nem mas porém então assim "
        "até muito pouco todo toda todos todas outro outra cada vez vezes "
        "coisa coisas fazer faz ter está estão ficar fica pode podem deve "
        "devem vai vão ainda depois antes aqui ali lá bem mal dia dias mês "
        "meses ano anos".split()
    )
)


@dataclass(frozen=True)
class Chunk:
    source: str      # nome do arquivo de origem
    heading: str     # trilha de títulos ("## Dores > ### Ciclo do gargalo")
    text: str        # conteúdo do trecho (inclui a linha do título)
    order: int       # posição original dentro do arquivo, pra remontar em ordem


def _tokens(text: str) -> list[str]:
    return [
        t for t in re.findall(r"[a-z0-9]+", _normalize(text))
        if len(t) > 2 and t not in _STOPWORDS
    ]


def split_markdown_sections(source: str, text: str, min_chars: int = 400) -> list[Chunk]:
    """Fatia um markdown por títulos (#, ##, ###), preservando a trilha.

    Seções menores que min_chars são fundidas com a seguinte, pra não gerar
    migalha que pontua alto por acaso e não carrega conteúdo de verdade.
    """
    lines = text.split("\n")
    raw: list[tuple[str, list[str]]] = []
    trail: dict[int, str] = {}
    current_heading = "(abertura)"
    current_lines: list[str] = []

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            if current_lines:
                raw.append((current_heading, current_lines))
            level = len(m.group(1))
            trail[level] = m.group(2).strip()
            for deeper in (2, 3):
                if deeper > level:
                    trail.pop(deeper, None)
            current_heading = " > ".join(
                trail[lv] for lv in sorted(trail) if lv <= level
            )
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        raw.append((current_heading, current_lines))

    # Funde seções pequenas com a próxima, mantendo a trilha da maior.
    merged: list[tuple[str, str]] = []
    buffer_heading, buffer_text = "", ""
    for heading, sec_lines in raw:
        sec_text = "\n".join(sec_lines).strip()
        if not sec_text:
            continue
        if buffer_text:
            buffer_text = f"{buffer_text}\n\n{sec_text}"
            if len(sec_text) >= len(buffer_text) // 2:
                buffer_heading = heading
        else:
            buffer_heading, buffer_text = heading, sec_text
        if len(buffer_text) >= min_chars:
            merged.append((buffer_heading, buffer_text))
            buffer_heading, buffer_text = "", ""
    if buffer_text:
        merged.append((buffer_heading, buffer_text))

    return [
        Chunk(source=source, heading=h, text=t, order=i)
        for i, (h, t) in enumerate(merged)
    ]


def score_chunk(chunk: Chunk, query_terms: list[str]) -> float:
    """Pontuação BM25 simplificada: frequência com retorno decrescente,
    normalizada pelo tamanho do trecho; termo achado no TÍTULO vale 3x."""
    if not query_terms:
        return 0.0
    body_tokens = _tokens(chunk.text)
    if not body_tokens:
        return 0.0
    heading_tokens = set(_tokens(chunk.heading))
    counts: dict[str, int] = {}
    for t in body_tokens:
        counts[t] = counts.get(t, 0) + 1

    length_norm = 1.0 + len(body_tokens) / 400.0
    score = 0.0
    for term in set(query_terms):
        tf = counts.get(term, 0)
        if tf:
            score += (tf / (tf + 1.5)) / length_norm
        if term in heading_tokens:
            score += 3.0 / length_norm
    return score


def build_query(*parts: str) -> list[str]:
    """Monta os termos de busca a partir dos campos do briefing. Ids com
    hífen ('varejo-moda-calcados') viram termos separados."""
    terms: list[str] = []
    for part in parts:
        if part:
            terms.extend(_tokens(part.replace("-", " ").replace("_", " ")))
    return terms


def select_sections(
    source: str, text: str, query_terms: list[str], budget_chars: int
) -> str:
    """Devolve os trechos mais relevantes de UM documento, em ordem original,
    dentro do orçamento. Fallback: erro ou nada relevante -> documento inteiro.
    """
    try:
        if len(text) <= budget_chars:
            return text
        chunks = split_markdown_sections(source, text)
        scored = [(score_chunk(c, query_terms), c) for c in chunks]
        relevant = [(s, c) for s, c in scored if s > 0]
        if not relevant:
            return text  # fallback: nada casou, melhor caro que sem contexto
        relevant.sort(key=lambda pair: pair[0], reverse=True)
        picked: list[Chunk] = []
        used = 0
        for s, c in relevant:
            if used + len(c.text) > budget_chars and picked:
                continue
            picked.append(c)
            used += len(c.text)
            if used >= budget_chars:
                break
        if not picked:
            return text
        picked.sort(key=lambda c: c.order)
        note = (
            f"[trechos selecionados de {source} por relevância ao briefing; "
            "o documento completo é maior]"
        )
        result = note + "\n\n" + "\n\n[...]\n\n".join(c.text for c in picked)
        # Documento pequeno: seleção + nota pode sair maior que o original
        # (pego em teste). Se não encolheu, não vale o recorte.
        return result if len(result) < len(text) else text
    except Exception:
        return text  # fallback duro: qualquer bug aqui nunca derruba a geração


def select_pool(
    documents: dict[str, str], query_terms: list[str], budget_chars: int
) -> dict[str, str]:
    """Seleção conjunta sobre vários documentos de referência: pontua os
    trechos de todos juntos e divide o orçamento entre os melhores, garantindo
    pelo menos o trecho mais relevante de cada documento (nenhuma fonte some
    por completo). Fallback: erro ou nada relevante -> tudo completo."""
    try:
        total = sum(len(t) for t in documents.values())
        if total <= budget_chars:
            return documents

        all_scored: list[tuple[float, Chunk]] = []
        best_per_doc: dict[str, tuple[float, Chunk]] = {}
        for name, text in documents.items():
            for chunk in split_markdown_sections(name, text):
                s = score_chunk(chunk, query_terms)
                all_scored.append((s, chunk))
                if s > 0 and (
                    name not in best_per_doc or s > best_per_doc[name][0]
                ):
                    best_per_doc[name] = (s, chunk)

        if not best_per_doc:
            return documents  # nada casou com o briefing: manda tudo

        picked: list[Chunk] = [c for _, c in best_per_doc.values()]
        used = sum(len(c.text) for c in picked)
        picked_ids = {(c.source, c.order) for c in picked}

        for s, c in sorted(all_scored, key=lambda p: p[0], reverse=True):
            if s <= 0 or used >= budget_chars:
                break
            if (c.source, c.order) in picked_ids:
                continue
            if used + len(c.text) > budget_chars:
                continue
            picked.append(c)
            picked_ids.add((c.source, c.order))
            used += len(c.text)

        result: dict[str, str] = {}
        for name in documents:
            doc_chunks = sorted(
                (c for c in picked if c.source == name), key=lambda c: c.order
            )
            if doc_chunks:
                note = (
                    f"[trechos selecionados de {name} por relevância ao "
                    "briefing; o documento completo é maior]"
                )
                joined = note + "\n\n" + "\n\n[...]\n\n".join(
                    c.text for c in doc_chunks
                )
                # Mesma guarda do select_sections: recorte que não encolhe
                # o documento não vale a nota.
                result[name] = (
                    joined if len(joined) < len(documents[name]) else documents[name]
                )
        if sum(len(t) for t in result.values()) >= total:
            return documents  # seleção não economizou nada: manda original
        return result
    except Exception:
        return documents  # fallback duro
