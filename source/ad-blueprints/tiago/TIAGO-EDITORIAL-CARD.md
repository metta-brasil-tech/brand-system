---
id: TIAGO-EDITORIAL-CARD
display_name: "Card de dados Tiago — bloco central com stats e ornamento pixel"
marca: tiago
archetype: tiago-editorial-card
params: { theme: offwhite, card: dark-teal, cta: inline, ornament: pixel-yellow }
slots: [headline, subhead, body]
image: { required: true, treatment: "ornamento gráfico ou foto editorial dark — contexto visual que reforça a estatística", prompt_ref: "image-prompts/tiago/style-editorial-collage.md" }
formato_nativo: [feed]
dna_ref: "design/banco-tiago-conteudo.md#§3"
status: ativo
---

# TIAGO-EDITORIAL-CARD · card de dados editorial

## Intenção
Slide de prova. Dados, stats ou lista de sintomas embarcados num card central com bg
dark-teal (#3D5762) ou preto (#0F1419). Eyebrow UPPER amarelo ("O DADO CRU:") abre o
bloco; stats centralizadas com mix bold/regular entregam o conteúdo; remate bold fecha
com método ("Não é falta de vontade. **É falta de método.**"). Ornamentos pixel amarelos
(triângulos ⚠, setas →) dispersos no canvas atrás do card dão texture editorial.
O leitor lê dado → contexto → método.

## Estrutura visual
Canvas off-white (#EDEEEE) com noise. Card central dark-teal ou preto com corner radius
32–40px, ocupando 78–88% do canvas (64px de margem lateral). Dentro do card: eyebrow
UPPER amarelo no topo; stats centralizadas brancas com mix bold (número/conceito-chave)
+ regular (contexto); remate bold com `👉` no bottom do card. Ornamentos pixel amarelos
(3–5 instâncias, 8–16px) espalhados nos cantos atrás do card.

## Quando brilha
Dados/stats que precisam respirar · lista de sintomas/sub-dores · bloco de prova
quantitativa com remate de método · segundo ou terceiro slide de carrossel após capa HERO.
Funil: TOFU/MOFU.

## Anti-padrões
Um único big number gigante isolado (use TIAGO-EDITORIAL-HERO) · citação literal de pessoa ·
CTA forte de comentário (use TIAGO-EDITORIAL-CTA) · card claro sobre fundo claro (quebra contraste).

## Direção de copy
- **eyebrow** (≤30ch, UPPER): label amarelo que abre o bloco. Ex: "O DADO CRU:", "A PROVA:", "NÃO É EXCEÇÃO:".
- **stats** (≤320ch, ≤8 linhas): mix de peso essencial — número/conceito-chave em bold, contexto em regular.
- **remate** (≤100ch, ≤2 linhas): frase fechamento bold que aplica método. Pode ter `👉` no final.
