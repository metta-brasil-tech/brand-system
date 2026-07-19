# Plano — imagem do tweet com proporção variável (como o Twitter real)

> Status: proposto · 18/07/2026 · autor: agente de imagem
> Escopo: `TIAGO-TWITTER-CARD-IMAGE` (e qualquer mock com foto embed)

## Problema

Hoje a foto embed do tweet **estica pra preencher o espaço que sobra e corta a
imagem**:

```css
.tw-embed        { flex: 1; }                 /* enche a altura restante */
.tw-embed-photo  { background-size: cover; }  /* corta pra preencher */
```

Resultado: uma foto paisagem (ex: cena do The Office, deitada) vira um bloco
alto e cortado; uma foto retrato também. A proporção original se perde. No
Twitter real a imagem aparece **na proporção dela**, dentro de limites.

Feedback do report "Fora de padrão": *"o tamanho das imagens tem que ser
variável… respeitar o formato original do Twitter."*

## Comportamento-alvo (Twitter/X real)

- A imagem é exibida **no aspecto dela** (paisagem deitada, retrato em pé,
  quadrada quadrada), sem esticar.
- Há **limites** (o X clampa): muito panorâmica → mostra até ~2:1; muito
  vertical → corta pra um teto (~3:4). Dentro da faixa, mostra o aspecto real.
- Cantos discretos (já está 16px ✓).

## Mudança no pipeline (passos)

**1. Medir a imagem (novo passo).**
Depois de obter a foto (gerada / upload / busca), ler `W×H` dos bytes
(PIL — já temos os bytes/data-URI no pipeline). Custo zero, sem IA.

**2. Calcular o aspecto de exibição (clamp estilo X).**
```
ar = H / W
ar_disp = clamp(ar, AR_MIN, AR_MAX)      # ex: AR_MIN≈0.5 (2:1 wide), AR_MAX≈1.33 (3:4 tall)
crop = (ar_disp != ar)                    # só corta se saiu da faixa
```
Bounds `AR_MIN`/`AR_MAX` calibráveis contra prints reais do X.

**3. Passar o aspecto pro render.**
`_blueprint_render.py` (archetype `tiago-twitter`) recebe `image_aspect` e
emite no `.tw-embed`:
```html
<div class="tw-embed" style="aspect-ratio: {W}/{H_disp}">…</div>
```

**4. Trocar o CSS do embed.**
```css
.tw-embed       { flex: 0 0 auto; aspect-ratio: var(--embed-ar, 16/9);
                  max-height: 62%; margin-top: 24px; border-radius: 16px; overflow: hidden; }
.tw-embed-photo { background-size: cover; }   /* cover só corta quando saiu da faixa (passo 2) */
```
`flex:0 0 auto` = a imagem para de esticar; `aspect-ratio` dá a altura natural;
`max-height` evita retrato dominar o card.

**5. Layout do card.** Com a imagem em altura própria, o bloco
(header + texto + imagem + engajamento) flui e **centraliza** no canvas
(já temos `justify-content:center`). A sobra branca vira variável — natural.

## Decisão de produto (2 opções de canvas)

| Opção | Como | Prós | Contras |
|---|---|---|---|
| **A — canvas fixo** (feed 4:5) + imagem no aspecto dela, centralizada | mantém 1080×1350 | posta direto no Instagram (formato fixo) | sobra branca variável em cima/embaixo |
| **B — canvas auto-height** (altura = conteúdo) | dimensão variável | 1:1 com print de tweet real | não é 4:5 fixo p/ feed do Instagram |

**DECISÃO (Nathan, 18/07): opção B — canvas auto-height.** O card do tweet
renderiza na altura do conteúdo (header + texto + imagem no aspecto dela +
engajamento), igual a um print de tweet real e cru. Saída com dimensão variável
(não 4:5 fixo). Implica um caminho de render que captura a altura natural (não
força FORMAT_DIMS) só pra os archetypes de mock (tweet).

## Onde mexer

- `api/generate.py` — medir a imagem e computar `image_aspect` (passo 1–2);
  passar ao render.
- `api/_blueprint_render.py` — archetype `tiago-twitter`: aceitar `image_aspect`
  e emitir `style="aspect-ratio:…"` no `.tw-embed`.
- `source/ad-blueprints/_engine.css` — trocar `flex:1` → `flex:0 0 auto` +
  `aspect-ratio` + `max-height` (passo 4).

## Esforço e conexão

- **Pequeno-médio**, sem custo de IA (só medição + CSS/HTML).
- É um caso concreto da **Fase 1** do plano maior (levar a lógica calibrada
  pro motor): *o motor mede a imagem e adapta o layout* — mesma família da
  lógica de foco (texto na zona vazia). Princípio guia: UX-first, tudo pensado
  pela ótica de quem usa o site.

## Teste de aceite

- Foto paisagem → embed deitado, sem corte (bate com o exemplo bom "Paz não é
  uma empresa…").
- Foto retrato → embed em pé, respeitando teto de altura.
- Foto quadrada → embed quadrado.
- Nenhuma imagem esticada/deformada; canto 16px; texto preto com negrito só no
  destaque; avatar = foto de perfil real.
