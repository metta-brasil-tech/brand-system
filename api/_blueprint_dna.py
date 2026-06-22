"""DNA do modelo — extrai a PROSE do blueprint (não só o front-matter).

Hoje o diretor de arte só recebe front-matter (archetype/theme/treatment/placement).
A prose do blueprint (`## Intenção`, `## Estrutura visual`, `## Anti-padrões`) —
onde mora o que o modelo manda E proíbe — nunca chegava ao prompt. Resultado:
DARK-COLAGEM proíbe "foto humana realista" mas o prompt saía "A businessman...
realistic" (o anti-padrão do próprio modelo).

`extract_dna(marca, model_id)` devolve um dict best-effort (campos faltando → ""
ou []) que o `_art_director.direct(model_dna=...)` injeta no prompt e que os juízes
(FASE 3) usam como rubric por modelo.

Parser simples por headings `## `. Reusa o front-matter de `_blueprint_render`
(fonte única — não reparseia YAML aqui).
"""
from __future__ import annotations

import re
import unicodedata

import _blueprint_render as br

# Headings da prose que viram campos da DNA (chave normalizada → campo do dict).
# Normalização remove acento/caixa, então "Intenção" → "intencao".
_SECTION_MAP = {
    "intencao": "intent",
    "estrutura visual": "structure",
    "anti-padroes": "anti_patterns",   # vira lista
    "antipadroes": "anti_patterns",
    "quando brilha": "when_shines",
    "direcao de copy": "copy_direction",
}
_LIST_FIELDS = {"anti_patterns"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def _strip_front_matter(md: str) -> str:
    """Devolve o corpo após o bloco `---...---` (mesmo recorte do _parse_front_matter)."""
    m = re.match(r"^---\s*\n.*?\n---\s*\n", md, re.DOTALL)
    return md[m.end():] if m else md


def _sections(body: str) -> dict[str, str]:
    """Mapa heading-normalizado → texto da seção (até o próximo `## `)."""
    out: dict[str, str] = {}
    parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE)
    # parts = [pré, head1, corpo1, head2, corpo2, ...]
    for i in range(1, len(parts) - 1, 2):
        head = _norm(parts[i])
        text = (parts[i + 1] or "").strip()
        if head:
            out[head] = text
    return out


def _split_items(text: str) -> list[str]:
    """Quebra a seção em itens. Aceita os separadores usados nos blueprints:
    ` · ` (mais comum), bullets `- `, `;` e novas linhas. Mantém os parênteses
    explicativos (são direção útil pro modelo)."""
    if not text:
        return []
    # Bullets de início de linha viram separador ANTES de achatar (são fronteira
    # de item). Quebras de linha restantes são só soft-wrap da prose → viram
    # espaço, senão "estética\ncartoon" partiria no meal do item. Separador real
    # entre itens nos blueprints é ` · ` (ou `;`).
    text = re.sub(r"^\s*[-*]\s+", "·", text, flags=re.MULTILINE)
    text = re.sub(r"\s*\n\s*", " ", text)
    raw = re.split(r"·|;", text)
    items = [re.sub(r"\s+", " ", it).strip(" .") for it in raw]
    return [it for it in items if it]


def extract_dna(marca: str, model_id: str) -> dict:
    """Lê `source/ad-blueprints/{marca}/{model_id}.md` e devolve a DNA do modelo.

    Best-effort: blueprint ausente → dict com `missing=True`. Campos de prose
    faltando → "" ou []. Nunca lança por blueprint malformado.
    """
    path = br._blueprint_path(marca, model_id)
    if not path.exists():
        return {"missing": True, "marca": marca, "model_id": model_id}

    md = br._read(path)
    fm = br._parse_front_matter(md)
    secs = _sections(_strip_front_matter(md))
    image = fm.get("image", {}) or {}
    params = fm.get("params", {}) or {}

    dna: dict = {
        "missing": False,
        "marca": (fm.get("marca") or marca or "").strip().lower(),
        "model_id": model_id,
        "archetype": fm.get("archetype", ""),
        "theme": params.get("theme", ""),
        "image_treatment": (image.get("treatment") or "").strip(),
        "image_required": image.get("required"),
        "intent": "",
        "structure": "",
        "anti_patterns": [],
        "when_shines": "",
        "copy_direction": "",
    }
    for head, text in secs.items():
        field = _SECTION_MAP.get(head)
        if not field:
            continue
        dna[field] = _split_items(text) if field in _LIST_FIELDS else text
    return dna


def dna_prompt_block(dna: dict | None) -> str:
    """Bloco em PT-BR pronto pra injetar no `user` do diretor de arte. "" quando
    não há DNA útil. O LLM lê os anti-padrões e os converte em negativos (EN) no
    brief; a intenção/estrutura viram direção positiva + composição."""
    if not dna or dna.get("missing"):
        return ""
    intent = (dna.get("intent") or "").strip()
    structure = (dna.get("structure") or "").strip()
    antis = dna.get("anti_patterns") or []
    if not (intent or structure or antis):
        return ""
    lines = ["DNA DO MODELO (do blueprint — OBRIGATÓRIO respeitar):"]
    if intent:
        lines.append(f"• INTENÇÃO: {intent}")
    if structure:
        lines.append(f"• ESTRUTURA VISUAL / ENQUADRAMENTO: {structure}")
    if antis:
        lines.append("• ANTI-PADRÕES (NÃO faça — converta cada um em negativo no brief, em inglês):")
        lines.extend(f"    - {a}" for a in antis)
    return "\n".join(lines)


def dna_judge_block(dna: dict | None) -> str:
    """Bloco em PT-BR pro JUIZ (FASE 3): a peça pronta tem que CONDIZER com a DNA.
    Framing diferente do diretor — aqui o LLM CONFERE a peça contra o spec do modelo
    (anti-padrão presente = reprova; layout fora da estrutura = nota baixa), em vez de
    gerar. "" quando não há DNA útil (degrada gracioso, sem rubric extra)."""
    if not dna or dna.get("missing"):
        return ""
    intent = (dna.get("intent") or "").strip()
    structure = (dna.get("structure") or "").strip()
    antis = dna.get("anti_patterns") or []
    if not (intent or structure or antis):
        return ""
    lines = ["SPEC DO MODELO (do blueprint — confira a peça contra ele):"]
    if intent:
        lines.append(f"• INTENÇÃO esperada: {intent}")
    if structure:
        lines.append(f"• ESTRUTURA/ENQUADRAMENTO esperado: {structure}")
    if antis:
        lines.append("• ANTI-PADRÕES (se a peça contém QUALQUER um destes = anti_pattern_violated):")
        lines.extend(f"    - {a}" for a in antis)
    return "\n".join(lines)
