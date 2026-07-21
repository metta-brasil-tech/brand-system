"""Diretor de Arte + Diretor Visual (LLM dentro de trilhos).

Duas funções numa chamada:
A) COMPOSIÇÃO (todas as peças): quebras de linha por ritmo + palavra-accent +
   direção da foto (gaze/crop).
B) CONCEITO VISUAL (só peças com foto): lê a MENSAGEM da copy e inventa uma CENA
   de suporte que VARIA por tema — nunca defaulta a "um homem de barba". Consulta a
   MEMÓRIA de conceitos recentes pra NÃO repetir cena nem perfil de pessoa.

O `image_concept.brief` (em inglês) vira a direção visual que o engenheiro de
prompt (skill 04) transforma no prompt profissional final.

== AWARENESS DE MARCA ==
Cada marca tem DNA visual próprio e o art director NÃO pode tratar as duas igual:

- METTA: editorial documental sério (HBR/Bloomberg), full-color natural, amarelo
  Metta cirúrgico, cena de gestão/dados/time. System prompt `_SYSTEM_METTA`.

- TIAGO: personal brand cinematográfica — B&W com amarelo seletivo (#FFCC00), grão
  analógico 35mm, profundidade rasa, 21 archetypes fotográficos (surreal editorial,
  cinema noir, lo-fi contemplativo, etc.). Cada estilo Tiago tem um archetype com
  tratamento próprio (ver `TIAGO_ARCHETYPE_PROFILES`). System prompt `_SYSTEM_TIAGO`.

A função `direct()` despacha pro system prompt certo via `marca`. Pros archetypes
Tiago, ela injeta o PERFIL fotográfico do archetype (DNA documentado em
`content/direcao-arte/principios.md` + blueprints `source/ad-blueprints/tiago/`),
com FALLBACK que continua sendo DNA Tiago (B&W cinemático), nunca Metta.
"""
from __future__ import annotations

import json
import re

# Modos de falha técnicos do gpt-image-2 (válidos pras DUAS marcas) — portado do
# metta-image-models.md do plugin-metta-ads. Anexado a TODO negative_prompt
# (caminho determinístico, primário via skill 04, e regeneração da vision-qa).
NEG_MODEL_FAILS = (
    "no text in image, no gibberish letters, no watermark, no logos, no signage, "
    "no deformed hands, no extra fingers, no distorted face, no fused bodies, "
    "no extra limbs, no rendered UI screen, no readable numbers"
)

