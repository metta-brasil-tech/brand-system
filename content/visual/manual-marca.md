---
title: "Manual de Marca — Página do Design System Figma"
aliases:
  - "Manual de Marca DS"
  - "Brand Manual Page"
tags:
  - marca/metta
  - status/vigente
  - tema/design
  - tema/marca
  - tipo/referencia
  - tipo/figma-spec
formato_consumo: contexto-skill
prioridade_carregamento: media
versao: "1.0"
sucedido_por: null
complementar_com: "[[Metta - Plataforma de Marca]]"
summary: "Spec da página '📖 Manual de Marca' criada dentro do arquivo Figma Design System (file key 0zEMoFMq6FlIXbANZs9LCG). Sintetiza visualmente a estratégia, posicionamento e comunicação Metta em 7 seções, ancorada nos docs canônicos do vault."
created: 2026-05-03
updated: 2026-05-03
---

# Manual de Marca — Página do Design System Figma

> Página visual dentro do **Design System Metta** (arquivo Figma) que sintetiza, em formato editorial navegável, a estratégia, posicionamento e comunicação da marca. Não substitui os docs canônicos do vault — é uma **camada de apresentação visual** desses docs, integrada ao DS.

## ⚡ TL;DR

- **Localização:** Figma · Design System · página `📖 Manual de Marca` (sob seção `───── ESTRATÉGIA ─────`).
- **File key:** `0zEMoFMq6FlIXbANZs9LCG` · **Page ID:** `429:3` · **Root frame:** `429:4`
- **Dimensões:** 2040×17162px · vertical scroll · 8 seções
- **Padrão visual:** alinhado ao DS (BG `#FAFCFD`, padding 80, header Zalando Sans Expanded Heavy 64 + barra amarela 120×6, fontes Inter variants).
- **Conteúdo:** TOC + §1 Essência · §2 Posicionamento · §3 Estratégia · §4 Personalidade · §5 Comunicação · §6 Manifesto · §7 Aplicação.
- **Fonte de verdade:** docs do vault — esta página é projeção visual, não substitui [[Metta - Plataforma de Marca]], [[Metta - Identidade Verbal]], [[Metta - Manifesto de Marca]].

## 🎯 Quando consultar este doc

- Vai **atualizar** a página Manual de Marca no Figma — checar specs antes de editar.
- Onboarding de pessoa nova ao DS — explicar o que é a página e onde fica.
- Decisão de **propagar** mudança de plataforma de marca pro DS visual — ver mapeamento doc → seção.
- Vai criar página visual semelhante em outro arquivo (Documentos, apresentação) — usar como referência de estrutura.

## §1 Estrutura da página

### §1.1 Localização no DS

A página foi inserida entre **Changelog & Versioning** e **FUNDAMENTOS**, dentro de uma nova seção divisória `───── ESTRATÉGIA ─────`. A ordem editorial reflete que a estratégia precede a expressão visual:

```
📘 Capa
📋 Changelog & Versioning
───── ESTRATÉGIA ─────                  ← novo divisor
📖 Manual de Marca                       ← novo
───── FUNDAMENTOS ─────
🎨 Cor · 🔤 Tipografia · 📐 Espaçamento
───── MARCA ─────
🅼 Logos · 🖼️ Fundos · 🔣 Ícones
───── COMPONENTES ─────
🔘 Botões · 🧭 Cabeçalho & Rodapé
───── MODELOS ─────
📢 Ads · 🎞️ Carrosséis · 🖨️ Posters · 🌐 LPs
───── REFERÊNCIA ─────
🧪 Playground · Banco — Fotos Tiago
```

### §1.2 Seções (top → down) ^estrutura-secoes

| § | Seção | BG | Origem do conteúdo |
|---|---|---|---|
| 0 | Header + Sumário | `#0C161B` (noite) | título "Manual de Marca", TOC com 7 links |
| 1 | Essência | `#FAFCFD` (branco gelo) | [[Metta - Plataforma de Marca]] §02 |
| 2 | Posicionamento | `#EBF3F7` (gelo azul) | [[Metta - Plataforma de Marca]] §01–§03 |
| 3 | Estratégia | `#FAFCFD` | [[Metta - Plataforma de Marca]] §04 + [[Metta - Manifesto de Marca]] |
| 4 | Personalidade | `#EBF3F7` | [[Metta - Plataforma de Marca]] §05 + [[Metta - Identidade Verbal]] |
| 5 | Comunicação | `#FAFCFD` | [[Metta - Identidade Verbal]] (tom, vocabulário, glossário, mensagens) |
| 6 | Manifesto | `#0C161B` (noite) | [[Metta - Manifesto de Marca]] (versão condensada) |
| 7 | Aplicação | `#FAFCFD` | quando consultar + ponte pras outras páginas do DS |

