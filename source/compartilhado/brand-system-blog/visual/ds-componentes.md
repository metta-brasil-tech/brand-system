# Componentes

Os componentes da Metta são as **unidades visuais reusáveis** que combinam tokens (cor, tipografia, forma, espaçamento, elevação) numa peça funcional. Cada componente tem regra clara de uso editorial — onde aplicar, em que estado, com que conteúdo. **Componente fora do sistema descaracteriza a marca tão rápido quanto cor improvisada.**

Esta página cobre os componentes editoriais principais: **CTA, Card, Pill, Headline display, Espaço de respiro, Padrões de movimento**. Componentes mais técnicos (form fields, dropdowns, toasts) ficam no catálogo técnico do DS.

## Botões CTA

Botões primários da marca. **Sempre forma `full` (pill)**, peso `Expanded Bold` (700) com font-stretch 132%. Três variantes — uma escolha não é estética, é funcional.

<div class="cta-demo-list">
  <div class="cta-demo-row">
    <div class="cta-demo-meta">
      <strong>CTA Amarelo</strong>
      <span class="cta-tag">primário · ação principal</span>
      <p>Use pra a ação principal de qualquer peça (apenas 1 por composição). Background amarelo Metta sobre on-primary night-10.</p>
    </div>
    <div class="cta-demo-stage">
      <button class="ds-cta ds-cta-yellow">Quero participar</button>
    </div>
  </div>
  <div class="cta-demo-row">
    <div class="cta-demo-meta">
      <strong>CTA Escuro</strong>
      <span class="cta-tag">secundário · ação alternativa</span>
      <p>Use pra ação secundária ao lado do CTA primário. Background night-10 com texto branco. Hover: night-20.</p>
    </div>
    <div class="cta-demo-stage">
      <button class="ds-cta ds-cta-dark">Saiba mais</button>
    </div>
  </div>
  <div class="cta-demo-row">
    <div class="cta-demo-meta">
      <strong>CTA Claro</strong>
      <span class="cta-tag">sobre fundo escuro</span>
      <p>Versão para fundo escuro (manifesto, hero noite). Background branco gelo com texto night-10. Hover: night-95.</p>
    </div>
    <div class="cta-demo-stage cta-demo-stage--dark">
      <button class="ds-cta ds-cta-light">Conheça o método</button>
    </div>
  </div>
</div>

### Regras CTA
- **Apenas 1 CTA primário (amarelo) por peça.** Múltiplos amarelos competem e diluem hierarquia.
- **CTA secundário (escuro)** pode coexistir com primário, mas sempre subordinado visualmente.
- **Texto sempre verbo no imperativo** — "Quero participar", "Agendar diagnóstico", "Acessar". Nunca "Clique aqui", nunca "Saiba mais sobre nossos serviços".
- **Largura proporcional ao texto** (com padding `spacing-6` lateral, `spacing-4` vertical). Nunca CTA full-width em peça editorial — fica fraqueza visual.
- **Estado disabled** com opacidade 40% e cursor `not-allowed`. Usar com parcimônia — preferir esconder a desabilitar.

## Cards

5 variantes de card, cada uma com função editorial. **Card padrão** é o default; outras variantes têm propósito específico.

### Card padrão
Use pra qualquer item de lista, grid de features ou conteúdo neutro. Forma `md` (12px), elevação Level 1.

<div class="ds-card">
  <h4>Workshop quinzenal</h4>
  <p>Diagnóstico estratégico ao vivo, em grupo restrito de empresários no mesmo porte.</p>
</div>

### Card elevated
Use pra featured items, callouts hero ou conteúdo que precisa "saltar" do resto. Forma `xl` (24px), elevação Level 3. **Mais peso visual** — usar com parcimônia.

<div class="ds-card ds-card-elevated">
  <h4>Aplicação aberta</h4>
  <p>Programa SMTM 2026 · vagas limitadas. Análise gratuita em 48h, decisão dos dois lados.</p>
</div>

### Card stat
Use pra estatísticas, métricas e resultados quantitativos. **Número grande** puxa o olhar primeiro, label e descrição apoiam.

<div class="ds-card ds-card-stat">
  <div class="ds-card-stat-number">+47%</div>
  <div class="ds-card-stat-label">Faturamento mensal</div>
  <div class="ds-card-stat-desc">Crescimento médio em 8 meses pros clientes que completaram a primeira fase de implementação.</div>
</div>

### Card icon
Use pra apresentar features, capacidades ou itens de lista visual onde o ícone reforça o conceito. Ícone sempre estilo SVG do DS (viewBox 24x24, stroke-width 2.2, currentColor).

<div class="ds-card ds-card-icon">
  <div class="ds-card-icon-svg">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
  </div>
  <h4>Resposta em até 48h</h4>
  <p>Toda aplicação é avaliada pessoalmente pela equipe. Quem não se encaixa é avisado direto, sem call vazia.</p>
</div>

### Card filled
Use em peças de **destaque máximo** — garantia, oferta, callout final. Fundo `inverse-surface` (night-10) contrastante. **Apenas 1 por peça**.

<div class="ds-card ds-card-filled">
  <span class="ds-card-eyebrow">Garantia contratual</span>
  <h4>Se não bater, a Metta responde</h4>
  <p>Cláusula irrevogável no contrato. Compromisso compartilhado pela meta.</p>
</div>

### Regras Card
- **Padding interno** sempre `spacing-5` (24px) no padrão; `spacing-7` (48px) no elevated/filled.
- **Cards no mesmo grid** sempre com altura igual (`grid-template-columns` com `1fr` e `align-items: stretch`).
- **Não aninhar cards.** Card dentro de card vira ruído estrutural.
- **Card stat** apenas com 1 número visível — não use 2-3 stats no mesmo card.