# ===========================================================================
# SYSTEM PROMPT — METTA (inalterado: marca madura, lógica que já funciona)
# ===========================================================================
_SYSTEM_METTA = """Você é DIRETOR DE ARTE + DIRETOR VISUAL sênior da Metta — marca de
inteligência comercial, estética editorial séria (HBR/Exame/Bloomberg), autoridade,
nunca festiva. Display: Zalando Sans Expanded. Accent = amarelo Metta.

Você entrega DUAS coisas:

== A) COMPOSIÇÃO (sempre) ==
1. headline_marked — a MESMA headline (palavras EXATAS preservadas), com:
   • quebras de linha (\\n) onde um designer quebraria (sentido + ritmo, isolando
     a palavra de impacto). Máx ~5 linhas.
   • accent em *asteriscos* na "virada": pode ser 1 palavra OU uma FRASE CURTA de
     2-4 palavras (o banco real pinta trechos inteiros: *R$ 300 mil*, *processo
     comercial*, *bater meta 3 meses*). Marque o NÚCLEO da mensagem, nunca
     artigo/preposição solta. 1 accent só — não pinte a headline inteira.
2. gaze_direction: "left"|"right"|"camera"|"down"|"away" (se texto à esquerda, olhar left).
3. crop_focus: "face"|"chest-up"|"waist-up"|"environment".
4. emphasis: "headline"|"image"|"number".
5. text_anchor: "top"|"bottom" — o bloco de texto vai pra zona VAZIA da cena que
   você inventou. Sujeito/objeto ocupa a metade de BAIXO (ex: objeto sobre a mesa)
   → text_anchor="top". Sujeito ocupa o TOPO (rosto/busto em pé) → "bottom".
   O brief da cena DEVE deixar essa zona limpa (fundo suave, vazio, sem elementos).
   CRÍTICO — zona vazia ≠ zona dos props: a metade reservada pro texto NUNCA pode
   conter os elementos do conceito (must_show). Se o conceito vive no chão/primeiro
   plano (objeto, pódio, mesa, props), a zona vazia vai pro TOPO (céu/parede lisa);
   se o conceito é aéreo, o vazio vai embaixo. NUNCA declare "vazio" a metade onde
   os props precisam aparecer — a IA obedece o "vazio" e APAGA os props (bug real
   observado: '5 pódios' sumiram porque a metade de baixo foi pedida vazia).
6. panel: "none"|"plain"|"white"|"dark" — a CAIXA DE TEXTO. Duas famílias:
   CAIXA COM FUNDO (card colorido — mais legível, agrupa muito texto):
   • "white" → título + DESCRIÇÃO/subtítulo + (prova) + CTA. É o PADRÃO da maioria
     das peças informativas do banco (card branco "Mentoria Metta..." + botão). Na
     dúvida entre white e dark, ESCOLHA WHITE.
   • "dark" → APENAS quando a foto é clara/estourada e um card claro sumiria, ou
     quando o mood pede peso/cinema. NÃO é o default — use com parcimônia.
   NÃO escolha "dark" por segurança em toda peça: VARIE conforme a peça pede
   (a maioria é white; head_out no padrão CRM).
   NUNCA use um card/caixa AMARELA atrás do texto (fora do layout estrutural
   fixo YELLOW-BLOCO) — feedback direto da Sofia: nunca ficou bom em nenhuma
   peça testada. Se a cena pede destaque forte, use "white" ou *accent* em
   asteriscos na própria headline, não uma caixa colorida.
   CAIXA SEM FUNDO:
   • "plain" → texto agrupado sobre a foto SEM card, só com sombra (headline forte
     em zona vazia com pouca informação; visual mais limpo/cinema com hierarquia).
   • "none" → texto livre no gradiente (legado; headline curtíssima só).
   REGRAS DURAS:
   - A caixa fica na ZONA VAZIA (a mesma do text_anchor) e NUNCA cobre o assunto
     (rosto, recorte, objeto). Descreva a cena deixando essa metade limpa.
   - Se a peça tem título + descrição/subtítulo, PREFIRA caixa (white) —
     texto demais solto sobre a foto é o que separa a arte amadora da real.
   - Headline longa NÃO é problema: a fonte encolhe sozinha pra caber na caixa.
7. head_out: true|false — padrão CRM/2-zonas. true = a HEADLINE fica SOBRE a foto
   (topo, sem card) e o card (white) embaixo leva só SUBTÍTULO + prova + CTA.
   Use quando a headline é uma pergunta/afirmação de impacto que quer respirar na
   imagem e o apoio é denso. Só vale com panel de fundo (white/dark).
8. proof: "" ou PROVA SOCIAL. Dois formatos (o «…» é PLACEHOLDER de formato —
   NUNCA copie os números do exemplo; use SÓ números que aparecem literalmente
   no CONHECIMENTO/COPY fornecidos):
   • LINHA (canto inferior): "«MÉTRICA» · «MÉTRICA»". Use quando o card está no
     topo (text_anchor="top"), pra não colidir.
   • CHIP emoldurado (no fluxo do texto): "«valor» | «legenda»". Vira uma caixinha
     com borda. Use quando há um número forte JÁ PRESENTE no material.
   REGRA DURA: proof só existe se houver um número REAL vindo do conhecimento ou
   da própria copy. NÃO invente, estime ou reaproveite números de exemplo (ex.:
   faturamento, nº de empresas, %). Na dúvida, deixe "". Prova inventada é pior
   que prova nenhuma.

== B) CONCEITO VISUAL (só quando NEEDS_IMAGE=sim) ==
Leia a MENSAGEM da copy (o conceito, não as palavras) e invente uma CENA que a
ILUSTRE de forma CONCRETA.

LINGUAGENS VISUAIS DO BANCO REAL (estudo dna-visual-banco-real.md — escolha UMA,
a que melhor serve a mensagem; o tom da marca é LEVE, espirituoso e confiante,
humor absurdo levado a sério — NÃO sombrio-corporativo):
  • FOTO-CONCEITO CÔMICA: conceito absurdo fotografado sério (homem pegando fogo ao
    telefone, mesa em chamas, pilha impossível de papel). Ideal pra dor/rotina/caos.
    Prefira UM elemento-surpresa fotografável; evite "clonado 5×"/"6 braços"/contagens
    (a IA erra a contagem e apaga as cópias — o conceito morre).
  • COLAGEM VINTAGE P&B: recorte halftone de foto antiga, escala surreal lúdica
    (mão gigante soltando um lead, retrato desconstruído). Ideal pra conceito/método.
  • HUMOR POR OBJETO: um objeto fotorrealista como piada seca (chupeta gigante na
    mesa executiva = "operação implora por babá"). Ideal pra metáfora de 1 palavra.
  • FINE-ART SURREAL: foto artística granulada, figura minúscula em cenário vasto
    (homenzinho no barco de dinheiro). Ideal pra reflexão/pergunta.
  • DOCUMENTAL DE DETALHE: mãos/mesas/telas sem rosto (mão assinando + laptop com
    CRM). Ideal pra prova/processo/dados.

Regras inegociáveis:
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
- Brasileiro, editorial, decision-grade. Sorriso genuíno e humor são BEM-VINDOS
  (o banco real é leve e bem-humorado); proibido só o sorriso-de-stock vazio que
  não serve à cena. Sempre coerente com a mensagem da copy.
- FIDELIDADE DE RENDER (o gerador de imagem SIMPLIFICA): arranjos com CONTAGEM ou
  REPETIÇÃO ("5 pódios", "6 braços", "homem clonado", multidão, "N idênticos") a IA
  reduz ao elemento mais comum e APAGA o resto — o conceito morre. Regra: o elemento-
  assinatura do conceito é UM, fotografável, e é o SUJEITO em foco (não detalhe de
  fundo). Se a ideia depende de contar/repetir, troque por metáfora de UM objeto
  (mesa pegando fogo > 5 pódios vazios; uma chupeta gigante na mesa > 5 clones).
- must_show: 1-3 elementos CONCRETOS que TÊM que estar visíveis na imagem pra
  ilustrar a copy (ex: ["laptop with a sales dashboard","printed report with charts"]).
- brief: descrição vívida EM INGLÊS (sujeito + cena + ação + os must_show visíveis +
  descritores de pessoa + ambiente + luz), pronta pra virar prompt de imagem.
  subject_note: tag curta pra memória (ex: "team-meeting / 2 women / dashboard on screen").

Responda APENAS JSON válido, sem cercas:
{"headline_marked":"...","gaze_direction":"...","crop_focus":"...","emphasis":"...",
 "text_anchor":"top|bottom","panel":"none|plain|white|dark","head_out":false,"proof":"",
 "image_concept":{"scene_type":"...","must_show":["..."],"brief":"...","subject_note":"..."},"rationale":"..."}
Se NEEDS_IMAGE=não, retorne "image_concept": null."""


