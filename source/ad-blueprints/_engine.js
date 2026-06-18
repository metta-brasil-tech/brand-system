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
    var _arch = ad && ad.getAttribute('data-arch');
    if (_arch === 'typo' || _arch === 'number-hero') {
      var stack = box.querySelector('.stack') || box;
      var cap = _arch === 'number-hero' ? 300
                : (ad.getAttribute('data-scale') === 'giant' ? 210 : 150);
      var target = box.clientHeight * (_arch === 'number-hero' ? 0.72 : 0.64);
      var g = 0;
      while (stack.offsetHeight < target && !over() && size < cap && g < 140) {
        size += 3; head.style.fontSize = size + 'px'; g++;
      }
      if (over()) { size -= 4; head.style.fontSize = size + 'px'; }
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

  // COLAGEM SEGURA: depois da foto + da headline fitada, garante que o texto
  // (headline → body → sub) NÃO fique embaixo do CTA. O CTA é absolute/bottom em
  // photo-side/typo, então uma headline alta empurra o body pra dentro dele.
  // Encolhe na ordem certa até liberar; se nem no piso liberar, marca colisão.
  function clearCta(ad) {
    var cta = ad.querySelector('.cta-wrap, .teh-cta-wrap, .tecta-cta-wrap, .tch-cta-wrap, .tyb-cta-wrap');
    if (!cta) return false;
    // Só importa quando o CTA é sobreposto (absolute/fixed). CTA no fluxo nunca colide.
    var pos = getComputedStyle(cta).position;
    if (pos !== 'absolute' && pos !== 'fixed') return false;
    var stack = ad.querySelector('.stack') || ad.querySelector('.layer');
    if (!stack) return false;
    var head = ad.querySelector('.t-head');
    var body = ad.querySelector('.t-body, .bullets, .t-list');
    var sub  = ad.querySelector('.t-sub');
    var gap = 20, floorHead = 30, floorTxt = 14, guard = 0;
    function hit() { return clash(stack, cta, gap); }
    while (hit() && guard < 200) {
      guard++;
      var hs = head ? px(head, 'fontSize') : 0;
      if (head && hs > floorHead) { head.style.fontSize = (hs - 2) + 'px'; continue; }
      var bs = body ? px(body, 'fontSize') : 0;
      if (body && bs > floorTxt) { body.style.fontSize = (bs - 1) + 'px'; continue; }
      var ss = sub ? px(sub, 'fontSize') : 0;
      if (sub && ss > floorTxt) { sub.style.fontSize = (ss - 1) + 'px'; continue; }
      break; // nada mais pra encolher
    }
    return hit(); // ainda colide no piso = overflow real (sinaliza pro QA)
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
