"""Validation layer for generated copy pieces.

Per Agente_Copy_Criacao_v5.1_CORRIGIDO.md secao 10, a peca passa por quatro
checagens antes da entrega:

  1. Avaliacao contra o ICP ("faz sentido para esse publico?").
  2. Revisao de gramatica, fluencia e aderencia ao tom de voz da marca.
  3. Skill de Validacao (nota automatica) -- ainda stub, ver abaixo.
  4. Segundo agente avaliador (auto-critica final, ETAPA SEPARADA do
     julgamento interno que ja acontece durante a geracao em generator.py).

Todas via chamada ao Claude (modelo Opus, por ser julgamento de qualidade de
copy -- ver Documento_Mestre_Projeto_v2.md secao 7: "Opus para julgamento de
copy (tom, angulo, calibracao de voz)"), exceto a Skill de Validacao (stub).

A secao 10/15 tambem menciona uma "Skill de Validacao" (nota automatica) que
ja existe em algum lugar do time, mas ainda nao foi localizada nem integrada
("Localizar e integrar antes do MVP"). SkillDeValidacao abaixo e um stub
explicito para essa peca ausente -- nao deve ser confundido com a validacao
real quando ela for integrada.

O segundo agente avaliador (item 4) e distinto do julgamento em
generator.py._judge: aquele roda MULTIPLAS vezes durante a escrita, reescreve
o rascunho e faz parte do loop de geracao; este roda UMA vez, sobre a peca ja
pronta, so critica (nunca reescreve), e reprovacao aqui nao bloqueia a
entrega automaticamente -- e sinal pro humano que aprova a publicacao, igual
a nota da skill. Confusao entre os dois ja existiu no codigo (o prompt de
generator.py chegou a se chamar "segundo agente avaliador" por engano) --
corrigido, e este modulo e o unico lugar onde o segundo agente de verdade
roda.

O caller passa um client `anthropic.Anthropic` ja construido; este modulo
nunca instancia um client sozinho.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

VALIDATION_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class ICPFitResult:
    passed: bool
    reasoning: str


@dataclass(frozen=True)
class ToneCheckResult:
    passed: bool
    correcao: str
    fluencia: str
    aderencia_tom: str
    reasoning: str


@dataclass(frozen=True)
class SecondEvaluatorResult:
    """Verdict of the second evaluator agent (auto-critica final, separada
    do julgamento interno de rascunho em generator.py). Never rewrites the
    piece -- only says whether it would hesitate to ship it, and why."""

    approved: bool
    feedback: str


@dataclass(frozen=True)
class SkillDeValidacaoResult:
    """Placeholder output for the (not-yet-located) Skill de Validacao.

    score is always None here. This class exists so the pipeline has a slot
    to plug the real skill into later, but it must never be mistaken for a
    real score -- `is_stub` is always True and `note` says so explicitly.
    """

    score: float | None
    note: str
    is_stub: bool = True


def _extract_json(text: str) -> dict:
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def check_icp_fit(client: anthropic.Anthropic, piece: dict, icp: str) -> ICPFitResult:
    """Ask Claude whether the piece makes sense for the given ICP.

    `piece` is expected to carry at least `full_text` (or hook/corpo/cta).
    """
    full_text = piece.get("full_text") or "\n\n".join(
        part for part in (piece.get("hook"), piece.get("corpo"), piece.get("cta")) if part
    )

    prompt = f"""Voce e um revisor de copywriting. Avalie se a peca abaixo faz sentido \
para o ICP (publico-alvo) descrito, considerando linguagem, dores/desejos citados e nivel \
de consciencia do publico.

ICP:
{icp}

Peca:
{full_text}

