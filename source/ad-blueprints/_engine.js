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
    var box = head.closest('.layer, .half-text, .card') || head.closest('.ad');
    if (!box) return;
    var floor = 38;
    var size = px(head, 'fontSize');
    var guard = 0;
    // encolhe a headline enquanto a caixa transbordar — vertical OU horizontal
    // (horizontal pega palavra longa única que não quebra, ex: split estreito)
    function over() {
      return box.scrollHeight > box.clientHeight + 2 ||
             head.scrollWidth > head.clientWidth + 2;
    }
    // 1) encolhe se transbordar (copy longa)
    while (over() && size > floor && guard < 90) {
      size -= 2; head.style.fontSize = size + 'px'; guard++;
    }
    // 2) CRESCE até dominar (só typo) — tipografia É o ad; copy curta tem que
    //    encher a tela (DNA do C/H/K). Cresce até a coluna de texto ocupar ~64%
    //    do canvas ou quase transbordar.
    var ad = head.closest('.ad');
    if (ad && ad.getAttribute('data-arch') === 'typo') {
      var stack = box.querySelector('.stack') || box;
      var cap = (ad.getAttribute('data-scale') === 'giant') ? 210 : 150;
      var target = box.clientHeight * 0.64;
      var g = 0;
      while (stack.offsetHeight < target && !over() && size < cap && g < 140) {
        size += 3; head.style.fontSize = size + 'px'; g++;
      }
      if (over()) { size -= 4; head.style.fontSize = size + 'px'; }
    }
    return size;
  }

  function run() {
    var fits = [];
    document.querySelectorAll('.ad .t-head').forEach(function (h) { fits.push(fitHead(h)); });
    document.documentElement.setAttribute('data-fit', fits.join(','));
    // QA: detecta overflow do conteúdo além do canvas (camada .layer/.card)
    var over = 0;
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
