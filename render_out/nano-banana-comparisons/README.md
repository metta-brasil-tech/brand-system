# Comparações Nano Banana — validação da Fase C

Gerado em 2026-07-10 durante a validação do pipeline `api/_nano_pipeline.py`
(branch `feat/nano-banana-hybrid`). Guardado aqui pra referência futura.

## `posts-reais-vs-simulados/`

Cada `sim-<id>.png` é o post `<id>` de `data/applications-index.json`
**simulado** pelo pipeline: post real → referência do Nano Banana Pro (herda
paleta/grão/tratamento) + copy real → `_blueprint_render` (motor de layout
real). Comparar com o post real em `assets/applications/ads/thumbs/<id>.webp`.

Lição validada aqui (v2, todas as 6 peças revisadas com essa lógica): a cena
tem que **ilustrar o conceito** da copy, nunca um sujeito decorativo.

- `A-headline-foto-dark` ("eu quero você fora") → empresário saindo por uma
  porta iluminada, não um retrato parado.
- `YELLOW-SPLIT` ("a chave da liberdade não está no balcão") → o balcão vira
  literalmente uma jaula de madeira, porta iluminada ao fundo fora de alcance.
- `D-foto-fullbleed-overlay` ("engenharia reversa do vendedor") → diagrama
  técnico/blueprint saindo do vendedor como um raio-x do processo.
- `NEWS-CARD` (composição corrigida) → time inteiro visível, sem corte.
- `LIGHT-SURREAL` e `B-foto-top-headline-mixed` já eram conceituais desde a
  v1 (pedra esmagando saúde; dono-funcionário no próprio caixa).

## `carrossel-motores/`

Mesma cena panorâmica (transformação caos operacional → método → time)
gerada nos 3 motores testados, pra decidir o motor do carrossel:

- `nano-banana-pro.png` — `gemini-3-pro-image-preview`, ~20s. **Escolhido**:
  empata/ganha do gpt-image e cabe num timeout de request da Vercel.
- `nano-banana-flash.png` — `gemini-2.5-flash-image`, ~8s. Mais gráfico/rápido.
- `gpt-image.png` — `gpt-image-2` (OpenAI), ~148s. Ótimo mas não cabe numa
  request Vercel direta (precisaria job assíncrono).
