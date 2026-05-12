---
title: "Metta — UI Kit Editorial"
tags:
  - marca/metta
  - status/normativo
  - tema/design
  - tipo/componentes
summary: "10 componentes editoriais validados (CTAPill, SectionOpener, StrategyTechRow, QuoteBlock, etc.). Snippets JSX prontos. Carregar quando construir LP, playbook, ou material editorial longo."
created: 2026-04-28
updated: 2026-04-28
---

# Metta — UI Kit Editorial

> **Source canônico:** `system-source/ui_kits/editorial/components.jsx` + `index.html` (demo).
> **Quando carregar:** briefing pede LP, playbook, página editorial longa, manual de marca, demo interativo.
> **Tokens canônicos:** ver [[metta-tokens]].
> **Para ads/stories/posts curtos:** prefira [[metta-components]] (snippets CSS atômicos).

---

## §0. Quando usar UI Kit vs Components

| Caso | Use |
|---|---|
| Ad Instagram/Stories curto | [[metta-components]] (CSS atômico) |
| Carrossel social (slides curtos) | [[metta-components]] + [[catalogo/content-styles]] |
| Landing page institucional | UI Kit (este doc) — `Header` + `SectionOpener` + `StrategyTechRow` + `Footer` |
| Playbook editorial / O Código Metta | UI Kit — `SectionOpener` + `QuoteBlock` + `StrategyTechRow` |
| Manual de marca interativo | UI Kit completo (todos os componentes) |
| Pitch deck (slides) | [[catalogo/slides]] |

---

## §1. Componentes (10)

### 1.1 `<Header>` — header com logo + nav + CTA
**Variantes:** `tone="dark"` (default) ou `tone="light"`

```jsx
<Header tone="dark" />
// → Logo (auto-seleciona variante por tone) + nav links + CTAPill primary "Baixar Brand Kit"
```

**Specs:**
- Padding: `22px 8%`
- Border bottom: `rgba(255,255,255,0.06)` (dark) ou `rgba(12,22,27,0.06)` (light)
- Logo: SVG do `system-source/assets/logos/` (colorido_h pra dark, colorido_escuro_h pra light)
- Nav items: Expanded Medium 540, 12px, UPPERCASE, ls 0.14em
- CTA: ver `<CTAPill variant="primary">`

---

### 1.2 `<Footer>` — footer institucional
```jsx
<Footer />
// → Signature SVG + versão do manual + contato em amarelo
```

