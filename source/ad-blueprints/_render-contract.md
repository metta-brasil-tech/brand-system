# Render Contract — sistema blueprint-driven de ads Metta

Este doc rege como QUALQUER ad Metta é renderizado. Cada modelo tem um
`<id>.md` (blueprint) que declara seu `archetype` + `params`; o renderizador
(`api/_blueprint_render.py`) combina blueprint + copy + imagem usando o motor
(`_engine.css` + `_engine.js`) e **cria** uma peça adaptada à copy — não clona.

## Filosofia (não-negociável)
Alinhado a `design/banco-ads-figma.md`: **criar do zero adaptando à copy, nunca
clonar template e encaixar texto**. Layout é FLUXO (flex), headline tem auto-fit,
proporções respondem ao volume de texto. "Parecido com o modelo", não idêntico.

## Réguas DURAS (o motor garante)
- **Canvas:** story 1080×1920 · feed 1080×1350 · sqr 1080×1080. `overflow:hidden`.
- **Fonte display** (headline/tag/CTA): **Zalando Sans Expanded** (`--m-display`).
- **Fonte texto** (subhead/body): **Inter** (`--m-text`).
- **Tokens:** só `var(--m-*)`. Nunca hex hardcoded. Amarelo `--m-yellow` só em
  accent/CTA/símbolo; preto puro só em texto/dark surface.
- **Margens seguras:** `--pad-x` 80 · `--pad-y` 120.
- **CTA:** pill `border-radius:999px`, UPPERCASE.
- **Foto:** nunca recortar sujeito humano; editorial, dessaturada; sem stock genérico.

## Archetypes (vocabulário fechado)
| archetype | descrição | params relevantes |
|-----------|-----------|-------------------|
| `typo` | tipografia pura | theme, align, scale(normal\|giant), accent |
| `photo-side` | texto + foto bleed lateral | theme, photo(right-bleed\|left-bleed), block(none\|yellow) |
| `photo-full` | foto/ilustração fullbleed + overlay | theme, anchor(bottom\|top\|center), align |
| `photo-band` | faixa foto + faixa texto | photo(top\|bottom), theme |
| `object-center` | objeto central + headline | theme |
| `card-mock` | cartão de rede social (tweet) | (light fixo) |
| `logo-wall` | grade de logos + headline | theme |
| `framed` | moldura + conteúdo central | theme |
| `split` | metade mídia / metade texto | theme |

## Front-matter esperado em cada blueprint
```yaml
---
id: A-headline-foto-dark
marca: metta
archetype: photo-side
params: { theme: dark, photo: right-bleed, block: none, align: left, cta: yellow }
slots: [tag, headline, subhead, body, cta]
image: { required: true, treatment: "editorial dessaturada, sujeito íntegro" }
formato_nativo: [story, feed]
dna_ref: "design/banco-ads-figma.md#§4.1"
---
```
O corpo em prosa (intenção, quando brilha, anti-padrões, direção de copy) é pra
leitura humana e pro briefing de copy — o renderizador só lê o front-matter.

## Temas
- `dark` — bg night-10, texto branco, accent amarelo (default Metta institucional)
- `light` — bg night-95, texto night-10
- `yellow` — bg amarelo, texto night-10
- `paper` — bg escuro esverdeado (motivo carta/contrato)
