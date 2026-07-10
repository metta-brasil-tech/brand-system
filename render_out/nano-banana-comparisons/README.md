# Comparações Nano Banana — validação da Fase C

Gerado em 2026-07-10 durante a validação do pipeline `api/_nano_pipeline.py`
(branch `feat/nano-banana-hybrid`). Guardado aqui pra referência futura.

## `posts-reais-vs-simulados/`

Cada `sim-<id>.png` é o post `<id>` de `data/applications-index.json`
**simulado** pelo pipeline: post real → referência do Nano Banana Pro (herda
paleta/grão/tratamento) + copy real → `_blueprint_render` (motor de layout
real). Comparar com o post real em `assets/applications/ads/thumbs/<id>.webp`.

Lição validada aqui: a cena tem que **ilustrar o conceito** da copy, não pôr
um sujeito decorativo (`sim-ad-a-eu-quero-voce-fora.png` é a versão conceitual
— empresário saindo pela porta iluminada, não um retrato parado).

Ressalva conhecida: `sim-ad-news-card-risco-zero-varejo.png` saiu com o
sujeito cortado na faixa inferior — pendência de composição (corrigir via
guia de cena melhor ou o recompositor full-bleed de `backup/vision-first`).

## `carrossel-motores/`

Mesma cena panorâmica (transformação caos operacional → método → time)
gerada nos 3 motores testados, pra decidir o motor do carrossel:

- `nano-banana-pro.png` — `gemini-3-pro-image-preview`, ~20s. **Escolhido**:
  empata/ganha do gpt-image e cabe num timeout de request da Vercel.
- `nano-banana-flash.png` — `gemini-2.5-flash-image`, ~8s. Mais gráfico/rápido.
- `gpt-image.png` — `gpt-image-2` (OpenAI), ~148s. Ótimo mas não cabe numa
  request Vercel direta (precisaria job assíncrono).
