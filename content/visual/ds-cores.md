---
title: "Metta — Design Tokens"
aliases:
  - "Tokens"
  - "Design Tokens Metta"
tags:
  - marca/metta
  - status/normativo
  - tema/design
  - tipo/tokens
  - usado-por/skill-design-metta
formato_consumo: referencia-completa
prioridade_carregamento: 1
versao: 2.0
sucessor_de: _archive/refactor-2026-05-03-v2/metta-tokens-v1.md.bak
summary: "Design tokens Metta seguindo arquitetura 3-tier (ref/sys/comp) inspirada no Material Design 3 do Google. Source of truth de cores, tipografia, espaçamento, shape, elevation, motion. Distribuível pra outras áreas (cloud, propostas comerciais, apresentações). PRD e skills referenciam este arquivo."
created: 2026-04-28
updated: 2026-05-03
---

# Metta — Design Tokens v2.0

> **Status:** NORMATIVO. Fonte canônica de cores, tipografia, espaçamento, shape, elevation e motion. PRD, skills (`design-metta`) e código que aplicar a marca **leem** deste arquivo. Em conflito: este vence.
>
> **Arquitetura:** 3-tier (ref/sys/comp) seguindo Material Design 3 do Google. Cada tier tem responsabilidade clara, naming consistente, retrocompatibilidade preservada via aliases bridge.
>
> **CSS canônico:** `system-source/colors_and_type.css` é a tradução desta documentação em CSS importável.

---

## TL;DR (consulta rápida)

```css
/* COR */
background: var(--metta-sys-color-primary);          /* #FFBE18 */
color:      var(--metta-sys-color-on-primary);       /* #0C161B */
background: var(--metta-sys-color-surface);          /* tema-aware */
color:      var(--metta-sys-color-on-surface);

/* SHAPE */
border-radius: var(--metta-sys-shape-corner-md);     /* 12px */

/* SPACING */
padding: var(--metta-sys-spacing-5);                 /* 24px */

/* ELEVATION (suave) */
box-shadow: var(--metta-sys-elevation-2);

/* MOTION */
transition: all var(--metta-sys-motion-duration-medium) var(--metta-sys-motion-easing-standard);
```

---

## §1. Arquitetura — 3 tiers

```
TIER 3 — COMPONENT (--metta-comp-*)        tokens específicos por componente (CTA, card, label-pill)
                       ↑ aponta pra
TIER 2 — SYSTEM    (--metta-sys-*)         roles semânticos (primary, surface, typescale, shape, motion)
                       ↑ aponta pra
TIER 1 — REFERENCE (--metta-ref-*)         valores crus (paleta tonal, typeface, durations puras)
```

**Regra de ouro:**
- Código de produto (LP, ad, slide) → usa **comp** preferencialmente, **sys** se comp não existe
- Nunca importar **ref** direto em código de produto (exceto raríssimas exceções documentadas)
- Designer/dev: nova cor/tom → adiciona em **ref**, mapeia em **sys**, expõe em **comp**

---

## §2. TIER 1 — Reference Tokens

### 2.1 Paleta Yellow (primary brand) — escala tonal

| Token | HEX | Uso típico |
|---|---|---|
| `--metta-ref-palette-yellow-30` | `#B38400` | Darker — text on yellow surface |
| `--metta-ref-palette-yellow-40` | `#D9A100` | Inverse-primary em dark theme |
| `--metta-ref-palette-yellow-50` | `#FFBE18` | ★ default brand yellow |
| `--metta-ref-palette-yellow-55` | `#FFB618` | Solid variant — pressed state |
| `--metta-ref-palette-yellow-60` | `#FFC531` | Hover state |
| `--metta-ref-palette-yellow-70` | `#FFCE50` | Aux backgrounds |
| `--metta-ref-palette-yellow-80` | `#FFD66D` | Gradient mid |
| `--metta-ref-palette-yellow-90` | `#FFE3A6` | Gradient soft / on-primary-container dark |
| `--metta-ref-palette-yellow-95` | `#FFE4A1` | Soft fills — primary-container light |
| `--metta-ref-palette-yellow-99` | `#FFFAEC` | Whisper tint |

### 2.2 Paleta Night (neutral) — escala tonal

