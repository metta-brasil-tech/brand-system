"""Two-stage copy generation for Agente Copy (Metta Brasil).

Pipeline mirrors the documented architecture (Documento_Mestre_Projeto_v2 /
Agente_Copy_Criacao_v5.1, "Arquitetura técnica"):

  1. Sonnet drafts the structural piece (hook + corpo + CTA) respecting the
     copy-type-specific flow from SKILLMETTACOPY.md.
  2. Opus judges tone / angle / voice calibration against tom-de-voz-metta.md
     and the skill's QA checklist, and may send the draft back for revision.

The Anthropic knowledge base is plain markdown read fresh each cycle — no RAG,
no embeddings, per the docs. Model IDs are fixed by the routing decision:
Sonnet 5 for structural work, Opus 4.8 for copy judgment. Never Haiku.

Depends on the `anthropic` SDK (add `anthropic` to requirements.txt — owned by
another agent). The caller supplies a constructed `anthropic.Anthropic` client;
this module never instantiates one or reads keys.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import anthropic

# Structural drafting vs. copy judgment. Do not use Haiku (documented decision).
SONNET_MODEL = "claude-sonnet-5"
OPUS_MODEL = "claude-opus-4-8"

# Repo root holds the markdown knowledge base (this file lives in src/).
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Per-brand knowledge files, in the load order the docs prescribe. Tom de voz
# first (primary voice constraint), then the operational skill, then context.
_BRAND_FILES: dict[str, tuple[str, ...]] = {
    "metta": (
        "tom-de-voz-metta.md",
        "SKILLMETTACOPY.md",
        "avatar.md",
        "posicionamento.md",
        "oferta.md",
        "provas.md",
        "glossario-2.md",
    ),
}

Brand = Literal["metta", "tiago"]

# Reuse interview.Brief if the parallel task has landed it; otherwise fall back
# to a minimal local definition so import ordering doesn't block this module.
# Field name must match interview.Brief.type_specific (not "extra") since real
# Brief instances always carry that name.
try:
    from src.interview import Brief  # type: ignore[import-not-found]
except ImportError:
    try:
        from interview import Brief  # type: ignore[import-not-found]
    except ImportError:

        @dataclass
        class Brief:
            brand: Brand
            copy_type: str
            objective: str
            icp: str
            angle_choice: str
            emotional_axis: str
            cta: str
            platform: str = "instagram"
            type_specific: dict[str, Any] = field(default_factory=dict)


try:
    from src.icp_catalog import icp_knowledge_file  # type: ignore[import-not-found]
except ImportError:
    from icp_catalog import icp_knowledge_file  # type: ignore[import-not-found]


@dataclass
class GenerationResult:
    hook: str
    corpo: str
    cta: str
    full_text: str
    hook_variations: list[str]
    content_pillar: str
    target_icp: str
    platform: str
    linkedin_adaptation: str | None = None
    revision_notes: list[str] = field(default_factory=list)


class KnowledgeBase:
    """Reads the brand's markdown knowledge base fresh (no chunking, no cache)."""

    def __init__(self, brand: Brand, root: Path = _REPO_ROOT) -> None:
        if brand not in _BRAND_FILES:
            # Tiago's tom-de-voz file doesn't exist in the repo yet, so the
            # "tiago" brand can't be embedded. Fail loudly rather than mixing
            # voices — Metta and Tiago must never blend.
            raise NotImplementedError(
                f"Brand {brand!r} has no knowledge base yet. Only 'metta' is "
                "supported until tom-de-voz-tiago.md exists."
            )
        self.brand = brand
        self.root = root
        self._documents = self._load()

    def _load(self) -> dict[str, str]:
        documents: dict[str, str] = {}
        for filename in _BRAND_FILES[self.brand]:
            documents[filename] = (self.root / filename).read_text(encoding="utf-8")
        return documents

    def as_context(self) -> str:
        blocks = [
            f"<documento fonte=\"{name}\">\n{content}\n</documento>"
            for name, content in self._documents.items()
        ]
        return "\n\n".join(blocks)

    def document(self, filename: str) -> str:
        return self._documents[filename]


