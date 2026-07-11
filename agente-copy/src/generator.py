"""Two-stage copy generation for Agente Copy (Metta Brasil).

Pipeline mirrors the documented architecture (Documento_Mestre_Projeto_v2 /
Agente_Copy_Criacao_v5.1, "Arquitetura técnica"), with one deviation from
those docs: both stages run on Sonnet now, not just the first.

  1. Sonnet drafts the structural piece (hook + corpo + CTA) respecting the
     copy-type-specific flow from SKILLMETTACOPY.md.
  2. Sonnet judges tone / angle / voice calibration against tom-de-voz-metta.md
     and the skill's QA checklist, and may send the draft back for revision.

The Anthropic knowledge base is plain markdown read fresh each cycle — no RAG,
no embeddings, per the docs. Model ID: Sonnet 5 for both structural work and
copy judgment (decisão de custo, jul/2026 -- os docs registram "Opus para
julgamento de copy" como decisão do Tiago; ver validator.py e os 3 documentos
mestres para o histórico dessa decisão antes de reverter). Never Haiku.

Depends on the `anthropic` SDK (add `anthropic` to requirements.txt — owned by
another agent). The caller supplies a constructed `anthropic.Anthropic` client;
this module never instantiates one or reads keys.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import anthropic

# Structural drafting and copy judgment both run on Sonnet. Do not use Haiku
# (documented decision).
SONNET_MODEL = "claude-sonnet-5"

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
            length: str = ""
            include_case: bool = True
            type_specific: dict[str, Any] = field(default_factory=dict)


try:
    from src.icp_catalog import icp_knowledge_file  # type: ignore[import-not-found]
except ImportError:
    from icp_catalog import icp_knowledge_file  # type: ignore[import-not-found]

try:
    from src import retrieval  # type: ignore[import-not-found]
except ImportError:
    import retrieval  # type: ignore[import-not-found]


# Seleção de trechos (RAG lexical, ver src/retrieval.py). Desligável sem
# mudança de código: COPY_AGENT_RAG=0 nas env vars da Vercel volta ao
# comportamento antigo (base completa em toda chamada). Lido a cada chamada
# de propósito, pra teste conseguir alternar sem recarregar o módulo.
def _rag_enabled() -> bool:
    return os.environ.get("COPY_AGENT_RAG", "1") != "0"


# Voz e regras de escrita nunca são fatiadas: o modelo escreve A PARTIR
# delas, não as consulta. A seleção vale só pros documentos de referência.
_RAG_KEEP_FULL = frozenset({"tom-de-voz-metta.md", "SKILLMETTACOPY.md"})


def _brief_query(brief: Brief) -> list[str]:
    """Termos de busca extraídos do briefing, pra pontuar os trechos.

    _enum_value (definido adiante neste módulo) extrai o valor real do enum;
    str() cru viraria "CopyType.POST_UNICO" e sujaria a busca com o nome da
    classe (pego na primeira auditoria com inspect_rag_selection.py)."""
    type_specific = getattr(brief, "type_specific", None) or {}
    return retrieval.build_query(
        brief.objective,
        brief.angle_choice,
        str(brief.icp),
        str(_enum_value(getattr(brief, "copy_type", "")) or ""),
        str(_enum_value(getattr(brief, "emotional_axis", "") or "") or ""),
        brief.cta,
        " ".join(str(v) for v in type_specific.values()),
    )


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
    # Legenda que acompanha a peça quando publicada -- distinta do `corpo`
    # pra tipos onde o corpo NÃO é o texto que vira legenda (reels: corpo é
    # o roteiro falado, descricao é o texto embaixo do vídeo). Pra tipos
    # onde corpo já É a legenda (post_unico, carrossel), o modelo repete/
    # resume o corpo aqui em vez de inventar um texto novo -- ver
    # _build_structural_prompt.
    descricao: str = ""
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

    def as_context(self, exclude: frozenset[str] = frozenset()) -> str:
        blocks = [
            f"<documento fonte=\"{name}\">\n{content}\n</documento>"
            for name, content in self._documents.items()
            if name not in exclude
        ]
        return "\n\n".join(blocks)

    def as_context_selected(
        self, query_terms: list[str], exclude: frozenset[str] = frozenset()
    ) -> str:
        """Como as_context, mas com seleção de trechos nos documentos de
        referência (voz e skill sempre inteiras -- ver _RAG_KEEP_FULL).
        Fallback embutido no retrieval: nada relevante ou erro -> documento
        completo, idêntico ao as_context."""
        full = {
            name: content
            for name, content in self._documents.items()
            if name not in exclude and name in _RAG_KEEP_FULL
        }
        pool = {
            name: content
            for name, content in self._documents.items()
            if name not in exclude and name not in _RAG_KEEP_FULL
        }
        selected = retrieval.select_pool(
            pool, query_terms, retrieval.POOL_BUDGET_CHARS
        )
        blocks = []
        for name in self._documents:  # preserva a ordem de carga documentada
            content = full.get(name) or selected.get(name)
            if content:
                blocks.append(
                    f"<documento fonte=\"{name}\">\n{content}\n</documento>"
                )
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

    def generate(self, brief: Brief, winners_benchmark: str = "") -> GenerationResult:
        """winners_benchmark: bloco de texto opcional com criativos que
        comprovadamente performaram (banco de vencedores, v5.1 seção 9) --
        entra no prompt estrutural como referência do que funciona com esse
        público. Vazio = comportamento idêntico ao de antes do banco existir.
        O caller (API do brand-system) é quem busca isso no storage; este
        módulo não conhece KV."""
        if brief.brand != "metta":
            raise NotImplementedError(
                f"Brand {brief.brand!r} is not supported yet. Full support "
                "requires tom-de-voz-tiago.md, which is not in the repo."
            )

        knowledge = self._knowledge_base(brief.brand)
        draft = self._draft_structural(brief, knowledge, winners_benchmark)

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
            hook=_remove_travessao(draft["hook"]),
            corpo=_remove_travessao(draft["corpo"]),
            cta=_remove_travessao(draft["cta"]),
            full_text=_remove_travessao(self._assemble(draft)),
            hook_variations=[_remove_travessao(h) for h in draft["hook_variations"]],
            content_pillar=draft["content_pillar"],
            target_icp=draft["target_icp"],
            platform=brief.platform,
            descricao=_remove_travessao(draft.get("descricao", "")),
            linkedin_adaptation=_remove_travessao(linkedin) if linkedin else linkedin,
            revision_notes=revision_notes,
        )

    def _knowledge_base(self, brand: Brand) -> KnowledgeBase:
        if brand not in self._knowledge_bases:
            self._knowledge_bases[brand] = KnowledgeBase(brand)
        return self._knowledge_bases[brand]

    def _draft_structural(
        self, brief: Brief, knowledge: KnowledgeBase, winners_benchmark: str = ""
    ) -> dict[str, Any]:
        response = self.client.messages.create(
            model=SONNET_MODEL,
            # Reproduzido em produção com stage="draft_structural": o modelo
            # gasta parte do orçamento num bloco de thinking (não pedido
            # explicitamente) antes de montar o JSON do schema, e 4000
            # estourava antes de sobrar espaço pro JSON final.
            max_tokens=16000,
            system=_build_system_prompt(brief.brand, brief.copy_type),
            messages=[{"role": "user", "content": _cached_content(_build_structural_prompt(brief, knowledge, winners_benchmark))}],
            output_config={"format": {"type": "json_schema", "schema": _DRAFT_SCHEMA}},
        )
        return _extract_json(response, stage="draft_structural")

    def _judge(
        self, brief: Brief, knowledge: KnowledgeBase, draft: dict[str, Any]
    ) -> dict[str, Any]:
        response = self.client.messages.create(
            model=SONNET_MODEL,
            # Opus -> Sonnet 5 (decisão de custo, jul/2026 -- pedido explícito
            # da Sofia após o pipeline estourar tokens; ver nota no docstring
            # do módulo). Era o último uso de Opus no agente de copy; as
            # outras 4 checagens de validator.py já tinham migrado antes.
            #
            # max_tokens=16000 (herdado do tempo em que este era Opus):
            # reproduzido ao vivo 3x: com thinking=adaptive + effort=high, a
            # resposta nunca saía do bloco de thinking pra escrever o JSON
            # final -- nem em 4000, nem 12000, nem 32000 (sempre
            # stop_reason=max_tokens, só bloco de thinking). Não era
            # orçamento pequeno, era incompatibilidade real entre thinking
            # estendido e saída forçada em json_schema -- tira o thinking e
            # o "effort: high" (que só se aplica com thinking) do julgamento.
            # Mesmo sem esses dois parâmetros, o modelo ainda gasta parte do
            # orçamento num bloco de thinking implícito antes do JSON (achado
            # em _draft_structural com o mesmo padrão de output_config) --
            # 16000 dá a mesma margem que resolveu lá. Mantido no valor alto
            # ao trocar pra Sonnet como precaução (mesma família de bug já
            # vista nas 4 chamadas de validator.py).
            max_tokens=16000,
            output_config={
                "format": {"type": "json_schema", "schema": _JUDGMENT_SCHEMA},
            },
            system=_build_system_prompt(brief.brand, brief.copy_type),
            messages=[{
                "role": "user",
                "content": _cached_content(_build_judgment_prompt(brief, knowledge, draft), marker="=== BRIEFING ==="),
            }],
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
        angles = _extract_json(response, stage="propose_angles")["angles"]
        return [
            {key: _remove_travessao(value) if isinstance(value, str) else value
             for key, value in angle.items()}
            for angle in angles
        ]

    def derive_winner_variations(
        self, brand: Brand, winner_text: str, performance_notes: str = ""
    ) -> dict[str, Any]:
        """Banco de vencedores (v5.1 seção 9): a partir de um criativo que
        comprovadamente performou, deriva as versões A, B e C mantendo os
        elementos responsáveis pela performance -- o modelo primeiro NOMEIA
        esses elementos (pra ficarem auditáveis na resposta) e só então varia
        o resto. Sonnet, seguindo a decisão de custo de jul/2026 que migrou
        todos os usos de Opus deste agente pra Sonnet 5 (ver docstring do
        módulo); reverter é trocar só o model abaixo."""
        if brand != "metta":
            raise NotImplementedError(
                f"Brand {brand!r} is not supported yet. Full support "
                "requires tom-de-voz-tiago.md, which is not in the repo."
            )
        if not winner_text.strip():
            raise ValueError("winner_text vazio: cole a copy do criativo vencedor.")
        knowledge = self._knowledge_base(brand)
        response = self.client.messages.create(
            model=SONNET_MODEL,
            # Mesma margem do _judge: o modelo gasta parte do orçamento num
            # bloco de thinking implícito antes do JSON do schema.
            max_tokens=16000,
            system=_build_system_prompt(brand, "criativos"),
            messages=[{
                "role": "user",
                "content": _cached_content(
                    _build_winner_variations_prompt(winner_text, performance_notes, knowledge),
                    marker="=== CRIATIVO VENCEDOR ===",
                ),
            }],
            output_config={
                "format": {"type": "json_schema", "schema": _WINNER_VARIATIONS_SCHEMA},
            },
        )
        data = _extract_json(response, stage="derive_winner_variations")
        data["variations"] = [
            {key: _remove_travessao(value) if isinstance(value, str) else value
             for key, value in variation.items()}
            for variation in data["variations"]
        ]
        return data

    @staticmethod
    def _assemble(draft: dict[str, Any]) -> str:
        return "\n\n".join(
            part for part in (draft["hook"], draft["corpo"], draft["cta"]) if part
        )


# --- Prompt construction -----------------------------------------------------


def _icp_context(icp_id: str, query_terms: list[str] | None = None) -> str:
    """Conteúdo do documento de ICP do segmento escolhido (v5.1 seção 14:
    "escreve embebido de ICP"). Vazio quando o id não veio do catálogo (ex.:
    testes com string livre) -- nesse caso o rótulo ainda aparece no
    briefing, só sem o documento completo.

    Com query_terms e RAG ligado, o documento é reduzido aos trechos mais
    relevantes ao briefing (o de mentoria tem 72 mil caracteres inteiro, e
    ia completo pro rascunho E pro julgamento). Fallback no retrieval:
    nada relevante ou erro -> documento completo."""
    filename = icp_knowledge_file(icp_id)
    if filename is None:
        return ""
    path = _REPO_ROOT / filename
    if not path.is_file():
        return ""
    content = path.read_text(encoding="utf-8")
    if query_terms is not None and _rag_enabled():
        content = retrieval.select_sections(
            filename, content, query_terms, retrieval.ICP_BUDGET_CHARS
        )
    return f'<documento fonte="{filename}">\n{content}\n</documento>'

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
        "CTA, é link na bio. Nunca use termos proprietários como hashtag. Tamanho "
        "real (mediana medida em 24 posts reais de @metta.brasil): ~127 palavras, "
        "~740 caracteres -- não escreva peça de landing page, é uma legenda de "
        "Instagram. Se usar case espelho, mencione em 1-2 frases (nome, resultado), "
        "não conte a história toda com múltiplos parágrafos. Protagonista é sempre "
        "o método/mecanismo, nunca a jornada emocional/identitária de quem lê -- "
        "isso é registro do Tiago pessoal, não da Metta institucional."
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
        "Roteiro (campo corpo): gancho → ciclo do gargalo → por que as outras "
        "falharam → mecanismo fazedoria → case espelho com nome e número. CTA final "
        "majoritariamente link na bio; alternativa é pergunta reflexiva sem link. "
        "A descrição (campo descricao) é o texto ESCRITO que acompanha o vídeo "
        "publicado -- diferente do roteiro falado, segue o padrão de post único "
        "(pode fechar só com hashtags, sem CTA)."
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
        "O texto precisa soar escrito por gente, não por IA. Proibido travessão "
        "(—) como pontuação: use vírgula, dois-pontos ou ponto final. Os documentos "
        "de referência abaixo usam travessão no texto DELES; não imite isso na "
        "peça. Evite também paralelismos artificiais em sequência ('não é X, é Y' "
        "repetido) e fechos de frase simétricos demais.\n\n"
        f"Formato desta peça: {_copy_type_guidance(copy_type)}"
    )


def _cached_content(prompt: str, marker: str = "=== BRIEFING DA PEÇA ===") -> list[dict[str, Any]]:
    """Quebra o prompt em (base de conhecimento cacheável) + (parte
    dinâmica do brief) e marca a primeira com cache_control -- a base de
    conhecimento (~174 mil caracteres) é a mesma em toda chamada de
    _draft_structural e, dentro de um mesmo generate(), em toda rodada do
    loop de _judge (até 2x com max_revisions=1); reenviar isso a preço
    cheio a cada chamada era o maior custo real medido em produção
    (1,88M tokens de entrada vs 84 mil de saída no dashboard). Cache
    "ephemeral" tem TTL de 5 min -- confortável pro tempo de um generate()
    inteiro rodar. Se o marcador não aparecer no texto (não deveria
    acontecer com os dois prompts que chamam isso), cai pra um único bloco
    sem cache -- funciona igual, só sem o desconto."""
    idx = prompt.find(marker)
    if idx == -1:
        return [{"type": "text", "text": prompt}]
    return [
        {"type": "text", "text": prompt[:idx], "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": prompt[idx:]},
    ]


# Arquivos que a peça não usa quando não vai trazer prova social (case com
# nome+número de provas.md, detalhe de oferta/preço de oferta.md) -- excluí-
# los do prompt corta ~40 mil caracteres (~10 mil tokens) de entrada sem
# perder nada que a peça conseguiria usar.
_CASE_SKIP: frozenset[str] = frozenset({"provas.md", "oferta.md"})


def _is_short_length(length: str) -> bool:
    """True se o tamanho-alvo pedido é pequeno demais pra caber case/oferta.

    Só confia em número quando o texto fala explicitamente de "caracteres"
    (os chips do formulário sempre incluem essa palavra) -- sem isso, um
    número solto é ambíguo demais ("2 parágrafos" não é 2 caracteres) e
    cairia num falso positivo perigoso (corta contexto de uma peça que na
    verdade não é curta). Sem essa palavra, cai pra palavra-chave
    ("curto", "chamariz") como sinal mais fraco.
    """
    if not length:
        return False
    lowered = length.lower()
    if "caracter" in lowered:
        numbers = [int(n) for n in re.findall(r"\d+", length)]
        if numbers:
            return max(numbers) <= 400
    return any(kw in lowered for kw in ("curto", "chamariz"))


def _should_skip_case(brief: Brief) -> bool:
    """Duas razões independentes pra não trazer prova social, e qualquer
    uma das duas basta: (1) o usuário desmarcou "incluir prova social"
    explicitamente (Brief.include_case=False) -- vale mesmo em peça longa;
    (2) o tamanho-alvo é curto demais pra caber case de qualquer jeito,
    mesmo com o controle explícito deixado ligado (é restrição física, não
    preferência) -- ver _is_short_length."""
    include_case = getattr(brief, "include_case", True)
    return (not include_case) or _is_short_length(getattr(brief, "length", ""))


def _build_structural_prompt(
    brief: Brief, knowledge: KnowledgeBase, winners_benchmark: str = ""
) -> str:
    query = _brief_query(brief) if _rag_enabled() else None
    icp_context = _icp_context(brief.icp, query_terms=query)
    icp_block = f"{icp_context}\n\n" if icp_context else ""
    skip_case = _should_skip_case(brief)
    skip = _CASE_SKIP if skip_case else frozenset()
    doc_list = "tom de voz, skill de copy, avatar, posicionamento, glossário"
    if not skip_case:
        doc_list = "tom de voz, skill de copy, avatar, posicionamento, oferta, provas, glossário"
    case_note = (
        "\n\nEsta peça NÃO recebeu os documentos de oferta/provas (usuário "
        "pediu sem prova social, ou o tamanho-alvo não cabe case de qualquer "
        "forma) -- não invente case/cliente/número aqui; foque em "
        "dor/contradição/mecanismo."
        if skip_case else ""
    )
    if query is not None:
        context = knowledge.as_context_selected(query, exclude=skip)
        selection_note = (
            "\n\nTom de voz e skill de copy estão completos; dos demais "
            "documentos você recebeu os trechos mais relevantes a este "
            "briefing (marcados como 'trechos selecionados'). Não presuma "
            "nada sobre o que ficou de fora deles."
        )
    else:
        context = knowledge.as_context(exclude=skip)
        selection_note = ""
    return (
        f"Use a base de conhecimento abaixo ({doc_list}"
        + (", documento de ICP do segmento" if icp_context else "")
        + ") para escrever a peça."
        + case_note + selection_note + "\n\n"
        f"{context}\n\n"
        f"{icp_block}"
        + (
            "=== CRIATIVOS VENCEDORES (benchmark de performance) ===\n"
            "Os criativos abaixo comprovadamente performaram com esse público "
            "(critério do marketing: leads qualificados / CTR). Use como "
            "referência do que funciona -- ângulo de entrada, formato de "
            "gancho, tipo de prova. NÃO copie frases: a peça nova precisa ser "
            "original.\n\n"
            f"{winners_benchmark}\n\n"
            if winners_benchmark.strip() else ""
        )
        + "=== BRIEFING DA PEÇA ===\n"
        f"{_render_brief(brief)}\n\n"
        "=== TAREFA ===\n"
        "Escreva a peça montada por partes, respeitando a estrutura do tipo de copy "
        "descrita no system prompt e no fluxo da SKILLMETTACOPY.md. Ative pelo menos "
        "duas dores conectadas do ciclo do gargalo e nomeie pelo menos uma "
        "contradição interna."
        + (
            ""
            if skip_case
            else " Traga um case espelho nominal do segmento quando possível."
        )
        + "\n\n"
        "Entregue: hook, corpo, CTA; no mínimo 3 variações de hook distintas; a "
        "indicação de pilar de conteúdo e o ICP-alvo; e a descrição/legenda que "
        "acompanha a peça quando publicada. Para reels, a descrição é um texto "
        "DIFERENTE do corpo (que é o roteiro falado no vídeo) -- a legenda escrita "
        "que fica embaixo do vídeo no post, seguindo o mesmo padrão de descrição de "
        "post único (pode fechar sem CTA, só com hashtags de nicho, postura de "
        "autoridade). Para os demais tipos, onde o corpo já É a legenda "
        "(post_unico, carrossel), repita ou resuma o corpo no campo descricao em "
        "vez de inventar um texto novo -- mas preserve os parágrafos com quebra de "
        "linha dupla (\\n\\n) entre eles, igual ao corpo. Uma legenda real de feed "
        "não sai como bloco único: tem respiro entre ideias. Nunca colapse os "
        "parágrafos numa massa de texto só, mesmo ao resumir.\n\n"
        "IMPORTANTE: o campo hook e o campo corpo são montados em sequência na "
        "peça final (hook, depois corpo, depois CTA) -- NUNCA repita o hook como "
        "primeira linha do corpo, isso duplica a frase de abertura quando a peça "
        "é montada. O corpo começa direto no desenvolvimento, sem repetir o "
        "hook.\n\n"
        "Responda no schema JSON pedido."
    )


def _build_judgment_prompt(
    brief: Brief, knowledge: KnowledgeBase, draft: dict[str, Any]
) -> str:
    skip_case = _should_skip_case(brief)
    case_item = (
        "" if skip_case else "case espelho nominal; "
    )
    case_skip_note = (
        "\n\nEsta peça foi pedida SEM prova social (usuário desmarcou, ou o "
        "tamanho-alvo não cabe case) -- NÃO reprove por falta de case/número/"
        "cliente nominal, isso foi intencional, não uma falha."
        if skip_case else ""
    )
    return (
        "Você é o revisor de rascunho do Agente Copy (julgamento interno de geração --"
        " NÃO é o segundo agente avaliador; esse roda depois, uma vez, sobre a peça já "
        "pronta). Julgue o rascunho abaixo contra o tom de "
        "voz institucional da Metta (tom-de-voz-metta.md) e o QA CHECKLIST da "
        "SKILLMETTACOPY.md. Você tem autoridade para REPROVAR e reescrever — não "
        "aprove por inércia."
        + case_skip_note + "\n\n"
        f"Rode o checklist item a item: 2+ dores conectadas do ciclo; linguagem emic; "
        f"{case_item}garantia contratual quando cabível; tom de empresário "
        "falando (não coach); nenhuma urgência artificial; números específicos; "
        "contradição interna nomeada; o empresário se reconheceria; nenhuma palavra "
        "da lista 'nunca use'. Rode também os 7 testes de validação institucional "
        "(categoria nova, protagonismo do método, prova nominal, vocabulário próprio "
        "aplicado, oscilação rigor/acessibilidade, combate ao sistema e não à pessoa, "
        "coerência tonal do CTA).\n\n"
        f"{knowledge.document('tom-de-voz-metta.md')}\n\n"
        f"{knowledge.document('SKILLMETTACOPY.md')}\n\n"
        f"{_icp_context(brief.icp, query_terms=_brief_query(brief) if _rag_enabled() else None)}\n\n"
        "=== BRIEFING ===\n"
        f"{_render_brief(brief)}\n\n"
        "=== RASCUNHO A AVALIAR ===\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        "Cheque também: o corpo NÃO pode repetir o hook como primeira linha (a "
        "peça final monta hook + corpo + CTA em sequência, então repetir duplica a "
        "abertura) -- reprove e corrija se isso acontecer. E nenhum campo pode "
        "conter travessão (—) como pontuação: é marca de texto de IA, proibido na "
        "peça publicada -- se encontrar, reescreva com vírgula, dois-pontos ou "
        "ponto final.\n\n"
        "Se qualquer item falhar, defina approved=false, explique o que falhou em "
        "feedback e devolva a peça reescrita e corrigida em 'piece'. Se passar em "
        "tudo, defina approved=true e devolva a peça (com ajustes finos se quiser). "
        "Preserve sempre as 3+ variações de hook, o pilar, o ICP-alvo e a descrição "
        "(campo descricao -- pra reels é a legenda escrita, diferente do roteiro "
        "falado no corpo; pros demais tipos pode repetir/resumir o corpo, mas "
        "SEMPRE com quebra de linha dupla entre parágrafos, nunca como bloco único)."
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


def _build_winner_variations_prompt(
    winner_text: str, performance_notes: str, knowledge: KnowledgeBase
) -> str:
    return (
        "Um criativo da Metta comprovadamente performou (critério do marketing: "
        "mais leads qualificados / melhor CTR). Sua tarefa tem duas partes, nesta "
        "ordem:\n"
        "1. IDENTIFIQUE os elementos responsáveis pela performance -- o que nessa "
        "copy fez ela funcionar (o gancho? a dor específica? a prova? o formato do "
        "CTA? a cadência?). Liste cada elemento de forma concreta e auditável.\n"
        "2. DERIVE exatamente 3 variações -- A, B e C -- que MANTÊM esses elementos "
        "intactos e variam o restante (outra abertura, outra prova/case do banco, "
        "outro fecho, outra forma de entrar na mesma dor). Variação não é paráfrase: "
        "cada versão precisa ser uma peça nova que preserve o que performa. Pra cada "
        "variação, diga em uma linha o que mudou em relação à original.\n\n"
        f"{knowledge.as_context()}\n\n"
        "=== CRIATIVO VENCEDOR ===\n"
        f"{winner_text}\n\n"
        + (f"=== O QUE O MARKETING SABE SOBRE A PERFORMANCE ===\n{performance_notes}\n\n"
           if performance_notes.strip() else "")
        + "=== TAREFA ===\n"
        "Responda no schema JSON pedido: performance_elements (lista) e as "
        "variações A, B e C (hook, corpo, cta, o_que_mudou)."
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
    length = getattr(brief, "length", "")
    if length:
        lines.append(
            f"Tamanho-alvo do texto: {length} -- MIRE nessa faixa (aproximada, "
            "não conte caractere a caractere); prevalece sobre o tamanho típico "
            "do formato. Se for curto, corte case/exemplos longos; se for longo, "
            "desenvolva mais."
        )
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
        # Legenda que acompanha a peça quando publicada. Pra reels, é texto
        # DIFERENTE do `corpo` (que é o roteiro falado) -- ver instrução em
        # _build_structural_prompt. Pra tipos onde o corpo já é a legenda
        # (post_unico, carrossel), o modelo pode repetir/resumir o corpo
        # aqui em vez de inventar um segundo texto.
        "descricao": {"type": "string"},
    },
    "required": [
        "hook",
        "corpo",
        "cta",
        "hook_variations",
        "content_pillar",
        "target_icp",
        "descricao",
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

_WINNER_VARIATIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        # O que fez a peça performar, nomeado ANTES de variar -- fica na
        # resposta pra auditoria humana (a pessoa vê o que foi preservado).
        "performance_elements": {"type": "array", "items": {"type": "string"}},
        "variations": {
            # Sem minItems/maxItems (mesma limitação da API dos outros arrays
            # deste arquivo); o "exatamente 3" fica no texto do prompt.
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": ["A", "B", "C"]},
                    "hook": {"type": "string"},
                    "corpo": {"type": "string"},
                    "cta": {"type": "string"},
                    "o_que_mudou": {"type": "string"},
                },
                "required": ["label", "hook", "corpo", "cta", "o_que_mudou"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["performance_elements", "variations"],
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


def _remove_travessao(text: str) -> str:
    """Remove travessão (em-dash) da peça final, trocando por vírgula.

    Pedido explícito do cliente: travessão é marca registrada de texto de IA
    e não pode aparecer na copy publicada. A regra também está nos prompts
    (system + julgamento), mas o modelo imita o próprio material de
    referência (a skill tem dezenas de travessões no texto dela), então esta
    é a garantia determinística de que nenhum passa. Só mexe no em-dash (—);
    meia-risca (–) fica intacta porque faixas numéricas legítimas usam ela
    ("R$ 200k–600k", "90–180 caracteres")."""
    if "—" not in text:
        return text
    # Pausa no meio da frase vira vírgula; sobras coladas em pontuação
    # existente são normalizadas depois.
    cleaned = re.sub(r"\s*—\s*", ", ", text)
    cleaned = re.sub(r",\s*,", ",", cleaned)
    cleaned = re.sub(r"([.!?:;])\s*,\s*", r"\1 ", cleaned)
    cleaned = re.sub(r"^,\s*", "", cleaned, flags=re.MULTILINE)
    return cleaned


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
