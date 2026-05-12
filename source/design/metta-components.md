---
title: "Metta — Componentes Visuais Recorrentes"
tags:
  - marca/metta
  - status/normativo
  - tema/design
  - tipo/componentes
summary: "Mini-componentes reutilizáveis: CTAs, separadores, watermarks, blobs, frames. Carregar quando construir peças (snippets prontos)."
created: 2026-04-28
updated: 2026-04-28
---

# Metta — Componentes Visuais Recorrentes

> **Status:** NORMATIVO. Componentes validados em uso. Atenção aos itens marcados [DEPRECATED].
> **Tokens canônicos:** ver [[metta-tokens]].

---

## §1. Botão CTA (Call to Action)

```css
/* CTA Pill Padrão (amarelo) — preferido */
.cta-pill {
  background: #FFBE18;
  color: #0C161B;
  border-radius: 82-126px; /* full rounded */
  padding: 27-41px 50-77px;
  font-weight: 700;
  font-stretch: 132%; /* Expanded Bold */
  font-size: 34-42px;
  letter-spacing: 1%;
  text-transform: uppercase;
}

/* CTA Retangular (carousel/cards) */
.cta-rect {
  background: #FFBE18;
  border-radius: 12-14px;
  padding: 17px 50px;
}

/* CTA Branco (variante) */
.cta-white {
  background: #FFFFFF;
  color: #0C161B;
  border-radius: 72px;
}

/* CTA Escuro (sobre fundo dourado) */
.cta-dark {
  background: #0C161B;
  color: #FFFFFF;
  border-radius: 72px;
}
```

> ❌ **DEPRECATED:** `cta-glow` com `box-shadow: 0px 45px 108px rgba(255, 190, 24, 0.19)` — viola PRD §6.4.

---

## §2. Separadores

```css
/* Sobre fundo escuro */
.divider-light { width: 100%; height: 1px; background: rgba(255,255,255,0.2); }

/* Sobre fundo claro */
.divider-dark { width: 100%; height: 1px; background: rgba(12,22,27,0.12); }
```

---

## §3. ~~Efeitos de Blur/Glow~~ [DEPRECATED — PRD §6.4]

Todos os efeitos abaixo foram **proibidos** pelo PRD §6.4. Documentados aqui apenas pra referência histórica:

- `blur-shadow` (filter: blur(157px))
- `glass-card` (backdrop-filter: blur(43.5px))
- `teal-glow` (filter: blur(198px))
- `dark-vignette` (filter: blur(199px))
- `soft-glow` (filter: blur(534px))

**Substituições aceitas:**
- Atmosfera escura → fundo `#0C161B` sólido + tipografia hierárquica
- Glassmorphism → card `#0C161B` com border `rgba(255,255,255,0.12)`
- Glow → contraste de cor + escala tipográfica

---

## §4. Overlays sobre Fotos (apenas funcionais, sem blur)

```css
/* Overlay escuro sólido */
.overlay-heavy { background: rgba(0,0,0,0.6); }

/* Overlay médio */
.overlay-medium { background: rgba(0,0,0,0.4); }

/* Gradiente fade-to-black (TÉCNICA APROVADA) */
.fade-to-black {
  background: linear-gradient(180deg, transparent 55%, rgba(13,12,12,0.52) 69%, rgba(13,12,12,1) 100%);
}

/* Vinheta radial */
.vignette {
  background: radial-gradient(circle at 50% 31%, rgba(4,11,15,0) 25%, rgba(4,11,15,1) 100%);
}
```

> ❌ **DEPRECATED:** `overlay-frost` com `filter: blur(157px)`.

---

## §5. ~~Elipses Decorativas Geométricas~~ [DEPRECATED — PRD §6.4]

Anéis decorativos `border: 6385px solid` foram removidos. Substituir por composição editorial pura.

---

## §6. Watermark Tipográfico

```css
/* Texto gigante como pattern de fundo */
.typo-watermark {
  font-size: 295px;
  font-weight: 650; /* Expanded Semibold */
  font-stretch: 132%;
  color: #0C161B;
  line-height: 0.87em;
  letter-spacing: -1%;
  overflow: hidden;
  /* Posicionado com offset negativo pra ficar parcialmente visível */
}
```

---

## §7. Ghost Watermark "metta"

```css
.ghost-watermark {
  font-size: 200px;
  font-weight: 870; /* Expanded Heavy */
  font-stretch: 132%;
  color: #1A2A35; /* dark on dark, baixa opacidade */
  position: absolute;
  bottom: -20px;
  letter-spacing: -2%;
  text-transform: lowercase;
  overflow: hidden;
  opacity: 0.15;
}
```

> ⚠️ Aplicar SOMENTE no wordmark "metta" textual (não no logo oficial). Logo oficial NUNCA recebe ghost (PRD §6.4).

---

## §8. Wordmark Fragment (Partial Crop)

Large "metta", "me", or "etta" em `#FFBE18` bleeding off bottom edge of frame. Brand-recall device em closing slides. Tamanho: 180-250px, Expanded Heavy (870), lowercase.

---

## §9. Circular Image Frame

```css
.circular-photo-frame {
  width: 70%;
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  position: absolute;
  right: -5%;
}
```

---

## §10. ~~Concentric Arc Rings~~ [DEPRECATED — PRD §6.4]

Anéis concêntricos low-opacity foram removidos. Substituir por gradient sutil.

---

## §11. Organic Yellow Blob

```css
.yellow-blob {
  background: radial-gradient(ellipse at 40% 30%, #FFC531, #FFBE18, #F5A623);
  border-radius: 40% 60% 55% 45% / 50% 40% 60% 50%;
  width: 45%;
  height: 80%;
  position: absolute;
  right: 0;
}
```

---

## §12. Torn Paper Edge

Ripped/torn paper texture em carousel slide edges. White tear on dark bg, dark tear on yellow bg. Transition device entre carousel slides.

---

## §13. Yellow Transition Band

Horizontal yellow (`#FFBE18`) band (~8-10px ou ~40-60px) spanning full width. Contém logo + label. Separa photo zone de text zone.

---

## §14. Ticker/Pattern Header

Horizontal strip com repeated "metta | 22/30 | metta" pattern. Regular Book (400), ~13px. Pra series content.

---

## §15. Navigation Arrow Circle

```css
.nav-arrow {
  width: 32px;
  height: 32px;
  border: 1px solid currentColor;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
```
Carousel next-slide indicator. Bottom-right position.

---

## §16. Chat UI Mockup

Simulated WhatsApp/iMessage interface: speech bubble + input bar com Metta avatar + "escrevendo..." indicator. Pra conversational framing.

---

## §17. Pill Tags (Services/Navigation)

```css
.pill-tag {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.3);
  font-size: 11px;
  font-weight: 540; /* Expanded Medium */
  font-stretch: 132%;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
```
Pra: "LIVROS", "TREINAMENTOS", "FORMAÇÕES", "MENTORIA", "CONSULTORIA"

---

## 🔗 Relacionados
- [[metta-tokens]] — cores, tipografia
- [[Metta - PRD Identidade Visual]] — §6.4 efeitos proibidos (regras absolutas)
- [[figma-plugin-api]] — versões dos componentes em Plugin API
