# Brief de captação — fotos originais do Tiago

Por que existe: **~50% do banco real é L1 (foto real do especialista)** — a única
linguagem que a IA nunca gera (`dna-visual-banco-real.md`). Hoje a biblioteca tem
3 fotos de palco (`assets/tiago/recortes/`) e é o gargalo confirmado: na bateria
de 9/jul, TIAGO-PHOTO-RAW reprovou porque a foto usada não era o Tiago.

Consomem foto real hoje: `TIAGO-PHOTO-RAW`, `TIAGO-STORY-COVER-HERO`,
`TIAGO-EDITORIAL-CTA` (flag `prefer_upload`) + todas as peças Metta L1
(palco, escritório, recorte com contorno amarelo).

## Identidade visual do sujeito (já codificada no sistema)

Blazer grafite sobre camiseta preta lisa, óculos retangulares escuros, barba
curta — expressão confiante, tom **leve e bem-humorado** (o banco real não é
sombrio). Trazer também 1 variação camisa social azul (existe no banco: palco).

## Cenários (em ordem de prioridade)

| # | Cenário | Uso no banco | Shots mínimos |
|---|---|---|---|
| 1 | **Estúdio fundo neutro liso** (cinza claro e navy) | Recortes com contorno amarelo (assinatura L1), photo-side A/B, capas | 15 — corpo inteiro + meio corpo; olhar pra ESQ e pra DIR; braços cruzados, apontando, mão no queixo, segurando notebook/pasta; 2-3 com humor leve |
| 2 | **Palco / evento** (mic, plateia desfocada) | `operacao-funciona-sem-voce`, autoridade | 10 — falando, andando, plateia ao fundo, contra-luz |
| 3 | **Escritório / reunião real** (mesa, tela com dashboard) | `me-de-60-minutos`, `servicos-300-milmes`, L7 | 10 — reunião conduzindo, apontando pra tela, 1:1 com cliente |
| 4 | **Lifestyle conceitual** (poltrona, ambiente inusitado) | `talento-ou-prisao` (poltrona no campo) | 8 — sentado poltrona, em pé ambiente amplo, respiro grande |
| 5 | **Retrato dramático** (chiaroscuro, meio-perfil) | Família DARK Metta | 8 — luz lateral única, fundo preto, sério e meio-sorriso |

## Regras técnicas (pro fotógrafo)

- **Resolução**: lado maior ≥ 3000px (story 1080×1920 renderiza @2×). RAW + export.
- **Orientação**: TODO cenário em retrato E paisagem — os blueprints recortam.
- **Respiro**: enquadrar com folga generosa (headroom e laterais) — o layout
  ancora texto em faixa vazia e o rosto **nunca** pode cair no topo ~11% do
  story (safe zone do IG). Foto apertada = foto inutilizável.
- **Direção de olhar dos DOIS lados**: layouts photo-side usam foto à direita E
  à esquerda — o olhar deve apontar pra dentro da peça.
- **Pra recorte**: fundo limpo + luz separando o sujeito do fundo (rim light).
- **Expressão**: maioria confiante/leve; algumas sérias pro DARK. Zero "sorriso
  de stock com braços cruzados olhando pra câmera" em excesso (anti-slop 16).

## Entrega e ingestão

1. Selecionar ~40–60 aproveitáveis.
2. Recortes (PNG alfa) → `assets/tiago/recortes/` · cenas inteiras →
   `assets/fotografia/` (webp, mid + thumbs como as existentes).
3. Marcar na biblioteca com flag `fotoReal` (roteamento L1 nunca gera).