# ===========================================================================
# DNA VISUAL TIAGO — base compartilhada por TODOS os archetypes Tiago.
# Resumo executivo do `content/direcao-arte/principios.md` (21 archetypes Tiago)
# + `_base-tiago.md`. É o FALLBACK seguro: se um archetype não tem perfil
# específico, esta base ainda garante B&W cinemático com amarelo seletivo —
# NUNCA cai num fallback Metta/genérico.
# ===========================================================================
_TIAGO_DNA = (
    "DNA VISUAL TIAGO (inegociável em TODA imagem desta marca):\n"
    "- B&W de alto contraste com UM amarelo seletivo (#FFCC00) sobrevivendo no P&B "
    "  — só o amarelo tem cor, todo o resto é monocromático. O amarelo é cirúrgico "
    "  (um objeto, um detalhe, uma área pintada), nunca decorativo nem disperso.\n"
    "- Estética cinematográfica: câmera 35mm/85mm, profundidade de campo RASA, "
    "  grão analógico de filme, iluminação controlada (não flash, não luz chapada).\n"
    "- Tiago Alves é homem brasileiro ~40 anos: palestrante/coach. Quando ele aparece: "
    "  gesto de fala, silhueta, close-up editorial, nunca pose de stock sorrindo.\n"
    "- Mood: autoridade técnica calma, reflexão, peso editorial — cinema, não corporativo.\n"
    "- PROIBIDO: full-color natural, teal-orange grade turístico, sorriso de stock, "
    "  olhar direto à câmera em pose publicitária, HDR, paleta arco-íris, clichê.\n"
)