## Etiquetas Pill

Tags em **caixa alta** com espaçamento entre letras. Duas variantes: contorno (neutra) e preenchimento (destaque amarelo).

<div class="pill-demo-stage">
  <span class="ds-pill">Elite</span>
  <span class="ds-pill">Premium</span>
  <span class="ds-pill">Exclusive</span>
  <span class="ds-pill ds-pill-filled">Inteligência comercial</span>
  <span class="ds-pill ds-pill-filled">Mentoria SMTM</span>
</div>

### Aplicação
- **Pill contorno** — categorização neutra, marcador de plano (Elite, Premium), tag editorial.
- **Pill amarelo** — destaque de tema/conceito proprietário, marca-d'água editorial, badge de coleção.
- **Sempre uppercase** com tracking 0.18em. Nunca title case ou lowercase.
- **Texto curto** (1–3 palavras). Pill com frase é cartaz, não tag.

## Tipografia de destaque (Display Headlines)

5 variações de display headline. Use a que melhor reforça o tom da peça — **uppercase agressivo** pra autoridade, **sentence case** pra editorial, **mixed weight** pra ritmo, **itálico ou marker** pra ênfase tipográfica não-cromática.

### Variação 01 — Caixa alta + destaque amarelo

Headline corporativa direta com palavra-chave em amarelo Metta. Use em peças institucionais e CTAs principais.

<div class="ds-headline-stage">
  <div class="ds-headline ds-headline-v1">Demita o achismo. Construa <span class="ds-headline-accent">método</span>.</div>
</div>

### Variação 02 — Caixa baixa + destaque escuro

Tom editorial, narrativo. Use em peça mais longa, leitura literária.

<div class="ds-headline-stage">
  <div class="ds-headline ds-headline-v2">A inteligência comercial existe. Está <span class="ds-headline-accent-dark">invisível</span> na sua operação.</div>
</div>

### Variação 03 — Pesos misturados (Heavy + Light)

Cria ritmo tipográfico sem cor. Use em peça que precisa contraste sem amarelo.

<div class="ds-headline-stage">
  <div class="ds-headline ds-headline-v3">Método <span class="ds-headline-light">não é</span> luxo.</div>
</div>

### Variação 04 — Destaque em itálico

Ênfase narrativa. Use em quote, citação literária, tom mais reflexivo.

<div class="ds-headline-stage">
  <div class="ds-headline ds-headline-v4">A única consultoria que <em>responde</em> contratualmente pela meta.</div>
</div>

### Variação 05 — Marca-texto amarelo

Highlight horizontal sobre palavra-chave. Use pra ênfase visual em texto narrativo.

<div class="ds-headline-stage">
  <div class="ds-headline ds-headline-v5">Empresário no seu porte <span class="ds-headline-marked">trava aqui</span>.</div>
</div>

### Regras Headline
- **Apenas 1 headline display por peça.** Múltiplos display competem.
- **Linha quebrada por intenção** — controle as quebras manualmente em headlines curtas (use `<br>` ou shy hyphen).
- **Destaque em UMA palavra ou expressão curta**. Destaque em frase inteira não é destaque.
- **Nunca centralize headline longa** — leitura sofre. Headline curta (3-4 palavras) pode centralizar; headline longa sempre alinhada à esquerda.

## Espaço de respiro

Container único central com tom sutil. **Área de respiro em anúncios e stories.** Forma `2xl` (32px), preenchimento `spacing-7` (48px). **Nunca composto por 4 retângulos** — sempre 1 frame único arredondado.

<div class="ds-breathing-stage">
  <div class="ds-breathing-room">
    <h4>Espaço de respiração</h4>
    <p>Tint sutil sobre o background, corner 32px, padding 48px. CTA fica embedado dentro, headline acima, content abaixo.</p>
  </div>
</div>

### Aplicação
- **Ad estático** — frame central que isola headline + CTA do fundo fotográfico.
- **Story** — bloco editorial sobre paisagem que respeita zona safe do Instagram.
- **Slide** — bloco de destaque em apresentação executiva.

### Regras
- **Apenas 1 espaço de respiro por peça.** Múltiplos viram caixas dentro de caixas.
- **Background atrás precisa contraste suficiente.** Tint do bloco precisa diferenciar do fundo.
- **Nunca borda visível** no espaço de respiro — distinção é só por background sutil.

## Padrões de movimento

5 padrões editoriais reusáveis em LP, hero, story:

1. **Reveal** — fade-in + translate-Y conforme entra na viewport
2. **Magnetic** — hover sutil que puxa elemento na direção do cursor
3. **Counter** — números crescem de 0 ao final em scroll
4. **Ken Burns** — zoom lento em foto hero (1.0 → 1.06 max)
5. **Tipo-machine controlada** — texto letra por letra em manifesto

Detalhes completos de cada padrão (curva, duração, parâmetros) na **página Movimento** do DS.

## Componentes não cobertos aqui

Esta página cobre os componentes **editoriais e de marca**. Componentes mais técnicos ficam no catálogo técnico do DS:

- Form fields (input, textarea, select, checkbox, radio)
- Modal e dialog
- Toast e snackbar
- Dropdown e menu
- Breadcrumb e pagination
- Tab e accordion
- Tooltip e popover
- Avatar, badge, chip
- Progress bar e skeleton

## Para implementação técnica

Tokens completos por componente, snippets de código, mapeamento Figma e exemplos React/Vue ficam no **catálogo técnico do Design System**. Esta página cobre o uso editorial — quando aplicar, com que conteúdo, com que estado.
