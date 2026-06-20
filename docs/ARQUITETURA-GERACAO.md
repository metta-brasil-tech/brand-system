# Arquitetura — Geração de Criativos (brand-system)

Guia técnico do pipeline de geração de anúncios. Lê-se em 5 min e evita
redescobrir tudo do zero.

## Visão geral do fluxo

```
wizard (embed/criar.html)  →  POST /api/generate
  → 01 briefing-parser   (PULADO no modo wizard — copy vem do usuário)
  → 02 style-selector    (PULADO quando model_id é forçado pelo wizard)
  → 03 blueprint         (source/ad-blueprints/<marca>/<ID>.md = FONTE DE VERDADE)
  → 04 image-prompt + image-gen  (skill 04 escreve prompt → OpenAI gpt-image-2)
  → render HTML          (api/_blueprint_render.py + _engine.css)
  → 06 QA                (api/_qa.py — gate mecânico)
  → 07 vision-qa         (api/_vision_qa.py — peça isolada: ilustra a copy? mutila?)
  → 08 crítico           (api/_critic.py — same-designer test contra referência do banco)
```

> O **vision-qa** + **crítico** rodam num loop que regenera a imagem (até
> `VISION_QA_MAX`) injetando o feedback acionável no brief da próxima tentativa.
> Detalhes e o mapa de insights portados do plugin-metta-ads em
> `docs/INSIGHTS-PLUGIN-METTA-ADS.md`.

## Componentes-chave

| Arquivo | Papel |
|---|---|
| `source/ad-blueprints/<marca>/<ID>.md` | **Fonte de verdade** de cada estilo: `archetype`, `image.required/treatment/prompt_ref`, `params`. Quando há blueprint, o YAML é ignorado. |
| `api/_blueprint_render.py` | Renderer. `_markup()` (Metta) e `_markup_tiago()` mapeiam `archetype` → HTML. |
| `source/ad-blueprints/_engine.css` | Motor de CSS, escopado por `data-arch` e `data-marca`. |
| `api/_art_director.py` | Direção de arte. **Despacha por marca** (`_SYSTEM_METTA` vs `_SYSTEM_TIAGO`). |
| `engine/brand-knowledge/image-prompts/<marca>/_base*.md` + `style-*.md` | Templates de prompt de imagem (carregados pela skill 04). `engine/` é **submódulo git** (`ad-generator`). |
| `api/_qa.py` | Validador estático (archetype, headline, body de tweet, overflow). |
| `api/_vision_qa.py` | Checagem por visão da peça **isolada**: relevância copy↔imagem + integridade do layout. |
| `api/_critic.py` | Crítico **comparativo**: escolhe referência do banco (`applications-index.json`) e roda o *same-designer test* + anti-slop + texto-inventado. Gated por `CRITIC_COMPARE`. |
| `api/_evaluator.py` | **Juiz final**: nota holística 0-10 por dimensão (relevância/marca/hierarquia/acabamento) + veredito SHIP/REVISAR/DESCARTAR + ajustes + `image_fixable`. Consolida vision-qa + critic como guardrail (defeito objetivo limita o veredito). Roda sob demanda — ver `render_out/_avaliar_criativos.py`. |
| `api/_autogen.py` | **Loop de auto-melhoria** (`generate_until_approved`): gera → avalia (juiz final) → se não-SHIP e `image_fixable`, regera injetando os ajustes como direção visual de prioridade máxima → reavalia, até SHIP ou `max_attempts`. Guarda a melhor tentativa. Demo: `render_out/_autogen_demo.py`. |
| `content/direcao-arte/anti-slop.md` | Checklist anti-slop (16 itens) usado pelo crítico. |
| `scripts/validate_styles.py` | Guard de regressão do chain inteiro. Rode antes de publicar. |

## DNA por marca

**Metta** (B2B gestão de vendas): editorial cinema, dark moody, autoridade. Amarelo
`#FFBE18`. Fonte display Zalando Sans Expanded.

**Tiago Alves** (marca pessoal) — **trabalha em DOIS registros** (o `style-*.md` do
archetype decide qual):
- **Registro lo-fi/documental**: foto crua de celular, luz natural, colorida —
  `photo-raw`, `story-*`, `twitter`.
- **Registro cinema/surreal**: B&W cinemático + amarelo seletivo `#FFCC00`, colagem
  surreal, noir — `editorial-hero/dark/card`, `dark-surreal`.

> ⚠️ O `_base-tiago.md` **não** pode banir globalmente "dark cinema" ou "surreal" —
> isso briga com o registro 2. Restrições de registro vivem no `style-*.md` do archetype.

## O rosto do Tiago (limitação importante)

`gpt-image-2` é **texto→imagem**: NÃO reproduz uma pessoa real com fidelidade. Os 3
archetypes que mostram o rosto (`tiago-photo-raw`, `tiago-editorial-cta`,
`tiago-story-hero`) têm `image.prefer_upload: true` — o ideal é o usuário **subir uma
foto real recortada** do Tiago. Sem upload, o pipeline gera um fallback que apenas
*parece* com ele (descrição em `_TIAGO_LIKENESS` no art director) e emite o
diagnóstico `04-AVISO`. Os 69 ads reais da Metta já usam foto real recortada — esse é
o padrão correto (`archetype_foto: tiago-conselheiro`).

## Catálogo (referência viva)

`data/applications-index.json` — 109 peças canônicas (73 ads). Campo `archetype_foto`
= taxonomia validada de foto (executivo-em-decisao, tiago-conselheiro, etc.), ensinada
ao art director em `image-prompts/metta/_base.md`.

> Nota: alguns `archetype_foto` estão **mal rotulados** no dado (ad de executivo
> genérico marcado como `tiago-conselheiro`). É qualidade de dado, não código.

## Modelo LLM (custo)

A skill 04 roda via LiteLLM. Default = **`claude-sonnet-4-6`** (`engine/adapters/llm.py`)
— Sonnet basta pra escrever prompt de imagem (~40% mais barato que Opus). Override por
env `LLM_MODEL_CLAUDE` na Vercel. Geração de imagem = `IMAGE_GEN_PROVIDER` (gpt-image-2).

## Antes de publicar

```bash
python3 scripts/validate_styles.py   # chain dos 33 estilos; exit !=0 = quebrou algo
```

## Deploy (submódulo!)

`engine/` é submódulo. Mudanças lá: commit DENTRO de `engine/`, push, depois
commit do ponteiro no repo principal + push. A Vercel auto-deploya do `main`.