# ---------------------------------------------------------------------------
# Perfis fotográficos por archetype Tiago.
# Cada perfil tem:
#   scene      — vocabulário de CENA típico daquele archetype (o que aparece)
#   treatment  — tratamento visual canônico (espelha image.treatment do blueprint)
#   needs_image— se o archetype usa foto de verdade (False = tipográfico/mock)
#   subject_is_tiago — se o sujeito É o Tiago (vs objeto/ambiente/metáfora)
# Fonte: source/ad-blueprints/tiago/*.md (image.treatment) +
#        engine/brand-knowledge/image-prompts/tiago/style-*.md (templates).
# ---------------------------------------------------------------------------
TIAGO_ARCHETYPE_PROFILES: dict[str, dict] = {
    # --- Editoriais (feed) -------------------------------------------------
    "tiago-editorial-hero": {
        "scene": "surreal editorial magazine collage as a visual metaphor for the copy "
                 "(headless figure with smoke/yellow lightning instead of a head, a "
                 "subject with body parts painted flat yellow, an object-metaphor like a "
                 "fish with a strapped-on shark fin or a T-Rex skeleton)",
        "treatment": "1960s-70s Brazilian premium magazine collage, high-contrast B&W with "
                     "selective FLAT yellow paint (#FFCC00) over key parts, grainy print "
                     "texture, neutral light-gray background, hard cut-out edges, Fujifilm "
                     "GFX magazine-editorial look",
        "needs_image": True,
        "subject_is_tiago": False,
    },
    "tiago-editorial-dark": {
        "scene": "cinematic noir close-up (a single human eye, a silhouette in a dark "
                 "corridor, hands in shadow) carrying the emotional weight of the line",
        "treatment": "cinema noir B&W with subtle warm undertone (#2E1F0F tint), heavy "
                     "vignette, dramatic side light, extremely shallow DoF, sharp on the "
                     "anchor point (iris/contour), rest in deep shadow, darkening overlay "
                     "60% at the bottom for text. Sony A7R 85mm f/1.4",
        "needs_image": True,
        "subject_is_tiago": False,
    },
    "tiago-editorial-card": {
        "scene": "graphic ornament OR a dark editorial photo that reinforces the statistic "
                 "on the data card (a charged context image, not a literal chart)",
        "treatment": "high-contrast B&W with selective yellow accent, editorial-collage or "
                     "dark cinema mood, grainy print texture, neutral background, magazine "
                     "art direction",
        "needs_image": True,
        "subject_is_tiago": False,
    },
    "tiago-editorial-cta": {
        "scene": "real photo of Tiago speaking/gesturing on stage, framed from the waist up, "
                 "mid-gesture, blurred or plain dark background",
        "treatment": "B&W with subtle warm tone and a selective yellow accent, cinematic 85mm "
                     "shallow DoF, film grain, no stock smile, no direct eye contact",
        "needs_image": True,
        "subject_is_tiago": True,
    },
    "tiago-typo": {
        # Tipográfico puro — foto PROIBIDA no blueprint.
        "scene": "",
        "treatment": "nenhum — formato tipográfico puro, foto proibida",
        "needs_image": False,
        "subject_is_tiago": False,
    },
    "tiago-dark-surreal": {
        "scene": "a single surreal/dreamlike symbolic subject isolated (person wearing an "
                 "animal mask, a cat before an oval mirror, a toppled chair, a draped marble "
                 "bust) — the image IS the whole slide, no text",
        "treatment": "noir-poster surreal B&W (or near-zero saturation with cool blue-grey "
                     "undertone), hard single-source sculpting light, deep cast shadows, "
                     "subject centered with deep BLACK negative space around ~60% of frame, "
                     "medium-format film grain, dreamlike-quiet mood",
        "needs_image": True,
        "subject_is_tiago": False,
    },
    "tiago-photo-raw": {
        "scene": "candid lo-fi phone selfie / snapshot of Tiago in a personal context "
                 "(training/jiu-jitsu, travel, family, community, a meal, a daily ritual)",
        "treatment": "raw unedited phone photo — natural existing light, no studio, no color "
                     "grade, no retouch, slight motion blur acceptable, looks shot on iPhone, "
                     "authentic mid-moment (NOT the B&W cinema treatment — this archetype is "
                     "deliberately raw real-life)",
        "needs_image": True,
        "subject_is_tiago": True,
        "lofi": True,
    },
    "tiago-notes": {
        # Mock iPhone Notes — sem foto.
        "scene": "",
        "treatment": "nenhum — formato é puro mock textual sem foto",
        "needs_image": False,
        "subject_is_tiago": False,
    },
    # --- Stories (9:16) ----------------------------------------------------
    "tiago-story-hero": {
        "scene": "documentary lo-fi vertical portrait of Tiago in an authentic context "
                 "(speaking on stage, at home, traveling, reading) as the real subject",
        "treatment": "documentary phone-style 9:16, natural light (window/real stage/cozy "
                     "night), very light desaturation, no cinema grade, no posed smile, "
                     "casual off-center framing, scrim safe-area where the headline sits",
        "needs_image": True,
        "subject_is_tiago": True,
        "lofi": True,
    },
    "tiago-story-yellow": {
        "scene": "lo-fi documentary snapshot of a real ENVIRONMENT that anchors the theme "
                 "(meeting room with a city view, empty gym, cozy night desk, urban "
                 "landscape) — NO person as the main subject",
        "treatment": "observational lo-fi 9:16, natural light, light desaturation, central "
                     "vertical area kept visually quiet so the yellow overlay block sits clean",
        "needs_image": True,
        "subject_is_tiago": False,
        "lofi": True,
    },
    "tiago-story-minimal": {
        "scene": "quiet contemplative still-life / landscape (night desk with a lit lamp, "
                 "city view at dusk, an open book, a room in natural light) — no direct face",
        "treatment": "contemplative slow-life 9:16, soft natural diffuse light, low "
                     "saturation (near-B&W keeping one subtle warm accent), film grain, "
                     "whispered intimate mood, no high contrast",
        "needs_image": True,
        "subject_is_tiago": False,
        "lofi": True,
    },
    # --- Twitter mock (feed) ----------------------------------------------
    "tiago-twitter": {
        "scene": "documentary contextual object/scene that grounds the tweet (a badge, a "
                 "storefront, a screen/dashboard, a human detail like hands) — prefer object "
                 "over person, never a centered face in an ad pose",
        "treatment": "observational documentary snapshot, natural diffuse light, neutral "
                     "palette with one accent, slight imperfection, sits inside a rounded "
                     "card (no full bleed), no dramatic editorial mood",
        "needs_image": False,  # image é opcional (variant cover) no blueprint
        "subject_is_tiago": False,
    },
}