Alternância de BG (`#FAFCFD` ↔ `#EBF3F7` ↔ `#0C161B`) cria ritmo visual e separa seções sem precisar de divisores explícitos.

## §2 Padrão visual aplicado

Toda página segue **o mesmo sistema** dos outros docs do DS:

- **Largura:** 2040px (idêntica às páginas Cor, Tipografia, etc.)
- **Padding seção:** 80px lateral, 96–160px vertical
- **Header de seção:** kicker §X (16px Expanded Medium, amarelo, tracking 8%) → título 64px Expanded Heavy → barra amarela 120×6 → lead 22px Regular muted
- **Cards:** radius 24, padding 40–48, stroke `#E0EBF2` ou `#EBF2F7`
- **Cards-âncora:** radius 32, padding 64, fill noite ou amarelo
- **Tipografia:**
  - Display Hero: Zalando Sans Expanded Heavy 110–130
  - Title: Zalando Sans Expanded Heavy 64
  - Subtitle: Zalando Sans Expanded Heavy 36
  - Card title: Zalando Sans Expanded Bold 24–28
  - Body: Inter 17–22, line-height 145–155%
  - Kicker: Zalando Sans Expanded Medium 13–16, letter-spacing 8–12%

## §3 Mapeamento conteúdo Figma → docs vault

Cada seção é uma **projeção visual** de um doc canônico. Ao atualizar a fonte, propagar pra Figma:

| Mudou no doc... | Atualizar na seção... |
|---|---|
| Propósito, visão, promessa, posicionamento, valores, drivers (em [[Metta - Plataforma de Marca]]) | §1 Essência · §2 Posicionamento · §3 Estratégia · §4 Personalidade |
| Pilares de tom, vocabulário, glossário, mensagens-chave (em [[Metta - Identidade Verbal]]) | §4 Personalidade (traços) · §5 Comunicação |
| Tagline, recusas, crenças, futuro, CTA-mantra (em [[Metta - Manifesto de Marca]]) | §6 Manifesto |
| Era Jurássica / antagonista (em [[Metta - Manifesto de Marca]] PARTE II) | §3 Estratégia (bloco antagonista) |
| Reason to Believe, 3 diferenciais (em [[Metta - Plataforma de Marca]] §03) | §2 Posicionamento (bloco RTB) |

## §4 Conteúdo por seção

### §4.1 Header
- **Título:** "Manual de Marca" (130px Expanded Heavy, 2 linhas)
- **Sub:** "Estratégia, posicionamento e comunicação da Metta — o porquê, o pra quem e o como falamos com o mercado."
- **Sumário:** 7 itens com kicker §, nome, descrição

### §4.2 Essência
- **Propósito duplo** em card noite com 2 colunas (01/02 amarelas + frase)
- **Visão de futuro** + **Promessa de marca** lado a lado (visão branca, promessa amarela)

### §4.3 Posicionamento
- **Declaração de posicionamento** em card branco grande (56px)
- **Para quem · Insight · Tensão** em 3 cards
- **Reason to Believe** em 3 cards escuros (Fazedoria · Ciência · Garantia)

### §4.4 Estratégia
- **6 valores** em grid 3×2 (cards brancos com numeração amarela)
- **Antagonista** em card noite com tagline "Era Jurássica da Gestão Comercial." e 4 inimigos (Gurus · Consultorias · Tech sem processo · Motivação como método)

### §4.5 Personalidade
- **Arquétipos** Sábio + Governante (2 cards lado a lado, cada um com pills de atributos)
- **4 traços** em grid 2×2 (cada um com pill anti-padrão "Não é arrogante/genérica/pedante/vaga")
- **Atitude de fala** (FALA COMO ✓ × NÃO FALA COMO ✗)

### §4.6 Comunicação
- **5 pilares de tom** em faixa horizontal (Direta · Confiante · Humana · Especialista · Acessível)
- **Vocabulário** em tabela "USE → EVITE" (8 pares, com strikethrough)
- **Glossário** em grid 3×2 (Inteligência Comercial · Ciência Comportamental · Meta · Previsibilidade · Fazedoria · Ecossistema)
- **Mensagens-chave** em 6 cards escuros (Diferencial · Leveza · Método · Ciência · Público · Mercado)