**Specs:**
- Background: `--blue-deep` (#0A1013)
- Padding: `48px 8%`
- Signature: `system-source/assets/signatures/assinatura_metta_branco.svg` (height 34px)
- Texto legal: Expanded Light 270, 11px, UPPERCASE, ls 0.28em
- Email destaque em `--yellow-primary`

---

### 1.3 `<CTAPill variant>` — botão primário com hover/press

**Variantes:** `primary` (yellow) | `dark` (escuro com border yellow) | `ghost` (transparent com border white)

```jsx
<CTAPill variant="primary" onClick={...}>QUERO PARTICIPAR</CTAPill>
<CTAPill variant="dark">SAIBA MAIS</CTAPill>
<CTAPill variant="ghost">VOLTAR</CTAPill>
```

**Specs:**
- Padding: `14px 28px`
- Border-radius: `999px` (pill)
- Tipografia: Expanded Bold 700, 13px, UPPERCASE, ls 0.06em
- **Estados:**
  - Default → cor da variante
  - Hover → primary: `#FFC531`; dark: `#1A2A35`; ghost: `rgba(255,255,255,0.08)`
  - Pressed → primary vira `#FFB618` + `transform: scale(0.97)`
- Transition: `transform .12s ease, background .15s ease`

---

### 1.4 `<SectionOpener>` — chapter opener com número grande

**Variantes:** `tone="dark"` (default) | `"yellow"` | `"light"`

```jsx
<SectionOpener
  tone="dark"
  num="01"
  kicker="CAPÍTULO UM"
  title="Bater meta não é arte. É método."
  lede="A diferença entre empresas que crescem e empresas que travam não está em talento — está em sistema. Esse capítulo quebra essa premissa em 6 partes."
/>
```

**Specs:**
- Grid: `120px 1fr` com `gap: 48px`, max-width 1200px
- Padding: `120px 8% 100px`
- Número: Expanded Heavy 870, 96px, lh 0.85, ls -0.02em
- Kicker: Expanded Medium 540, 12px, UPPERCASE, ls 0.18em
- Title: Expanded Heavy 870, clamp(42px, 5.5vw, 72px), lh 0.95
- Lede: Regular Book 400, 20px, lh 1.55, max-width 640px
- **Cores por tone:**
  - Dark: bg `--blue-night`, text `--white`, número `--yellow-primary`, kicker `--yellow-primary`, lede `--steel-blue`
  - Yellow: bg `--yellow-primary`, text `--blue-night`, número `--blue-night`, kicker `rgba(12,22,27,0.55)`, lede `rgba(12,22,27,0.7)`
  - Light: bg `--white`, text `--blue-night`, número `--blue-night`, kicker `--blue-gray`, border-top `rgba(12,22,27,0.08)`

---

### 1.5 `<StrategyTechRow>` — 2 colunas (estratégia + spec)

```jsx
<StrategyTechRow
  tone="light"
  kicker="LOGO"
  title="Por que o símbolo nunca usa glow"
  body="A versão antiga aplicava rgba(255,190,24,0.24) inset — removido em Apr/2026. Glow no logo descarta densidade visual e empurra a marca pra estética genérica de SaaS."
  spec={
    <>
      <SpecRow label="Drop shadow" value="✗ Proibido" />
      <SpecRow label="Inset glow" value="✗ Removido" />
      <SpecRow label="Outline" value="✗ Nunca" />
      <SpecRow label="Solid only" value="✓ Default" />
    </>
  }
/>
```

**Specs:**
- Grid: `1fr 1fr` com `gap: 80px`, max-width 1200px
- Padding: `80px 8%`
- Border-top: 1px (com cor por tone)
- **Coluna esquerda:** kicker + h3 (Expanded Semibold 650, 34px) + p (17px, lh 1.7)
- **Coluna direita (spec):** card com `border-radius: 20px`, padding 32px, bg `--ice-blue` (light) ou `--dark-card` (dark)

---

### 1.6 `<SpecRow>` — linha label/value tabular

```jsx
<SpecRow label="Yellow primary" value="#FFBE18" mono />
<SpecRow label="Headline weight" value="870 (Expanded Heavy)" />
```

**Specs:**
- Display flex space-between, gap 24px
- Padding: `12px 0`
- Border-bottom: `1px solid rgba(12,22,27,0.08)`
- Label: Expanded Medium 540, 11px, UPPERCASE, ls 0.14em, color `--blue-gray`
- Value: 14px, text-align right, `font-variant-numeric: tabular-nums`
- `mono={true}` → `font-family: ui-monospace, SF Mono, Menlo, monospace`

---

### 1.7 `<ColorSwatch>` — display de cor com hex

```jsx
<ColorSwatch hex="#FFBE18" name="Yellow Primary" />
<ColorSwatch hex="#0C161B" name="Blue Night" onDark />
```

**Specs:**
- Layout: 48x48 swatch + nome/hex
- Swatch: `border-radius: 12px`, border 1px (`rgba(255,255,255,0.1)` se onDark)
- Nome: Expanded Semibold 650, 13px
- Hex: 11px, ls 0.06em, `font-variant-numeric: tabular-nums`

---

### 1.8 `<QuoteBlock>` — citação editorial

```jsx
<QuoteBlock cite="Tiago Alves" tone="light">
  Método substitui improviso. Quem improvisa hoje, paga amanhã.
</QuoteBlock>
```

**Specs:**
- Max-width: 700px
- Margin: `48px 0`
- Quote text: Regular Light 300, 26px, lh 1.5, italic, ls -0.01em
- Cite: Expanded Medium 540, 11px, UPPERCASE, ls 0.18em, color `--blue-gray-light`
- Cor por tone: dark → text `--white`; light → text `--blue-night`

---

### 1.9 `<YellowBand>` — faixa de marca

**Variantes:** `thick={false}` (6px decorative) | `thick={true}` (48px com texto)

```jsx
<YellowBand />  {/* faixa fina 6px */}
<YellowBand thick>METTA · INTELIGÊNCIA COMERCIAL · BORA BATER META</YellowBand>
```

**Specs:**
- Width 100%, background `--yellow-primary`
- **Thick mode:** height 48px, text Expanded Medium 540, 12px, UPPERCASE, ls 0.22em, color `--blue-night`, gap 24px

---

### 1.10 `<TransitionBand>` — separator com label + número

```jsx
<TransitionBand tone="yellow" label="Capítulo 02 — Identidade Verbal" num="02" />
<TransitionBand tone="dark" label="Aplicações" num="03" />
```

**Specs:**
- Padding: `18px 8%`
- Display: flex space-between
- Tipografia: Expanded Semibold 650, 15px, ls 0.02em
- **Yellow:** bg `--yellow-primary`, text `--blue-night`, número `--blue-night` em weight 870
- **Dark:** bg `--blue-night`, text `--white`, número `--yellow-primary` em weight 870

---

## §2. Composição de uma página editorial completa

Sequência canônica (vide `system-source/ui_kits/editorial/index.html`):

```
<Header tone="dark" />
<SectionOpener tone="dark" num="01" kicker title lede />
<StrategyTechRow tone="light" kicker title body spec />
<TransitionBand tone="yellow" label num />
<SectionOpener tone="yellow" num="02" ... />
<QuoteBlock>...</QuoteBlock>
<StrategyTechRow tone="dark" ... />
<YellowBand thick>METTA · INTELIGÊNCIA COMERCIAL</YellowBand>
<Footer />
```

**Ritmo:** Dark → Light → Yellow → Light → Dark → Yellow band → Footer

---

## §3. Adaptação pra Plugin API (Figma)

Os componentes JSX acima são pra **HTML/CSS**. Pra criar no Figma via `mcp__figma-remote__use_figma`, traduzir cada componente:

| JSX | Plugin API equivalent |
|---|---|
| `<CTAPill primary>` | `createCTA(parent, text, { bg: '#FFBE18', fg: '#0C161B', radius: 999 })` ([[figma-plugin-api]] §4) |
| `<YellowBand thick>` | `figma.createFrame()` + auto-layout HORIZONTAL + bg `#FFBE18` + height 48 + text child |
| `<SectionOpener>` | `figma.createFrame()` + grid de 2 colunas com auto-layout VERTICAL + número text + kicker text + headline text + lede text |
| `<StrategyTechRow>` | 2 frames lado a lado em auto-layout HORIZONTAL |
| `<QuoteBlock>` | text node single (italic, light weight 300) + cite text |
| `<Header>` | frame HORIZONTAL com logo image + nav frame + CTA frame |
| `<Footer>` | frame com signature image + texto + email |

**Helpers JS pra Plugin API:** ver [[figma-plugin-api]] §6 (`hexToRgb`).

---

## §4. Assets locais (system-source)

**SVGs disponíveis** (já no vault, sem precisar baixar do Drive):

```
system-source/assets/
├── logos/         (13 SVGs — horizontal/vertical, 6 variantes de cor)
├── symbols/       (5 SVGs — apenas o ícone circular)
├── signatures/    (5 SVGs — "metta | INTELIGÊNCIA COMERCIAL" lockup)
└── backgrounds/   (10 JPGs — gradientes + flat plates)
```

Em código novo, **prefira referenciar local** (`../system-source/assets/logos/logo_metta_colorido_h.svg`) ao invés de baixar do Drive — menos latência, sem dependência de rede.

> Ver [[metta-logos]] §1 pra mapeamento entre arquivo local ↔ Drive ID (ambos são fontes válidas).

---

## §5. Hard rules (do system-source SKILL.md)

❌ **Cores:** apenas tokens em `colors_and_type.css`. Yellow `#FFBE18` é load-bearing — use só pra CTAs, single-word highlights, símbolo fill, accent marks.

❌ **Tipografia:** apenas SF Pro Variable (ou Zalando Sans Expanded fallback — obrigatório em PPTX/Google Slides desde 2026-05-12; Roboto Flex deprecated). Nunca Inter/Arial/Helvetica/Open Sans. Headlines → Expanded (132%). Body → Regular (100%). Use `font-weight` e `font-stretch` direto, não `font-variation-settings`.

❌ **Logo:** nunca aplicar glow, shadow ou outer stroke no logo ou símbolo.

❌ **Copy:** Brazilian Portuguese, "você", no emoji, no corporate jargon. Direto, founder-voice, confiante.

❌ **Icons:** no emoji, no SVG micro-kit inventado. Use marcas tipográficas (caracteres em rounded squares), o Símbolo Metta, ou **Material Symbols Rounded** (Google Fonts) se UI affordance icons forem estritamente necessários — flag como substituição.

```html
<link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0">

<span class="material-symbols-rounded"
  style="font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24;">
  rocket_launch
</span>
```

---

## 🔗 Relacionados
- [[metta-tokens]] — cores, tipografia, radii, spacing, shadows
- [[metta-components]] — snippets CSS atômicos (CTA, watermark, blob)
- [[metta-logos]] — Drive IDs (fonte remota) + system-source/ (fonte local)
- [[figma-plugin-api]] — execução em Figma
- [[catalogo/landing-pages]] — patterns de hero, OOH, print
- [[Metta - PRD Identidade Visual]] §6.4 — efeitos proibidos
- **Source canônico:** `system-source/ui_kits/editorial/components.jsx`
- **Demo interativo:** `system-source/ui_kits/editorial/index.html`
- **Previews por elemento:** `system-source/preview/*.html` (24 arquivos)