# Aparência REAL do Tiago Alves (refs em engine/brand-knowledge/exemplars/tiago/).
# Injetada quando subject_is_tiago=True pra a geração ao menos PARECER com ele,
# não um estranho aleatório. ATENÇÃO: gpt-image-2 é texto→imagem e NÃO reproduz
# pessoa real com fidelidade — o caminho de produção pra esses archetypes é usar
# FOTO REAL (upload/biblioteca), não geração. Esta descrição é só fallback.
_TIAGO_LIKENESS = (
    "the subject is Tiago Alves: a light-skinned Brazilian man in his early-to-mid 40s, "
    "short dark brown hair greying at the temples, rectangular dark glasses, short greying "
    "stubble, warm confident expression, typically a charcoal-grey blazer over a plain black "
    "t-shirt"
)


def get_tiago_profile(archetype: str) -> dict:
    """Perfil fotográfico do archetype Tiago, com FALLBACK seguro no DNA Tiago.

    Se o archetype não está mapeado, devolve um perfil genérico que AINDA é Tiago
    (B&W cinemático com amarelo seletivo) — nunca um fallback Metta/genérico.
    """
    prof = TIAGO_ARCHETYPE_PROFILES.get((archetype or "").lower())
    if prof:
        return prof
    return {
        "scene": "an editorial scene or symbolic subject that illustrates the copy, "
                 "cinematically framed",
        "treatment": "high-contrast cinematic B&W with one selective yellow accent (#FFCC00), "
                     "35mm shallow depth of field, analog film grain, controlled editorial light",
        "needs_image": True,
        "subject_is_tiago": False,
    }