| Token | HEX | Uso típico |
|---|---|---|
| `--metta-ref-palette-night-5` | `#0A1013` | Deepest dark |
| `--metta-ref-palette-night-10` | `#0C161B` | ★ core dark — surface dark |
| `--metta-ref-palette-night-15` | `#131F25` | Surface container dark |
| `--metta-ref-palette-night-20` | `#1A2A35` | Elevated card dark |
| `--metta-ref-palette-night-25` | `#1E2D36` | Surface bright dark / container highest |
| `--metta-ref-palette-night-30` | `#2E3E47` | Slate panels |
| `--metta-ref-palette-night-40` | `#435965` | Bluegray default — on-surface-variant light |
| `--metta-ref-palette-night-50` | `#688594` | Bluegray light |
| `--metta-ref-palette-night-60` | `#75919F` | Bluegray soft |
| `--metta-ref-palette-night-70` | `#94B5C8` | On-dark muted |
| `--metta-ref-palette-night-80` | `#A8B3B9` | Dividers |
| `--metta-ref-palette-night-85` | `#B0CAD8` | Steel — on-surface-variant dark |
| `--metta-ref-palette-night-90` | `#C9DAE3` | Border de pills |
| `--metta-ref-palette-night-95` | `#EBF3F7` | Container high light / ice-blue |
| `--metta-ref-palette-night-97` | `#EFF3F5` | Container light / outline default |
| `--metta-ref-palette-night-99` | `#FAFCFD` | Container low light / ice |
| `--metta-ref-palette-night-100` | `#FFFFFF` | Surface light / on-primary |

### 2.3 Utilitários específicos não-tonais

Pra casos que a paleta night não cobre. Use só quando absolutamente necessário.

| Token | HEX | Uso |
|---|---|---|
| `--metta-ref-palette-neutral-pure-black` | `#000000` | Preto absoluto pra ads que pedem máximo contraste |
| `--metta-ref-palette-neutral-overlay-navy` | `#020F15` | Overlay sobre fotos com tinge específico |

### 2.4 Opacity — state layers + dividers

```css
--metta-ref-opacity-state-hover:    0.08;
--metta-ref-opacity-state-focus:    0.12;
--metta-ref-opacity-state-pressed:  0.16;
--metta-ref-opacity-divider-dark:   0.20;   /* white sobre fundo escuro */
--metta-ref-opacity-yellow-subtle:  0.10;
```

### 2.5 Typeface

```css
--metta-ref-typeface-brand:    'SF Pro';
--metta-ref-typeface-fallback: 'Zalando Sans Expanded';  /* OFL, Google Fonts — use em PPTX/Google Slides/Canva. Roboto Flex deprecated em 2026-05-12 */
--metta-ref-typeface-mono:     ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
```

### 2.6 Type axes (raw)

```css
--metta-ref-axis-wdth-regular:  100;   /* font-stretch normal */
--metta-ref-axis-wdth-expanded: 132;   /* font-stretch expanded */

--metta-ref-axis-wght-light:    270;
--metta-ref-axis-wght-regular:  400;
--metta-ref-axis-wght-medium:   510;
--metta-ref-axis-wght-medium-p: 590;
--metta-ref-axis-wght-semibold: 650;
--metta-ref-axis-wght-bold:     700;
--metta-ref-axis-wght-heavy:    870;
```

### 2.7 Duration / easing (raw)

```css
--metta-ref-duration-50:    50ms;
--metta-ref-duration-200:  200ms;
--metta-ref-duration-300:  300ms;
--metta-ref-duration-500:  500ms;
--metta-ref-duration-700:  700ms;

--metta-ref-easing-standard:   cubic-bezier(0.4, 0, 0.2, 1);
--metta-ref-easing-emphasized: cubic-bezier(0.2, 0, 0, 1);
--metta-ref-easing-decelerate: cubic-bezier(0, 0, 0.2, 1);
--metta-ref-easing-accelerate: cubic-bezier(0.4, 0, 1, 1);
```

---

## §3. TIER 2 — System Tokens (light theme default)

### 3.1 Color roles — Brand

