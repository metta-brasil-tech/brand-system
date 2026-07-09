# Plano — peça DUAL-FORMATO (feed 4:5 + story 9:16 numa geração só)

> Pedido da Sofia (2026-07-09): "um modelo que cria ambos os tamanhos".
> **Veredito de custo: é BARATO.** O que custa numa peça é LLM de copy/conceito
> (~1-2 chamadas) e a IMAGEM do gpt-image-2 (~$0,19). O render HTML→PNG é grátis.
> Dual-formato reusa copy + imagem e só renderiza 2×: **custo ≈ 1 peça + $0**.

## Como funciona (nada de gerar duas vezes)

1. Pipeline roda 1× até o render (briefing → copy → diretor de arte → imagem).
2. Render 2×: `_blueprint_render.render(..., format="feed")` e `format="story")`.
   O motor JÁ é adaptativo por formato (`.ad[data-format]` no `_engine.css`
   muda altura 1350↔1920; auto-fit do `_engine.js` reacomoda o texto).
3. Vision-QA/crítico rodam só no formato PRIMÁRIO (feed) — o secundário herda
   o veredito (mesma copy, mesma imagem). Zero custo extra de QA.

## O que precisa mudar (pequeno)

- **`api/generate.py`**: aceitar `formats: ["feed","story"]` (hoje `format` é
  string única). Loop de render no fim; resposta ganha `variants: [{format,
  html, png?}]`. Retrocompat: `format` singular segue funcionando.
- **`cli.py`**: flag `--formats feed,story` (hoje `--format`).
- **Wizard (`embed/criar.html`)**: card novo no passo de formato —
  **“Feed + Story (2 tamanhos)”** — manda `formats` no POST; a tela de
  resultado mostra os 2 previews com botão de download em cada.
- **Atenção story**: zona segura do topo (header do IG) já existe no engine
  (`.ad[data-format="story"] .brand-mark { top: 120px }`), mas blueprints
  `formato_nativo: [feed]` (ex: NEWS-CARD) podem compor mal em 9:16 — o card
  dual só habilita quando o estilo tem `formatos` incluindo os dois (o wizard
  já filtra estilos por formato hoje).

## Limite honesto

Nem todo estilo fica bom nos dois formatos (LOGO-WALL em story espicha a
grade). Fase 13 do PLANO-MESTRE (safe-zones) resolve isso direito; até lá o
dual-formato fica restrito aos estilos com `formatos: ['feed','ad-story']`
no wizard (já são 8 na Metta).

## Custo estimado por peça dual

| Item | Single | Dual |
|---|---|---|
| LLM copy/conceito | ~R$0,05-0,15 | igual (reusa) |
| gpt-image-2 | ~$0,19 | igual (reusa a MESMA imagem) |
| Render PNG | grátis | grátis ×2 |
| Vision-QA | ~R$0,05 | igual (só no primário) |

**Total dual ≈ total single.** O ganho é 2 entregáveis pelo preço de 1.
