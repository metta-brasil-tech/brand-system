---
id: METTA-TWEET-CARD
display_name: "Tweet-card brandado — statement curto + avatar Metta"
marca: metta
archetype: card-mock
params: { theme: dark, name: Metta, handle: "@metta.brasil" }
slots: [tag, headline, subhead, body, cta]
image: { required: false }
formato_nativo: [story, feed]
dna_ref: "design/banco-ads-figma.md#§novo-tweet-card"
status: ativo
---

# METTA-TWEET-CARD · tweet-card brandado

## Intenção
Formato de post de rede social completamente brandado Metta. Card centralizado com
avatar + nome no topo, statement curto e impactante como o "tweet", complemento abaixo
e call final. A força está na brevidade: uma frase, uma ideia, memorizável e shareável.
Não vende — provoca raciocínio rápido.

## Estrutura visual
Card centralizado sobre fundo light (ou dark). Topo com avatar circular Metta + nome
+ handle, como header de tweet. Centro com o statement em tipografia grande (a headline)
ocupando 50-60% do card. Body como complemento curto e call final na base. Leitura:
autoridade (avatar) → provocação (statement) → complemento → call.

Prova de print REAL (o motor injeta sozinho): selo verificado DOURADO (organização no
X — a Metta é empresa), logo do X no canto, linha de timestamp + Visualizações e barra
de engajamento com números plausíveis (fake mas determinísticos pela copy — a mesma
peça re-renderizada mantém os números). Desligável com `engagement: none` nos params.

## Quando brilha
Quote curta de autoridade · dado de impacto com credencial ("R$2.3M gerados, 3 meses,
mesmo time") · provocação viral de raciocínio rápido · reframe de mercado · break
tipográfico entre imagens num carrossel. Funil: TOFU/viral.

## Anti-padrões
Copy longa (>160ch destrói o DNA de tweet) · foto humana de fundo (mata a legibilidade
do card) · tom corporativo genérico (precisa soar humano e direto) · mais de um call
(o tweet-card provoca, não empilha ofertas).

## Direção de copy
- **headline** (≤160ch, ≤5 linhas): o "tweet" — statement afiado. Até 3 palavras em
  amarelo usando `*asteriscos*`.
- **subhead** (opcional): reforça o statement.
- **body** (opcional, ≤80ch): complemento — fonte, métrica ou contexto.
- **cta**: call final curto. CTA no fim.