| Token | Aponta pra | Uso |
|---|---|---|
| `--metta-sys-color-primary` | `yellow-50` (#FFBE18) | Primary brand, CTAs, accents |
| `--metta-sys-color-on-primary` | `night-10` | Texto sobre primary |
| `--metta-sys-color-primary-hover` | `yellow-60` | Hover do primary |
| `--metta-sys-color-primary-pressed` | `yellow-55` | Pressed do primary |
| `--metta-sys-color-primary-container` | `yellow-95` | Background sutil amarelo |
| `--metta-sys-color-on-primary-container` | `night-10` | Texto sobre primary-container |

> **Não há roles `secondary` nem `tertiary`** — a Metta institucional opera com paleta dual (Yellow + Night). Marca pessoal Tiago Alves tem seu próprio DS separado com Steel e Coral.

### 3.2 Color roles — Surface (hierarquia)

| Token | Light | Dark | Uso |
|---|---|---|---|
| `--metta-sys-color-surface` | `night-100` | `night-10` | Background base da página |
| `--metta-sys-color-surface-bright` | `night-100` | `night-25` | Highest tone |
| `--metta-sys-color-surface-dim` | `night-95` | `night-5` | Lowest tone |
| `--metta-sys-color-surface-container-lowest` | `night-100` | `night-5` | |
| `--metta-sys-color-surface-container-low` | `night-99` | `night-10` | Cards padrão |
| `--metta-sys-color-surface-container` | `night-97` | `night-15` | Sections, tags |
| `--metta-sys-color-surface-container-high` | `night-95` | `night-20` | Cards elevated, hover states |
| `--metta-sys-color-surface-container-highest` | `#E0E6E9` | `night-25` | Active state, card filled |
| `--metta-sys-color-on-surface` | `night-10` | `night-100` | Texto principal |
| `--metta-sys-color-on-surface-variant` | `night-40` | `night-85` | Texto secundário |

### 3.3 Color roles — Outline e Inverse

```css
--metta-sys-color-outline:           var(--metta-ref-palette-night-97);  /* #EFF3F5 */
--metta-sys-color-outline-variant:   rgba(202, 217, 224, 0.87);

--metta-sys-color-background:        var(--metta-sys-color-surface);
--metta-sys-color-on-background:     var(--metta-sys-color-on-surface);

--metta-sys-color-inverse-surface:    night-10 (light) / night-99 (dark);
--metta-sys-color-inverse-on-surface: night-99 (light) / night-10 (dark);
--metta-sys-color-inverse-primary:    yellow-80 (light) / yellow-30 (dark);
```

### 3.4 Typescale

Cada role tem 5 sub-tokens: `font`, `size`, `weight`, `stretch`, `line-height`. Naming inspirado no M3.

| Role | Size | Weight | Stretch | LH | Case | Uso |
|---|---|---|---|---|---|---|
| `display-hero` | 100-142px | 870 (Heavy) | 132% | 0.88 | UPPER | Headline máximo impacto |
| `display-large` | 78-99px | 650 (Semibold) | 132% | 0.90 | sentence | Hero secundário, posters |
| `display-medium` | 60-75px | 650 | 132% | 0.90 | sentence | Statement walls |
| `headline-large` | 44-51px | 870 | 132% | 0.82 | UPPER | Section openers |
| `headline-medium` | 40-44px | 650 | 132% | 0.95 | sentence | Subseções, callouts |
| `headline-small` | 28-32px | 590 | 100% | 1.05 | sentence | Sub-headlines, perguntas |
| `body-large` | 36-42px | 590 | 100% | 1.17 | sentence | Body em ad/story |
| `body-medium` | 30-35px | 590 | 100% | 1.20 | sentence | Pain points, listas |
| `body-small` | 24-30px | 400 | 100% | 1.17 | sentence | Captions, metadata |
| `label-large` | 26-28px | 540 | 132% | 1.0 | UPPER +10% ls | Tags, eyebrows large |
| `label-medium` | 24px | 540 | 132% | 1.0 | UPPER +12% ls | Pills (Premium, Elite) |
| `label-editorial` | 9-11px | 270 | 132% | 1.0 | UPPER +28% ls | Editorial markers |

### 3.5 Shape

```css
--metta-sys-shape-corner-none:  0px;     /* PROIBIDO em uso normal */
--metta-sys-shape-corner-xs:    4px;     /* chips, badges */
--metta-sys-shape-corner-sm:    8px;     /* inputs, ícones */
--metta-sys-shape-corner-md:    12px;    /* cards padrão */
--metta-sys-shape-corner-lg:    20px;    /* cards grandes, modal */
--metta-sys-shape-corner-xl:    24px;    /* hero cards, breathing room */
--metta-sys-shape-corner-2xl:   32px;    /* área de respiro central */
--metta-sys-shape-corner-full:  999px;   /* CTAs pill, badges */
```

### 3.6 Spacing — 8pt grid

```css
--metta-sys-spacing-1:  4px;    --metta-sys-spacing-2:  8px;
--metta-sys-spacing-3:  12px;   --metta-sys-spacing-4:  16px;
--metta-sys-spacing-5:  24px;   --metta-sys-spacing-6:  32px;
--metta-sys-spacing-7:  48px;   --metta-sys-spacing-8:  64px;
--metta-sys-spacing-9:  96px;   --metta-sys-spacing-10: 128px;
```

### 3.7 Elevation (suaves — mood editorial, não 3D)

```css
--metta-sys-elevation-0: none;
--metta-sys-elevation-1: 0 1px 2px rgba(12, 22, 27, 0.05);
--metta-sys-elevation-2: 0 5px 14px rgba(12, 22, 27, 0.06);
--metta-sys-elevation-3: 0 12px 28px rgba(12, 22, 27, 0.08);
--metta-sys-elevation-4: 0 18px 40px rgba(12, 22, 27, 0.11);
--metta-sys-elevation-5: 0 28px 60px rgba(12, 22, 27, 0.14);
```

> Glow ambient (yellow/teal) **REMOVIDO** em mai/2026. Metta é editorial, não atmosférico.

### 3.8 Motion

```css
--metta-sys-motion-duration-instant: 50ms;
--metta-sys-motion-duration-short:   200ms;
--metta-sys-motion-duration-medium:  300ms;
--metta-sys-motion-duration-long:    500ms;
--metta-sys-motion-duration-x-long:  700ms;

--metta-sys-motion-easing-standard:   cubic-bezier(0.4, 0, 0.2, 1);
--metta-sys-motion-easing-emphasized: cubic-bezier(0.2, 0, 0, 1);
--metta-sys-motion-easing-enter:      cubic-bezier(0, 0, 0.2, 1);
--metta-sys-motion-easing-exit:       cubic-bezier(0.4, 0, 1, 1);
```

> ❌ **PROIBIDO:** bouncy/spring/overshoot, scale > 1.02 em hover, color inversion no press, gradient-shift no hover.

### 3.9 State layers

```css
--metta-sys-state-hover-opacity:   0.08;
--metta-sys-state-focus-opacity:   0.12;
--metta-sys-state-pressed-opacity: 0.16;
```

### 3.10 Layout — safe zones

```css
/* Story 1080×1920 */
--metta-sys-layout-story-safe-x:           51px;
--metta-sys-layout-story-safe-y-top:      308px;
--metta-sys-layout-story-safe-width:      978px;
--metta-sys-layout-story-safe-height:    1303px;

/* Reels */
--metta-sys-layout-reels-safe-y-top:      226px;
--metta-sys-layout-reels-bottom-risk:     618px;
--metta-sys-layout-reels-safe-height:    1076px;

/* Page */
--metta-sys-layout-page-padding-x:       10%;
--metta-sys-layout-page-padding-x-mobile: 6%;
--metta-sys-layout-section-padding-y:    100px;
--metta-sys-layout-content-max-width:    900px;
--metta-sys-layout-grid-gap:             24px;
```

### 3.11 Gradients — todos lineares

```css
--metta-sys-gradient-golden-linear:
  linear-gradient(135deg, var(--metta-ref-palette-yellow-50) 0%, var(--metta-ref-palette-yellow-80) 50%, var(--metta-ref-palette-yellow-90) 100%);

--metta-sys-gradient-night-linear:
  linear-gradient(135deg, var(--metta-ref-palette-night-10) 0%, var(--metta-ref-palette-night-25) 60%, var(--metta-ref-palette-night-40) 100%);

--metta-sys-gradient-light-linear:
  linear-gradient(135deg, var(--metta-ref-palette-night-100) 0%, #E0E6E9 100%);

--metta-sys-gradient-yellow-soft:
  linear-gradient(226deg, #FFC443 10%, var(--metta-ref-palette-yellow-55) 97%);
```

> ❌ **REMOVIDOS:** gradients cônicos (golden-conic, night-conic) e radial-yellow (tom amarromzado). Usar só lineares — controle previsível em qualquer composição.

---

## §4. TIER 3 — Component Tokens

### 4.1 CTA Yellow (primário)

```css
--metta-comp-cta-yellow-container-color:           var(--metta-sys-color-primary);
--metta-comp-cta-yellow-container-color-hover:     var(--metta-sys-color-primary-hover);
--metta-comp-cta-yellow-container-color-pressed:   var(--metta-sys-color-primary-pressed);
--metta-comp-cta-yellow-label-color:               var(--metta-sys-color-on-primary);
--metta-comp-cta-yellow-container-shape:           var(--metta-sys-shape-corner-full);
--metta-comp-cta-yellow-container-padding-x:       var(--metta-sys-spacing-6);
--metta-comp-cta-yellow-container-padding-y:       var(--metta-sys-spacing-4);
--metta-comp-cta-yellow-pressed-scale:             0.97;
```

**Estados:**
- Default: yellow-50
- Hover: yellow-60 (clareia)
- Pressed: yellow-55 + scale(0.97)
- Focus-visible: ring sutil `box-shadow: 0 0 0 2px surface, 0 0 0 4px on-surface-variant` (NÃO outline yellow grosso)

### 4.2 CTA Dark (secundário)

```css
--metta-comp-cta-dark-container-color:             var(--metta-ref-palette-night-10);
--metta-comp-cta-dark-container-color-hover:       var(--metta-ref-palette-night-20);
--metta-comp-cta-dark-label-color:                 var(--metta-ref-palette-night-100);
--metta-comp-cta-dark-container-shape:             var(--metta-sys-shape-corner-full);
```

### 4.3 CTA Light (sobre fundo escuro)

```css
--metta-comp-cta-light-container-color:            var(--metta-ref-palette-night-100);
--metta-comp-cta-light-container-color-hover:      var(--metta-ref-palette-night-95);
--metta-comp-cta-light-label-color:                var(--metta-ref-palette-night-10);
--metta-comp-cta-light-container-shape:            var(--metta-sys-shape-corner-full);
```

### 4.4 Card padrão

```css
--metta-comp-card-container-color:                 var(--metta-sys-color-surface-container-low);
--metta-comp-card-container-shape:                 var(--metta-sys-shape-corner-md);
--metta-comp-card-container-padding:               var(--metta-sys-spacing-5);
--metta-comp-card-elevation:                       var(--metta-sys-elevation-1);
```

### 4.5 Card elevated

```css
--metta-comp-card-elevated-container-color:        var(--metta-sys-color-surface-container-high);
--metta-comp-card-elevated-container-shape:        var(--metta-sys-shape-corner-xl);
--metta-comp-card-elevated-elevation:              var(--metta-sys-elevation-3);
```

### 4.6 Variações de card

5 variações no DS final (card-accent, card-horizontal e outras especulações foram removidas):

| Variação | Função | Background | Border | Notas |
|---|---|---|---|---|
| **Card padrão** | Listas, grids neutros | `surface-container-low` | `outline-variant` | Default |
| **Card elevated** | Hero, featured | `surface-container-high` | none | Elevation 3 |
| **Card stat** | Métricas, números | `surface-container-low` | `outline-variant` | Number 56px yellow primary heavy |
| **Card icon** | Features, capacidades | `surface-container-low` | `outline-variant` | Icon container 44×44 surface-container-high |
| **Card filled** | Callout máximo | `surface-container-highest` (tema-aware) | `outline-variant` | Em dark theme vira `night-25` automaticamente |

Todos com `min-height: 220px`, `padding: 28px`, `gap: 16px`, `corner-md`.

### 4.7 Label pill

```css
--metta-comp-label-pill-container-color:           transparent;
--metta-comp-label-pill-container-shape:           var(--metta-sys-shape-corner-full);
--metta-comp-label-pill-outline-color:             var(--metta-ref-palette-night-90);
--metta-comp-label-pill-outline-width:             1px;
--metta-comp-label-pill-padding-x:                 14px;
--metta-comp-label-pill-padding-y:                 8px;
--metta-comp-label-pill-label-color:               var(--metta-sys-color-on-surface-variant);
--metta-comp-label-pill-label-font-weight:         540;
--metta-comp-label-pill-label-font-stretch:        132%;
--metta-comp-label-pill-label-letter-spacing:      0.12em;
--metta-comp-label-pill-label-transform:           uppercase;
```

Variante filled: background `primary`, text `on-primary`, sem border.

### 4.8 Headline display — 5 variações

1. **Uppercase + accent yellow** (canônico) — peso 870, palavra-chave em primary
2. **Sentence case + accent yellow** — peso 650, sentence case, palavra-chave em primary
3. **Mixed weight (Heavy + Light)** — heavy 870 + algumas palavras em light 270, mesma cor
4. **Italic accent (sem cor)** — palavra-chave em itálico heavy, sem mudar cor
5. **Background marker (yellow highlight)** — palavra-chave com bg primary + on-primary inline

### 4.9 Yellow band divider

```css
--metta-comp-yellow-band-color:                    var(--metta-sys-color-primary);
--metta-comp-yellow-band-height:                   6px;
```

---

## §5. SYS Color Roles — Dark theme

```css
[data-theme="dark"] {
  --metta-sys-color-primary:               var(--metta-ref-palette-yellow-50);
  --metta-sys-color-on-primary:            var(--metta-ref-palette-night-10);
  --metta-sys-color-primary-hover:         var(--metta-ref-palette-yellow-60);
  --metta-sys-color-primary-pressed:       var(--metta-ref-palette-yellow-55);
  --metta-sys-color-primary-container:     var(--metta-ref-palette-night-20);
  --metta-sys-color-on-primary-container:  var(--metta-ref-palette-yellow-90);

  --metta-sys-color-surface:                  var(--metta-ref-palette-night-10);
  --metta-sys-color-surface-bright:           var(--metta-ref-palette-night-25);
  --metta-sys-color-surface-dim:              var(--metta-ref-palette-night-5);
  --metta-sys-color-surface-container-lowest: var(--metta-ref-palette-night-5);
  --metta-sys-color-surface-container-low:    var(--metta-ref-palette-night-10);
  --metta-sys-color-surface-container:        var(--metta-ref-palette-night-15);
  --metta-sys-color-surface-container-high:   var(--metta-ref-palette-night-20);
  --metta-sys-color-surface-container-highest:var(--metta-ref-palette-night-25);
  --metta-sys-color-on-surface:               var(--metta-ref-palette-night-100);
  --metta-sys-color-on-surface-variant:       var(--metta-ref-palette-night-85);

  --metta-sys-color-outline:                  rgba(255, 255, 255, 0.20);
  --metta-sys-color-outline-variant:          rgba(58, 109, 137, 0.28);

  --metta-sys-color-inverse-surface:    var(--metta-ref-palette-night-99);
  --metta-sys-color-inverse-on-surface: var(--metta-ref-palette-night-10);
  --metta-sys-color-inverse-primary:    var(--metta-ref-palette-yellow-30);
}
```

---

## §6. Aliases bridge — retrocompatibilidade

Tokens v1 mantidos ativos via aliases pra não quebrar código legado. **Em código novo, prefira sys/comp.**

```css
/* Brand v1 */
--metta-yellow:        var(--metta-sys-color-primary);
--metta-yellow-alt:    var(--metta-ref-palette-yellow-55);
--metta-yellow-light:  var(--metta-ref-palette-yellow-60);
--metta-yellow-soft:   var(--metta-ref-palette-yellow-95);
--metta-blue-night:    var(--metta-ref-palette-night-10);
--metta-blue-deep:     var(--metta-ref-palette-night-5);
--metta-white:         var(--metta-ref-palette-night-100);
--metta-ice:           var(--metta-ref-palette-night-99);
--metta-ice-blue:      var(--metta-ref-palette-night-95);
--metta-bluegray:      var(--metta-ref-palette-night-40);

/* Markdown v1 names */
--yellow-primary:    var(--metta-sys-color-primary);
--blue-night:        var(--metta-ref-palette-night-10);
--white:             var(--metta-ref-palette-night-100);
--ice:               var(--metta-ref-palette-night-99);
--blue-gray:         var(--metta-ref-palette-night-40);

/* Semantic v1 */
--fg-1:              var(--metta-sys-color-on-surface);
--fg-2:              var(--metta-ref-palette-night-40);
--bg-1:              var(--metta-sys-color-surface);
--bg-2:              var(--metta-sys-color-surface-container-low);
--accent:            var(--metta-sys-color-primary);

/* Radii v1 */
--radius-md:    var(--metta-sys-shape-corner-md);
--radius-pill:  var(--metta-sys-shape-corner-full);

/* Spacing v1 */
--space-5: var(--metta-sys-spacing-5);

/* Shadows v1 */
--shadow-sm:    var(--metta-sys-elevation-1);
--shadow-md:    var(--metta-sys-elevation-2);
--shadow-lg:    var(--metta-sys-elevation-3);
```

---

## §7. REGRAS DURAS (PRD §6.4)

❌ **PROIBIDO em qualquer aplicação:**
- Glow no logo (`box-shadow`, `inset shadow`, `filter: drop-shadow` com glow amarelo)
- Blur pesado em fotos (>20px)
- Sombras no logo
- Outline/ghost no logo
- Recriar/redesenhar o logo em SVG/CSS — **sempre baixar do Drive**
- Fonte que não seja SF Pro Variable (primária) ou Zalando Sans Expanded (fallback oficial pra PPTX/Google Slides desde 2026-05-12 — Roboto Flex deprecated)
- Tagline "INTELIGÊNCIA COMERCIAL" sem tracking de 9%+ em UPPERCASE
- Tier badges (ELITE/EXCLUSIVE/PREMIUM) sem pill com border + tracking 12%
- Gradients cônicos ou radial amarromzado
- Bouncy/spring motion
- Glow ambient atmosférico (atmosférico não é Metta)

---

## §8. Mudanças vs v1

### Estrutural
- Reorganização em 3 tiers (ref/sys/comp) seguindo M3
- Naming consistente com tier prefix
- Tema dark explícito via `[data-theme="dark"]`

### Adicionado
- Paleta tonal completa Yellow (10 tons) e Night (17 tons)
- Roles inversos `on-*` (on-primary, on-surface, etc.)
- Surface containers escalonados (lowest/low/medium/high/highest)
- Typescale com 5 sub-tokens cada
- Elevation 0-5 com valores suaves
- Motion como tokens
- State layer opacity tokens
- Component tokens pra CTA Yellow/Dark/Light, Card padrão/elevated/stat/icon/filled, label-pill, headline display, breathing-room, yellow-band

### Removido (escopo Metta institucional apenas)
- Paletas Steel e Coral (ficam no DS Tiago Alves separado)
- Roles `secondary` e `tertiary` (sem cores secondary/tertiary na Metta)
- Neutrals específicos: near-black, teal-dark, teal-mid, overlay-gray, twitter-dark, dark-content, light-bg, body-gray (substituídos pela paleta night)
- Gradients cônicos (golden-conic, night-conic) → linear
- Gradient yellow-radial (tom amarromzado) → removido
- Glow ambient (yellow + teal) → removido (atmosférico não é Metta)
- Card border-accent variation
- Headline outline text variation
- Headline underline yellow accent variation

### Compatibilidade
- 100% dos tokens v1 essenciais funcionando via §6 aliases bridge

---

## §10. Motion patterns — reveal, magnetic, counter, kenburns

> Adicionado em 2.1 (2026-05-03). Patterns consagrados na LP Aplicação SMTM v5, agora ready-to-use no DS.

### 10.1 Setup (1× por página)

```html
<!-- No <head>: -->
<script>document.documentElement.classList.add('js');</script>

<!-- Antes do </body>: -->
<script src="path/to/system-source/motion.js"></script>
```

`motion.js` auto-inicializa todos os patterns abaixo via `data-*` attributes.

### 10.2 Block reveal (`data-reveal`)

Aparição cinematográfica — fade + slide(40px) + blur(10px) → 0 em 1100ms easing emphasized.

```html
<div data-reveal>
  <h2>Meu título</h2>
  <p>Conteúdo do bloco</p>
</div>
```

**Variant soft** (sem blur, slide menor 20px, 850ms — pra parágrafos longos onde blur prejudica leitura):

```html
<p data-reveal="soft">Texto longo que precisa ser legível durante o reveal...</p>
```

**Stagger entre múltiplos elementos:**

```html
<div data-reveal style="--reveal-delay: 0ms">Primeiro</div>
<div data-reveal style="--reveal-delay: 80ms">Segundo</div>
<div data-reveal style="--reveal-delay: 160ms">Terceiro</div>
```

Ou via CSS com `nth-child`:

```css
.cards-grid > [data-reveal]:nth-child(2) { --reveal-delay: 80ms; }
.cards-grid > [data-reveal]:nth-child(3) { --reveal-delay: 160ms; }
```

### 10.3 Magnetic CTA (`data-magnetic`)

Mouse atrai botão até 18% do delta. Funciona em qualquer elemento — recomendado em CTAs primários.

```html
<a class="cta-yellow" data-magnetic href="#">Aplicar</a>
```

Auto-desativado em touch devices (`pointer: coarse`) e `prefers-reduced-motion`.

### 10.4 Counter animation (`data-counter`)

Anima de 0 ao valor final em 1.8s easing decelerate, dispara quando 50% do elemento entra na viewport.

```html
<span data-counter="47" data-prefix="+" data-suffix="%">+0%</span>
<span data-counter="23" data-decimal="1" data-suffix="×">0×</span>
<span data-counter="5" data-prefix="R$ " data-suffix=" bi+">R$ 0 bi+</span>
```

**Atributos:**
- `data-counter` — valor final (obrigatório)
- `data-prefix` — antes do número (opcional)
- `data-suffix` — depois do número (opcional)
- `data-decimal` — casas decimais (default 0)
- `data-duration` — ms (default 1800)

### 10.5 Comp tokens

```css
--metta-comp-reveal-duration:        1100ms;  /* block reveal */
--metta-comp-reveal-duration-soft:    850ms;  /* soft variant */
--metta-comp-reveal-distance:          40px;  /* translateY block */
--metta-comp-reveal-distance-soft:     20px;  /* translateY soft */
--metta-comp-reveal-blur:              10px;  /* filter blur block */
```

Override por componente substituindo o token localmente.

### 10.6 Keyframes

```css
@keyframes metta-reveal-rise        { /* fade + slide + blur */ }
@keyframes metta-reveal-rise-soft   { /* fade + slide */ }
@keyframes metta-kenburns           { /* zoom + pan loop pra hero photos */ }
```

### 10.7 A11y

`@media (prefers-reduced-motion: reduce)` desativa todas as animações automaticamente. Magnetic e counter respeitam via JS. **Sempre incluído no comportamento default** — boa prática obrigatória.

### 10.8 Quando usar cada pattern

| Pattern | Quando usar |
|---|---|
| **Block reveal** | Cards, headlines, blocos visuais com peso |
| **Soft reveal** | Parágrafos longos, ledes, textos onde blur prejudica leitura |
| **Magnetic CTA** | Botões primários (1-2 por página) — não em links secundários |
| **Counter** | Estatísticas-âncora (1-3 por página) — não exagerar |
| **Kenburns** | Foto hero único — não em múltiplas imagens (cansativo) |

---

## §11. Changelog

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-03 | **2.1** | Motion patterns adicionados ao DS — reveal, magnetic, counter, kenburns. Helper `motion.js` auto-init via `data-*`. Comp tokens `--metta-comp-reveal-*` |
| 2026-05-03 | **2.0 normativo** | Promovido após curadoria — escopo só Metta, gradients lineares, elevation suave, sem glow, +CTA Light, 5 variações de card, 5 variações de headline |
| 2026-05-03 | 2.0-rc1 | Refator 3-tier proposto |
| 2026-04-28 | 1.0 | Single-tier flat (legacy) |

---

## 🔗 Documentos relacionados

- [[Metta - PRD Identidade Visual]] — regras de aplicação, hierarquia
- [[lp-patterns-modernos]] — curadoria UI/UX premium pra LPs
- [[Skill - Agente de Design]] — doc humana navegável da skill
- Skill executável: `.claude/commands/design-metta.md`
- CSS canônico: `system-source/colors_and_type.css`
- Site preview interativo: `Branding Metta 2.0/output/design-system-v2/index.html`
- v1 arquivado: `_archive/refactor-2026-05-03-v2/metta-tokens-v1.md.bak`