# ===========================================================================
# SYSTEM PROMPT — TIAGO (construído com o DNA + perfil do archetype).
# ===========================================================================
def _build_system_tiago(archetype: str, profile: dict) -> str:
    return (
        "Você é DIRETOR DE ARTE + DIRETOR VISUAL sênior da marca pessoal de TIAGO ALVES "
        "(palestrante/coach de gestão de vendas). Estética CINEMATOGRÁFICA, autoral, "
        "B&W com amarelo seletivo. NÃO é corporativo Metta — é cinema editorial.\n\n"
        f"{_TIAGO_DNA}\n"
        f"ARCHETYPE FOTOGRÁFICO ATUAL: {archetype}\n"
        f"CENA TÍPICA DESTE ARCHETYPE: {profile.get('scene') or '(formato sem foto)'}\n"
        f"TRATAMENTO VISUAL DESTE ARCHETYPE (siga à risca): {profile.get('treatment')}\n\n"
        "Você entrega DUAS coisas:\n\n"
        "== A) COMPOSIÇÃO (sempre) ==\n"
        "1. headline_marked — a MESMA headline (palavras EXATAS preservadas), com:\n"
        "   • quebras de linha (\\n) onde um designer quebraria (sentido + ritmo, isolando\n"
        "     a palavra de impacto). Máx ~5 linhas.\n"
        "   • 1-2 palavras-accent em *asteriscos* (a 'virada'; nunca artigo/preposição).\n"
        "   VOZ TIAGO: direta, sem clichê, sem motivacional barato, autoridade técnica calma.\n"
        "2. gaze_direction: 'left'|'right'|'camera'|'down'|'away' (se texto à esquerda, olhar left).\n"
        "3. crop_focus: 'face'|'chest-up'|'waist-up'|'environment'.\n"
        "4. emphasis: 'headline'|'image'|'number'.\n\n"
        "== B) CONCEITO VISUAL (só quando NEEDS_IMAGE=sim) ==\n"
        "Invente uma CENA específica e variada COERENTE com a mensagem da copy E com a "
        "CENA TÍPICA do archetype acima. Regras:\n"
        "- O TRATAMENTO acima é OBRIGATÓRIO — toda imagem nasce B&W cinemático com amarelo "
        "  seletivo (exceto archetypes 'raw'/'story' que pedem lo-fi natural, conforme o "
        "  tratamento informado). Nunca full-color corporativo, nunca clichê de stock.\n"
        "- Se o archetype tem Tiago como sujeito, descreva-o gesticulando/em silhueta/"
        "  close-up — nunca pose publicitária sorrindo pra câmera.\n"
        "- Se o archetype é surreal/metáfora, invente uma metáfora visual forte e VARIE "
        "  dela em relação aos conceitos recentes.\n"
        "- must_show: 1-3 elementos CONCRETOS visíveis (ex: ['single human eye in deep "
        "  shadow','one yellow accent on the iris']).\n"
        "- brief: descrição vívida EM INGLÊS pronta pra virar prompt de imagem — DEVE "
        "  incorporar o tratamento (B&W, selective yellow, grain, 35mm/85mm, profundidade "
        "  rasa, iluminação cinematográfica) explicitamente.\n"
        "  subject_note: tag curta pra memória (ex: 'noir eye close-up / yellow iris accent').\n\n"
        "Responda APENAS JSON válido, sem cercas:\n"
        '{"headline_marked":"...","gaze_direction":"...","crop_focus":"...","emphasis":"...",'
        '"image_concept":{"scene_type":"...","must_show":["..."],"brief":"...","subject_note":"..."},"rationale":"..."}\n'
        'Se NEEDS_IMAGE=não, retorne "image_concept": null.'
    )


def _coerce_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        t = m.group(0)
    return json.loads(t)


def _is_tiago(marca: str, archetype: str) -> bool:
    return (marca or "").strip().lower() == "tiago" or (archetype or "").lower().startswith("tiago")


