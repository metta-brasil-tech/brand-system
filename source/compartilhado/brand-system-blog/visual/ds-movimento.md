# Movimento

5 durações + 4 curvas de aceleração. Tom: **sólido, confiante, inevitável**. Nada elástico, nada bouncy, nada que pareça brincadeira de UI infantil. Movimento na Metta serve à hierarquia editorial — mostra causa e consequência, marca transição entre estados, dá ritmo de leitura. **Animações decorativas (parallax exagerado, autoplay de carrossel sem motivo, efeitos hover gratuitos) estão proibidas.**

## Curvas de aceleração

Quatro curvas oficiais. Cada uma cobre um momento específico de animação. **As tiles abaixo rodam em loop infinito** — observe o dot percorrendo a faixa pra sentir a curva.

<div class="motion-grid">
  <div class="motion-tile motion-standard">
    <span class="motion-name">Padrão</span>
    <code class="motion-curve">cubic-bezier(0.4, 0, 0.2, 1)</code>
    <div class="motion-track"><div class="motion-dot"></div></div>
    <p class="motion-desc">Curva neutra. Acelera no início e desacelera no fim. <strong>Default pra mudança de estado, hover, transições UI.</strong></p>
  </div>
  <div class="motion-tile motion-emphasized">
    <span class="motion-name">Enfatizada</span>
    <code class="motion-curve">cubic-bezier(0.2, 0, 0, 1)</code>
    <div class="motion-track"><div class="motion-dot"></div></div>
    <p class="motion-desc">Mais dramática. Aceleração marcante no início, longo deslize no fim. <strong>Pra transições importantes que precisam puxar o olho.</strong></p>
  </div>
  <div class="motion-tile motion-enter">
    <span class="motion-name">Entrada</span>
    <code class="motion-curve">cubic-bezier(0, 0, 0.2, 1)</code>
    <div class="motion-track"><div class="motion-dot"></div></div>
    <p class="motion-desc">Sem aceleração inicial — entra direto e desacelera. <strong>Pra elementos surgindo na tela (modal, dropdown, fade-in).</strong></p>
  </div>
  <div class="motion-tile motion-exit">
    <span class="motion-name">Saída</span>
    <code class="motion-curve">cubic-bezier(0.4, 0, 1, 1)</code>
    <div class="motion-track"><div class="motion-dot"></div></div>
    <p class="motion-desc">Acelera continuamente até sair. <strong>Pra elementos saindo da tela (modal fechando, dismiss, fade-out).</strong></p>
  </div>
</div>

## Duração

Cinco valores de duração. **Mesma escala 8-pontos do espaçamento aplicada ao tempo** — escolha durações dentro da família, nunca arbitrário.

<div class="spacing-list">
  <div class="spacing-row"><span class="name">duration-instant</span><span class="value">50ms</span><div class="bar" style="width:7%"></div></div>
  <div class="spacing-row"><span class="name">duration-short</span><span class="value">200ms</span><div class="bar" style="width:28%"></div></div>
  <div class="spacing-row"><span class="name">duration-medium</span><span class="value">300ms</span><div class="bar" style="width:42%"></div></div>
  <div class="spacing-row"><span class="name">duration-long</span><span class="value">500ms</span><div class="bar" style="width:71%"></div></div>
  <div class="spacing-row"><span class="name">duration-x-long</span><span class="value">700ms</span><div class="bar" style="width:100%"></div></div>
</div>

### Aplicação típica

| Duração | Uso |
|---------|-----|
| **instant (50ms)** | Highlight de seleção, feedback tátil instantâneo |
| **short (200ms)** | Hover, focus, mudança de estado de UI (default da maioria) |
| **medium (300ms)** | Transição entre views, dropdown abrindo, card flip |
| **long (500ms)** | Modal entrada/saída, hero reveal em LP, animação narrativa |
| **x-long (700ms)** | Animação cinematográfica de capa, sequência multi-stage |

## Padrões editoriais de movimento

5 padrões reusáveis em LPs, hero sections e stories. Auto-iniciam via `data-*` attributes e respeitam `prefers-reduced-motion` (acessibilidade). **Cada exemplo abaixo está rodando ao vivo** — clique em "Repetir" pra ver de novo.

### 1. Reveal

Elementos surgem em sequência conforme entram na viewport. Combina **fade-in + translate-Y sutil** (8 a 16px de baixo pra cima). Use em listas, cards de feature, blocos de section longa.

<div class="motion-demo">
  <div class="motion-demo-stage">
    <div class="motion-block" data-motion="reveal" data-motion-demo="block">
      <strong class="motion-block-title">Demita o achismo</strong>
      <span class="motion-block-sub">Construa método.</span>
    </div>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">data-motion="reveal"</code>
    <button class="motion-replay" data-rerun="block">Repetir</button>
  </div>
</div>

**Stagger** — múltiplos elementos com delay incremental:

<div class="motion-demo">
  <div class="motion-demo-stage">
    <div class="motion-stagger" data-motion-demo="stagger">
      <div data-motion="reveal" style="--reveal-delay:0ms"></div>
      <div data-motion="reveal" style="--reveal-delay:120ms"></div>
      <div data-motion="reveal" style="--reveal-delay:240ms"></div>
      <div data-motion="reveal" style="--reveal-delay:360ms"></div>
      <div data-motion="reveal" style="--reveal-delay:480ms"></div>
    </div>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">stagger 80–120ms</code>
    <button class="motion-replay" data-rerun="stagger">Repetir</button>
  </div>
</div>

- Curva: **Entrada** (`cubic-bezier(0, 0, 0.2, 1)`)
- Duração: `medium` (300ms) por elemento
- Stagger entre elementos: 80–120ms

### 2. Magnetic

Hover sutil em CTA — botão "puxa" levemente em direção ao cursor. Cria sensação de **resposta tátil** sem teatralidade. **Passe o mouse no botão abaixo.**

<div class="motion-demo">
  <div class="motion-demo-stage">
    <button class="ds-cta ds-cta-yellow" data-motion="magnetic">Passe o mouse</button>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">data-motion="magnetic"</code>
    <span class="motion-note">desativa em mobile · respeita reduced motion</span>
  </div>
</div>

- Curva: **Padrão**
- Duração: `short` (200ms)
- Translate máximo: 6px

### 3. Counter

Números crescem de 0 ao valor final em scroll. Usado em métricas hero (faturamento, número de empresas, anos de mercado).

<div class="motion-demo">
  <div class="motion-demo-stage">
    <span class="motion-counter" data-motion="counter" data-to="47" data-prefix="+" data-suffix="%" data-duration="1500" data-motion-demo="counter">+0%</span>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">data-motion="counter"</code>
    <button class="motion-replay" data-rerun="counter">Repetir</button>
  </div>
</div>

- Curva: **Enfatizada** (acelera, depois desacelera)
- Duração: `long` (500ms) ou `x-long` (700ms) conforme magnitude do número
- Easing aplicado ao valor numérico, não só ao estilo CSS

### 4. Ken Burns

Zoom lento em foto de hero. Cria sensação cinematográfica sem distrair do conteúdo. Usado apenas em capa/abertura — nunca em foto de meio de peça.

<div class="motion-demo">
  <div class="motion-demo-stage motion-demo-stage--photo">
    <div class="motion-kenburns" aria-hidden="true"></div>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">scale 1.0 → 1.06 · 10s loop</code>
    <span class="motion-note">linear · sem easing</span>
  </div>
</div>

- Curva: **Linear** (sem easing pra movimento contínuo)
- Duração: 8s a 12s (loop sutil)
- Scale: 1.0 → 1.06 (nunca mais que 8% — vira efeito de pós-produção barato)

### 5. Tipo-machine (mecanografia controlada)

Texto aparece letra por letra. Usado em **manifesto narrativo, abertura de VSL**. Diferente do efeito "typewriter" comum: sem cursor piscando, sem som de máquina, sem aceleração visível.

<div class="motion-demo">
  <div class="motion-demo-stage">
    <p class="motion-typewriter" data-motion="typewriter" data-speed="42" data-motion-demo="typewriter">Quem ganha não improvisa o método.</p>
  </div>
  <div class="motion-demo-meta">
    <code class="motion-attr">data-motion="typewriter"</code>
    <button class="motion-replay" data-rerun="typewriter">Repetir</button>
  </div>
</div>

- Velocidade: 30–40ms por caractere
- Pausas em pontuação forte (ponto final, travessão)
- Curva linear

## Princípios invioláveis

### O que NUNCA fazer
- **Bouncy / spring / overshoot.** Animação que "passa do ponto e volta" não pertence à marca.
- **Easter eggs visuais.** Confete, animação especial em hover de logo, mascote piscando — tudo proibido. Marca não brinca.
- **Autoplay de vídeo com som.** Som ativa só por ação do usuário.
- **Carrossel automático sem controle do usuário.** Permite navegação manual sempre.
- **Animação > 1s sem propósito narrativo.** Se não está contando história, mais curta.
- **Ignorar `prefers-reduced-motion`.** Toda animação respeita a preferência do usuário.

### O que SEMPRE fazer
- **Movimento serve à hierarquia.** Pergunta antes de animar: o que isso comunica? Se a resposta é "fica bonito", remova.
- **Curva consistente** dentro do mesmo padrão de UI. Hover de todos os botões usa a mesma curva.
- **Duração proporcional à distância.** Elemento que se move 8px usa `short` (200ms). Elemento que se move 200px usa `medium` (300ms).
- **Reduced motion = sem animação.** Não substitua por versão mais lenta — desligue completamente.

## Para implementação técnica

Helper `motion.js` com auto-trigger via `data-*` attributes, snippets de Web Animations API, exemplos de implementação em React/Vue e referência completa de tokens CSS ficam no **catálogo técnico do Design System**.