Responda apenas com um JSON no formato:
{{"passed": true ou false, "reasoning": "explicacao objetiva em portugues"}}"""

    response = client.messages.create(
        model=VALIDATION_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    data = _extract_json(text)
    return ICPFitResult(passed=bool(data["passed"]), reasoning=data["reasoning"])


def check_grammar_tone(
    client: anthropic.Anthropic, piece: dict, tom_de_voz: str
) -> ToneCheckResult:
    """Check correcao, fluencia and aderencia ao tom de voz da marca.

    `tom_de_voz` is the raw content of the brand's tom-de-voz knowledge file.
    """
    full_text = piece.get("full_text") or "\n\n".join(
        part for part in (piece.get("hook"), piece.get("corpo"), piece.get("cta")) if part
    )

    prompt = f"""Voce e um revisor de copywriting. Avalie a peca abaixo em tres eixos: \
correcao gramatical, fluencia de leitura e aderencia ao tom de voz da marca descrito.

Tom de voz da marca:
{tom_de_voz}

Peca:
{full_text}

Responda apenas com um JSON no formato:
{{
  "passed": true ou false,
  "correcao": "avaliacao objetiva da correcao gramatical",
  "fluencia": "avaliacao objetiva da fluencia",
  "aderencia_tom": "avaliacao objetiva da aderencia ao tom de voz",
  "reasoning": "resumo da decisao final"
}}"""

    response = client.messages.create(
        model=VALIDATION_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    data = _extract_json(text)
    return ToneCheckResult(
        passed=bool(data["passed"]),
        correcao=data["correcao"],
        fluencia=data["fluencia"],
        aderencia_tom=data["aderencia_tom"],
        reasoning=data["reasoning"],
    )


def run_second_evaluator(
    client: anthropic.Anthropic, piece: dict, tom_de_voz: str
) -> SecondEvaluatorResult:
    """Segundo agente avaliador: auto-critica final, ETAPA SEPARADA do
    julgamento que roda dentro de generator.py durante a escrita do rascunho.

    Roda uma unica vez, sobre a peca ja pronta (depois do loop de revisao e
    da adaptacao LinkedIn, se houver) -- e o ultimo gate antes da aprovacao
    humana. Nao reescreve nada; so aponta se hesitaria em publicar e por que.
    Reprovacao aqui e sinal pro humano decidir, igual a nota da skill -- nao
    bloqueia a entrega sozinha (regra de aprovacao humana obrigatoria).
    """
    full_text = piece.get("full_text") or "\n\n".join(
        part for part in (piece.get("hook"), piece.get("corpo"), piece.get("cta")) if part
    )

    prompt = f"""Voce e o segundo agente avaliador do Agente Copy da Metta Brasil -- uma \
etapa de auto-critica INDEPENDENTE do julgamento que ja aconteceu durante a escrita do \
rascunho. Voce recebe a peca JA PRONTA, revisada e aprovada internamente, e faz uma ultima \
leitura cetica antes da entrega ao humano que aprova a publicacao. Voce nao reescreve a \
peca -- so aponta se ela esta pronta pra ir ao ar ou nao, e por que.

Tom de voz da marca:
{tom_de_voz}

Peca pronta para revisao final:
{full_text}

Responda apenas com um JSON no formato:
{{"approved": true ou false, "feedback": "critica objetiva -- o que faria voce hesitar antes de publicar isso, ou por que esta pronta"}}"""

    response = client.messages.create(
        model=VALIDATION_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    data = _extract_json(text)
    return SecondEvaluatorResult(approved=bool(data["approved"]), feedback=data["feedback"])


def run_skill_de_validacao(piece: dict) -> SkillDeValidacaoResult:
    """Stub for the Skill de Validacao referenced in secao 10/15 of the spec.

    The real skill has not been located by the team yet ("Skill de Validacao
    nao localizada... Localizar e integrar antes do MVP"). This function
    unmistakably marks its output as a placeholder rather than silently
    pretending to be the real thing.
    """
    return SkillDeValidacaoResult(
        score=None,
        note=(
            "STUB: a Skill de Validacao real ainda nao foi localizada nem integrada "
            "(ver Agente_Copy_Criacao_v5.1_CORRIGIDO.md, secao 15). Este resultado "
            "nao e uma nota real -- e um placeholder ate a skill ser encontrada e "
            "conectada ao fluxo."
        ),
    )
