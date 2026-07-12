# Safe zones — Instagram feed & story

Fonte canônica das zonas seguras usadas pela checagem por visão (`api/_vision_qa.py`).
Portado de `plugin-metta-ads/lib/metta-safe-zones.md` (v0.6 vision-first), adaptado
ao pipeline do brand-system. **Julgamento visual, não gate mecânico** — a UI do
Instagram cobre partes do canvas e o revisor confere olhando a peça.

## Story / Reels (1080×1920 · 9:16)

| Zona | Coordenadas | Fração da altura | Risco |
|---|---|---|---|
| Header IG | y = 0 a 220 | ~topo 11,5% | Handle, hora, "Compartilhar" cobrem o conteúdo |
| Footer IG | y = 1640 a 1920 | ~base 14,5% | Botão de ação e barra de navegação cobrem o conteúdo |
| **Zona útil** | **y = 220 a 1640** | 11,5%–85,5% | Toda copy, marca e CTA da peça |

Headline, subhead, CTA e marca **não podem** começar no topo ~11% nem terminar na
base ~15% do story. Imagem de fundo pode sangrar (full-bleed) — a regra é sobre
elementos que carregam informação.

## Feed (1080×1350 · 4:5)

| Zona | Coordenadas | Fração da altura | Risco |
|---|---|---|---|
| Margem superior | y = 0 a 60 | ~topo 4,5% | Truncamento em alguns devices |
| Margem inferior | y = 1290 a 1350 | ~base 4,5% | Texto encostando na borda |
| **Zona útil** | **y = 60 a 1290** | 4,5%–95,5% | Conteúdo seguro |

## Quadrado (1080×1080 · 1:1)

Sem UI sobreposta específica; valem as margens de respiro do feed (~4,5% por borda)
para elementos essenciais.

## Regras de julgamento (o que o revisor confere no PNG)

1. **CTA inteiro visível** — pill/bloco com a curvatura completa dentro do canvas,
   com folga da borda inferior.
2. **Nada essencial cortado** — headline, subhead, CTA e marca inteiros. Bleed é
   permitido só em imagem de fundo e elemento decorativo intencional.
3. **Essenciais dentro da zona útil** — conforme as tabelas acima, por formato.
4. **Anti-tarja** — barra preta/chapada de preenchimento pra "esticar" a proporção
   reprova (já listada no `anti-slop.md`, item 14). Story é recomposição real do
   feed, não o feed com letterbox.

## Exceções legítimas

- Elemento decorativo (número rotacionado na lateral, padrão de fundo) pode sair
  do canvas se o efeito for proposital.
- Texto decorativo sem função informativa pode viver fora da zona útil.
- **O banco manda:** se uma peça campeã do banco viola uma "regra" daqui, a peça
  vence — ajuste o doc, não reprove o padrão do banco.
