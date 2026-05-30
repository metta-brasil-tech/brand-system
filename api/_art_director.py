"""Diretor de Arte (LLM dentro de trilhos).

Eleva de "template preenchido" pra "composição de designer". Dado o brief + copy
+ archetype + tema, um DA sênior decide, POR PEÇA:
  - headline_marked: quebras de linha por ritmo/sentido + 1-2 palavras-accent (a
    "virada") marcadas com *asteriscos*. NÃO muda as palavras, só compõe.
  - gaze_direction / crop_focus: direção de arte da FOTO (olhar do sujeito puxa
    pro texto; enquadramento editorial) — vira instrução no prompt de imagem.
  - emphasis: elemento focal.

Saída JSON estrita. Usa o LLM do pipeline (LLMAdapter.complete).
"""
from __future__ import annotations

import json
import re

_SYSTEM = """Você é DIRETOR DE ARTE sênior da Metta — marca de inteligência comercial,
estética editorial séria (HBR/Exame/Bloomberg), autoridade, nunca festiva.
Tipografia display: Zalando Sans Expanded (larga, pesada, caixa-alta). Accent = amarelo Metta.

Sua tarefa: dada a COPY já escrita e o ESTILO escolhido, tomar decisões de COMPOSIÇÃO
como um designer faria à mão. Você NÃO reescreve a copy — preserva as palavras exatas.

Decida:
1. headline_marked — a MESMA headline, com:
   • quebras de linha (\\n) onde um designer quebraria: por sentido e ritmo, equilibrando
     o comprimento das linhas, isolando a palavra de impacto na sua própria linha quando
     potencializa. Caixa e pontuação preservadas. Máx ~5 linhas.
   • 1 ou 2 palavras-accent envoltas em *asteriscos* — a "virada" da frase, a palavra que
     sozinha entrega a tensão. Nunca marque artigo/preposição. Nunca mais de 2.
2. gaze_direction — pra onde o sujeito da foto olha, puxando o olho pro texto:
   "left" | "right" | "camera" | "down" | "away". (Se o texto fica à esquerda, sujeito olha left.)
3. crop_focus — enquadramento: "face" | "chest-up" | "waist-up" | "environment".
4. emphasis — elemento que domina: "headline" | "image" | "number".
5. rationale — 1 frase curta explicando a decisão de composição.

Responda APENAS com JSON válido, sem cercas, neste formato:
{"headline_marked": "...", "gaze_direction": "...", "crop_focus": "...", "emphasis": "...", "rationale": "..."}"""


def _coerce_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        t = m.group(0)
    return json.loads(t)


def direct(copy: dict, archetype: str, theme: str, marca: str, brief: str,
           llm, placement: str = "") -> dict:
    """Retorna diretivas de composição. `llm` precisa ter .complete(system, user)."""
    headline = (copy.get("headline") or "").strip()
    if not headline:
        return {}
    text_side = "esquerda" if placement in ("right-bleed", "fullbleed", "") else "direita"
    user = (
        f"MARCA: {marca}\nESTILO (archetype): {archetype} · tema: {theme}\n"
        f"PLACEMENT da foto: {placement or 'sem foto'} (texto fica à {text_side})\n"
        f"BRIEF: {brief or '(institucional)'}\n\n"
        f"COPY:\nheadline: {headline}\n"
        f"subhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\n"
        f"cta: {copy.get('cta','')}\n\n"
        f"Componha. Lembre: preserve as palavras EXATAS da headline; só adicione \\n e *accent*."
    )
    resp = llm.complete(system=_SYSTEM, user=user, max_tokens=600)
    content = getattr(resp, "content", resp)
    out = _coerce_json(content)

    # Salvaguarda: a headline marcada não pode perder/trocar palavras. Compara
    # tokens alfanuméricos ignorando *asteriscos* e quebras. Se divergir, descarta
    # o headline_marked (mantém o resto das diretivas).
    hm = out.get("headline_marked", "")
    def toks(s):
        return re.findall(r"\w+", (s or "").lower())
    if hm and toks(hm.replace("*", "")) != toks(headline):
        out["headline_marked"] = ""  # não confia — usa a headline original
        out["_headline_rejected"] = True
    return out
