"""Validation layer for generated copy pieces.

Per Agente_Copy_Criacao_v5.1_CORRIGIDO.md secao 10, a peca passa por quatro
checagens antes da entrega:

  1. Avaliacao contra o ICP ("faz sentido para esse publico?").
  2. Revisao de gramatica, fluencia e aderencia ao tom de voz da marca.
  3. Skill de Validacao (nota automatica) -- ver abaixo.
  4. Segundo agente avaliador (auto-critica final, ETAPA SEPARADA do
     julgamento interno que ja acontece durante a geracao em generator.py).

Todas via chamada ao Claude (modelo Opus, por ser julgamento de qualidade de
copy -- ver Documento_Mestre_Projeto_v2.md secao 7: "Opus para julgamento de
copy (tom, angulo, calibracao de voz)").

Confirmado pelo Tiago: a "Skill de Validacao" da secao 10/15 nao e uma skill
separada a localizar em outro lugar do time -- e a MESMA SKILLMETTACOPY.md
usada pra escrever, aqui reaplicada em modo leitura sobre a peca ja pronta
(em vez de guiar a escrita, ela audita o que ja foi feito contra o proprio
QA CHECKLIST). run_skill_de_validacao recebe o conteudo de SKILLMETTACOPY.md
como `skill_content` -- o caller e responsavel por carrega-lo (mesmo arquivo
que generator.py._BRAND_FILES ja usa pra escrever).

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

# Opus -> Sonnet 5 (decisão de custo, jul/2026). As 4 checagens deste módulo
# são uma camada de AUDITORIA pós-geração, separada do portão de qualidade
# real (generator.py._judge, que continua em Opus e roda dentro do loop de
# escrita). Medição real: mover estas 4 pra Sonnet corta ~40% do custo delas
# sem tocar no julgamento que de fato reprova rascunho fraco. Se a qualidade
# dos pareceres cair de forma perceptível, reverter é trocar só esta linha de
# volta pra "claude-opus-4-8".
VALIDATION_MODEL = "claude-sonnet-5"


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
    """Output of the Skill de Validacao (SKILLMETTACOPY.md em modo leitura).

    `is_stub` fica True somente quando `skill_content` vem vazio (arquivo nao
    encontrado/nao carregado pelo caller) -- nesse caso score e None e a nota
    explica o motivo, em vez de fingir uma avaliacao real sem a skill em maos.
    """

    score: float | None
    note: str
    is_stub: bool


def _extract_json(text: str) -> dict:
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def _text_of(response: anthropic.types.Message, stage: str = "?") -> str:
    """Mesmo endurecimento de generator.py._text_of: next() sem default
    estourava StopIteration cru quando a resposta nao tinha bloco de texto
    (reproduzido em producao, embora nestas 4 chamadas nao haja thinking --
    blindagem defensiva, nao um bug confirmado aqui). `stage` identifica qual
    das 4 chamadas falhou (icp_fit/grammar_tone/second_evaluator/skill_de_validacao)."""
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        block_types = [block.type for block in response.content]
        raise RuntimeError(
            f"[{stage}] Resposta sem bloco de texto (blocos recebidos: {block_types}, "
            f"stop_reason: {getattr(response, 'stop_reason', '?')})."
        )
    return text_blocks[0]


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
        # 4096 -> 16000: reproduziu em producao no second_evaluator (stage
        # abaixo) -- 4096 nao bastava, mesma familia de bug do generator.py
        # (thinking implicito consome o orcamento antes do JSON final,
        # stop_reason=max_tokens sem nenhum bloco de texto). 16000 e a mesma
        # margem que resolveu la; subindo nas 4 chamadas deste arquivo porque
        # usam o mesmo _text_of/_extract_json e o mesmo modelo.
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _text_of(response, stage="icp_fit")
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
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _text_of(response, stage="grammar_tone")
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

    prompt = f"""Voce e o segundo agente avaliador do Agente Copy -- uma \
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
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _text_of(response, stage="second_evaluator")
    data = _extract_json(text)
    return SecondEvaluatorResult(approved=bool(data["approved"]), feedback=data["feedback"])


def run_skill_de_validacao(
    client: anthropic.Anthropic, piece: dict, skill_content: str
) -> SkillDeValidacaoResult:
    """Skill de Validacao: SKILLMETTACOPY.md reaplicada em modo leitura sobre
    a peca ja pronta, devolvendo uma nota de 0 a 10 contra o proprio QA
    CHECKLIST da skill -- a mesma regra usada pra escrever, aqui usada pra
    auditar o que ja foi escrito.

    Distinta do segundo agente avaliador (approved/feedback, sem nota) e do
    julgamento interno de generator.py._judge (reescreve o rascunho).
    """
    if not skill_content.strip():
        return SkillDeValidacaoResult(
            score=None,
            note=(
                "Sem SKILLMETTACOPY.md carregado -- o caller nao passou o conteudo "
                "da skill (skill_content vazio), entao nao ha o que auditar."
            ),
            is_stub=True,
        )

    full_text = piece.get("full_text") or "\n\n".join(
        part for part in (piece.get("hook"), piece.get("corpo"), piece.get("cta")) if part
    )

    prompt = f"""Voce e a Skill de Validacao do Agente Copy -- a mesma \
skill abaixo usada pra ESCREVER, aqui reaplicada em modo LEITURA sobre uma peca ja \
pronta. Releia o QA CHECKLIST da skill e avalie a peca item a item contra ele.

Skill de copy da marca (usada para escrever esta peca):
{skill_content}

Peca pronta para auditoria:
{full_text}

Responda apenas com um JSON no formato:
{{"score": nota de 0 a 10 (numero, pode ter uma casa decimal), "note": "avaliacao objetiva item a item do QA CHECKLIST, em portugues"}}"""

    response = client.messages.create(
        model=VALIDATION_MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _text_of(response, stage="skill_de_validacao")
    data = _extract_json(text)
    return SkillDeValidacaoResult(score=float(data["score"]), note=data["note"], is_stub=False)
