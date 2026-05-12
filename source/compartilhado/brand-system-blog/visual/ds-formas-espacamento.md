# Formas e Espaçamento

Dois sistemas estruturais que governam toda a geometria da Metta: **arredondamento de cantos** (formas) e **escala de espaçamento**. Ambos seguem progressão fixa — nada de raio arbitrário entre escalas, nada de espaço improvisado. A regra editorial: **geometria precisa comunica autoridade técnica**, geometria solta comunica improviso.

## Formas — raio de canto

8 valores oficiais. **Raio arbitrário entre 40 e 150px é proibido** — gera o "efeito balão" que descaracteriza a marca. Se você precisa de algo entre `2xl` (32px) e `full` (pill), reconsidere o componente, não invente um raio intermediário.

<div class="shape-grid">
  <div class="shape-item">
    <div class="shape-box" style="border-radius:0px"></div>
    <div class="shape-meta"><strong>none</strong><code>0px</code><span>proibido em uso normal</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:4px"></div>
    <div class="shape-meta"><strong>xs</strong><code>4px</code><span>chips, tags inline, code pill</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:8px"></div>
    <div class="shape-meta"><strong>sm</strong><code>8px</code><span>inputs, controles pequenos</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:12px"></div>
    <div class="shape-meta"><strong>md</strong><code>12px</code><span>card padrão (default)</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:20px"></div>
    <div class="shape-meta"><strong>lg</strong><code>20px</code><span>seções, blocos editoriais</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:24px"></div>
    <div class="shape-meta"><strong>xl</strong><code>24px</code><span>card elevated, hero</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:32px"></div>
    <div class="shape-meta"><strong>2xl</strong><code>32px</code><span>espaço de respiro, callout</span></div>
  </div>
  <div class="shape-item">
    <div class="shape-box" style="border-radius:999px"></div>
    <div class="shape-meta"><strong>full</strong><code>999px</code><span>pills, CTA, badges</span></div>
  </div>
</div>

### Regras
- **Card padrão** sempre `md` (12px). Card destacado/hero sempre `xl` (24px).
- **Botões CTA** sempre `full` (pill). Inputs sempre `sm` (8px).
- **Containers de seção** entre `lg` (20px) e `2xl` (32px) conforme densidade visual.
- **Tags e badges** sempre `full` em peças editoriais; `xs` apenas em UI técnica densa.
- **Nunca misturar 3+ raios diferentes** na mesma peça — escolha uma família visual e mantenha.

## Espaçamento — escala de 8 pontos estendida

10 valores oficiais. Grade base de 8 pontos com extensão pra densidades editoriais maiores (96px e 128px). **Nunca espaçamento arbitrário** — se nenhum dos 10 funciona, a estrutura do componente está errada.

<div class="spacing-list">
  <div class="spacing-row"><span class="name">spacing-1</span><span class="value">4px</span><div class="bar" style="width:3%"></div></div>
  <div class="spacing-row"><span class="name">spacing-2</span><span class="value">8px</span><div class="bar" style="width:6%"></div></div>
  <div class="spacing-row"><span class="name">spacing-3</span><span class="value">12px</span><div class="bar" style="width:9%"></div></div>
  <div class="spacing-row"><span class="name">spacing-4</span><span class="value">16px</span><div class="bar" style="width:12%"></div></div>
  <div class="spacing-row"><span class="name">spacing-5</span><span class="value">24px</span><div class="bar" style="width:19%"></div></div>
  <div class="spacing-row"><span class="name">spacing-6</span><span class="value">32px</span><div class="bar" style="width:25%"></div></div>
  <div class="spacing-row"><span class="name">spacing-7</span><span class="value">48px</span><div class="bar" style="width:38%"></div></div>
  <div class="spacing-row"><span class="name">spacing-8</span><span class="value">64px</span><div class="bar" style="width:50%"></div></div>
  <div class="spacing-row"><span class="name">spacing-9</span><span class="value">96px</span><div class="bar" style="width:75%"></div></div>
  <div class="spacing-row"><span class="name">spacing-10</span><span class="value">128px</span><div class="bar" style="width:100%"></div></div>
</div>

### Aplicação típica

| Faixa | Token | Uso |
|-------|-------|-----|
| **Densidade alta (UI/inline)** | `1` a `3` (4–12px) | Gap entre ícone e texto, padding interno de chip/tag, gap em listas inline |
| **Densidade média (cards/forms)** | `3` a `5` (12–24px) | Padding interno de card, gap entre campos de form, espaço entre H3 e parágrafo |
| **Densidade média-alta (blocos)** | `5` a `6` (24–32px) | Padding lateral de card destacado, gap entre cards no grid, espaço entre H2 e parágrafo |
| **Densidade baixa (sections)** | `7` a `8` (48–64px) | Padding vertical interno de section, gap entre blocos de section |
| **Densidade muito baixa (peça)** | `9` a `10` (96–128px) | Espaço vertical entre sections em peça longa, padding hero |

### Regras
- **Mesmo gap = mesma família**. Em grid de cards, todos os gaps iguais. Misturar `spacing-4` e `spacing-5` no mesmo grid quebra ritmo.
- **Padding lateral consistente** em peça inteira. Se a section abre em `spacing-8`, todas as outras devem abrir em `spacing-8` também (ou em outro valor único da mesma faixa).
- **Espaço acima de H2 sempre maior que abaixo.** O espaço separa do bloco anterior; o espaço abaixo conecta com o conteúdo da seção.

## Geometria precisa, alinhamento rigoroso

Princípio editorial que sustenta os dois sistemas: **cada elemento ancorado no grid, nada solto, nada flutuante**. O grid pode não ser visível (não usamos linhas de grade exibidas em peças finais), mas precisa estar implícito em qualquer composição.

- Headline alinhada ao mesmo eixo vertical do parágrafo.
- Cards no mesmo grid horizontal compartilham mesma altura (ou usam a mesma escala de altura).
- Margens externas de peça respeitam grid (geralmente múltiplo de `spacing-7` ou `spacing-8`).
- Imagens crop respeitam aspect ratios definidos (4:5, 1:1, 9:16, 16:9 — ver Direção de Arte).

## Para implementação técnica

Tokens completos como CSS variables, Figma styles e mapeamento Plugin API ficam no **catálogo técnico do Design System**. Esta página cobre o que governa o uso editorial.