class CopyGenerator:
    # 2 -> 1: reduz o teto de chamadas Opus por pedido de 3 para 2 (draft +
    # até 2 julgamentos em vez de até 3) -- corta o pior caso de custo por
    # usuário sem depender de nenhuma infra nova de rate limit.
    def __init__(self, client: anthropic.Anthropic, max_revisions: int = 1) -> None:
        self.client = client
        self.max_revisions = max_revisions
        self._knowledge_bases: dict[Brand, KnowledgeBase] = {}

    def generate(self, brief: Brief) -> GenerationResult:
        if brief.brand != "metta":
            raise NotImplementedError(
                f"Brand {brief.brand!r} is not supported yet. Full support "
                "requires tom-de-voz-tiago.md, which is not in the repo."
            )

        knowledge = self._knowledge_base(brief.brand)
        draft = self._draft_structural(brief, knowledge)

        # The Opus pass judges against the QA checklist and can send the piece
        # back for revision; it is not a rubber stamp. We loop until it approves
        # or we exhaust max_revisions, keeping the last (revised) draft either way.
        revision_notes: list[str] = []
        for _ in range(self.max_revisions + 1):
            judgment = self._judge(brief, knowledge, draft)
            if judgment["approved"]:
                draft = judgment["piece"]
                break
            revision_notes.append(judgment["feedback"])
            draft = judgment["piece"]

        linkedin = None
        if brief.platform.lower() == "linkedin":
            linkedin = self._adapt_linkedin(brief, knowledge, draft)

        return GenerationResult(
            hook=draft["hook"],
            corpo=draft["corpo"],
            cta=draft["cta"],
            full_text=self._assemble(draft),
            hook_variations=draft["hook_variations"],
            content_pillar=draft["content_pillar"],
            target_icp=draft["target_icp"],
            platform=brief.platform,
            linkedin_adaptation=linkedin,
            revision_notes=revision_notes,
        )

    def _knowledge_base(self, brand: Brand) -> KnowledgeBase:
        if brand not in self._knowledge_bases:
            self._knowledge_bases[brand] = KnowledgeBase(brand)
        return self._knowledge_bases[brand]

    def _draft_structural(self, brief: Brief, knowledge: KnowledgeBase) -> dict[str, Any]:
        response = self.client.messages.create(
            model=SONNET_MODEL,
            # Reproduzido em produção com stage="draft_structural": o modelo
            # gasta parte do orçamento num bloco de thinking (não pedido
            # explicitamente) antes de montar o JSON do schema, e 4000
            # estourava antes de sobrar espaço pro JSON final.
            max_tokens=16000,
            system=_build_system_prompt(brief.brand, brief.copy_type),
            messages=[{"role": "user", "content": _build_structural_prompt(brief, knowledge)}],
            output_config={"format": {"type": "json_schema", "schema": _DRAFT_SCHEMA}},
        )
        return _extract_json(response, stage="draft_structural")

    def _judge(
        self, brief: Brief, knowledge: KnowledgeBase, draft: dict[str, Any]
    ) -> dict[str, Any]:
        response = self.client.messages.create(
            model=OPUS_MODEL,
            # Reproduzido ao vivo 3x: com thinking=adaptive + effort=high, a
            # resposta nunca saía do bloco de thinking pra escrever o JSON
            # final -- nem em 4000, nem 12000, nem 32000 (sempre
            # stop_reason=max_tokens, só bloco de thinking). Não era
            # orçamento pequeno, era incompatibilidade real entre thinking
            # estendido e saída forçada em json_schema -- tira o thinking e
            # o "effort: high" (que só se aplica com thinking) do julgamento.
            # Mesmo sem esses dois parâmetros, o modelo ainda gasta parte do
            # orçamento num bloco de thinking implícito antes do JSON (achado
            # em _draft_structural com o mesmo padrão de output_config) --
            # 16000 dá a mesma margem que resolveu lá.
            max_tokens=16000,
            output_config={
                "format": {"type": "json_schema", "schema": _JUDGMENT_SCHEMA},
            },
            system=_build_system_prompt(brief.brand, brief.copy_type),
            messages=[{"role": "user", "content": _build_judgment_prompt(brief, knowledge, draft)}],
        )
        return _extract_json(response, stage="judge")

    def _adapt_linkedin(
        self, brief: Brief, knowledge: KnowledgeBase, draft: dict[str, Any]
    ) -> str:
        response = self.client.messages.create(
            model=SONNET_MODEL,
            max_tokens=4000,
            system=_build_system_prompt(brief.brand, brief.copy_type),
            messages=[{"role": "user", "content": _build_linkedin_prompt(brief, draft)}],
        )
        return _text_of(response, stage="linkedin_adaptation")

    def propose_angles(
        self, brand: Brand, copy_type: str, icp: str, objective: str, raw_idea: str = ""
    ) -> list[dict[str, str]]:
        """Propõe 3 ângulos narrativos (A/B/C) com justificativa, antes de
        escrever qualquer peça (v5.1 seção 7 / critério de aceitação 5:
        "sugere ângulos A/B/C antes de escrever"). O usuário escolhe um -- só
        então a geração de fato roda, evitando retrabalho."""
        if brand != "metta":
            raise NotImplementedError(
                f"Brand {brand!r} is not supported yet. Full support "
                "requires tom-de-voz-tiago.md, which is not in the repo."
            )
        knowledge = self._knowledge_base(brand)
        response = self.client.messages.create(
            model=SONNET_MODEL,
            # 1500 nao era suficiente -- em producao a resposta vinha cortada
            # no meio de uma string (JSONDecodeError: Unterminated string),
            # mesma margem dos outros dois usos de SONNET_MODEL neste arquivo.
            max_tokens=4000,
            system=_build_system_prompt(brand, copy_type),
            messages=[
                {
                    "role": "user",
                    "content": _build_angles_prompt(copy_type, icp, objective, raw_idea, knowledge),
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": _ANGLES_SCHEMA}},
        )
        return _extract_json(response, stage="propose_angles")["angles"]

    @staticmethod
    def _assemble(draft: dict[str, Any]) -> str:
        return "\n\n".join(
            part for part in (draft["hook"], draft["corpo"], draft["cta"]) if part
        )


# --- Prompt construction -----------------------------------------------------


def _icp_context(icp_id: str) -> str:
    """Conteúdo do documento de ICP do segmento escolhido (v5.1 seção 14:
    "escreve embebido de ICP"). Vazio quando o id não veio do catálogo (ex.:
    testes com string livre) -- nesse caso o rótulo ainda aparece no
    briefing, só sem o documento completo."""
    filename = icp_knowledge_file(icp_id)
    if filename is None:
        return ""
    path = _REPO_ROOT / filename
    if not path.is_file():
        return ""
    return f'<documento fonte="{filename}">\n{path.read_text(encoding="utf-8")}\n</documento>'

# Copy-type-specific structure, drawn from SKILLMETTACOPY.md's Instagram Orgânico
# flow and the criação doc's copy types. Keeps the model on the real cadence per
# format instead of a generic hook/corpo/CTA shape.
_COPY_TYPE_GUIDANCE: dict[str, str] = {
    "carrossel": (
        "Carrossel: capa (slide 1) é a linha de hook isolada, nunca saudação nem "
        "contexto. Corpo em slides de parágrafos curtos (1-3 frases), progressão "
        "tensão → por que acontece → o que muda. Mediana de 9 slides (2-11). CTA no "
        "fechamento: gatilho de comentário é o padrão mais comum (usado pra ativar "
        "automação de DM), link na bio vem em segundo lugar e bem menos frequente; "
        "cerca de 1/3 das peças fecha sem CTA de conversão, em tom institucional. "
        "Hashtags quase nunca em carrossel — não force."
    ),
    "post_unico": (
        "Post único (estático): a frase de abertura carrega o peso inteiro — não há "
        "segunda chance. Muitos posts fecham só com 4-6 hashtags de nicho (#gestao "
        "#vendas #lideranca #empresario), sem CTA — postura de autoridade. Quando há "
        "CTA, é link na bio. Nunca use termos proprietários como hashtag."
    ),
    "descricao": (
        "Descrição de post: no estático a descrição É a copy principal, não um campo "
        "à parte. Calibre extensão pela peça que acompanha; feche com CTA claro."
    ),
    "stories": (
        "Stories: sequência dor → desejo → necessidade (social selling). Stories "
        "encadeados, cada um ativando um eixo, terminando em caixinha de perguntas ou "
        "gatilho de comentário. Fragmente o corpo em telas curtas."
    ),
    "reels": (
        "Reels: hook é quase sempre frase de identificação direta, não pergunta. "
        "Roteiro: gancho → ciclo do gargalo → por que as outras falharam → mecanismo "
        "fazedoria → case espelho com nome e número. CTA final majoritariamente link "
        "na bio; alternativa é pergunta reflexiva sem link."
    ),
    "criativo": (
        "Criativo / Ad Meta: hook de dor dupla do ciclo (max 3s) → identificação → "
        "mecanismo rápido (1 frase de fazedoria) → case espelho (nome + segmento + "
        "resultado) → CTA 'Agendar diagnóstico' (nunca 'Compre agora')."
    ),
}


def _copy_type_guidance(copy_type: str) -> str:
    return _COPY_TYPE_GUIDANCE.get(
        copy_type,
        "Estrutura padrão: hook (dor dupla do ciclo) → corpo (identificação + "
        "mecanismo + case espelho) → CTA de baixa fricção ('Agendar diagnóstico').",
    )


def _build_system_prompt(brand: Brand, copy_type: str) -> str:
    if brand != "metta":
        raise NotImplementedError(
            f"System prompt for brand {brand!r} not implemented — Tiago voice "
            "file does not exist yet."
        )
    return (
        "Você é o Agente Copy da Metta Brasil: um copywriter de resposta direta "
        "especializado em mentoria high-ticket para empresários >R$200k/mês.\n\n"
        "Você escreve na voz INSTITUCIONAL da Metta — nunca na voz pessoal do Tiago "
        "Alves. As duas vozes jamais se misturam. A Metta é autoridade técnica que "
        "opera como movimento: autoridade sem arrogância, técnica sem academicismo, "
        "movimento sem fanatismo. O protagonista é o método e o resultado, nunca a "
        "Metta falando de si.\n\n"
        "Escreva embebido de ICP, linguagem EMIC do cliente e do tom de voz da marca. "
        "Use linguagem de operação (tirador de pedido, apagando incêndio, tô "
        "dependente de mim), prova nominal (cliente + número exato), e nunca urgência "
        "artificial, FOMO, 'mindset', 'próximo nível' ou linguagem de coach.\n\n"
        f"Formato desta peça: {_copy_type_guidance(copy_type)}"
    )


def _build_structural_prompt(brief: Brief, knowledge: KnowledgeBase) -> str:
    icp_context = _icp_context(brief.icp)
    icp_block = f"{icp_context}\n\n" if icp_context else ""
    return (
        "Use a base de conhecimento abaixo (tom de voz, skill de copy, avatar, "
        "posicionamento, oferta, provas, glossário"
        + (", documento de ICP do segmento" if icp_context else "")
        + ") para escrever a peça.\n\n"
        f"{knowledge.as_context()}\n\n"
        f"{icp_block}"
        "=== BRIEFING DA PEÇA ===\n"
        f"{_render_brief(brief)}\n\n"
        "=== TAREFA ===\n"
        "Escreva a peça montada por partes, respeitando a estrutura do tipo de copy "
        "descrita no system prompt e no fluxo da SKILLMETTACOPY.md. Ative pelo menos "
        "duas dores conectadas do ciclo do gargalo e nomeie pelo menos uma "
        "contradição interna. Traga um case espelho nominal do segmento quando "
        "possível.\n\n"
        "Entregue: hook, corpo, CTA; no mínimo 3 variações de hook distintas; a "
        "indicação de pilar de conteúdo e o ICP-alvo. Responda no schema JSON pedido."
    )


def _build_judgment_prompt(
    brief: Brief, knowledge: KnowledgeBase, draft: dict[str, Any]
) -> str:
    return (
        "Você é o revisor de rascunho do Agente Copy (julgamento interno de geração --"
        " NÃO é o segundo agente avaliador; esse roda depois, uma vez, sobre a peça já "
        "pronta). Julgue o rascunho abaixo contra o tom de "
        "voz institucional da Metta (tom-de-voz-metta.md) e o QA CHECKLIST da "
        "SKILLMETTACOPY.md. Você tem autoridade para REPROVAR e reescrever — não "
        "aprove por inércia.\n\n"
        "Rode o checklist item a item: 2+ dores conectadas do ciclo; linguagem emic; "
        "case espelho nominal; garantia contratual quando cabível; tom de empresário "
        "falando (não coach); nenhuma urgência artificial; números específicos; "
        "contradição interna nomeada; o empresário se reconheceria; nenhuma palavra "
        "da lista 'nunca use'. Rode também os 7 testes de validação institucional "
        "(categoria nova, protagonismo do método, prova nominal, vocabulário próprio "
        "aplicado, oscilação rigor/acessibilidade, combate ao sistema e não à pessoa, "
        "coerência tonal do CTA).\n\n"
        f"{knowledge.document('tom-de-voz-metta.md')}\n\n"
        f"{knowledge.document('SKILLMETTACOPY.md')}\n\n"
        f"{_icp_context(brief.icp)}\n\n"
        "=== BRIEFING ===\n"
        f"{_render_brief(brief)}\n\n"
        "=== RASCUNHO A AVALIAR ===\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        "Se qualquer item falhar, defina approved=false, explique o que falhou em "
        "feedback e devolva a peça reescrita e corrigida em 'piece'. Se passar em "
        "tudo, defina approved=true e devolva a peça (com ajustes finos se quiser). "
        "Preserve sempre as 3+ variações de hook, o pilar e o ICP-alvo."
    )


def _build_angles_prompt(
    copy_type: str, icp: str, objective: str, raw_idea: str, knowledge: KnowledgeBase
) -> str:
    icp_context = _icp_context(icp)
    return (
        "Antes de escrever qualquer peça, proponha 3 ângulos narrativos "
        "diferentes para a mesma ideia -- Ângulo A, B e C -- cada um com uma "
        "abordagem concreta (não genérica) e uma linha de justificativa de "
        "por que pode performar com esse ICP. Isso evita retrabalho: o "
        "usuário escolhe um ângulo antes da peça ser escrita.\n\n"
        f"{knowledge.as_context()}\n\n"
        + (f"{icp_context}\n\n" if icp_context else "")
        + "=== CONTEXTO DA PEÇA ===\n"
        f"Tipo de copy: {copy_type}\n"
        f"ICP: {icp}\n"
        f"Objetivo: {objective}\n"
        + (f"Ideia/tema de partida: {raw_idea}\n" if raw_idea else "")
        + "\n=== TAREFA ===\n"
        "Gere exatamente os ângulos A, B e C. Responda no schema JSON pedido."
    )


def _build_linkedin_prompt(brief: Brief, draft: dict[str, Any]) -> str:
    # Real rewrite for LinkedIn per criação doc seção 4 — not copy-paste. Carrossel
    # vira PDF-style, descrição fica mais densa, tom apropriado da plataforma.
    return (
        "Reescreva a peça de Instagram abaixo para o LinkedIn. NÃO é copy-paste: é "
        "reescrita com o tom apropriado da plataforma. Carrossel de IG vira formato "
        "PDF-style (documento) no LinkedIn; a descrição fica mais densa e analítica. "
        "Mantenha a voz institucional da Metta e o mesmo ângulo, mas adeque a cadência "
        "e a densidade ao leitor de LinkedIn (mais texto corrido, menos fragmentação, "
        "registro de profissional sênior). Entregue a peça completa adaptada em texto "
        "corrido.\n\n"
        "=== PEÇA ORIGINAL (Instagram) ===\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        f"Objetivo: {brief.objective}\nCTA: {brief.cta}"
    )


def _enum_value(field: Any) -> Any:
    """Enum members mixed in with str print as 'Brand.METTA' in f-strings on
    this Python version (__format__ falls back to Enum's, not str's) — always
    read .value explicitly before interpolating brand/copy_type/platform/axis."""
    return field.value if isinstance(field, Enum) else field


def _render_brief(brief: Brief) -> str:
    lines = [
        f"Marca: {_enum_value(brief.brand)}",
        f"Tipo de copy: {_enum_value(brief.copy_type)}",
        f"Objetivo: {brief.objective}",
        f"ICP: {brief.icp}",
        f"Ângulo escolhido: {brief.angle_choice}",
        f"Eixo emocional: {_enum_value(brief.emotional_axis)}",
        f"CTA: {brief.cta}",
        f"Plataforma: {_enum_value(brief.platform)}",
    ]
    type_specific = getattr(brief, "type_specific", None)
    if type_specific:
        for key, value in type_specific.items():
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


# --- Response parsing --------------------------------------------------------

_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "hook": {"type": "string"},
        "corpo": {"type": "string"},
        "cta": {"type": "string"},
        "hook_variations": {
            # Sem minItems aqui: a API da Anthropic rejeita output_config.format.schema
            # com minItems/maxItems fora de {0, 1} ("minItems values other than 0 or 1
            # are not supported"). O "no minimo 3" e reforcado pelo prompt (linha do
            # _build_structural_prompt) e cobrado de novo no checklist do _judge.
            "type": "array",
            "items": {"type": "string"},
        },
        "content_pillar": {"type": "string"},
        "target_icp": {"type": "string"},
    },
    "required": [
        "hook",
        "corpo",
        "cta",
        "hook_variations",
        "content_pillar",
        "target_icp",
    ],
    "additionalProperties": False,
}

