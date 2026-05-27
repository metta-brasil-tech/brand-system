---
title: "Metta — PRD Identidade Visual"
aliases:
  - "PRD Visual"
  - "Manual Visual Metta"
tags:
  - marca/metta
  - status/normativo
  - tema/design
  - tipo/identidade
  - tipo/manual
summary: "Specs técnicas: logo, paleta, tipografia, tokens. Fonte de verdade absoluta — vence skills e memórias em conflito."
created: 2026-04-10
updated: 2026-04-28
---
# PRD - Identidade Visual Metta
## Product Requirements Document para Agente de Design

---

## §0. Como ler este documento

> ⚠️ Este PRD é a **fonte de verdade absoluta** do design system Metta. Em conflito com qualquer outro documento (skills, memórias, catálogos), o PRD vence.

### Hierarquia interna (do mais forte ao mais fraco)

1. **§6.4 Efeitos proibidos** — REGRA ABSOLUTA, nunca quebrar (glow, blur pesado, glassmorphism, anéis, ghost no logo)
2. **§2 Logotipo + §6 Elementos gráficos** — NORMATIVO, regras de aplicação obrigatórias
3. **§3 Paleta + §4 Tipografia** — NORMATIVO, ver tokens canônicos em [[metta-tokens]]
4. **§5 Arquitetura de marca + §7 Fotografia + §8 Aplicações + §9 Consistência** — NORMATIVO, padrões a seguir
5. **§10 Tokens** — REFERENCE (consolidados em [[metta-tokens]])
6. **§11 Checklist** — NORMATIVE (validação obrigatória)
7. **§12 Biblioteca de Assets** — REFERENCE (catálogo Drive, ver [[metta-logos]])
8. **§13 Composições editoriais** — REFERENCE (descreve a fonte/figma — não cria regra nova; conflita com §6.4? §6.4 vence)

### Em conflito interno

- Regra mais alta na hierarquia vence
- §13 (REFERENCE) descreve o que **existe** na fonte; §6.4 (NORMATIVE) descreve o que **deve existir**. Se §13 documenta um efeito proibido por §6.4, §13 está descrevendo design legado a ser remediado, não autorizando.

### Documentos relacionados

- [[metta-tokens]] — tokens consolidados (cores, tipografia, radii, spacing, shadows, semantic)
- [[metta-ui-kit]] — componentes editoriais JSX (Header, SectionOpener, QuoteBlock, etc.)
- [[metta-components]] — componentes CSS atômicos (CTAs, watermarks, blobs)
- [[metta-logos]] — IDs Drive + mapeamento local SVG
- [[figma-plugin-api]] — snippets de execução
- [[Skill - Agente de Design]] — doc humana da skill executável
- Skill executável: `.claude/commands/design-metta.md`
- **Source canônico:** `system-source/` — assets, CSS, fonts, ui_kit JSX, previews (importado do Metta Design System.zip Apr/2026)

### Convenção de tags

- `[NORMATIVE]` — regra a seguir; conflito = peça rejeitada
- `[REFERENCE]` — descritivo; usar como guia, não como regra
- `[DEPRECATED]` — descontinuado; não aplicar; substituir per remediação documentada

---

## 1. Sobre a Marca [NORMATIVE]

### Missao
**"Profissionalizar o mercado de gestao comercial no Brasil."**
Em outras palavras: extinguir o jeito jurassico de se fazer gestao comercial e bater meta no Brasil.

### Posicionamento
**"O ecossistema de inteligencia comercial para empresarios."**

### Proposta de Valor
Solucoes para pessoas e empresas baterem metas de forma mais leve, facil e sustentavel.

### Tagline do Logo
**INTELIGENCIA COMERCIAL** (sempre acompanha o logotipo em versoes completas)

---

## 2. Logotipo [NORMATIVE]