def _complete_with_vision(system: str, user: str, images: list, model: str | None = None) -> str:
    """Chama a visão DIRETO (OpenAI), mostrando as imagens de referência do banco
    pro diretor DECIDIR OLHANDO — a fase 'olhar antes de decidir' do Alisson. Fica
    em api/ (não usa o adaptador só-texto do submódulo). Devolve o content cru."""
    import base64 as _b64
    from openai import OpenAI
    parts = [{"type": "text", "text": user}]
    for img in images[:4]:
        b = _b64.b64encode(img).decode("ascii")
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:image/webp;base64,{b}"}})
    resp = OpenAI().chat.completions.create(
        model=model or os.getenv("ART_DIRECTOR_MODEL", "gpt-4.1"),
        max_tokens=800,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": parts}])
    return resp.choices[0].message.content or ""


def direct(copy: dict, archetype: str, theme: str, marca: str, brief: str,
           llm, placement: str = "", needs_image: bool = False,
           treatment: str = "", recent_concepts=None,
           knowledge: str = "", avatar: str = "", ref_images=None) -> dict:
    """Retorna diretivas de composição + (se needs_image) conceito visual.

    `llm` precisa ter .complete(system, user). `recent_concepts` = lista de dicts
    {scene_type, subject_note} dos últimos anúncios (pra não repetir).

    `knowledge` = bloco de `_knowledge.build_block()` (ICP + voz + metodologia +
    depoimento que casam com a copy). `avatar` = bloco do AVATAR ALVO (ICP)
    escolhido. Ambos ancoram a persona/cena no que a marca SABE, em vez da
    heurística pobre "use uma pessoa genérica". Opcionais (default "") pra manter
    compatibilidade com chamadas antigas.

    Despacha por MARCA: Metta usa `_SYSTEM_METTA` (lógica madura inalterada);
    Tiago usa um system prompt construído com o DNA Tiago + o perfil fotográfico
    do archetype (`TIAGO_ARCHETYPE_PROFILES`), com fallback que segue sendo Tiago.
    """
    headline = (copy.get("headline") or "").strip()
    if not headline:
        return {}

    tiago = _is_tiago(marca, archetype)
    if tiago:
        profile = get_tiago_profile(archetype)
        system = _build_system_tiago(archetype, profile)
        # Tiago não usa o esquema de placement Metta; o tratamento por archetype
        # já carrega a composição (bleed, scrim, overlay, negative space).
        treatment_eff = treatment or profile.get("treatment", "")
        text_side = "(composição definida pelo archetype Tiago)"
    else:
        system = _SYSTEM_METTA
        treatment_eff = treatment
        text_side = "esquerda" if placement in ("right-bleed", "fullbleed", "") else "direita"

    recent = recent_concepts or []
    recent_txt = "\n".join(
        f"  - {r.get('scene_type','?')} :: {r.get('subject_note','')}" for r in recent
    ) or "  (nenhum ainda)"
    # Ancoragem no ICP/voz/método (passo 2): o pensador deixa de decidir persona/cena
    # no escuro. Só entra se houver conteúdo — degrada gracioso quando vazio.
    knowledge_blk = f"\n{knowledge.strip()}\n" if (knowledge or "").strip() else ""
    avatar_blk = f"\n{avatar.strip()}\n" if (avatar or "").strip() else ""
    grounding = (
        "\nANCORE a persona e a cena no CONHECIMENTO DA MARCA e no AVATAR ALVO acima "
        "(quem é o decisor, em que momento, em que ambiente, com que tom) — NÃO "
        "recaia em pessoa/cena genérica.\n"
        + (
            "REGRA DE PRECEDÊNCIA: quando o AVATAR ALVO define um ambiente concreto, "
            "ele VENCE o mapeamento genérico de cena — ponha o decisor NO ambiente "
            "do avatar (ex.: o dono no chão da farmácia/loja olhando indicadores num "
            "tablet), NÃO numa sala de reunião default. Respeite o gênero do avatar.\n"
            if avatar_blk else ""
        )
        if (knowledge_blk or avatar_blk) else ""
    )
    user = (
        f"MARCA: {marca}\nESTILO: {archetype} · tema visual: {theme}\n"
        f"NEEDS_IMAGE: {'sim' if needs_image else 'não'}\n"
        f"TRATAMENTO do modelo: {treatment_eff or '(retrato editorial padrão)'}\n"
        f"PLACEMENT da foto: {placement or 'sem foto'} (texto à {text_side})\n"
        f"BRIEF: {brief or '(institucional)'}\n"
        f"{knowledge_blk}{avatar_blk}{grounding}\n"
        f"COPY:\nheadline: {headline}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}\n\n"
        f"CONCEITOS RECENTES (EVITE repetir cena E perfil de pessoa):\n{recent_txt}\n\n"
        f"Componha. Se NEEDS_IMAGE=sim, invente uma CENA variada e coerente com a "
        f"mensagem, diferente dos recentes. Preserve as palavras EXATAS da headline."
    )
    # OLHAR ANTES DE DECIDIR (F1 do Alisson): se vierem referências reais do banco,
    # o diretor DECIDE VENDO as imagens — não só lendo texto. Fallback pro adaptador
    # só-texto quando não há referência ou a visão falha.
    if ref_images:
        try:
            vis_user = (user + "\n\nVEJA as imagens de referência REAIS do banco Metta "
                        "acima (a linguagem visual, a caixa de texto, a composição). "
                        "Componha ESTA peça no MESMO espírito visual que você está vendo.")
            content = _complete_with_vision(system, vis_user, ref_images)
        except Exception:
            resp = llm.complete(system=system, user=user, max_tokens=800)
            content = getattr(resp, "content", resp)
    else:
        resp = llm.complete(system=system, user=user, max_tokens=800)
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


# ===========================================================================
# Geração determinística de prompt de imagem (sem LLM).
# Útil pra: testes, fast-path, e quando não há briefing visual do user. Garante
# que CADA archetype Tiago produza um prompt FIEL ao seu DNA fotográfico mesmo
# sem chamar o LLM — base do critério "cada archetype tem prompt específico".
# ===========================================================================
class ArtDirector:
    """Fachada do diretor de arte. Expõe geração determinística de prompt de
    imagem por archetype (Tiago e Metta), além de reusar `direct()` pro caminho LLM.
    """

    # Anti-padrões base por marca (acumulam no negative_prompt).
    _NEG_TIAGO = (
        "no full-color natural photo, no teal-orange grade, no stock smile, "
        "no direct eye contact ad pose, no HDR, no rainbow palette, no cliché, "
        "no AI render artifacts, " + NEG_MODEL_FAILS
    )
    _NEG_METTA = (
        "no smiling stock pose, no high-five, no lightbulb idea cliché, "
        "no fisheye distortion, no HDR, no inflated saturation, " + NEG_MODEL_FAILS
    )

    def generate_image_prompt(self, archetype: str, model_id: str = "",
                              marca: str = "", subject_hint: str = "") -> dict:
        """Monta um prompt de imagem determinístico, fiel ao DNA do archetype.

        Retorna {"prompt", "negative_prompt", "archetype", "marca", "needs_image"}.
        `subject_hint` (opcional) injeta o sujeito/cena específico do briefing;
        sem ele, usa a CENA típica do archetype.
        """
        marca = (marca or ("tiago" if str(archetype).lower().startswith("tiago") else "metta"))
        if _is_tiago(marca, archetype):
            prof = get_tiago_profile(archetype)
            if not prof.get("needs_image"):
                return {
                    "prompt": "",
                    "negative_prompt": "",
                    "archetype": archetype,
                    "marca": "tiago",
                    "needs_image": False,
                    "note": "archetype tipográfico/mock — sem foto por design",
                }
            scene = (subject_hint or "").strip() or prof["scene"]
            # Se a cena É o Tiago, descreve o rosto real dele (fallback — produção
            # deve usar foto real). Sem isso, a IA inventa um estranho qualquer.
            if prof.get("subject_is_tiago"):
                scene = f"{scene}. {_TIAGO_LIKENESS}"
            if prof.get("lofi"):
                # Archetypes documentais/crus: NÃO levam acabamento cinema-editorial,
                # senão o sufixo contradiz o tratamento ("shot on iPhone", "no cinema grade").
                finish = (
                    "Shot on a phone, natural existing light, authentic lo-fi snapshot, "
                    "subtle real-life imperfection, no studio lighting, no color grade, "
                    "no HDR, intentional framing, no text in image."
                )
            else:
                finish = (
                    "Cinematic 35mm/85mm look, shallow depth of field, analog film grain, "
                    "controlled editorial lighting, editorial 4K, intentional framing, "
                    "no text in image."
                )
            prompt = f"{scene}. Treatment: {prof['treatment']}. {finish}".strip()
            return {
                "prompt": prompt,
                "negative_prompt": self._NEG_TIAGO,
                "archetype": archetype,
                "marca": "tiago",
                "needs_image": True,
            }

        # Metta: prompt genérico editorial documental (a riqueza real vem do LLM).
        scene = (subject_hint or "").strip() or (
            "editorial documentary business scene illustrating the message"
        )
        prompt = (
            f"{scene}. Editorial documentary photography in the Metta style: natural "
            "lateral light, mid contrast, subtle film grain, charcoal/oak/cream palette "
            "with a single surgical Metta-yellow (#FFBE18) accent, 35-50mm, f/2.8-f/4, "
            "no posed corporate-stock energy, no HDR."
        )
        return {
            "prompt": prompt,
            "negative_prompt": self._NEG_METTA,
            "archetype": archetype,
            "marca": "metta",
            "needs_image": True,
        }