_ANGLES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "angles": {
            # Sem minItems/maxItems pelo mesmo motivo do hook_variations acima -- a
            # API rejeita o schema inteiro se qualquer array tiver esses valores fora
            # de {0, 1}. O "exatamente 3" fica só no texto do prompt (_build_angles_prompt).
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": ["A", "B", "C"]},
                    "abordagem": {"type": "string"},
                    "justificativa": {"type": "string"},
                },
                "required": ["label", "abordagem", "justificativa"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["angles"],
    "additionalProperties": False,
}

_JUDGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "feedback": {"type": "string"},
        "piece": _DRAFT_SCHEMA,
    },
    "required": ["approved", "feedback", "piece"],
    "additionalProperties": False,
}


def _text_of(response: anthropic.types.Message, stage: str = "?") -> str:
    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        # Acontece quando thinking consome o max_tokens inteiro e nao sobra
        # espaco pra resposta final -- StopIteration puro nao dizia isso.
        # `stage` identifica qual chamada falhou (draft_structural/judge/
        # linkedin_adaptation/propose_angles) -- as quatro chamam _text_of
        # e o erro sozinho nao dizia qual delas foi.
        block_types = [block.type for block in response.content]
        raise RuntimeError(
            f"[{stage}] Resposta sem bloco de texto (blocos recebidos: {block_types}, "
            f"stop_reason: {getattr(response, 'stop_reason', '?')})."
        )
    return text_blocks[0]


