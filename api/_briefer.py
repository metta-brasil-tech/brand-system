"""Briefer A↔B — refina o prompt de imagem ANTES de gastar geração (Fase 12).

Bate-bola propositor↔crítico portado do plugin-metta-ads: um agente PROPÕE uma
reescrita do prompt de imagem mirando os 3 erros reais mapeados (ICP genérico,
amarelo Metta ausente, baixa concretude); outro CRITICA contra os limites do
gpt-image (mãos/texto/faces/UI/numerais) + a composição-por-slot e devolve
correções. Itera N rodadas e só então o prompt vai pro image-gen.

Gated: chamado só quando BRIEFER=1 (default OFF). Degrada gracioso — qualquer
falha de LLM/parse devolve o prompt original intocado, então o pipeline nunca
quebra por causa do refino.
"""
from __future__ import annotations

import json
import os
import re

# Reusa os modos de falha do gpt-image que o _art_director já cataloga, pro
# crítico checar contra a MESMA lista que vira negative_prompt no fim.
from _art_director import NEG_MODEL_FAILS


def _coerce_json(text: str) -> dict:
    """Idêntico ao de _art_director: tolera fences e prosa em volta do JSON."""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        t = m.group(0)
    return json.loads(t)


_SYSTEM_PROPOSITOR = """Você é ENGENHEIRO DE PROMPT DE IMAGEM sênior, refinando um \
prompt que JÁ existe antes de mandá-lo pro gpt-image. Seu trabalho NÃO é reescrever \
do zero — é CONSERTAR três falhas recorrentes sem perder o que já está bom:

1. ICP GENÉRICO → ancore a persona/cena no AVATAR ALVO e no CONHECIMENTO DA MARCA \
(quem é o decisor, em que momento, em que ambiente concreto). Nada de "uma pessoa", \
"um profissional": dê papel, ambiente e ação específicos.
2. AMARELO METTA AUSENTE → quando o tema/marca pede, traga o amarelo Metta como cor \
presente na cena (objeto, luz, peça de roupa, superfície) — não como overlay de texto.
3. BAIXA CONCRETUDE → troque abstração por um objeto/gesto/ambiente específico e \
fotografável. Cena que dá pra apontar, não conceito vago.

Preserve aspect ratio e o enquadramento/composição-por-slot. Se o CRÍTICO apontou \
problemas, corrija CADA um. Devolva SOMENTE JSON:
{"prompt": "<prompt de imagem refinado, em inglês>", "rationale": "<1 frase: o que mudou>"}"""


_SYSTEM_CRITICO = """Você é CRÍTICO de prompt de imagem. Avalia um prompt CANDIDATO \
contra os limites do gpt-image e a direção de arte. Reprove se:
- pede texto/letras/números/logos/UI legíveis na imagem (o modelo erra isso);
- arrisca mãos/dedos/faces/corpos deformados sem necessidade;
- a persona/cena continua genérica (sem ICP/ambiente concreto);
- o amarelo Metta foi pedido pela direção e sumiu;
- abandonou o aspect ratio ou a composição-por-slot.

Devolva SOMENTE JSON:
{"approved": true|false, "issues": ["<problema acionável>", ...]}
Se aprovado, "issues" vazio. Seja exigente mas conciso: no máx 3 issues, os que mais importam."""


def _propose(llm, base_prompt: str, grounding: str, critic_issues: list[str]) -> dict:
    issues_blk = ""
    if critic_issues:
        issues_blk = (
            "\nO CRÍTICO REPROVOU a versão anterior. Corrija CADA item:\n- "
            + "\n- ".join(critic_issues)
        )
    user = (
        f"PROMPT ATUAL:\n{base_prompt}\n\n"
        f"{grounding}"
        f"{issues_blk}\n\n"
        "Refine mirando ICP concreto, amarelo Metta (se a direção pedir) e concretude."
    )
    resp = llm.complete(system=_SYSTEM_PROPOSITOR, user=user, max_tokens=700)
    out = _coerce_json(getattr(resp, "content", resp))
    return out


def _critique(llm, candidate: str, grounding: str) -> dict:
    user = (
        f"PROMPT CANDIDATO:\n{candidate}\n\n"
        f"{grounding}\n"
        f"MODOS DE FALHA DO MODELO a evitar: {NEG_MODEL_FAILS}\n\n"
        "Avalie."
    )
    resp = llm.complete(system=_SYSTEM_CRITICO, user=user, max_tokens=400)
    out = _coerce_json(getattr(resp, "content", resp))
    return out


def enabled() -> bool:
    """Gate: default OFF. Liga com BRIEFER=1 (opt-in)."""
    return os.getenv("BRIEFER", "0") == "1"


def refine(
    llm,
    prompt: str,
    *,
    marca: str = "",
    avatar: str = "",
    knowledge: str = "",
    art_direction: str = "",
    placement: str = "",
    rounds: int | None = None,
) -> tuple[str, list[str]]:
    """Refina `prompt` em até `rounds` bate-bolas A↔B. Retorna (prompt, log).

    Degrada gracioso: qualquer exceção devolve o prompt ORIGINAL + um log
    explicando o pulo. `rounds` default vem de BRIEFER_ROUNDS (=1).
    """
    log: list[str] = []
    if not (prompt or "").strip():
        return prompt, ["briefer: prompt vazio — pulado"]

    n = rounds if rounds is not None else int(os.getenv("BRIEFER_ROUNDS", "1"))
    if n < 1:
        return prompt, ["briefer: rounds<1 — pulado"]

    grounding = "\n".join(
        x for x in [
            f"MARCA: {marca}" if marca else "",
            f"AVATAR ALVO (ICP):\n{avatar.strip()}" if (avatar or "").strip() else "",
            f"CONHECIMENTO DA MARCA:\n{knowledge.strip()}" if (knowledge or "").strip() else "",
            f"DIREÇÃO DE ARTE DA FOTO:\n{art_direction.strip()}" if (art_direction or "").strip() else "",
            f"COMPOSIÇÃO-POR-SLOT (placement): {placement}" if placement else "",
        ] if x
    ) or "(sem grounding adicional)"

    current = prompt
    issues: list[str] = []
    try:
        for i in range(1, n + 1):
            proposed = _propose(llm, current, grounding, issues)
            cand = (proposed.get("prompt") or "").strip()
            if not cand:
                log.append(f"briefer: rodada {i} sem prompt — mantém anterior")
                break
            current = cand
            rationale = (proposed.get("rationale") or "").strip()
            verdict = _critique(llm, current, grounding)
            issues = [s for s in (verdict.get("issues") or []) if isinstance(s, str) and s.strip()]
            approved = bool(verdict.get("approved")) and not issues
            log.append(
                f"briefer r{i}: {'APROVADO' if approved else 'reprovado'}"
                + (f" — {rationale}" if rationale else "")
                + (f" | issues={len(issues)}" if issues else "")
            )
            if approved:
                break
        if current != prompt:
            log.insert(0, f"briefer: prompt refinado em {min(n, len(log))} rodada(s)")
        else:
            log.append("briefer: prompt mantido (sem ganho)")
        return current, log
    except Exception as e:  # noqa: BLE001 — refino é best-effort, nunca quebra o pipeline
        return prompt, [f"briefer: PULADO ({e.__class__.__name__}: {str(e)[:100]}) — usa prompt original"]
