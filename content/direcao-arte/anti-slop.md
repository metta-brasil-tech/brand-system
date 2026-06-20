---
title: "Anti-Slop — Padrões de IA genérica a evitar"
aliases:
  - "Anti AI Slop"
  - "Checklist anti-slop"
tags:
  - marca/metta
  - marca/tiago
  - status/vigente
  - tema/design
  - tipo/direcao-arte
  - tipo/referencia
  - usado-por/critic-visual
---

# Anti-Slop — padrões de IA genérica

Checklist que o **crítico visual** (`api/_critic.py`) usa pra reprovar peças que
"cheiram a IA genérica". Portado do `metta-anti-slop.md` do plugin-metta-ads e
adaptado ao DNA das duas marcas (Metta editorial + Tiago cinema).

> **Regra-mãe:** se uma peça **real do banco** (`data/applications-index.json`)
> faz aquilo, é repertório legítimo — **não** é slop. Na dúvida, compare com a
> referência aberta antes de reprovar. O olho da referência vence a regra.

## A lista (16 itens)

1. **Gradiente arco-íris** ou multicolor decorativo. As marcas têm paleta fechada.
2. **Glassmorphism** — cartão de vidro fosco, blur translúcido flutuando.
3. **Ícones de biblioteca genérica** (Lucide/Heroicons/FontAwesome) colados. Ícone
   só via SVG próprio da marca.
4. **Layout em 3 faixas horizontais** simétricas sem hierarquia real.
5. **Box-shadow difusa estilo Tailwind** / cards flutuando sem motivo.
6. **Emoji** na peça.
7. **Tudo centralizado sem propósito** — a simetria vazia do "AI poster".
8. **Badge de e-commerce** não pedido ("OFERTA", "50% OFF", selo de garantia).
9. **Sorriso de stock** / aperto de mão clichê / lâmpada de ideia.
10. **Saturação inflada / HDR** / grade teal-orange turística.
11. **Texto rasterizado dentro da foto gerada** — palavras tortas que a IA inventa
    dentro da imagem. Texto é sempre via HTML por cima, nunca dentro do `gpt-image`.
12. **Tipografia default de sistema** (Arial/Helvetica) onde devia ser a display da
    marca (Zalando Sans Expanded na Metta; Inter no Tiago).
13. **Mockup de device genérico** sem contexto.
14. **Faixas pretas de preenchimento** (letterbox) forçando proporção — story é
    recomposição real do canvas 9:16, não feed esticado com tarja.
15. **Amarelo decorativo espalhado** — na Metta e no Tiago o amarelo é **cirúrgico**
    (um objeto, um detalhe), nunca difuso/decorativo.
16. **Sujeito-fantasma centralizado** — composição genérica que não herdou nada da
    linguagem do banco.

## Por que isso virou julgamento de visão, não regra de script

Insight do plugin-metta-ads: regras mecânicas rígidas (px mínimo, razão tipográfica,
"CTA sempre amarelo") **brigam com as peças campeãs do próprio banco**. O banco tem
ads que violam todas elas e funcionam. Por isso o anti-slop é avaliado por quem
**vê** a peça (o crítico comparando com a referência), não por um validador estático.
O `api/_qa.py` continua cuidando só do que é genuinamente binário (archetype válido,
headline presente, overflow/colisão, fonte injetada).