def _sanitize_json_text(text: str) -> str:
    """Às vezes o modelo devolve newline/tab CRU dentro de um valor string em
    vez do escape \\n/\\t que o JSON exige -- json.loads quebra com
    "Unterminated string starting at: ..." nesse caso (reproduzido em
    produção em propose_angles). Escapa esses caracteres de controle SÓ
    quando estão dentro de uma string (rastreando aspas não-escapadas),
    sem tocar no JSON estrutural em volta -- depois do json.loads, o \\n
    escapado decodifica de volta pro caractere real, então nada se perde."""
    out: list[str] = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\":
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch == "\n":
            out.append("\\n")
        elif in_string and ch == "\r":
            out.append("\\r")
        elif in_string and ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


def _extract_json(response: anthropic.types.Message, stage: str = "?") -> dict[str, Any]:
    text = _text_of(response, stage=stage)
    # Mesmo padrão defensivo do validator.py: extrai só entre a primeira "{" e
    # a ultima "}" -- protege contra prosa antes/depois do JSON. Nao protege
    # contra truncamento de verdade (json.loads ainda quebra nesse caso, e
    # deve quebrar -- o max_tokens e' quem previne isso, ver propose_angles).
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
    except ValueError as exc:
        raise ValueError(
            f"[{stage}] Resposta sem par '{{'/'}}' completo (provavel truncamento ou "
            f"ausencia de JSON) -- stop_reason: {getattr(response, 'stop_reason', '?')}, "
            f"texto completo recebido: {text!r}"
        ) from exc
    return json.loads(_sanitize_json_text(text[start:end]))
