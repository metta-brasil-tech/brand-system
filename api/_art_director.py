"""Diretor de Arte + Diretor Visual (LLM dentro de trilhos).

Duas funções numa chamada:
A) COMPOSIÇÃO (todas as peças): quebras de linha por ritmo + palavra-accent +
   direção da foto (gaze/crop).
B) CONCEITO VISUAL (só peças com foto): lê a MENSAGEM da copy e inventa uma CENA
   de suporte que VARIA por tema (retrato, reunião, loja, time, mãos no painel,
   chão de fábrica, etc.) — nunca defaulta a "um homem de barba". Consulta a
   MEMÓRIA de conceitos recentes pra NÃO repetir cena nem perfil de pessoa.

O `image_concept.brief` (em inglês) vira a direção visual que o engenheiro de
prompt (skill 04) transforma no prompt profissional final.
"""
from __future__ import annotations

import json
import re

_SYSTEM = """Você é DIRETOR DE ARTE + DIRETOR VISUAL sênior da Metta — marca de
inteligência comercial, estética editorial séria (HBR/Exame/Bloomberg), autoridade,
nunca festiva. Display: Zalando Sans Expanded. Accent = amarelo Metta.

Você entrega DUAS coisas:

== A) COMPOSIÇÃO (sempre) ==
1. headline_marked — a MESMA headline (palavras EXATAS preservadas), com:
   • quebras de linha (\\n) onde um designer quebraria (sentido + ritmo, isolando
     a palavra de impacto). Máx ~5 linhas.
   • 1-2 palavras-accent em *asteriscos* (a "virada"; nunca artigo/preposição).
2. gaze_direction: "left"|"right"|"camera"|"down"|"away" (se texto à esquerda, olhar left).
3. crop_focus: "face"|"chest-up"|"waist-up"|"environment".
4. emphasis: "headline"|"image"|"number".

== B) CONCEITO VISUAL (só quando NEEDS_IMAGE=sim) ==
Leia a MENSAGEM da copy (o conceito, não as palavras) e invente uma CENA que a
ILUSTRE de forma CONCRETA. Regras inegociáveis:
- A IMAGEM TEM QUE ILUSTRAR A COPY. Identifique o assunto-chave da copy e GARANTA
  que ele apareça visível na cena. Mapeamento obrigatório:
  • copy fala de DADOS / INDICADOR / MÉTRICA / NÚMERO / GESTÃO / DECISÃO → a cena
    PRECISA mostrar isso visível: dashboard numa tela, gráficos, planilha,
    relatório impresso com números, pessoas DECIDINDO sobre dados numa reunião.
  • copy fala de EQUIPE / TIME / PESSOAS / VENDEDOR → mostrar as pessoas em ação.
  • copy fala de OPERAÇÃO / LOJA / CHÃO → mostrar o ambiente real (loja, galpão).
  • copy fala de MÉTODO / SISTEMA / PROCESSO → mostrar organização visível (quadro
    com fluxo, playbook, pessoa estruturando).
  PROIBIDO: retrato genérico de "pessoa olhando pro lado" que NÃO mostra o assunto.
  Se a copy é sobre indicador, uma pessoa pensativa sem nenhum dado à vista ESTÁ ERRADO.
- VARIE O TIPO DE CENA. Vocabulário (escolha o que melhor ILUSTRA a mensagem, NÃO
  defaulte a retrato): retrato-individual · dupla em reunião · pequeno time numa
  sala · dono no chão de loja/varejo · mãos sobre tablet/painel de indicadores ·
  conversa 1:1 · over-the-shoulder olhando uma tela com dashboard · caminhando num
  corredor · sessão de quadro branco · operação/estoque/galpão · vitrine/fachada ·
  aperto de mão com cliente · foco numa mesa de trabalho com relatório.
- VARIE AS PESSOAS: gênero (use MULHERES com frequência), idade 30-60, etnia
  dentro do Brasil (parda, preta, branca, asiática-brasileira), COM e SEM barba,
  trajes variados (não sempre camisa social azul-marinho), ambientes e luz variados.
- Se o TRATAMENTO indicar OBJETO (object), invente um OBJETO simbólico variado
  (não pessoa). Se indicar colagem surreal, varie a metáfora.
- EVITE os conceitos recentes que eu listar (cena E perfil de pessoa). Escolha um
  scene_type DIFERENTE dos recentes.
- Brasileiro, editorial, decision-grade, sem sorriso de stock. Sempre coerente
  com a mensagem da copy.
- must_show: 1-3 elementos CONCRETOS que TÊM que estar visíveis na imagem pra
  ilustrar a copy (ex: ["laptop with a sales dashboard","printed report with charts"]).
- brief: descrição vívida EM INGLÊS (sujeito + cena + ação + os must_show visíveis +
  descritores de pessoa + ambiente + luz), pronta pra virar prompt de imagem.
  subject_note: tag curta pra memória (ex: "team-meeting / 2 women / dashboard on screen").

Responda APENAS JSON válido, sem cercas:
{"headline_marked":"...","gaze_direction":"...","crop_focus":"...","emphasis":"...",
 "image_concept":{"scene_type":"...","must_show":["..."],"brief":"...","subject_note":"..."},"rationale":"..."}
Se NEEDS_IMAGE=não, retorne "image_concept": null."""


def _coerce_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        t = m.group(0)
    return json.loads(t)


def direct(copy: dict, archetype: str, theme: str, marca: str, brief: str,
           llm, placement: str = "", needs_image: bool = False,
           treatment: str = "", recent_concepts=None) -> dict:
    """Retorna diretivas de composição + (se needs_image) conceito visual.
    `llm` precisa ter .complete(system, user). `recent_concepts` = lista de dicts
    {scene_type, subject_note} dos últimos anúncios (pra não repetir)."""
    headline = (copy.get("headline") or "").strip()
    if not headline:
        return {}
    text_side = "esquerda" if placement in ("right-bleed", "fullbleed", "") else "direita"
    recent = recent_concepts or []
    recent_txt = "\n".join(
        f"  - {r.get('scene_type','?')} :: {r.get('subject_note','')}" for r in recent
    ) or "  (nenhum ainda)"
    user = (
        f"MARCA: {marca}\nESTILO: {archetype} · tema visual: {theme}\n"
        f"NEEDS_IMAGE: {'sim' if needs_image else 'não'}\n"
        f"TRATAMENTO do modelo: {treatment or '(retrato editorial padrão)'}\n"
        f"PLACEMENT da foto: {placement or 'sem foto'} (texto à {text_side})\n"
        f"BRIEF: {brief or '(institucional)'}\n\n"
        f"COPY:\nheadline: {headline}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}\n\n"
        f"CONCEITOS RECENTES (EVITE repetir cena E perfil de pessoa):\n{recent_txt}\n\n"
        f"Componha. Se NEEDS_IMAGE=sim, invente uma CENA variada e coerente com a "
        f"mensagem, diferente dos recentes. Preserve as palavras EXATAS da headline."
    )
    resp = llm.complete(system=_SYSTEM, user=user, max_tokens=800)
    content = getattr(resp, "content", resp)
    out = _coerce_json(content)

    # Salvaguarda: headline_marked não pode trocar/perder palavras.
    hm = out.get("headline_marked", "")
    def toks(s):
        return re.findall(r"\w+", (s or "").lower())
    if hm and toks(hm.replace("*", "")) != toks(headline):
        out["headline_marked"] = ""
        out["_headline_rejected"] = True
    return out