### §4.7 Manifesto (alta voltagem visual)
- **Tagline gigante** "Para os que não aceitam o amadorismo." (110px sobre fundo noite)
- **3 colunas** (Nós nos recusamos · Nós acreditamos · Nós existimos para)
- **Visão de futuro** card destacado ("CNPJ patrocina a plenitude do CPF")
- **CTA-mantra** sobre fundo amarelo (64px, "Se você acredita que resultado é consequência de método, você é um de nós.")

### §4.8 Aplicação
- **6 casos de uso** (brief de copy, decisão estratégica, headline/hook, onboarding, reescrita, campanha)
- **Hierarquia em conflito** (5 níveis de prioridade entre docs)
- **Continuar explorando** (ponte pras outras seções do DS)
- **Footer:** "METTA · Manual de Marca · v1.0" + "Bater meta não é sorte. É método."

## §5 Como editar / propagar mudanças

### §5.1 Edição manual no Figma
- Abrir o arquivo Design System
- Página `📖 Manual de Marca`, root frame `Manual de Marca` (id `429:4`)
- Cada seção é um child do root (auto-layout vertical, stretch), independente
- Estilo segue tokens documentados em [[metta-tokens]]

### §5.2 Edição via Plugin API
- Snippets canônicos em [[figma-plugin-api]]
- Para textos: sempre `await figma.loadFontAsync(fontName)` e setar `fontName` ANTES de `characters` (gotcha já documentado)
- Para cards: helper `makeCard({ width, fill, padding, gap, stroke, cornerRadius, grow })`

### §5.3 Quando recriar do zero
Se mudar significativamente algum doc canônico (ex.: nova plataforma de marca), considerar recriar a página inteira via script para garantir consistência. O script de criação está versionado nesta sessão (Claude Code · 2026-05-03).

## §6 Decisões de arquitetura

- **Por que dentro do DS, não no Metta Brand?** O user pediu explicitamente "dentro do design system". Faz sentido: estratégia precede expressão visual, e ter a marca completa em um lugar ajuda quem usa o DS pra criar peças (o "porquê" mora ao lado do "como").
- **Por que 1 página única, não múltiplas?** Manuais de marca modernos navegam vertical; uma única página dá leitura linear coerente e mantém o padrão das outras páginas do DS (Cor tem 2033px, esta tem 17162 — mesmo conceito, escala maior).
- **Por que seção §6 em fundo escuro?** Manifesto pede alta voltagem dramática — o contraste com as seções anteriores cria pausa cinematográfica antes do CTA-mantra.

## §7 Referências usadas na construção

Pesquisa web (2026-05) confirmou estrutura padrão de brand books modernos:
- **3 partes clássicas:** About the Brand (essência/posicionamento/personalidade) → Visual Identity → Touchpoints
- **Seções essenciais:** Mission, Vision, Values, Positioning, Purpose, Tone of Voice, Brand Personality, Manifesto, Audience, Voice Pillars
- **Esta página cobre:** parte 1 inteira + Manifesto. Parte 2 (Visual Identity) já está nas outras páginas do DS. Parte 3 (Touchpoints) está nas seções MODELOS e COMPONENTES.

Fontes consultadas:
- Akrivi · "Comprehensive Brand Guidelines Examples in 2026"
- Map and Fire · "Brand Strategy, Brand Identity, Brand Archetypes, Tone of Voice"
- Digital Silk · "Brand Book Design: A Detailed Guide For 2026"
- Figma Community · "Massive Brand Guideline Template I 2026"

---

## 🔗 Documentos Relacionados

**Fonte do conteúdo:**
- [[Metta - Plataforma de Marca]]
- [[Metta - Identidade Verbal]]
- [[Metta - Manifesto de Marca]]
- [[Metta - Brandbook]]

**Tokens e componentes (padrão visual usado):**
- [[metta-tokens]]
- [[metta-components]]
- [[metta-ui-kit]]
- [[Metta - PRD Identidade Visual]]

**Index do DS:**
- [[README]] — índice da pasta design

**Brand System:**
- [[brand-system-spec]] — mini-app de marca consolidado (mar­ca + audiência + verbal + visual + direção de arte + metodologia + produtos)
