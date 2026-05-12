# Cores

A paleta da Metta é composta por **duas paletas-mãe** (Yellow e Night) e um conjunto de **funções de cor** (System Tokens) que decidem onde cada tom é aplicado em interface, peça editorial e ambiente. Toda cor que aparece em qualquer peça da marca vem desse sistema — não há cor improvisada, não há tom criado caso a caso. A regra editorial central segue: **neutros dominam, amarelo é assinatura, charcoal sustenta autoridade.**

## Como ler esta página

O sistema opera em **três camadas**:

1. **Reference Tokens** — as paletas-mãe Yellow e Night. São os tons brutos.
2. **System Tokens** — as funções de cor (primary, surface, on-surface, outline). Decidem qual tom da paleta vai onde.
3. **Component Tokens** — específicos de componente (botão CTA, card, pill). Herdam dos System Tokens.

Em peças editoriais e código de UI, **referencie sempre System Tokens** (`--metta-sys-color-primary`), nunca Reference Tokens diretamente. Isso garante que o tema (light/dark) e futuros refinamentos da paleta funcionem sem refatorar.

## Paleta Yellow

A cor de assinatura da Metta. **`yellow-50` (#FFBE18) é o amarelo institucional** — usado em destaques, faixas, elementos de marca. Os tons mais escuros (30-40) servem para texto sobre fundo claro; os mais claros (80-99) para containers, tints e backgrounds em situações específicas.

<div class="swatch-grid">
  <div class="swatch" style="background:#B38400;color:#fff" data-hex="#B38400" tabindex="0" role="button" aria-label="Copiar #B38400"><div class="swatch-meta"><strong>yellow-30</strong></div></div>
  <div class="swatch" style="background:#D9A100;color:#0C161B" data-hex="#D9A100" tabindex="0" role="button" aria-label="Copiar #D9A100"><div class="swatch-meta"><strong>yellow-40</strong></div></div>
  <div class="swatch" style="background:#FFBE18;color:#0C161B" data-hex="#FFBE18" tabindex="0" role="button" aria-label="Copiar #FFBE18" data-anchor="brand"><div class="swatch-meta"><strong>yellow-50</strong></div></div>
  <div class="swatch" style="background:#FFB618;color:#0C161B" data-hex="#FFB618" tabindex="0" role="button" aria-label="Copiar #FFB618"><div class="swatch-meta"><strong>yellow-55</strong></div></div>
  <div class="swatch" style="background:#FFC531;color:#0C161B" data-hex="#FFC531" tabindex="0" role="button" aria-label="Copiar #FFC531"><div class="swatch-meta"><strong>yellow-60</strong></div></div>
  <div class="swatch" style="background:#FFCE50;color:#0C161B" data-hex="#FFCE50" tabindex="0" role="button" aria-label="Copiar #FFCE50"><div class="swatch-meta"><strong>yellow-70</strong></div></div>
  <div class="swatch" style="background:#FFD66D;color:#0C161B" data-hex="#FFD66D" tabindex="0" role="button" aria-label="Copiar #FFD66D"><div class="swatch-meta"><strong>yellow-80</strong></div></div>
  <div class="swatch" style="background:#FFE3A6;color:#0C161B" data-hex="#FFE3A6" tabindex="0" role="button" aria-label="Copiar #FFE3A6"><div class="swatch-meta"><strong>yellow-90</strong></div></div>
  <div class="swatch" style="background:#FFE4A1;color:#0C161B" data-hex="#FFE4A1" tabindex="0" role="button" aria-label="Copiar #FFE4A1"><div class="swatch-meta"><strong>yellow-95</strong></div></div>
  <div class="swatch" style="background:#FFFAEC;color:#0C161B" data-hex="#FFFAEC" tabindex="0" role="button" aria-label="Copiar #FFFAEC"><div class="swatch-meta"><strong>yellow-99</strong></div></div>
</div>

## Paleta Night

A paleta neutra que sustenta toda a hierarquia tipográfica e estrutural. **`night-10` (#0C161B) é o charcoal institucional** — usado em fundos escuros de manifesto, destaques de alta voltagem, blocos editoriais densos. Os tons claros (95-100) são as superfícies padrão das peças em modo claro.

<div class="swatch-grid">
  <div class="swatch" style="background:#0A1013;color:#fff" data-hex="#0A1013" tabindex="0" role="button" aria-label="Copiar #0A1013"><div class="swatch-meta"><strong>night-5</strong></div></div>
  <div class="swatch" style="background:#0C161B;color:#fff" data-hex="#0C161B" tabindex="0" role="button" aria-label="Copiar #0C161B" data-anchor="brand"><div class="swatch-meta"><strong>night-10</strong></div></div>
  <div class="swatch" style="background:#131F25;color:#fff" data-hex="#131F25" tabindex="0" role="button" aria-label="Copiar #131F25"><div class="swatch-meta"><strong>night-15</strong></div></div>
  <div class="swatch" style="background:#1A2A35;color:#fff" data-hex="#1A2A35" tabindex="0" role="button" aria-label="Copiar #1A2A35"><div class="swatch-meta"><strong>night-20</strong></div></div>
  <div class="swatch" style="background:#1E2D36;color:#fff" data-hex="#1E2D36" tabindex="0" role="button" aria-label="Copiar #1E2D36"><div class="swatch-meta"><strong>night-25</strong></div></div>
  <div class="swatch" style="background:#2E3E47;color:#fff" data-hex="#2E3E47" tabindex="0" role="button" aria-label="Copiar #2E3E47"><div class="swatch-meta"><strong>night-30</strong></div></div>
  <div class="swatch" style="background:#435965;color:#fff" data-hex="#435965" tabindex="0" role="button" aria-label="Copiar #435965"><div class="swatch-meta"><strong>night-40</strong></div></div>
  <div class="swatch" style="background:#688594;color:#fff" data-hex="#688594" tabindex="0" role="button" aria-label="Copiar #688594"><div class="swatch-meta"><strong>night-50</strong></div></div>
  <div class="swatch" style="background:#75919F;color:#fff" data-hex="#75919F" tabindex="0" role="button" aria-label="Copiar #75919F"><div class="swatch-meta"><strong>night-60</strong></div></div>
  <div class="swatch" style="background:#94B5C8;color:#0C161B" data-hex="#94B5C8" tabindex="0" role="button" aria-label="Copiar #94B5C8"><div class="swatch-meta"><strong>night-70</strong></div></div>
  <div class="swatch" style="background:#A8B3B9;color:#0C161B" data-hex="#A8B3B9" tabindex="0" role="button" aria-label="Copiar #A8B3B9"><div class="swatch-meta"><strong>night-80</strong></div></div>
  <div class="swatch" style="background:#B0CAD8;color:#0C161B" data-hex="#B0CAD8" tabindex="0" role="button" aria-label="Copiar #B0CAD8"><div class="swatch-meta"><strong>night-85</strong></div></div>
  <div class="swatch" style="background:#C9DAE3;color:#0C161B" data-hex="#C9DAE3" tabindex="0" role="button" aria-label="Copiar #C9DAE3"><div class="swatch-meta"><strong>night-90</strong></div></div>
  <div class="swatch" style="background:#EBF3F7;color:#0C161B" data-hex="#EBF3F7" tabindex="0" role="button" aria-label="Copiar #EBF3F7"><div class="swatch-meta"><strong>night-95</strong></div></div>
  <div class="swatch" style="background:#EFF3F5;color:#0C161B" data-hex="#EFF3F5" tabindex="0" role="button" aria-label="Copiar #EFF3F5"><div class="swatch-meta"><strong>night-97</strong></div></div>
  <div class="swatch" style="background:#FAFCFD;color:#0C161B" data-hex="#FAFCFD" tabindex="0" role="button" aria-label="Copiar #FAFCFD" data-anchor="brand"><div class="swatch-meta"><strong>night-99</strong></div></div>
  <div class="swatch" style="background:#FFFFFF;color:#0C161B;border:1px solid #EBF3F7"><div class="swatch-meta"><strong>night-100</strong><code>#FFFFFF</code></div></div>
</div>

## Funções de cor

Os **System Tokens** mapeiam funções específicas para tons da paleta. São o que código e peças devem referenciar — nunca o HEX bruto. Tabela abaixo mostra o mapeamento para o tema **claro** (default das peças Metta).

### Marca

| Token | Mapeia para | Uso |
|-------|-------------|-----|
| `--metta-sys-color-primary` | `yellow-50` (#FFBE18) | Cor de marca. CTA primário, faixas de destaque, marcadores editoriais. |
| `--metta-sys-color-on-primary` | `night-10` (#0C161B) | Texto/ícone sobre fundo primário. |
| `--metta-sys-color-primary-hover` | `yellow-60` (#FFC531) | Estado hover de elementos primary. |
| `--metta-sys-color-primary-pressed` | `yellow-55` (#FFB618) | Estado pressed/active. |
| `--metta-sys-color-primary-container` | `yellow-95` (#FFE4A1) | Container destacado em fundo claro (badge, tint). |
| `--metta-sys-color-on-primary-container` | `night-10` | Texto sobre container primário. |

### Superfícies

| Token | Mapeia para | Uso |
|-------|-------------|-----|
| `--metta-sys-color-surface` | `night-100` (#FFFFFF) | Fundo padrão da peça/UI. |
| `--metta-sys-color-surface-container-low` | `night-99` (#FAFCFD) | Cards e blocos sutilmente destacados. |
| `--metta-sys-color-surface-container` | `night-97` (#EFF3F5) | Cards de média elevação. |
| `--metta-sys-color-surface-container-high` | `night-95` (#EBF3F7) | Cards mais destacados, sidebars. |
| `--metta-sys-color-surface-container-highest` | `#E0E6E9` | Estados ativos, controles selecionados. |
| `--metta-sys-color-on-surface` | `night-10` (#0C161B) | Texto principal sobre superfície. |
| `--metta-sys-color-on-surface-variant` | `night-40` (#435965) | Texto secundário, captions, metadados. |

### Estrutura

| Token | Mapeia para | Uso |
|-------|-------------|-----|
| `--metta-sys-color-outline` | `night-97` (#EFF3F5) | Bordas estruturais (cards, divisores). |
| `--metta-sys-color-outline-variant` | `rgba(202,217,224,0.87)` | Bordas mais sutis, separadores. |
| `--metta-sys-color-background` | = surface | Background absoluto da página. |
| `--metta-sys-color-on-background` | = on-surface | Texto sobre background. |

### Inverso (peças escuras dentro do tema claro)

| Token | Mapeia para | Uso |
|-------|-------------|-----|
| `--metta-sys-color-inverse-surface` | `night-10` (#0C161B) | Fundo escuro de bloco "manifesto" embutido em peça clara. |
| `--metta-sys-color-inverse-on-surface` | `night-99` (#FAFCFD) | Texto sobre fundo escuro inverso. |
| `--metta-sys-color-inverse-primary` | `yellow-80` (#FFD66D) | Primary ajustado para contraste em fundo escuro. |

## Tema escuro

Quando a peça opera em modo escuro (manifesto, capa de seção dramática, abertura de slide), o sistema reorganiza os tokens. O **primary continua sendo `yellow-50`**, mas as superfícies trocam de side: `surface` vira `night-10`, on-surface vira `night-100`, container-high passa para `night-25`. A regra do amarelo como assinatura única se mantém.

## Regras de aplicação

### Predominância
Neutros (branco gelo, gelo azul, charcoal) cobrem a maior parte de qualquer peça. **Amarelo cobre no máximo 5 a 10%.** Peça com fundo amarelo dominante quebra o sistema.

### Alternância de fundos em peça longa
Sections consecutivas devem alternar entre `surface-container-low` (#FAFCFD) e `surface-container-high` (#EBF3F7) para criar ritmo sem precisar de divisores explícitos. Manifesto pode quebrar essa alternância usando `inverse-surface` (charcoal) como bloco dramático.

### Contraste mínimo
- **Texto corrido** sobre fundo: 4.5:1 (WCAG AA)
- **Texto pequeno** (<14px): 7:1
- **Elementos de UI** (bordas, ícones funcionais): 3:1

A paleta é desenhada para que `on-surface` sobre `surface` cumpra os mínimos automaticamente. Combinações fora do sistema (ex: `night-50` sobre `surface`) precisam validação manual.

### O que NÃO fazer
- Aplicar amarelo como fundo dominante de peça inteira
- Usar Reference Tokens diretamente em código (sempre prefira System Tokens)
- Criar tons fora da paleta para "harmonizar" com foto ou contexto
- Misturar `night-50` (cinza médio) com texto fino — contraste insuficiente
- Aplicar `primary-container` (yellow-95) em texto pequeno ou ícone — função é container, não conteúdo

## Para implementação técnica

Tokens completos como CSS variables, JSON, código Figma e exemplos de aplicação em componentes ficam na **documentação técnica do Design System** (módulo Tokens). Esta página cobre a camada institucional — as decisões editoriais que governam o uso. Para a referência exaustiva de cada variável, busque o catálogo técnico.