### 2.1 Estrutura do Logo
O logotipo Metta e composto por:
- **Simbolo (Icone)**: Elemento geometrico formado por arcos concentricos e circulos, nas cores amarela (#FFBE18) e variantes. Composto por sub-elementos: "C Menor", "C Maior", "Arco Menor" e "Arco Maior".
- **Wordmark**: Tipografia customizada "METTA" baseada na fonte Inter, com ajustes especificos:
  - **Cantos arredondados** nas letras
  - **Adaptacao da letra T** (design custom)
  - **Ajuste de kerning** entre caracteres
- **Tagline**: "INTELIGENCIA COMERCIAL" posicionada ao lado ou abaixo do wordmark, separada por uma linha vertical

### 2.2 Versoes do Logo
| Versao | Uso | Fundo |
|--------|-----|-------|
| Logo completo (simbolo + wordmark + tagline) | Uso principal | Fundo escuro (#0C161B) ou claro (#FFFFFF) |
| Logo horizontal (simbolo + wordmark) | Uso secundario | Ambos |
| Simbolo isolado | Favicon, icones, espacos reduzidos | Ambos |
| Wordmark isolado | Aplicacoes especificas | Ambos |

### 2.3 Versoes por Tamanho
- **Grande**: Logo completo com todos os elementos (sem sombra/glow — apenas o arquivo oficial do Drive)
- **Medio**: Simbolo + wordmark + tagline em linha
- **Pequeno**: Simbolo + wordmark compacto
- **Minimo**: Apenas simbolo

### 2.4 Cores do Logo
- **Sobre fundo escuro (#0C161B)**: Simbolo em amarelo (#FFBE18/#FFB618), wordmark em branco (#FFFFFF)
- **Sobre fundo claro (#FFFFFF)**: Simbolo em amarelo (#FFBE18), wordmark em azul noite (#0C161B)
- **Sobre fundo amarelo (#FFBE18)**: Wordmark em azul noite (#0C161B)

### 2.5 ~~Efeitos do Logo~~ [REMOVIDO]
~~Versao com glow: `box-shadow: inset 0px 0px 43px 0px rgba(255, 190, 24, 0.24)`~~ **PROIBIDO** — glow/shadow no logo está banido pela regra absoluta de efeitos (ver seção "⚠️ REGRA ABSOLUTA — EFEITOS PROIBIDOS" na seção 6). Usar sempre o arquivo oficial do logo do Drive sem nenhum efeito adicional.

A versão ghost/outline também foi descontinuada. Se precisar de tratamento sutil do logo (ex: watermark de fundo), usar apenas o arquivo oficial em opacity baixa (15-25%) — sem stroke tracejado, sem fill ghost, sem box-shadow.

### 2.6 Area de Protecao e Grid
O logo foi construido sobre um grid tipografico preciso, com linhas de referencia para alinhamento vertical e horizontal. Manter area de protecao equivalente a altura do simbolo ao redor de todo o logo.

---

## 3. Paleta de Cores [NORMATIVE]
> Tokens canônicos consolidados em [[metta-tokens]] §1. Esta seção mantém valores de referência semiótica.

### 3.1 Cores Primarias

#### Amarelo (Cor Principal da Marca)
| Variacao | HEX | Uso |
|----------|-----|-----|
| Amarelo Principal | `#FFBE18` | Cor primaria, CTAs, simbolo, destaques |
| Amarelo Claro | `#FFC531` | Strokes, elementos secundarios |
| Amarelo Medio | `#FFCE50` | Backgrounds auxiliares, gradientes |
| Amarelo Suave | `#FFE4A1` | Backgrounds leves, hover states |

**Associacoes semioticas**: Sol, Luz, Calor, Ouro, Prosperidade, Otimismo, Energia, Criatividade, Inteligencia, Atencao

#### Azul Noite (Cor Base)
| Variacao | HEX | Uso |
|----------|-----|-----|
| Azul Noite | `#0C161B` | Backgrounds escuros, textos sobre fundo claro |
| Azul Noite Profundo | `#0A1013` | Backgrounds muito escuros |

**Associacoes semioticas**: Seriedade, Autoridade, Confianca, Estabilidade, Inteligencia, Calma, Profundidade

### 3.2 Cores Secundarias

#### Branco Gelo
| Variacao | HEX | Uso |
|----------|-----|-----|
| Branco Puro | `#FFFFFF` | Backgrounds claros, textos sobre fundo escuro |
| Branco Gelo | `#FAFCFD` | Backgrounds neutros, cards |
| Gelo Azulado | `#EBF3F7` | Backgrounds secundarios |
| Cinza Muito Claro | `#EFF3F5` | Backgrounds de secoes |
| Cinza Claro | `#F0F0F0` | Backgrounds, divisores |
| Cinza | `#EDEDED` | Backgrounds de contraste |

**Associacoes semioticas**: Leveza, Amplitude, Neutralidade, Sofisticacao, Claridade, Frescor, Calma, Serenidade

#### Azul Acinzentado
| Variacao | HEX | Uso |
|----------|-----|-----|
| Azul Acinzentado | `#435965` | Textos secundarios, labels, elementos de suporte |
| Azul Acinzentado Claro | `#688594` | Textos terciarios, detalhes |
| Azul Acinzentado Suave | `#75919F` | Tags, labels, metadata |
| Azul Acinzentado Muito Claro | `#A8B3B9` | Linhas de grid, divisores sutis |

**Associacoes semioticas**: Solidez, Confianca, Neutralidade, Pragmatismo, Modernidade, Resistencia, Elegancia, Intelectual

### 3.3 Gradientes

| Nome | CSS | Uso |
|------|-----|-----|
| Gradiente Radial Claro | `radial-gradient(circle at 73% 2%, #FFFFFF 36%, #E0E6E9 100%)` | Backgrounds de destaque claro |
| Gradiente Radial Escuro | `radial-gradient(circle at 50% 41%, #0C161B 0%, #0C161B 100%)` | Backgrounds escuros com profundidade |
| Gradiente Amarelo | `radial-gradient(circle at 82% 10%, #FFBE18 59%)` | Highlights, fundos especiais |
| Gradiente Angular | `conic-gradient(from 78deg at 33% 75%, #0C161B 5%, #435965 62%, #1E2D36 82%)` | Backgrounds premium/sofisticados |
| Gradiente Linear Amarelo | `linear-gradient(226deg, #FFC443 10%, #FFB618 97%)` | Elementos decorativos, formas |

### 3.4 Cores com Opacidade (Uso Recorrente)
| Cor | Uso |
|-----|-----|
| `rgba(12, 22, 27, 0.2)` | Separadores, divisores sobre fundo claro |
| `rgba(12, 22, 27, 0.6)` | Textos secundarios sobre fundo claro |
| `rgba(255, 255, 255, 0.2)` | Separadores, divisores sobre fundo escuro |
| `rgba(255, 190, 24, 0.1)` | Background sutil amarelo |
| ~~`rgba(255, 190, 24, 0.24)` — Glow/sombra do logo~~ | **REMOVIDO** — glow no logo proibido |
| `rgba(58, 109, 137, 0.28)` | Linhas de grid sobre fundo escuro |
| `rgba(67, 89, 101, 0.08)` | Fills ghost/fantasma |
| `rgba(202, 217, 224, 0.87)` | Strokes de outline |

---

## 4. Tipografia [NORMATIVE]
> Tokens canônicos consolidados em [[metta-tokens]] §2. Esta seção mantém regras de aplicação por contexto.
> **Refator de 2026-05-27:** Inter removida. Sistema agora opera com **duas fontes primárias open-source**: Zalando Sans Expanded (display) + Inter (body). Documentação anterior (SF Pro Variable + dois eixos no mesmo arquivo) está arquivada em `_archive/`.

### 4.1 Duas Fontes Primárias

A marca opera com **duas fontes**, ambas SIL OFL 1.1, instaladas e distribuídas livremente. Cada uma tem uma função editorial separada:

| Fonte | Função | Quando usar |
|---|---|---|
| **Zalando Sans Expanded** | Display | Títulos, H1, headlines, CTAs, labels UPPERCASE, big numbers, divider titles |
| **Inter** | Body | Parágrafos, subtítulos, captions, descrições, body em cards, tabelas |

**Não há mais "eixo de largura" via `font-stretch`.** As duas larguras editoriais (display expandido + body neutro) vêm de **famílias diferentes**, não do mesmo arquivo variável. Essa simplificação:
- Elimina dependência de fonte proprietária (SF Pro era Apple-only).
- Garante renderização idêntica em macOS, Windows, Linux, Google Slides, PowerPoint, Canva.
- Permite distribuir em PPTX/Keynote sem restrição de licença.

### 4.2 Variações Nomeadas — Pesos por Fonte

#### Zalando Sans Expanded — display (8 pesos disponíveis)

| Variação | `font-weight` | Caracteres visuais | Uso dominante |
|----------|---------------|--------------------|---------------|
| **Black** | 900 | Máxima presença, traços grossos | Display hero, big numbers, watermarks tipográficos |
| **ExtraBold** | 800 | Forte e sólido | H1 de máximo impacto, divider title |
| **Bold** | 700 | Forte e legível | CTAs pill ("SAIBA MAIS", "QUERO PARTICIPAR"), headlines padrão |
| **SemiBold** | 650 | Peso editorial equilibrado | Headlines de poster (74-142px), display institucional, títulos de seção |
| **Medium** | 540 | Peso limpo pra tracking largo | Labels/tags UPPERCASE (ELITE, PREMIUM, MENTORIA), breadcrumbs com tracking 9-12% |
| **Regular** | 410 | Display leve | Setup mixed-weight (parte "leve" antes do Heavy) |
| **Light** | 270 | Ultrafino delicado | Taglines sutis, frases ultralight em stories, sub-captions decorativas |
| **ExtraLight** | 200 | Hairline | Uso raro · marcação decorativa fina |

#### Inter — body (8 pesos disponíveis)

| Variação | `font-weight` | Caracteres visuais | Uso dominante |
|----------|---------------|--------------------|---------------|
| **Black** | 900 | Body com presença máxima | Ênfase pontual inline em body |
| **ExtraBold** | 800 | Body forte | Destaque inline em parágrafo |
| **Bold** | 700 | Body bold | Ênfase em meio a texto corrido |
| **SemiBold** | 600 | Sub-headline sólida | Sub-headlines, destaques inline, ênfase secundária |
| **Medium** | 500 | Body com peso médio | Body large, descrições em cards, pain points |
| **Regular** | 400 | Leitura neutra padrão | Body corrido, legendas, descrições, manifesto (justified) |
| **Light** | 300 | Tom suave | Body sutil, taglines complementares |
| **Thin** | 100 | Hairline | Captions decorativas, fine print, footers |

> Inter também tem variante **Italic** completa (8 pesos) — usar em citações, ênfase semântica, títulos de obra.

### 4.3 Import e CSS

**Importação Google Fonts (uma linha cobre as duas):**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zalando+Sans+Expanded:ital,wght@0,200..900;1,200..900&family=Inter:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
```

**CSS — dois stacks distintos por função:**

```css
/* Body global / texto regular */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Headlines, display, CTAs, labels UPPERCASE */
h1, h2, .t-display, .cta-pill, .t-label {
  font-family: 'Zalando Sans Expanded', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

**PPTX / Google Slides:** ambas as fontes estão no catálogo do Google Fonts (Google Slides puxa direto, sem ação manual). Pra PPTX no PowerPoint/Keynote, instalar localmente — disponível em github.com/zalando/typefaces (Zalando) e github.com/rsms/inter (Inter).

**Licenças:** ambas **SIL OFL 1.1**. Livres pra distribuir em PPTX, embedar, usar comercialmente, redistribuir.

### 4.4 Regras Invioláveis

- **Inter NUNCA em headline ou display.** Inter é geometricamente neutra, não tem o peso editorial expandido. Display = Zalando Sans Expanded, sempre.
- **Zalando Sans Expanded NUNCA em body longo.** Foi pensada pra display — cansa leitura em parágrafos.
- **SF Pro NUNCA em lugar nenhum.** Removida do sistema em 2026-05-27.
- **Fontes PROIBIDAS:** Arial, Helvetica, Open Sans, Roboto, Roboto Flex (deprecated em 2026-05-12), SF Pro (removida 2026-05-27), qualquer outra fora do par Zalando + Inter.

**Single exception (legado):** `Metta - Blackbook Empresários.pdf` ainda usa Nordique Pro (pré-refator). Refazer na próxima atualização de conteúdo.

### 4.4 Escala Tipográfica (base 1080px de largura)

#### Regra de tamanho mínimo para Instagram
- **Texto legível** (body, features, CTAs): mínimo **36px**
- **Texto decorativo** (labels, tags, metadata): mínimo **24px**
- Abaixo de 24px apenas em impressos A4+ ou landing pages desktop

#### Display / Headlines (use Expanded 132%)
| Nível | Tamanho | Variação recomendada | Line-height | Letter-spacing | Uso |
|-------|---------|---------------------|-------------|----------------|-----|
| Display Hero | 120-142px | Expanded Heavy (870) | 0.82-0.90em | -1% a -4% | Headline impactante, frase hero |
| Display XL | 100-121px | Expanded Heavy (870) | 0.82-0.95em | -1% | Headlines de anúncio |
| Display L | 78-99px | Expanded Semibold (650) | 0.90em | -1% | Headlines editoriais, posters |
| Display M | 60-75px | Expanded Semibold (650) | 0.90em | -1% | Headlines de modelo/story |
| Display S | 52-57px | Expanded Heavy (870) | 0.95em | -1% | Headlines menores |

#### Títulos de seção
| Nível | Tamanho | Variação | Line-height | Letter-spacing |
|-------|---------|----------|-------------|----------------|
| H1 | 44-51px | Expanded Heavy (870) | 0.82em | -1% |
| H2 | 40-44px | Expanded Semibold (650) | 0.90em | -1% |
| H3 | 32-40px | Regular Medium+ (590) | 0.90em | -1% |
| H4 | 28-32px | Regular Medium+ (590) | 0.90em | -1% |

#### Body / Corpo
| Nível | Tamanho | Variação | Line-height | Letter-spacing |
|-------|---------|----------|-------------|----------------|
| Body L | 36-42px | Regular Medium+ (590) | 1.17em | -1% |
| Body M | 30-35px | Regular Medium+ (590) | 1.20em | -1% |
| Body S | 24-30px | Regular Book (400) | 1.17em | -1% |
| Body Light | 24-52px | Regular Light (270) / Expanded Light (270) | 1.17em | -1% |

#### Labels / Tags (use Expanded Medium 132% ou Regular Medium 100%)
| Nível | Tamanho | Variação | Letter-spacing | Case |
|-------|---------|----------|----------------|------|
| Label L | 26-28px | Expanded Medium (540) | +9-12% | UPPERCASE |
| Label S | 24px | Expanded Medium (540) | +12% | UPPERCASE |
| Label Editorial | 9-11px | Expanded Light (270) | +200-300% | UPPERCASE |

### 4.5 Regras Tipográficas por Contexto

#### Modo Conversão (Anúncios A-L, CTAs diretos)
- Headlines: **Expanded Heavy (870) + 132%**, UPPERCASE, letter-spacing -1%, line-height 0.82-0.95em
- Body: **Regular Medium+ (590)**, sentence case, letter-spacing -1%, line-height 1.17-1.20em
- Labels: **Expanded Medium (540)**, UPPERCASE, letter-spacing +9-12%
- CTAs: **Expanded Bold (700) + 132%**, UPPERCASE, letter-spacing +1%

#### Modo Editorial / Institucional (Posters, Slides, Landing Pages)
- Headlines: **Expanded Semibold (650) + 132%**, Sentence case, letter-spacing -1%, line-height 1.0-1.1em
- Mixed-weight headlines: **Expanded Regular (410)** no setup + **Expanded Heavy (870)** no impacto
- Color highlighting: palavras-chave em `#FFBE18` dentro de headline branco
- Labels: **Expanded Light (270)**, UPPERCASE, letter-spacing +200-300%, 9-11px

#### Modo Marca Pessoal (Tiago Alves)
- Headlines: **Expanded Heavy (870) + 132%**, ALL-CAPS, tight leading (~0.90-0.95)
- Accent de ênfase: steel blue `#4A7FA5` em palavras-chave (não em CTAs)
- Body: **Regular Book (400)**, com **Regular Semibold (650)** para bold inline
- Breadcrumbs: **Expanded Medium (540)** UPPERCASE letter-spacing +12%, nos cantos superiores
- Exceção lowercase: frases de intimidade ("já tentou / de tudo") — **Expanded Heavy (870)** lowercase

#### Regra universal
- **Headlines e destaques**: SEMPRE família Expanded (`font-stretch: 132%`)
- **Body, labels, descrições**: família Regular (`font-stretch: 100%`)
- **Light (270)**: palavras suaves, taglines, textos decorativos
- **Heavy (870)**: máxima ênfase em headlines de impacto

### 4.6 Implementação CSS de Referência

```css
/* Registra a fonte variável com todo o range de eixos */
/* Stack base */
body {
  font-family: 'Inter', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 400;
  font-stretch: 100%;
  font-optical-sizing: auto;
  letter-spacing: -0.01em;
}

/* Variações Expanded (headlines/destaques) */
.expanded-heavy    { font-weight: 870; font-stretch: 132%; }
.expanded-bold     { font-weight: 700; font-stretch: 132%; }
.expanded-semibold { font-weight: 650; font-stretch: 132%; }
.expanded-medium   { font-weight: 540; font-stretch: 132%; }
.expanded-regular  { font-weight: 410; font-stretch: 132%; }
.expanded-light    { font-weight: 270; font-stretch: 132%; }

/* Variações Regular (body/textos) */
.regular-semibold  { font-weight: 650; font-stretch: 100%; }
.regular-medium-p  { font-weight: 590; font-stretch: 100%; }
.regular-medium    { font-weight: 510; font-stretch: 100%; }
.regular-book      { font-weight: 400; font-stretch: 100%; }
.regular-light     { font-weight: 270; font-stretch: 100%; }

/* Headlines default (modo conversão) */
h1, h2, .headline {
  font-weight: 870;
  font-stretch: 132%;
  text-transform: uppercase;
  letter-spacing: -0.01em;
  line-height: 0.9;
}

/* CTA pill */
.cta {
  font-weight: 700;
  font-stretch: 132%;
  text-transform: uppercase;
  letter-spacing: 0.01em;
}
```

> **AVISO TÉCNICO:** NÃO usar `font-variation-settings: 'wdth' 132` quando também declarar `font-stretch`. A especificação CSS determina que `font-weight` e `font-stretch` sobrepõem os eixos correspondentes em `font-variation-settings`. Use sempre as propriedades CSS diretas.

---

## 5. Arquitetura de Marca (Sub-marcas) [NORMATIVE]

### 5.1 Hierarquia de Produtos

```
METTA (marca mae)
|
|-- Mentorias
|   |-- ELITE (tier mais exclusivo)
|   |-- EXCLUSIVE (tier intermediario)
|   |-- PREMIUM (tier de entrada premium)
|
|-- SMTM - "Supere a Meta Todo Mês"
|   |-- ELITE
|   |-- EXCLUSIVE
|   |-- PREMIUM
```

### 5.2 Sistema de Logos de Produto
Cada sub-marca segue o padrao:
- **Simbolo Metta** (icone) + **Nome do produto/tier** + **Badge de tier**
- Badges de tier sao pills/capsulas com borda branca e texto em caixa alta com tracking 12%
- Layout pode ser:
  - Horizontal: simbolo | wordmark | badge
  - Vertical/empilhado: simbolo em cima, wordmark + badge embaixo
  - Compacto: simbolo + sigla (SMTM)

### 5.3 Formatacao dos Nomes
- **"SUPERE A META TODO MES"**: Inter, weight 870, ~25px, letter-spacing -3%
- **"MENTORIA"**: Inter, weight 540, ~12px, letter-spacing 12%, caixa alta
- **Tier badges** (ELITE, EXCLUSIVE, PREMIUM): Inter, weight 540, ~13px, letter-spacing 12%, dentro de pill com border-radius ~33px

---

## 6. Elementos Gráficos [NORMATIVE]

### 6.1 Simbolo / Icone
O simbolo da Metta e composto por arcos concentricos que formam uma figura geometrica:
- **Arco Maior**: Circulo externo com abertura
- **Arco Menor**: Circulo interno com abertura
- **C Maior**: Forma de "C" externa
- **C Menor**: Forma de "C" interna
- Cores: Amarelo (#FFBE18) sobre fundos escuros, Azul noite (#0C161B) sobre fundos claros

### 6.2 Formas Decorativas
- Uso de shapes organicos/curvilineos com gradientes em amarelo
- Linhas divisorias finas (1px) com opacidade reduzida
- Grids de construcao visiveis em apresentacoes tecnicas (linhas em cor F0F0F0 ou rgba com opacidade)

### 6.3 Cantos Arredondados
- **Cards e containers**: border-radius ~12px
- **Badges/Pills**: border-radius ~33-48px (full rounded)
- **Stroke em badges**: ~1.4px em branco

### ⚠️ 6.4 REGRA ABSOLUTA — EFEITOS PROIBIDOS

**Nunca usar em nenhuma peça Metta:**

- **Glow effects** — radial gradients como "luz emanante", box-shadows coloridos em CTAs/botões, drop-shadows, text-shadows em headlines, inset box-shadows em logos, teal glow atmosférico, gold glow, soft glow, dark vignette por blur
- **Anéis e elipses decorativas** — concentric rings, stroked ellipses como textura de fundo, rings yellow-on-yellow, decorative arcs low-opacity
- **Blur atmosférico decorativo** — `filter: blur()` como efeito estético, `backdrop-filter: blur()` glassmorphism, blur como sombra difusa atrás de pessoas
- **Sombras coloridas** — `--shadow-logo-glow`, `--shadow-image-blur`, qualquer box-shadow com cor de marca

**O que CONTINUA permitido** (não são glow/rings):

- **Gradient backgrounds funcionais** — conic, linear, radial como surface color do frame
- **Dark overlay gradient sobre fotos** — gradiente linear `rgba()` crescente para legibilidade do texto (SEM `filter: blur()`, SEM `backdrop-filter`)
- **Circular photo masks** — foto redonda como avatar (componente funcional, não decoração)
- **Nav arrow circles simples** — stroke 1-2px, sem glow (UI funcional)

**Por quê:** a identidade Metta é direta, limpa, sem efeitos especiais. A hierarquia é construída com **tipografia + cor + espaço**. Qualquer glow/ring enfraquece o posicionamento "inteligência comercial" (método, ciência, processo).

**Em caso de dúvida:** NÃO usar o efeito. Reforçar tipografia ou contraste de cor em vez de adicionar brilho/sombra.

### 6.5 ~~Sombras e Efeitos~~ [REMOVIDO]
~~**Blur de fundo**: blur(111px) para sombras difusas de imagem~~
~~**Glow do logo**: inset box-shadow com amarelo em opacidade baixa~~
~~**Blur em imagens de fundo**: blur(31px) para efeito de profundidade~~

**Todos removidos** por conformidade com a regra absoluta em 6.4.

---

## 7. Fotografia e Imagens [NORMATIVE]

### 7.1 Estilo Fotografico
- Fotografias profissionais de alta qualidade
- Retratos da equipe com iluminacao controlada
- Ambientacao corporativa mas moderna

### 7.2 Composicao de Cards Pessoais
Cada membro da equipe tem um card visual com:
- Foto profissional recortada em shape organico (arcos concentricos da marca)
- Gradiente de sobreposicao (amarelo para a CEO/Head, escuro para gestores)
- Nome em **Zalando Sans Expanded Heavy (870 + 132%)**, ~44px
- Cargo em **Inter Book (400 + 100%)**, ~20-23px
- Logo Metta no canto
- Tagline "Inteligencia comercial para empresarios" em **Zalando Sans Expanded Heavy (870 + 132%)**, ~20px
- Selo/badge de cor ao fundo

### 7.3 Equipe Identificada
- **Tiago Alves** - CEO
- **Vanessa Bilovus** - Head de Produto
- **Kevin Santos** - Gestor de Projetos

### 7.4 O que Evitar (Referencia da marca antiga)
- Formato arredondado excessivo (tipografia muito "fofa")
- Imagens genericas (banco de imagem obvio)
- Estilo amigavel / simpatico em excesso
- Falta de hierarquia visual
- Falta de consistencia visual

---

## 8. Aplicações [NORMATIVE]

### 8.1 Formato Base
- **Slides/Apresentacoes**: 1920 x 1080px
- Backgrounds alternam entre escuro (#0C161B), claro (#FFFFFF), amarelo (#FFBE18) e cinzas

### 8.2 Aplicacao Digital
- Mockups de celular (iPhone) com interface da marca
- Redes sociais: posts com tipografia bold, contrastes fortes
- Tagline "O ecossistema de inteligencia comercial para empresarios" sempre presente

### 8.3 Aplicacao Fisica
- Totem de logo para recepcao/eventos
- Sinalizacao e impressos

### 8.4 Redes Sociais
- Badge "REDES SOCIAIS" em pill amarela com texto escuro
- Posts com imagens reais (nao genericas)
- Headlines em **Zalando Sans Expanded Heavy (870 + 132%)**
- Corpo em **Inter Book (400 + 100%)**

---

## 9. Regras de Consistência [NORMATIVE]

### 9.1 Hierarquia Visual
1. **Título principal**: Expanded Heavy (870) ou Expanded Semibold (650), `font-stretch: 132%`, 63-142px, letter-spacing -1% a -4%
2. **Subtítulo/Complemento**: Regular Medium+ (590) ou Expanded Light (270), 24-52px
3. **Labels/Categorias**: Expanded Medium (540) + 132%, UPPERCASE, 24-28px, tracking +9-12%
4. **Corpo de texto**: Regular Book (400) + 100%, 24-42px, line-height 1.17-1.20em

### 9.2 Contraste
- **Fundo escuro**: Texto branco (#FFFFFF) + destaques amarelo (#FFBE18)
- **Fundo claro**: Texto azul noite (#0C161B) + destaques amarelo (#FFBE18)
- **Fundo amarelo**: Texto azul noite (#0C161B)

### 9.3 Espacamento
- Padding em badges: ~11px vertical, 9-20px horizontal
- Gap entre elementos inline: ~13-18px
- Linhas separadoras: 1px, cor com 20% opacidade

---

## 10. Tokens de Design (Referência Rápida) [REFERENCE]
> ⚠️ Tokens canônicos agora vivem em [[metta-tokens]]. Esta seção é mantida como snapshot pra leitura rápida; em conflito, [[metta-tokens]] vence.

```css
/* Cores Primarias */
--color-yellow-primary: #FFBE18;
--color-yellow-light: #FFC531;
--color-yellow-medium: #FFCE50;
--color-yellow-soft: #FFE4A1;
--color-blue-night: #0C161B;
--color-blue-deep: #0A1013;

/* Cores Secundarias */
--color-white: #FFFFFF;
--color-ice: #FAFCFD;
--color-ice-blue: #EBF3F7;
--color-gray-100: #EFF3F5;
--color-gray-200: #F0F0F0;
--color-gray-300: #EDEDED;
--color-blue-gray: #435965;
--color-blue-gray-light: #688594;
--color-blue-gray-muted: #75919F;
--color-blue-gray-subtle: #A8B3B9;

/* Tipografia — Zalando Sans Expanded (ver Secao 4) */
--font-family-regular:  'Inter', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-family-expanded: 'Inter', 'Zalando Sans Expanded', sans-serif;
/* Body usa o stack Regular por padrão; headlines/display/CTAs trocam pro stack Expanded */
--font-family: var(--font-family-regular);
--font-weight-light: 270;
--font-weight-regular: 400;
--font-weight-expanded-regular: 410;
--font-weight-medium: 510;
--font-weight-label: 540;
--font-weight-medium-plus: 590;
--font-weight-semibold: 650;
--font-weight-bold: 700;
--font-weight-heavy: 870;
--font-stretch-regular: 100%;
--font-stretch-expanded: 132%;

/* Espacamento */
--radius-card: 12px;
--radius-pill: 33px;
--radius-full: 48px;

/* Sombras — REMOVIDAS por regra absoluta (ver 6.4). Não declarar shadow tokens. */
/* ~~--shadow-logo-glow: inset 0px 0px 43px 0px rgba(255, 190, 24, 0.24);~~ */
/* ~~--shadow-image-blur: blur(111px);~~ */
```

---

## 11. Checklist para o Agente de Design [NORMATIVE]

Ao criar qualquer material visual para a Metta, verificar:

- [ ] Assets obtidos do Google Drive (Secao 12) - nunca usar arquivos locais
- [ ] Logo correto selecionado conforme guia de selecao (Secao 12.6)
- [ ] Background correto selecionado conforme guia de selecao (Secao 12.6)
- [ ] Fonte Zalando Sans Expanded em uso, com variacao nomeada correta (Secao 4.2) + fallbacks corretos por eixo (Zalando Sans Expanded pra Expanded · Inter pra Regular) — obrigatorios em PPTX/Google Slides (Secao 4.3)
- [ ] Paleta de cores respeitada (amarelo, azul noite, branco gelo, azul acinzentado)
- [ ] Logo na versao correta para o fundo utilizado
- [ ] Hierarquia tipografica clara (display > heading > body > label)
- [ ] Letter-spacing negativo em headlines, positivo em labels
- [ ] Sem imagens genericas de banco
- [ ] Cantos arredondados consistentes (~12px cards, ~33px pills)
- [ ] Contraste adequado (texto legivel sobre qualquer fundo)
- [ ] Tagline "INTELIGENCIA COMERCIAL" com tracking 9%+ em caixa alta
- [ ] Badges de tier (ELITE/EXCLUSIVE/PREMIUM) em pills com borda e tracking 12%
- [ ] Sem estilo "fofo" ou excessivamente amigavel - manter tom profissional e autoritativo
- [ ] Gradientes seguem os padroes definidos (radial, angular, linear com as cores da paleta)
- [ ] Preferir SVG para logos/backgrounds; PNG para templates de reels

---

## 12. Biblioteca de Assets (Google Drive) [REFERENCE]
> Catálogo completo (Drive IDs por logo, background, modelo de reels) consolidado em [[metta-logos]].

> **Pasta raiz**: [Identidade Visual Metta](https://drive.google.com/drive/folders/1I7W7fYQw1NK4iVhMEkgnWIBjeZZtTQ7u)
>
> Todos os assets oficiais da marca estao centralizados no Google Drive. O agente de design deve buscar os arquivos diretamente do Drive usando os IDs abaixo. **Nunca usar arquivos locais.**

---

### 12.1 Background
**Pasta**: [Background](https://drive.google.com/drive/folders/12iw_vXsVD7PeqjKvz6O3uNLzhOAbtjYf)

| Arquivo | Formato | ID do Drive | Uso |
|---------|---------|-------------|-----|
| bg_gradiente_amarelo_1 | PNG | `1GrKUEC_kWb6Aamkj4FPfKHUi1Lr1at7F` | Fundo com gradiente amarelo |
| bg_gradiente_amarelo_1 | SVG | `1_cFZ4mh0-OcTntrV7iYqbVbQDp2rUYjN` | Fundo com gradiente amarelo (vetorial) |
| bg_gradiente_escuro_1 | PNG | `1pbu8JYrEm8DLvbtMbyZfNrpy8fiSX1v6` | Fundo com gradiente escuro |
| bg_gradiente_escuro_1 | SVG | `1iIOhDXHw39SEeS-a5zBe41eq8ChSdiSo` | Fundo com gradiente escuro (vetorial) |
| bg_liso_amarelo_1 | PNG | `1VyOcpC4kQDRZqVtk88WWuVNLDmhDlQoj` | Fundo liso amarelo variante 1 |
| bg_liso_amarelo_1 | SVG | `19WM0kTzLS69ga9mqRLNsG9LfeHvwkOXh` | Fundo liso amarelo variante 1 (vetorial) |
| bg_liso_amarelo_2 | PNG | `1k0wvNtRLRzX_IkKUq3WeXCqpsKZpeBHB` | Fundo liso amarelo variante 2 |
| bg_liso_amarelo_2 | SVG | `1SC-ssWO9ifWXttwv_sFf1IZrL_Nk3FFc` | Fundo liso amarelo variante 2 (vetorial) |
| bg_liso_amarelo_3 | PNG | `1m4W_iOIHMkTpzn3V-mF9xRVeXfGyrmnR` | Fundo liso amarelo variante 3 |
| bg_liso_amarelo_3 | SVG | `1_VnqAwB0xcsl_g0H2NntE_qzZPTmXCr5` | Fundo liso amarelo variante 3 (vetorial) |
| bg_liso_azul_1 | PNG | `1O6AWbrs_oUJcNuusLi_uemXDBV8EQfsk` | Fundo liso azul noite variante 1 |
| bg_liso_azul_1 | SVG | `17layZE3m4AW4oEaFR-daGG5L2Hy50nvN` | Fundo liso azul noite variante 1 (vetorial) |
| bg_liso_azul_2 | PNG | `1tKZxrP53s3R2wZ2M5LJ1j9rNzUEkeIqd` | Fundo liso azul noite variante 2 |
| bg_liso_azul_2 | SVG | `1j_4mFdzj6Dtd7EgYfxzpGrzOSdXdIHHz` | Fundo liso azul noite variante 2 (vetorial) |
| bg_liso_branco_gelo_1 | PNG | `1DJnhIyFCL94s7fuJI9ZHhwRXHe31MXsV` | Fundo liso branco gelo |
| bg_liso_branco_gelo_1 | SVG | `1N3AMODpJsZ7f1MpvWUmcUbf5ILRkRQnC` | Fundo liso branco gelo (vetorial) |
| bg_liso_cinza_1 | PNG | `19soa2bWk0OM9gt9vbiqOBcxnOaAwmKut` | Fundo liso cinza |
| bg_liso_cinza_1 | SVG | `1ZAIgmME7pqneLeCPqKdOxemgL4mWBf8P` | Fundo liso cinza (vetorial) |
| bg_liso_cinza_gelo_1 | PNG | `1PKsAsdWGmPKJObxn5g8XfXBgoAINNu_j` | Fundo liso cinza gelo |
| bg_liso_cinza_gelo_1 | SVG | `1m0bOiiaw-0mmswBofoLSxSfZViWU8c-S` | Fundo liso cinza gelo (vetorial) |

---

### 12.2 Logo Metta
**Pasta**: [Logo Metta](https://drive.google.com/drive/folders/1ut9l5T_ozyUbUjIqBDFPERRMIiEi6LuZ)

#### Simbolos (Icone isolado)
| Arquivo | Formato | ID do Drive | Cor |
|---------|---------|-------------|-----|
| Simbolo_metta_amarelo | PNG | `1L6yJ0gmxqKOsbGFg7MI3sc8JJZ-jdqzC` | Amarelo (#FFBE18) |
| Simbolo_metta_amarelo | SVG | `1dwPSsS49LZWJR7hd3HoaNnvgLkWquJs4` | Amarelo (#FFBE18) |
| Simbolo_metta_azul | PNG | `1Bnn6DVkar-nNVh6AWsi_Vktj3dViJtsv` | Azul noite (#0C161B) |
| Simbolo_metta_azul | SVG | `1HDDsK0WPyINzOk_ogxRBlaX00yp9dYjP` | Azul noite (#0C161B) |
| Simbolo_metta_azul2 | PNG | `1VBOJm_p8Yc2dc13DaTySh3sFORKMDP45` | Azul secundario |
| Simbolo_metta_azul2 | SVG | `1wvZxTOkZbfeRbuLju17XH6RQ2XL95SYk` | Azul secundario |
| Simbolo_metta_branco | PNG | `1b3tKx-ueGbHaAva3qVojXNlfiyK74Bbl` | Branco (#FFFFFF) |
| Simbolo_metta_branco | SVG | `1y2E3_xpZAAtsp6-CgGYfP4AftaMIVu2s` | Branco (#FFFFFF) |
| Simbolo_metta_cinza | PNG | `1it2DjVaJl5aVCFvyMU9pQdEEPyaXpmkU` | Cinza |
| Simbolo_metta_cinza | SVG | `1ZV9SAmeMdRUq89iKWu-YRLaXuohWtn-U` | Cinza |

#### Logo Completo (Simbolo + Wordmark) - Horizontal (_h) e Vertical (_v)
| Arquivo | Formato | ID do Drive | Cor | Orientacao |
|---------|---------|-------------|-----|------------|
| Logo_metta_colorido_h | PNG | `1zdIiaQedxsWH0IJqmGKUSJPZ8lb16siY` | Colorido (amarelo + branco) | Horizontal |
| Logo_metta_colorido_h | SVG | `1KJ4uiqHdX49Uhp2wg3E9HkzqawE7bYMQ` | Colorido (amarelo + branco) | Horizontal |
| Logo_metta_colorido_v | PNG | `1TAOMF6zc41fK4zGSzbf3WsjUl08b30Np` | Colorido (amarelo + branco) | Vertical |
| Logo_metta_colorido_v | SVG | `1-McHsQ1dT3RX5rGLWQv2cFL8TJOXidjB` | Colorido (amarelo + branco) | Vertical |
| Logo_metta_colorido_escuro_h | PNG | `1xXwyI40wfLmg7euILl1eoUzElCm7G_Kp` | Colorido escuro (amarelo + azul) | Horizontal |
| Logo_metta_colorido_escuro_h | SVG | `1OoU3dGAEPR8S8g10ZuR-vlSyqEv3YDOi` | Colorido escuro (amarelo + azul) | Horizontal |
| Logo_metta_colorido_escuro_v | PNG | `1WF7is4MRzYUBz144eVGFl70SKGzW8g6Z` | Colorido escuro (amarelo + azul) | Vertical |
| Logo_metta_colorido_escuro_v | SVG | `1XBx0a3Zi0Gjf8in1Mk-_ynxCYsM834B_` | Colorido escuro (amarelo + azul) | Vertical |
| Logo_metta_branco_h | PNG | `1dUkDiVqLASKO9b52rnVzlzXkG4LmP09F` | Branco monocromatico | Horizontal |
| Logo_metta_branco_h | SVG | `1UAttnww1716VzMNZtGWkyEEuEepmVeR4` | Branco monocromatico | Horizontal |
| Logo_metta_branco_v | PNG | `1726eRnBpslYqMi0DsVpm3NxcWGFvfND4` | Branco monocromatico | Vertical |
| Logo_metta_branco_v | SVG | `14bfXYU44-Vi_GUzt2h9K93u-mQ4tM4km` | Branco monocromatico | Vertical |
| Logo_metta_azul_h | PNG | `1DMqb6w8EMcsY7W8vja2unUkAJC_Oablm` | Azul noite monocromatico | Horizontal |
| Logo_metta_azul_h | SVG | `13Dz57SxqWTj8bpUcyr8P7N88k3atp8wN` | Azul noite monocromatico | Horizontal |
| Logo_metta_azul_v | PNG | `1pwxckpUPu_Wbvi2IPt6Cu_eJ06HvrT8E` | Azul noite monocromatico | Vertical |
| Logo_metta_azul_v | SVG | `1ON4zqLTBqlDSvU9M_tsAskCQXQH0FL9i` | Azul noite monocromatico | Vertical |
| Logo_metta_azul2_h | PNG | `1hbYDE0jvuksEdcI0Y8aU8AF80bPCsLrr` | Azul secundario monocromatico | Horizontal |
| Logo_metta_azul2_h | SVG | `17g9sUtqsLwV1Pgi6aQD5o72v6WRV4tck` | Azul secundario monocromatico | Horizontal |
| Logo_metta_azul2_v | PNG | `11t337xMRuUF2J8__dfxHgO9sXN4qHpr4` | Azul secundario monocromatico | Vertical |
| Logo_metta_azul2_v | SVG | `1waBE3chmyV58bibddkSbWJMTqK7baBUi` | Azul secundario monocromatico | Vertical |
| Logo_metta_cinza_h | PNG | `1KyPV4XPyPPGrrd3mLAQhvlZlz7pQUqhy` | Cinza monocromatico | Horizontal |
| Logo_metta_cinza_h | SVG | `1hjaZujL9UExoBb7YH8xHd68kTHa3pm3Z` | Cinza monocromatico | Horizontal |
| Logo_metta_cinza_v | PNG | `1N3yDA9CA8QonLnGwDKLcAXUYwtU-MWAz` | Cinza monocromatico | Vertical |
| Logo_metta_cinza_v | SVG | `1qHpKB3NXwtLBN3LNhKEKnISw3lfQM4d1` | Cinza monocromatico | Vertical |

#### Logo com Tagline
| Arquivo | Formato | ID do Drive | Descricao |
|---------|---------|-------------|-----------|
| Logo_metta_tagline_colorida_h | SVG | `1ml7q5kY5hR_JBThjk11Q53kunxccGKSE` | Logo horizontal com tagline "Inteligencia Comercial" |

#### Assinaturas (Logo compacto para rodapes e aplicacoes reduzidas)
| Arquivo | Formato | ID do Drive | Cor |
|---------|---------|-------------|-----|
| assinatura_metta_amarelo | PNG | `1g2-Wb27NSAv7xyhqHK22vVnoBOGr8fdj` | Amarelo |
| assinatura_metta_amarelo | SVG | `1O2ZBlXo1xkpEoo2fmwpP1Fo37RElRBlf` | Amarelo |
| assinatura_metta_azul | PNG | `1Wv9qMgK7MXFfiRIyNjPKlmhsuGHBr6YP` | Azul noite |
| assinatura_metta_azul | SVG | `1cwtzuv_pbdUXoZWQMeXOrsRXQcdtee7H` | Azul noite |
| assinatura_metta_azul2 | PNG | `1C2R_m-JpLW0UaK3ToW0xa_O7Idyp8N_P` | Azul secundario |
| assinatura_metta_azul2 | SVG | `1nfG03x-L8o3aXw6jVOVqesXJCNObiJ1d` | Azul secundario |
| assinatura_metta_branco | PNG | `16t01tM7AQnwHHt2w2sCKl5OuDN0cZeaT` | Branco |
| assinatura_metta_branco | SVG | `1UDca83ltIA640gTyzeFFkrCitf3nj_cq` | Branco |
| assinatura_metta_cinza | PNG | `1CA4M3Jk0-Lg0vfaMM9f3Utl5ldLCerY4` | Cinza |
| assinatura_metta_cinza | SVG | `1om5L1Gr-OUmP1lv55zWeRd69W4zLuDxa` | Cinza |

---

### 12.3 Logo Protocolo Metta
**Pasta**: [Logo Protocolo Metta](https://drive.google.com/drive/folders/1MMSc1AwL8A7sGznoSZ93ZfNb6IOh6Jmm)

| Arquivo | Formato | ID do Drive | Cor |
|---------|---------|-------------|-----|
| Logo Protocolo - Amarelo | PNG | `1TL1HWQJpN9xI8u51R7okcaO8QwEGAK2A` | Amarelo (#FFBE18) |
| Logo Protocolo - Branco | PNG | `1LX8sHyeQLRflCz8YfHgA4SKZmegaaSVW` | Branco (#FFFFFF) |
| Logo Protocolo - Cinza claro | PNG | `1UHfDdPN5K22ztb1vDK5eYAwHBW59_94Z` | Cinza claro |
| Logo Protocolo - Cinza Escuro | PNG | `1sKpln5cKSUWp1Mp-hWhh1xflF2GXDIad` | Cinza escuro |

---

### 12.4 Modelos Reels
**Pasta**: [Modelos Reels](https://drive.google.com/drive/folders/19YMuk58uDSZeyf4jdsRkUYbpcRMESRja)

Templates visuais para reels numerados de 1 a 16:

| Modelo | ID do Drive |
|--------|-------------|
| 1.png | `1aQGMUUrBcUuO9EjcaziF6w-PL3AXSfKy` |
| 2.png | `1jpWzEGomVy3IHXOiaTW08RIIQpSLJBxh` |
| 3.png | `1JD9Wlx53YfCmWYp4t-ehjUU9FHwmU0s4` |
| 4.png | `1UaeIYFGJqr_7XgCXbMSkCOJBGfRbE67v` |
| 5.png | `1w4kqQJ6lwSOOFHCe_8Q5GG6vefn9OAKX` |
| 6.png | `1-FOeSSowAqMd9oBYWLF3j2qnGFVDG7iz` |
| 7.png | `1wJE1Qp62CErh_Ubuyl7GaiwtnEujnZ8l` |
| 8.png | `1khaVtZlDxA1TQQmyyktcPXQGhBQuinWq` |
| 9.png | `1hFPvKnBpG_wme7znd2BUN9zLPKK9bCaB` |
| 10.png | `1HWiSeE4nNIYGpGxaNuIwrfepgNkPJpkd` |
| 11.png | `1XkeRQK-aSOUzzTTcr-7PgX-5ojSKbbm_` |
| 12.png | `1rVlr90QlEqkp72KZthqllDuEZW-Hwhh0` |
| 13.png | `1_YyxJ2pmcVnU8CsYUNO-DTMOOTf2WGRk` |
| 14.png | `1oTm-6DmBWipbP8tNe04BZqTCVDYzgEYA` |
| 15.png | `1G6RYfsq4g1DcWZttXcwN8CDN2wPxoeYW` |
| 16.png | `1seKK7_x7_wkxPfOEAoy_GjRNvw0M-uLT` |

---

### 12.5 Tipografia
**Pasta**: [Tipografia](https://drive.google.com/drive/folders/1XQ2Sw51ZPxmNkArZDTp4Egt7P8Drhyrk)

| Arquivo | ID do Drive | Descricao |
|---------|-------------|-----------|
| fonts-legacy-removed-2026-05-27 | `1SDXY_sNrpM9wMxQ5F2_IHq_boVz8jXoB` | Fonte Zalando Sans Expanded (regular) |
| Inter-Italic-Variable-Official.ttf | `1wuCfL7hwMpOvGJgZwxSyr-NPXMDfxaaL` | Fonte Zalando Sans Expanded (italico) |

---

### 12.6 Guia de Selecao de Assets

#### Qual logo usar?
| Situacao | Asset recomendado | Fundo |
|----------|-------------------|-------|
| Uso principal (destaque) | Logo_metta_colorido_h ou _v | Fundo escuro (#0C161B) |
| Uso sobre fundo claro | Logo_metta_colorido_escuro_h ou _v | Fundo claro (#FFFFFF) |
| Monocromatico sobre escuro | Logo_metta_branco_h ou _v | Fundo escuro |
| Monocromatico sobre claro | Logo_metta_azul_h ou _v | Fundo claro |
| Favicon, icone, espaco reduzido | Simbolo_metta_amarelo ou _branco | Qualquer |
| Rodape, assinatura compacta | assinatura_metta_* | Conforme fundo |
| Com tagline completa | Logo_metta_tagline_colorida_h | Fundo escuro |

#### Qual background usar?
| Situacao | Asset recomendado |
|----------|-------------------|
| Fundo com profundidade premium | bg_gradiente_escuro_1 |
| Fundo amarelo vibrante | bg_gradiente_amarelo_1 |
| Fundo solido amarelo | bg_liso_amarelo_1, _2 ou _3 |
| Fundo solido escuro | bg_liso_azul_1 ou _2 |
| Fundo neutro claro | bg_liso_branco_gelo_1 ou bg_liso_cinza_gelo_1 |
| Fundo cinza intermediario | bg_liso_cinza_1 |

---

### 12.7 Instrucoes para o Agente

1. **Buscar assets do Drive**: Sempre usar os IDs do Google Drive listados acima para baixar/referenciar arquivos. Nunca usar caminhos locais.
2. **Preferir SVG**: Para logos e backgrounds, preferir SVG quando disponivel (melhor qualidade em qualquer escala). Usar PNG quando SVG nao for suportado.
3. **Preferir PNG**: Para modelos de reels (pasta 12.4), usar os PNGs como base/template.
4. **Atualizacao**: Esta secao deve ser atualizada sempre que novos arquivos forem adicionados a pasta do Drive.

---

## 13. Composições Editoriais — Análise da Fonte (Rebranding) [REFERENCE]
> Descreve o que **existe** na fonte Figma. Não autoriza efeitos proibidos por §6.4 — quando §13 menciona blur/glow/shadow, está documentando design legado a ser remediado.

> **Nota:** as orientacoes de cores (secao 3) e tipografia (secao 4) permanecem inalteradas. Esta secao adiciona os padroes de COMPOSICAO e LAYOUT extraidos da analise direta dos frames das paginas "01. Playground" e "04.1 Metta" do arquivo Figma `Rebranding` — complementando o catalogo de estilos existente com especificacoes tecnicas de montagem.
>
> Fonte: [Figma — Rebranding](https://www.figma.com/design/dNVyxGVNxNbE6sA1F7OOXL/Rebranding) · paginas `01. Playground` (6:2) e `04.1 Metta` (427:81)

### 13.1 Formatos de Canvas Usados na Fonte

| Formato | Dimensoes | Uso documentado na fonte |
|---------|-----------|-------------------------|
| Slide 16:9 | 1920x1080 | Apresentacoes comerciais, statements de valor, aplicacoes mockup |
| Poster editorial | 2035x1414 | Posters institucionais print-scale (A5/A4) |
| Feed Instagram | 1080x1350 | Anuncios feed (ja documentado) |
| Story Instagram | 1080x1920 | Stories e reels cover (ja documentado) |

**Nota:** o poster editorial 2035x1414 e uma escala nao documentada no catalogo anterior. E o canvas usado para os posters 4-8 do Playground.

### 13.2 Nomes Reais dos Estilos no Figma

O arquivo Rebranding referencia as duas fontes através de **estilos nomeados** no painel de texto do Figma. Os nomes exatos a usar (e na API) são:

**Display — Zalando Sans Expanded:**

| Estilo no Figma | Peso (wght) | Uso dominante |
|---|---|---|
| `Zalando Sans Expanded / Black` | 900 | Display hero, big numbers |
| `Zalando Sans Expanded / ExtraBold` | 800 | H1 de máximo impacto, nomes em footer |
| `Zalando Sans Expanded / SemiBold` | 650 | Headlines de poster e slide (74-142px) |
| `Zalando Sans Expanded / Medium` | 540 | Labels uppercase, pill tags, badges |
| `Zalando Sans Expanded / Regular` | 410 | Display hero de slide com mixed-weight inline |
| `Zalando Sans Expanded / Light` | 270 | Texto sutil, sub-captions decorativas |

**Body — Inter:**

| Estilo no Figma | Peso (wght) | Uso dominante |
|---|---|---|
| `Inter / SemiBold` | 600 | Sub-headlines, ênfase inline |
| `Inter / Medium` | 500 | Body large, descrições em cards |
| `Inter / Regular` | 400 | Body corrido, role/cargo em credits (16-20px) |
| `Inter / Light` | 300 | Body sutil, taglines |

**Refator de 2026-05-27:** os estilos antigos `Inter / Expanded *` (e antes deles `Inter / Expanded *`) foram substituídos por `Zalando Sans Expanded / *` no Figma. A lógica de "1 fonte com dois eixos de largura via `font-stretch`" foi descontinuada — agora são duas famílias separadas, uma pra display, outra pra body. Em CSS basta `font-family: 'Zalando Sans Expanded'` ou `'Inter'`, sem ajuste de `font-stretch`.

### 13.3 Padrao Editorial Poster

Padrao observado nos frames `poster 5` (221:402) e `poster 6` (222:809) do Playground. Layout de impacto editorial print-scale para aplicacoes institucionais.

**Canvas:** 2035x1414
**Backgrounds validados:** `#0C161B` (azul noite) ou `#435965` (steel-blue como bg primario)

**Camadas (bottom to top):**

1. **Background solido** — cor do token
2. **Wordmark rotado signature** — "metta" lowercase gigante, rotacao 90°, width = altura do canvas (~1415px), flush bleed na borda esquerda, cor em baixo contraste com o bg
3. **Foto dominante** — rounded rectangle mask (~52px radius), ocupando 60-85% do canvas, rotacionada 90° quando o design pedir
4. **Headline central** — Zalando Sans Expanded Semibold 650, **74-137px**, sentence case, cor `#FFFFFF` ou `#EBF3F7`, letter-spacing -5%, line-height 0.9
5. **Sub-caption** (opcional) — Zalando Sans Expanded Semibold 650 em escala menor (~47px), cor `#435965` em bg claro ou card overlay
6. **Pill tag list** — fileira horizontal de servicos (detalhe em 13.5)
7. **Yellow brand band** — faixa horizontal amarela em uma borda do canvas (detalhe em 13.6)
8. **Logo stack compacto** — simbolo + wordmark, canto oposto a brand band (ex: top-right quando band esta bottom)
9. **URL footer** — `METTABRASIL.COM.BR` em Inter Medium 510, 18px, color `#435965`

**Quando usar:** posters institucionais de evento, pecas de feira, material impresso premium, capas de apresentacao.

### 13.4 Padrao Slide Statement

Padrao observado no frame `slide 3` (251:3723) do Playground. Layout de statement de valor comercial com footer de autoria persistente.

**Canvas:** 1920x1080
**Background:** `#0C161B`

**Area principal (y: 0-900):**
- Headline centralizado horizontalmente em x=965 (center)
- Tipografia: **Zalando Sans Expanded Regular 410 a 142.5px**, color `#EBF3F7` (ice-blue)
- Mixed-weight inline: palavras enfaticas trocam para **Expanded Semibold 650** (ex: "parceria", "aumentar o lucro")
- Mixed-color inline: palavras-chave coloridas em `#FFBE18` (amarelo) para destaque semantico
- Line-height 0.82, letter-spacing -1%
- Sentence case — NAO uppercase (ao contrario dos estilos de anuncio conversao A-L)

**Divider (y: 910):**
- Linha horizontal 1810x2px
- Cor `#435965` (steel)
- Margem lateral: 48px

**Footer persistente (y: 940-1018) — 4 colunas:**

| Col | Posicao | Conteudo | Especificacao |
|---|---|---|---|
| 1 | x=48 | Avatar + Name Stack | Ver 13.8 |
| 2 | x=580 | Tagline da marca | "Performance em vendas pode ser mais leve." — Zalando Sans Expanded Medium 540, 19.9px, `#435965`, max-width ~314px |
| 3 | x=1094 | Brand lockup pill | Ver 13.9 |
| 4 | x=1809 | Arrow navigation | Circle 48.6x48.6, icon → (proximo slide) |

**Quando usar:** apresentacoes comerciais, slides de abertura de capitulo, statements de valor com atribuicao de autor.

### 13.5 Pill Tag List (Componente Reusavel)

Componente de tags horizontais para listar servicos/categorias. Encontrado em posters e cards.

**Especificacao do container (cada tag):**
- Shape: rounded pill, radius `23.4px`
- Background: cor do token (ex: `#435965` sobre bg `#0C161B`)
- Border: `0.98px solid` mesma cor do background
- Padding: `14.3px` horizontal x `7.7px` vertical

**Especificacao do texto:**
- Font: **Zalando Sans Expanded Medium 540**
- Size: 9-11px (poster) ou escalar proporcional ao canvas
- Color: contrastante com o bg da pill (ex: `#0C161B` sobre `#435965`)
- Letter-spacing: `+12%` (0.12em)
- Text-transform: UPPERCASE

**Lista oficial de servicos (encontrada em poster 6):**
1. `LIVROS`
2. `TREINAMENTOS`
3. `FORMACOES`
4. `MBA`
5. `MENTORIA`
6. `CONSULTORIA`

**Layout:** horizontal, `inline-flex`, gap 0 ou sem gap entre pills adjacentes.

**Quando usar:** representar o ecossistema de servicos Metta, navegacao por categorias, badges de area em posters/cards.

### 13.6 Yellow Brand Band (Componente Reusavel)

Faixa horizontal full-width em `#FFBE18` que funciona como "assinatura de marca" em posters e layouts institucionais.

**Especificacao:**
- Altura: ~138px (proporcional ao canvas)
- Largura: full width do canvas
- Background: `#FFBE18`
- Padding: 162px horizontal, 35px vertical
- Layout: `flex justify-between items-center`

**Conteudo interno:**
- **Left:** brand lockup stack vertical (simbolo 72x68 + wordmark "metta" 173x68)
- **Right:** label `INTELIGÊNCIA COMERCIAL` em Zalando Sans Expanded Regular 410, 23.4px, color `#0C161B`, letter-spacing -1%

**Variante vertical:** rotacionar 90° para criar um spine na borda lateral do canvas (visto em Poster 6 rodando verticalmente com o logo lockup).

**Quando usar:** ancora de marca em posters editoriais, separador entre areas de conteudo em slides, footer de impacto em material institucional.

### 13.7 Vertical Rotated Wordmark Fragment (Componente Reusavel)

Padrao signature da marca Metta: wordmark "metta" rotacionado 90° e com crop/bleed na borda do canvas.

**Especificacao:**
- Texto: wordmark "metta" (lowercase, Inter style) — usar SVG oficial do Drive quando possivel
- Rotacao: exatamente 90° (vertical, leitura bottom-up)
- Dimensao: width ~265-280px x height = altura do canvas (ex: 1414px em poster A4)
- Posicao: flush bleed na borda **esquerda** do canvas (ou direita em variantes)
- Cor: low-contrast sobre o background
  - Sobre `#0C161B`: branco com opacity 80-100% (quando dominante) OR `#435965` (quando como textura)
  - Sobre `#FFBE18`: `#0C161B`
  - Sobre `#FFFFFF`: light gray #EBF3F7 ou azul #0C161B low opacity
- Z-order: camada de fundo, atras do conteudo principal mas acima do background color

**Quando usar:** posters editoriais, aplicacoes print, slides de statement onde o wordmark vira textura de fundo e ancora de marca.

### 13.8 Avatar + Name Stack (Componente Reusavel)

Padrao de atribuicao/credito usado em slides de statement, business cards e lanyards de evento.

**Especificacao:**
- **Avatar:** circular mask 72x72, foto da pessoa cropada e centralizada
- **Stack textual ao lado direito:**
  - Nome: **Zalando Sans Expanded Heavy 870**, 32.6px, color `#435965` (em slide claro) ou `#FFFFFF` (em dark), letter-spacing -1%, line-height 0.82
  - Role/cargo: **Inter 400**, 16.9px, mesma cor do nome, line-height 0.82
- Gap entre avatar e texto: ~16px
- Alinhamento: avatar esquerda, textos verticalmente centrados (align-items: center)

**Exemplos de uso na fonte:**
- Footer de slides de statement (autor do insight)
- Business cards (poster 4 tipo "card 1")
- Lanyards/crachas de evento (slide "7" mostra 3 exemplos)

### 13.9 Brand Lockup Pill (Componente Reusavel)

Lockup compacto da marca em formato pill horizontal, usado como ancora de brand em footers de slide e material institucional.

**Estrutura interna:**

```
[simbolo 43x41] [wordmark "metta" 93x18] [divider vertical 1x22] [label "INTELIGÊNCIA COMERCIAL"]
```

**Especificacao do container:**
- Shape: rounded pill, radius `46.8px`
- Padding: 16px horizontal, 13px vertical
- Gap interno entre elementos: ~14px

**Elementos:**
- **Simbolo:** icon Metta (imagem do Drive)
- **Wordmark:** "metta" lowercase (imagem ou texto em Inter)
- **Divider:** linha vertical 1x22px, color branco ou `#435965`
- **Label:** `INTELIGÊNCIA COMERCIAL` — Zalando Sans Expanded Regular 410, 17px, white (em dark) ou `#0C161B` (em light), letter-spacing +12%, uppercase

**Quando usar:** footer de slides, assinaturas de email signature, cards de credencial, watermarks institucionais, pop-ups de confirmacao.

### 13.10 Tokens de Layout Confirmados na Fonte

Coordenadas e medidas extraidas diretamente dos frames analisados. Usar como grid de referencia quando montar pecas novas na mesma linha visual.

**Slide 1920x1080 — grid padrao:**

| Elemento | X | Y | W | H |
|---|---|---|---|---|
| Margem lateral | 48 | — | — | — |
| Headline area | 965 (center) | 314 | 1611 | auto |
| Divider horizontal | 48 | 910 | 1810 | 2 |
| Avatar | 48 | 946 | 72 | 72 |
| Tagline column | 580 | 959 | 314 | auto |
| Brand lockup pill | 1094 | 942 | auto | 74 |
| Arrow circle | 1809 | 955 | 48.6 | 48.6 |

**Poster 2035x1414 — grid padrao:**

| Elemento | X | Y | W | H |
|---|---|---|---|---|
| Margem superior | 0 | 26.5 | — | — |
| Wordmark vertical (left bleed) | 0.17 | -0.79 | 280.8 | 1414.8 |
| Logo stack compacto (top-right) | 1933 | 66 | 49 | 138 |
| Headline area (center) | 751 | 204 | 335 | 986 |
| Photo mask (dominant) | 1313 | 0 | 858 | 1816 |
| URL footer | 350 | 1274 | auto | auto |
| Yellow brand band (top ou bottom) | — | — | full | 138 |

### 13.11 Escala de Headline por Canvas

Tamanhos observados na fonte, usar como referencia de Display Hero:

| Canvas | Display Hero | Weight | Notas |
|---|---|---|---|
| 1920x1080 (slide) | **142.5px** | Exp Regular 410 + Semibold 650 inline | tracking -1%, line-height 0.82 |
| 2035x1414 (poster) | 74-137px | Exp Semibold 650 | depende da area disponivel |
| 1080x1350 (feed) | 96-120px | Exp Heavy 870 | ja documentado |
| 1080x1920 (story) | 100-240px | Exp Heavy 870 | ja documentado |

**Correcao vs documentacao anterior:** slides 16:9 usam headlines ate 142.5px (nao 120-136 como citado em algumas tabelas). Posters editoriais podem chegar a 137px em headlines compactos.

### 13.12 Observacoes Finais e Diferencas vs Documentacao Anterior

**Confirmacoes (alinhado com PRD existente):**
- Paleta de cores primarias (#0C161B, #FFBE18, #FFFFFF, #EBF3F7, #435965)
- Inter como familia tipografica unica
- Wordmark como textura/decoracao
- Footer de slide com 4 colunas
- Pills como navegacao de categoria
- Yellow accent sobre dark

**Novas descobertas (adicionar ao repertorio):**
- Canvas editorial poster 2035x1414 (nao documentado antes)
- Zalando Sans Expanded usa `wdth 132`, nao 130
- Steel `#435965` como background PRIMARIO (nao apenas texto secundario)
- Tagline fixa: "Performance em vendas pode ser mais leve."
- Lista oficial de 6 servicos em pill tags (LIVROS, TREINAMENTOS, FORMACOES, MBA, MENTORIA, CONSULTORIA)
- Avatar + Name Stack como componente sistematico
- Slide headline chega a 142.5px (maior que documentado)
- Brand lockup pill tem estrutura exata: simbolo + wordmark + divider vertical + label
- Yellow brand band tem altura exata ~138px com padding 162/35

**Para o fluxo de criacao dentro do Figma via MCP (use_figma), consultar a secao 19 do `Skill - Agente de Design` — contem especificacoes tecnicas de Plugin API, nomes corretos de fontes, padroes de codigo e pitfalls conhecidos.**

---

*Documento gerado a partir da analise do arquivo Figma "Rebranding", pagina "04.1 Metta".*
*Fonte: https://www.figma.com/design/dNVyxGVNxNbE6sA1F7OOXL/Rebranding*
*Assets: https://drive.google.com/drive/folders/1I7W7fYQw1NK4iVhMEkgnWIBjeZZtTQ7u*

---

<!-- AUTO-RELATED-START -->
## 🔗 Documentos Relacionados

**Skill que implementa:**
- [[Skill - Agente de Design]]

**Compilação:**
- [[Metta - Brandbook]]

**Brand System:**
- [[brand-system-spec]] — mini-app de marca consolidado (embarca este PRD na aba Identidade Visual)

<!-- AUTO-RELATED-END -->
