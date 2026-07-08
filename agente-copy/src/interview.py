"""Interview engine for the Copy agent.

The agent never writes before it asks. This module models the pre-writing
interview: a set of base questions (the PMO list, section 5) plus questions
specific to each copy type (section 3), collected into a Brief that the
generation layer consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Brand(str, Enum):
    METTA = "metta"
    TIAGO = "tiago"


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class EmotionalAxis(str, Enum):
    DOR = "dor"
    DESEJO = "desejo"
    NECESSIDADE = "necessidade"


class CopyType(str, Enum):
    CARROSSEL = "carrossel"
    POST_UNICO = "post_unico"
    DESCRICAO_POST = "descricao_post"
    STORIES = "stories"
    REELS = "reels"
    CRIATIVOS = "criativos"


# Rótulo pra exibição na UI -- o .value do enum é o identificador em
# snake_case sem acento (contrato com o backend/testes), não o texto que um
# humano deveria ler no formulário.
COPY_TYPE_LABELS: dict[CopyType, str] = {
    CopyType.CARROSSEL: "Carrossel",
    CopyType.POST_UNICO: "Post único",
    CopyType.DESCRICAO_POST: "Descrição de post",
    CopyType.STORIES: "Stories",
    CopyType.REELS: "Reels",
    CopyType.CRIATIVOS: "Criativos",
}


@dataclass
class Brief:
    brand: Brand
    copy_type: CopyType
    objective: str
    icp: str
    angle_choice: str
    emotional_axis: EmotionalAxis | None
    cta: str
    platform: Platform
    # Tamanho-alvo do texto (ex: "90-180 caracteres", "curto", "texto longo",
    # ou o que o usuário escrever livremente). Vazio = sem restrição, o modelo
    # usa o tamanho típico do formato. Só orienta o prompt, não é validado
    # rigidamente -- o modelo mira essa faixa, não conta caractere a caractere.
    length: str = ""
    # Controle explícito do usuário sobre trazer prova social (case espelho
    # nominal). Default True preserva o comportamento de antes deste campo
    # existir. False é diferente de "peça curta corta automaticamente" (ver
    # generator._is_short_length) -- aqui é escolha direta, vale mesmo em
    # peça longa onde o usuário não quer case por outro motivo (ex: peça
    # institucional pura).
    include_case: bool = True
    type_specific: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    purpose: str
    # Conjunto fechado de respostas válidas, quando existir (ex: "30s"/"1min"/
    # "2min"). None para perguntas de texto livre (objective, icp, cta...) ou
    # onde a resposta certa não é uma escolha fixa (angle_choice -- a IA
    # deveria propor as 3 opções com justificativa, não é dropdown estático;
    # progression -- é a sequência que a IA aplica, não uma escolha do
    # usuário). Consumido pela UI do brandsystem pra decidir <select> vs
    # <input> (api/copy-agent.py + embed/agente-copy.html).
    options: tuple[str, ...] | None = None


# The brand question is NOT in the original PMO list (section 5). It is a
# deliberate addition to lock the inviolable separation of the two brand voices
# (Documento Mestre v2, section 1) before a single line is written. It is asked
# first, always, and pending Tiago's approval to keep or drop.
BRAND_QUESTION = Question(
    key="brand",
    prompt="Qual marca? (Metta ou Tiago Alves)",
    purpose="Trava a separação inviolável das vozes antes de escrever",
)

# Base questions from the PMO list (section 5), asked for every copy type.
# Format/tempo questions from the PMO belong to the per-type sets below, so they
# are not duplicated here.
BASE_QUESTIONS: list[Question] = [
    Question("objective", "Qual é o objetivo?", "Direciona toda a copy"),
    Question("icp", "Qual o ICP?", "Embebe a peça no público certo"),
    Question("angle_choice", "Qual ângulo deseja seguir? (A / B / C)", "Evita retrabalho antes de escrever"),
    Question(
        "emotional_axis",
        "Trabalhar dor, desejo ou necessidade — e qual?",
        "Define o eixo emocional",
        options=("dor", "desejo", "necessidade"),
    ),
    Question("cta", "Existe CTA específico?", "Define o fechamento"),
    Question(
        "platform",
        "Qual plataforma? (Instagram ou LinkedIn)",
        "Adapta o tom por plataforma",
        options=("instagram", "linkedin"),
    ),
]


TYPE_QUESTIONS: dict[CopyType, list[Question]] = {
    CopyType.CARROSSEL: [
        Question(
            "input_mode",
            "É só uma ideia ou um texto bruto para transformar?",
            "Define o fluxo de produção",
            options=("ideia solta", "texto bruto"),
        ),
        Question(
            "reading_time",
            "Quanto tempo de leitura? (30s / 1min / 2min)",
            "Dimensiona o tamanho da copy",
            options=("30s", "1min", "2min"),
        ),
    ],
    CopyType.POST_UNICO: [
        Question(
            "subtype",
            "Frase chamariz, frase de autor ou texto longo?",
            "Define o subtipo do estático",
            options=("frase chamariz", "frase de autor", "texto longo"),
        ),
        Question(
            "signature",
            "Há assinatura / @ / autoria a exibir?",
            "Ajusta o fecho do texto",
            options=("sim", "não"),
        ),
    ],
    CopyType.DESCRICAO_POST: [
        Question(
            "accompanies",
            "A descrição acompanha qual peça? (estático / carrossel / reels)",
            "Calibra extensão e função da legenda",
            options=("estático", "carrossel", "reels"),
        ),
        Question(
            "weight",
            "A descrição é o chamariz ou complementa o visual?",
            "Define o peso da copy na descrição",
            options=("chamariz", "complementa o visual"),
        ),
    ],
    CopyType.STORIES: [
        Question(
            "sequence_mode",
            "Story único ou sequência?",
            "Define se ativa a mecânica de progressão",
            options=("único", "sequência"),
        ),
        Question(
            "story_type",
            "Qual tipo? (enquete / caixinha / sequência / levantamento de dor)",
            "Seleciona a estrutura",
            options=("enquete", "caixinha", "sequência", "levantamento de dor"),
        ),
        Question(
            "progression",
            "Se sequência: qual progressão? (dor → desejo → necessidade)",
            "Define o eixo de cada story",
            # Sem options: é a sequência que a IA aplica automaticamente
            # quando sequence_mode="sequência", não uma escolha do usuário.
        ),
        Question(
            "closing_hook",
            "Gera comentário ou abre caixa de pergunta ao final?",
            "Define o gancho de social selling",
            options=("gera comentário", "abre caixa de pergunta"),
        ),
    ],
    CopyType.REELS: [
        Question(
            "subtype",
            "Qual subtipo? (longo de conteúdo / curto / respondendo caixinha)",
            "Define a estrutura do roteiro",
            options=("longo de conteúdo", "curto", "respondendo caixinha"),
        ),
        Question(
            "input_mode",
            "É só uma ideia ou um texto bruto?",
            "Define o fluxo de produção",
            options=("ideia", "texto bruto"),
        ),
        Question("duration", "Qual a duração-alvo do vídeo?", "Dimensiona o roteiro"),
        Question(
            "opening_hook",
            "Começa com gancho/pergunta?",
            "Define a abertura",
            options=("sim", "não"),
        ),
        Question(
            "origin_question",
            "Se respondendo caixinha: qual a pergunta de origem?",
            "Conecta o reels ao story anterior",
        ),
    ],
    CopyType.CRIATIVOS: [
        Question(
            "media",
            "Criativo estático ou em vídeo?",
            "Define o formato da copy",
            options=("estático", "em vídeo"),
        ),
        Question(
            "winner_or_new",
            "É criativo novo ou variação de um vencedor?",
            "Aciona o banco de vencedores (seção 6)",
            options=("novo", "variação de um vencedor"),
        ),
        Question(
            "cta_goal",
            "Qual objetivo? (lead / clique / agendamento)",
            "Direciona o CTA do criativo",
            options=("lead", "clique", "agendamento"),
        ),
    ],
}


COPY_TYPE_QUESTION = Question(
    key="copy_type",
    prompt="Qual formato? (carrossel / post_unico / descricao_post / stories / reels / criativos)",
    purpose="Seleciona o tipo e suas perguntas próprias",
)


_BRAND_ALIASES = {
    "metta": Brand.METTA,
    "tiago": Brand.TIAGO,
    "tiago alves": Brand.TIAGO,
}

_AXIS_ALIASES = {axis.value: axis for axis in EmotionalAxis}


def _parse_brand(value: str) -> Brand:
    return _BRAND_ALIASES[value.strip().lower()]


def _parse_platform(value: str) -> Platform:
    return Platform(value.strip().lower())


def _parse_copy_type(value: str) -> CopyType:
    return CopyType(value.strip().lower())


def _parse_axis(value: str) -> EmotionalAxis | None:
    normalized = value.strip().lower()
    for token, axis in _AXIS_ALIASES.items():
        if token in normalized:
            return axis
    return None


def build_brief_from_answers(answers: dict) -> Brief:
    """Build a Brief from a flat answer dict (e.g. from the brandsystem web UI).

    Base-question keys and the type-specific keys (from TYPE_QUESTIONS) live in
    the same dict; type-specific ones are routed into Brief.type_specific.
    """
    copy_type = _parse_copy_type(answers["copy_type"])
    type_keys = {q.key for q in TYPE_QUESTIONS[copy_type]}

    return Brief(
        brand=_parse_brand(answers["brand"]),
        copy_type=copy_type,
        objective=answers["objective"],
        icp=answers["icp"],
        angle_choice=answers["angle_choice"],
        emotional_axis=_parse_axis(answers.get("emotional_axis", "")),
        cta=answers["cta"],
        platform=_parse_platform(answers["platform"]),
        length=answers.get("length", ""),
        include_case=_parse_bool_default_true(answers.get("include_case", True)),
        type_specific={key: answers[key] for key in type_keys if key in answers},
    )


def _parse_bool_default_true(value: object) -> bool:
    """Aceita bool real (vindo de JSON) ou string ('sim'/'não'/'true'/'false')
    -- ausência do campo (None) default True, preserva o comportamento de
    antes deste campo existir (sempre tentava trazer case)."""
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("não", "nao", "false", "0", "")


def run_interview(copy_type: str | None = None) -> Brief:
    answers: dict[str, str] = {}

    answers[BRAND_QUESTION.key] = input(f"{BRAND_QUESTION.prompt}\n> ")

    for question in BASE_QUESTIONS:
        answers[question.key] = input(f"{question.prompt}\n> ")

    if copy_type is None:
        copy_type = input(f"{COPY_TYPE_QUESTION.prompt}\n> ")
    answers["copy_type"] = copy_type

    resolved_type = _parse_copy_type(answers["copy_type"])
    for question in TYPE_QUESTIONS[resolved_type]:
        answers[question.key] = input(f"{question.prompt}\n> ")

    return build_brief_from_answers(answers)
