/* AD ENGINE — auto-fit. Roda no load, antes do screenshot/html2canvas.
 * Reduz a headline (e opcionalmente sub/body) até caber no espaço, resolvendo
 * o defeito do tamanho fixo. Marca data-fit no <html> pra debug/QA. */
(function () {
  function px(el, prop) { return parseFloat(getComputedStyle(el)[prop]) || 0; }

  function fitHead(head) {
    if (!head) return;
    // Container real que limita o texto (não % do canvas). Em archetypes com
    // .layer absoluto inset:0 isso é o canvas; em photo-band/split/bloco é a
    // caixa de texto de fato — é o que evita corte (NEWS-CARD) e estouro (bloco).
    // .obj-text-zone (object-center full) é a mesma ideia: zona com altura
    // própria reservada acima do objeto full-bleed, não o canvas inteiro.
    // .text-panel PRIMEIRO: quando há caixa de texto, o limite do auto-fit é a
    // CAIXA (não a .layer/canvas) — é o que garante a headline encolher pra caber
    // na caixa e NUNCA vazar sobre a parte importante da imagem embaixo.
    var box = head.closest('.text-panel, .versus-col, .zone-head, .half-text, .card, .obj-text-zone, .layer') || head.closest('.ad');
    if (!box) return;
    var floor = 38;
    var size = px(head, 'fontSize');
    var guard = 0;
    var isPanel = box.classList && box.classList.contains('text-panel');
    // encolhe a headline enquanto a caixa transbordar — vertical OU horizontal
    // (horizontal pega palavra longa única que não quebra, ex: split estreito)
    function over() {
      if (box.scrollHeight > box.clientHeight + 2 ||
          head.scrollWidth > head.clientWidth + 2) return true;
      // Na CAIXA capada (max-height) o scrollHeight ignora o padding-bottom
      // quando o conteúdo enche o cap — o CTA assentava RENTE à borda do card
      // (curvatura vazando) em vez de respeitar o respiro. Exige que o último
      // filho caiba COM o padding.
      if (isPanel && box.lastElementChild) {
        var pb = parseFloat(getComputedStyle(box).paddingBottom) || 0;
        return box.lastElementChild.getBoundingClientRect().bottom + pb >
               box.getBoundingClientRect().bottom + 1;
      }
      return false;
    }
    // 1) encolhe se transbordar (copy longa)
    while (over() && size > floor && guard < 90) {
      size -= 2; head.style.fontSize = size + 'px'; guard++;
    }
    // 2) CRESCE até dominar (só typo) — tipografia É o ad; copy curta tem que
    //    encher a tela (DNA do C/H/K). Cresce até a coluna de texto ocupar ~64%
    //    do canvas ou quase transbordar.
    // Calibração pelo banco real (carrosséis): headline-FRASE fica em ~72-110px;
    // só número-hero/1-2 palavras pode ser gigante. O cap cai com o nº de palavras.
    var words = (head.textContent || '').trim().split(/\s+/).length;
    var ad = head.closest('.ad');
    var _arch = ad && ad.getAttribute('data-arch');
    if (_arch === 'typo' || _arch === 'number-hero') {
      var stack = box.querySelector('.stack') || box;
      var cap = _arch === 'number-hero' ? 300
                : (ad.getAttribute('data-scale') === 'giant' ? 210 : 150);
      if (words >= 8) cap = Math.min(cap, 92);
      else if (words >= 5) cap = Math.min(cap, 112);
      var target = box.clientHeight * (_arch === 'number-hero' ? 0.72 : 0.64);
      var g = 0;
      while (stack.offsetHeight < target && !over() && size < cap && g < 140) {
        size += 3; head.style.fontSize = size + 'px'; g++;
      }
      if (over()) { size -= 4; head.style.fontSize = size + 'px'; }
    } else if (box.classList && box.classList.contains('text-panel') &&
               !box.classList.contains('head-band')) {
      // CAIXA com fundo: headline CURTA cresce pra dominar o card (como no banco
      // real, ex: extraia), até a caixa quase encher a altura máx ou transbordar.
      var cap2 = 128, g2 = 0;
      if (words >= 8) cap2 = 92; else if (words >= 5) cap2 = 112;
      while (!over() && size < cap2 && g2 < 120) {
        size += 2; head.style.fontSize = size + 'px'; g2++;
      }
      if (over()) { size -= 2; head.style.fontSize = size + 'px'; }
    }
    // 4) LINHAS CHEIAS (padrão do banco: nenhuma peça real tem escada de 1
    //    palavra por linha gigante). Headline com 3+ palavras precisa de média
    //    >= 2 palavras por linha — senão encolhe até as linhas encherem.
    if (words >= 3) {
      var lh = px(head, 'lineHeight') || size * 0.92;
      var maxLines = Math.max(2, Math.ceil(words / 2.2));
      var g4 = 0;
      while (Math.round(head.offsetHeight / lh) > maxLines && size > floor && g4 < 60) {
        size -= 2; head.style.fontSize = size + 'px';
        lh = px(head, 'lineHeight') || size * 0.92;
        g4++;
      }
    }
    // 3) CASCATA anti-corte da caixa: a .text-panel tem max-height + overflow
    //    hidden — se a headline chegou no piso e o conteúdo AINDA transborda
    //    (sub/body longos), o corte seria SILENCIOSO (CTA sumia sem QA pegar).
    //    Encolhe sub/body até 20px e, em último caso, o respiro da caixa.
    if (box.classList && box.classList.contains('text-panel') && over()) {
      var kids = box.querySelectorAll('.t-sub, .t-body');
      var g3 = 0;
      while (over() && g3 < 40) {
        var shrunk = false;
        for (var ki = 0; ki < kids.length; ki++) {
          var fs = px(kids[ki], 'fontSize');
          if (fs > 20) { kids[ki].style.fontSize = (fs - 1) + 'px'; shrunk = true; }
        }
        if (!shrunk) break;
        g3++;
      }
      if (over()) {
        box.style.padding = '24px 30px';
        box.style.gap = '10px';
      }
      if (over()) {
        // ainda cortando: marca pro QA/visão (copy longa demais pra caixa)
        document.documentElement.setAttribute('data-panel-clipped', '1');
      }
    }
    return size;
  }

  // Dois retângulos se chocam? (horizontal sobrepõe E o texto invade a faixa do
  // CTA + um respiro `gap`). Usa getBoundingClientRect (vivo) — independe do layout.
  function clash(textEl, ctaEl, gap) {
    var a = textEl.getBoundingClientRect(), b = ctaEl.getBoundingClientRect();
    var hov = a.left < b.right && b.left < a.right;
    var vov = a.bottom > b.top - gap && a.top < b.bottom;
    return hov && vov;
  }

  // COLAGEM SEGURA (genérica, vale pra TODOS os 23 archetypes): depois da foto +
  // headline fitada, garante que NENHUM texto fique embaixo do CTA. Não depende de
  // nome de classe — acha qualquer CTA sobreposto (position absolute/fixed) e
  // qualquer texto (h1–h4/p/li) que colida com ele, e encolhe o de MAIOR fonte até
  // liberar. Se nem no piso liberar, devolve true (copy longa demais → data-collision).
  function clearCta(ad) {
    // 1) CTA sobreposto: o wrapper/botão de CTA que está absolute/fixed.
    //    Seletor preciso (evita o prefixo de estilo 'tecta-*' que contém 'cta').
    //    CTA no fluxo normal (tweet/notes) é estático → ignorado.
    var cta = null, ctas = ad.querySelectorAll('[class*="cta-wrap"], .cta, .ad-cta');
    for (var i = 0; i < ctas.length; i++) {
      var p = getComputedStyle(ctas[i]).position;
      if (p === 'absolute' || p === 'fixed') { cta = ctas[i]; break; }
    }
    if (!cta) return false;
    // 2) candidatos de texto: folhas com conteúdo, fora do próprio CTA.
    var nodes = ad.querySelectorAll('h1, h2, h3, h4, p, li');
    var text = [];
    for (var j = 0; j < nodes.length; j++) {
      var el = nodes[j];
      if (cta.contains(el) || el.contains(cta)) continue;
      if (!el.textContent.trim()) continue;
      text.push(el);
    }
    if (!text.length) return false;
    // 3) Enquanto QUALQUER texto colidir, encolhe o MAIOR texto do anúncio (não só
    //    o que colide): em layouts de pilha centrada (typo) quem invade o CTA é o
    //    body, mas quem ocupa o espaço é a headline — reduzi-la levanta a pilha
    //    inteira e tira o body de cima do botão. 2px por vez, até liberar ou piso.
    var gap = 18, floor = 14, guard = 0;
    function anyClash() { for (var k = 0; k < text.length; k++) if (clash(text[k], cta, gap)) return true; return false; }
    while (anyClash() && guard < 400) {
      guard++;
      var target = null, biggest = 0;
      for (var k = 0; k < text.length; k++) {
        var fs = px(text[k], 'fontSize');
        if (fs > floor && fs > biggest) { biggest = fs; target = text[k]; }
      }
      if (!target) break; // todos no piso e ainda colide → overflow real
      target.style.fontSize = (biggest - 2) + 'px';
    }
    return anyClash(); // ainda colide no piso = copy longa demais (sinaliza pro QA)
  }

  function run() {
    var fits = [];
    document.querySelectorAll('.ad .t-head').forEach(function (h) { fits.push(fitHead(h)); });
    document.documentElement.setAttribute('data-fit', fits.join(','));
    // Colagem segura: nenhum texto embaixo do CTA (encolhe até liberar)
    var collide = 0;
    document.querySelectorAll('.ad').forEach(function (ad) {
      if (clearCta(ad)) collide = 1;
    });
    document.documentElement.setAttribute('data-collision', collide);
    // QA: detecta overflow do conteúdo além do canvas (camada .layer/.card)
    var over = collide;
    document.querySelectorAll('.ad').forEach(function (ad) {
      var inner = ad.querySelector('.layer, .card, .half-text');
      if (inner && inner.scrollHeight > inner.clientHeight + 2) over = 1;
      if (ad.scrollHeight > ad.clientHeight + 2) over = 1;
    });
    document.documentElement.setAttribute('data-overflow', over);
    document.documentElement.setAttribute('data-engine-ready', '1');
  }

  var done = false;
  function once() { if (done) return; done = true; run(); }
  function schedule() {
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(once); }
    // Fallback: se fonts.ready não resolver (offline/headless), roda mesmo assim.
    setTimeout(once, 1200);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule);
  } else {
    schedule();
  }
})();
