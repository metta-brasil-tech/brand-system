# Pipeline de criação de ad — v3 (blueprint-driven)

Mapa do fluxo REAL após a reforma de 2026-05-29. Documenta o que está vivo,
o que morreu, e a direção de fonte única.

## Fluxo vivo (modo wizard — user escolhe modelo + escreve copy)

```
briefing + model_id + copy + (preset/direção visual)
  → [01 briefing-parser]  PULADO em wizard (marca vem do blueprint; nunca aborta)
  → [02 style-selector]   PULADO em wizard (model_id forçado)
  → gate de imagem        lê image.required do BLUEPRINT (sobrepõe YAML)
  → placement do slot      derivado do BLUEPRINT (archetype+params.photo)
  → [04 image-prompt-engineer]  DEFAULT roda o LLM: _base (identidade) +
                            preset (tratamento) + COMPOSIÇÃO-POR-SLOT + direção do user
  → gpt-image-1
  → [render blueprint]     HTML adaptativo (auto-fit, Zalando, tokens)
  → [QA]                   _qa.py — status/issues/warnings no retorno
```

## Fluxo livre (sem modelo escolhido — raro)
Igual, mas roda 01-briefing-parser (infere marca/intent) + 02-style-selector
(escolhe modelo). O selector pode alucinar ID → `_resolve_catalog()` ancora ao
catálogo real por tokens. Briefing pode pedir esclarecimento (`needs_input`).

## O que MORREU no v3 (não chamar)
| Skill/arquivo | Substituído por |
|---|---|
| `skills/03-layout-composer.md` (576 ln) | render blueprint (`_blueprint_render.py`) |
| `skills/05-assembler.md` + `api/_layouts.py.deprecated` | render HTML + html2canvas |
| Tamanho/tipografia/spacing dentro dos YAMLs | `_engine.css` + blueprints |

## Fontes de verdade (estado atual e alvo)
| Info | HOJE lê de | ALVO (fase P5) |
|---|---|---|
| Render (layout/type/cor) | **blueprint** ✅ | blueprint |
| Gate de imagem (required) | **blueprint** ✅ (sobrepõe YAML) | blueprint |
| Placement do slot | **blueprint** ✅ | blueprint |
| Tratamento de imagem | blueprint `image.treatment` + preset + `_base.md` | blueprint + `_base` |
| Seleção de estilo | YAML + vector (Qdrant) | **blueprint front-matter** (pendente) |
| Prompt de imagem por estilo | `image-prompts/style-X.md` | derivar do blueprint (pendente) |
| DNA / quando-brilha | `banco-ads-figma.md` + YAML | blueprint (banco vira índice) |

## v3.1 — Substrato de render + Diretor de Arte
- **Diretor de Arte** (`api/_art_director.py`, default ON): antes da imagem e do render,
  decide quebras de linha + palavra-accent da headline (preservando palavras) e a
  direção da foto (gaze/crop, que entra no prompt de imagem). Eleva de "template
  preenchido" pra "composição".
- **Export server-side** — substitui html2canvas (infiel/mole/não-determinístico):
  - **Produção (Vercel):** `api/render.js` (Node + `@sparticuz/chromium` + `puppeteer-core`)
    renderiza o HTML em Chromium real @2× DPI, screenshot do `.ad-canvas`, reduz pra
    1080×H com `sharp` (supersampling). O front (`criar.html`) faz POST em `/api/render`
    no download; fallback pro html2canvas se falhar.
  - **Local/worker:** `api/_render_png.py` (Playwright @2× + fallback Chrome subprocess),
    usado via `render_png=True` no `generate.py` (retorna `png_data_uri`).
- **Deploy:** `npm install` no build do Vercel puxa chromium/puppeteer. Função
  `api/render.js` configurada com memory 1024 + maxDuration 30 no `vercel.json`.

## Flags de ambiente
- `IMAGE_PROMPT_FASTPATH=1` — liga o atalho que pula o engenheiro de prompt
  (só sob pressão de timeout). Default 0 = engenheiro sempre roda.
- `IMAGE_QUALITY` low|medium|high · `IMAGE_GEN_PROVIDER` gpt-image-1|nano-banana-2
- `IMAGE_MAX_ATTEMPTS` (default 1)

## Pendências estruturais (P4/P5)
1. Selector: passar a lista real de IDs do blueprint no prompt do skill 02 +
   validar a saída (hoje só o guard resolve depois).
2. Consolidar YAML → blueprint (selector e image-prompt lendo 1 fonte); aposentar
   YAMLs e `style-X.md` redundantes; `banco-ads-figma.md` vira índice + filosofia.
