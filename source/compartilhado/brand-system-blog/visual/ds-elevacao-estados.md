# Elevação, Estados e Gradientes

Três sistemas auxiliares que dão **profundidade controlada** à composição: elevação (sombras suaves), estados de interação (overlays) e gradientes (transições oficiais). A Metta opera com paleta restrita nesses três — *editorial, não Material 3D*. Sombras pesadas, glows neon e gradientes coloridos não pertencem ao sistema.

## Elevação

6 níveis de elevação (0 a 5). Sombras **discretas** que criam hierarquia sem peso visual.

<div class="elevation-grid">
  <div class="elev-tile" style="box-shadow:none"><div><strong>Level 0</strong><code>none</code></div></div>
  <div class="elev-tile" style="box-shadow:0 1px 2px rgba(12,22,27,0.05)"><div><strong>Level 1</strong><code>0 1px 2px / .05</code></div></div>
  <div class="elev-tile" style="box-shadow:0 5px 14px rgba(12,22,27,0.06)"><div><strong>Level 2</strong><code>0 5px 14px / .06</code></div></div>
  <div class="elev-tile" style="box-shadow:0 12px 28px rgba(12,22,27,0.08)"><div><strong>Level 3</strong><code>0 12px 28px / .08</code></div></div>
  <div class="elev-tile" style="box-shadow:0 18px 40px rgba(12,22,27,0.11)"><div><strong>Level 4</strong><code>0 18px 40px / .11</code></div></div>
  <div class="elev-tile" style="box-shadow:0 28px 60px rgba(12,22,27,0.14)"><div><strong>Level 5</strong><code>0 28px 60px / .14</code></div></div>
</div>

### Aplicação

| Nível | Onde usar |
|-------|-----------|
| **0** | Fundo padrão sem destaque, blocos editoriais flat, peças de leitura |
| **1** | Card padrão (default do sistema) |
| **2** | Card em hover, dropdown/menu |
| **3** | Card elevated, modal, popover |
| **4** | Hero card, callout máximo |
| **5** | Sticky header em scroll, alerta crítico |

### Regras
- **Level 1** é o default — qualquer card que não pede destaque adicional usa Level 1.
- **Salto de elevação tem propósito**. Subir de Level 1 pra Level 3 sinaliza importância. Pular pra Level 5 sem motivo é ruído.
- **Nunca shadow custom**. Os 6 níveis cobrem 100% dos casos.
- **Em fundo escuro**, sombras perdem efeito visual. Use bordas (`outline-variant`) ou troca de superfície (`surface-container-high`) pra criar hierarquia.

## Estados de interação

Sobreposição **semitransparente de cor inversa** indica estado. Mesmo padrão pra todo elemento interativo (botão, card clicável, chip selecionável).

| Estado | Opacity | Quando aparece |
|--------|---------|----------------|
| **Hover** | 8% | Mouse sobre o elemento |
| **Focus** | 12% | Elemento focado via teclado (acessibilidade) |
| **Pressed** | 16% | Mouse/touch pressionado, click ativo |

### Demonstração

<div class="state-demo-list">
  <div class="state-demo-item">
    <div class="state-pill"><span>Padrão</span></div>
    <div class="state-info">Sem overlay. Background original do componente.</div>
  </div>
  <div class="state-demo-item">
    <div class="state-pill state-hover"><span>Hover · 8%</span></div>
    <div class="state-info">Overlay sutil que indica interatividade ao passar o mouse.</div>
  </div>
  <div class="state-demo-item">
    <div class="state-pill state-pressed"><span>Pressionado · 16%</span></div>
    <div class="state-info">Overlay mais denso confirma o feedback do clique.</div>
  </div>
</div>

### Regras
- **Cor do overlay segue o elemento** — em CTA amarelo, overlay é tom escuro; em CTA escuro, overlay é tom claro.
- **Foco SEMPRE visível** quando navegado por teclado. Acessibilidade não é opcional.
- **Transição de estado** sempre via `motion-duration-short` (200ms) com `motion-easing-standard`. Sem snap brusco, sem fade longo.

## Gradientes

**4 gradientes oficiais**, todos lineares pra controle previsível em qualquer composição. **Roxo, neon e amarelado decorativo são proibidos.** Gradiente é elemento estrutural, não ornamento.

<div class="grad-grid">
  <div class="grad-tile" style="background: linear-gradient(135deg, #FFBE18 0%, #FFD66D 50%, #FFE3A6 100%)">
    <span class="grad-label"><strong>Golden Linear</strong><code>--metta-sys-gradient-golden-linear</code></span>
  </div>
  <div class="grad-tile" style="background: linear-gradient(135deg, #0C161B 0%, #1E2D36 60%, #435965 100%); color: #fff">
    <span class="grad-label"><strong>Night Linear</strong><code>--metta-sys-gradient-night-linear</code></span>
  </div>
  <div class="grad-tile" style="background: linear-gradient(135deg, #FFFFFF 0%, #E0E6E9 100%); color: #0C161B">
    <span class="grad-label"><strong>Light Linear</strong><code>--metta-sys-gradient-light-linear</code></span>
  </div>
  <div class="grad-tile" style="background: linear-gradient(226deg, #FFC443 10%, #FFB618 97%)">
    <span class="grad-label"><strong>Yellow Soft</strong><code>--metta-sys-gradient-yellow-soft</code></span>
  </div>
</div>

### Aplicação

| Gradiente | Onde usar |
|-----------|-----------|
| **Golden Linear** | Hero institucional de alta voltagem, capa de manifesto, frame final de vídeo |
| **Night Linear** | Background de seção dramática, abertura de slide escura, frame de transição |
| **Light Linear** | Fundo neutro com profundidade sutil, hero de peça editorial leve |
| **Yellow Soft** | CTA de destaque máximo, badge premium, faixa de oferta especial |

### Regras
- **Gradiente é fundo**, não ornamento. Não use gradiente em ícone, logo, separator ou texto pequeno.
- **Apenas 1 gradiente por peça**. Misturar Golden + Night na mesma peça quebra a hierarquia.
- **Texto sobre gradiente** sempre validado em contraste contra os dois extremos do gradiente, não só o ponto médio.
- **Direção 135°** é o padrão (Golden, Night, Light). Yellow Soft usa 226° por exceção (capa específica).

## Princípio editorial comum

Os três sistemas têm o mesmo princípio: **profundidade visual controlada**. A Metta não opera com efeitos 3D pesados, drop shadows agressivas ou gradientes coloridos saturados. **Editorial > decorativo**. Quando em dúvida entre uma versão "mais bonita" e uma versão "mais sóbria", escolha a mais sóbria. Marca pesa pela hierarquia, não pelo enfeite.

## Para implementação técnica

Tokens completos, mapeamento Figma e snippets de código ficam no **catálogo técnico do Design System**.
