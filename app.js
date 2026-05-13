/* ============================================================
   METTA BRAND SYSTEM — APP CLIENT
   Sidebar render + hash routing + theme toggle + content lazy load
============================================================ */

const BrandSystem = (() => {
  let nav = null;
  let currentTabId = null;
  let currentSectionId = null;

  // ----------- ICON SET (estilo DS v2) -----------
  // viewBox 0 0 24 24 · stroke currentColor · stroke-width 2.2
  // linecap/linejoin round · fill none
  const ICONS = {
    home:    '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2h-4v-7H10v7H6a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    compass: '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    users:   '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    type:    '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>',
    palette: '<circle cx="13.5" cy="6.5" r="1.5"/><circle cx="17.5" cy="10.5" r="1.5"/><circle cx="8.5" cy="7.5" r="1.5"/><circle cx="6.5" cy="12.5" r="1.5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.6-.7 1.6-1.6 0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1 0-.9.7-1.6 1.6-1.6H16c3.3 0 6-2.7 6-6 0-5.5-4.5-10-10-10z"/>',
    camera:  '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
    package: '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    layers:  '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    external:'<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    target:   '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    'trending-up': '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    briefcase:'<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    quote:    '<path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 2v6c0 1.25.75 2 2 2h2c0 4-2 5-3 5"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 2v6c0 1.25.75 2 2 2h2c0 4-2 5-3 5"/>',
    mic:      '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
    arrowLeft:'<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>',
    youtube:  '<path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"/><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"/>',
    clock:    '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    search:   '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    link:     '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    check:    '<polyline points="20 6 9 17 4 12"/>'
  };

  // ----------- DATA UTILS -----------
  function formatUpdatedAt(iso) {
    if (!iso) return '';
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '';
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays < 1) return 'atualizado hoje';
    if (diffDays === 1) return 'atualizado ontem';
    if (diffDays < 7) return `atualizado há ${diffDays} dias`;
    if (diffDays < 30) {
      const w = Math.floor(diffDays / 7);
      return `atualizado há ${w} ${w === 1 ? 'semana' : 'semanas'}`;
    }
    const meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
    return `atualizado em ${date.getDate()} ${meses[date.getMonth()]} ${date.getFullYear()}`;
  }

  function svgIcon(name, size = 18) {
    const inner = ICONS[name] || '';
    return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
  }

  // ----------- THEME -----------
  function initTheme() {
    const saved = localStorage.getItem('brand-theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    document.querySelectorAll('.theme-toggle button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === saved);
    });
  }
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('brand-theme', theme);
    document.querySelectorAll('.theme-toggle button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === theme);
    });
  }

  // ----------- NAV RENDER -----------
  async function loadNav() {
    const res = await fetch('data/nav.json');
    nav = await res.json();
    renderSidebar();
  }

  function renderSidebar() {
    const container = document.getElementById('nav-tabs');
    if (!container) return;

    const groups = {};
    nav.tabs.forEach(tab => {
      const g = tab.group || 'principal';
      if (!groups[g]) groups[g] = [];
      groups[g].push(tab);
    });

    container.innerHTML = '';
    Object.entries(groups).forEach(([groupName, tabs]) => {
      const groupEl = document.createElement('div');
      groupEl.className = 'nav-group';
      const labelEl = document.createElement('div');
      labelEl.className = 'nav-group-label';
      labelEl.textContent = groupName;
      groupEl.appendChild(labelEl);

      tabs.forEach(tab => {
        const btn = document.createElement('button');
        btn.className = 'tab';
        btn.dataset.tabId = tab.id;
        btn.dataset.label = tab.label;
        btn.innerHTML = `<span class="icon">${svgIcon(tab.icon, 18)}</span><span class="label">${tab.label}</span>`;
        btn.addEventListener('click', () => {
          const firstSec = tab.sections.find(s => !s.hidden) || tab.sections[0];
          navigate(tab.id, firstSec ? firstSec.id : null);
        });
        groupEl.appendChild(btn);

        const subnav = document.createElement('div');
        subnav.className = 'subnav';
        subnav.dataset.parent = tab.id;

        // Sections visíveis (filtra hidden — usadas só pra roteamento de transcrições)
        const visibleSections = tab.sections.filter(s => !s.hidden);

        // Quando a aba tem só 1 section visível sem subgroup, esconde a subnav (redundante).
        if (visibleSections.length === 1 && !visibleSections[0].subgroup) {
          subnav.classList.add('hidden-single');
        }

        let lastSubgroup = null;
        visibleSections.forEach(sec => {
          // Render subgroup label se mudou
          if (sec.subgroup && sec.subgroup !== lastSubgroup) {
            const sgLabel = document.createElement('div');
            sgLabel.className = 'subnav-group-label';
            sgLabel.textContent = sec.subgroupLabel || sec.subgroup;
            subnav.appendChild(sgLabel);
            lastSubgroup = sec.subgroup;
          } else if (!sec.subgroup) {
            lastSubgroup = null;
          }

          const a = document.createElement('a');
          a.href = `#/${tab.id}/${sec.id}`;
          a.dataset.tabId = tab.id;
          a.dataset.sectionId = sec.id;
          a.textContent = sec.label;
          if (sec.highlight) a.classList.add('highlight');
          if (sec.placeholder) a.classList.add('placeholder');
          if (sec.subgroup) a.classList.add('subgroup-item');
          a.addEventListener('click', (e) => {
            e.preventDefault();
            navigate(tab.id, sec.id);
          });
          subnav.appendChild(a);
        });
        groupEl.appendChild(subnav);
      });

      container.appendChild(groupEl);
    });
  }

  // ----------- ROUTING -----------
  function parseHash() {
    const h = location.hash.replace(/^#\/?/, '').split('?')[0];
    const [tabId, sectionId] = h.split('/');
    return { tabId: tabId || null, sectionId: sectionId || null };
  }

  function navigate(tabId, sectionId) {
    location.hash = `#/${tabId}` + (sectionId ? `/${sectionId}` : '');
  }

  function onHashChange() {
    let { tabId, sectionId } = parseHash();
    if (!tabId) {
      tabId = nav.tabs[0].id;
      sectionId = (nav.tabs[0].sections.find(s => !s.hidden) || nav.tabs[0].sections[0])?.id || null;
    }
    const tab = nav.tabs.find(t => t.id === tabId);
    if (!tab) return;
    if (!sectionId) sectionId = (tab.sections.find(s => !s.hidden) || tab.sections[0])?.id || null;

    currentTabId = tabId;
    currentSectionId = sectionId;
    updateActiveStates();
    updateBreadcrumb(tab, sectionId);
    loadSection(tab, sectionId);
  }

  function updateActiveStates() {
    document.querySelectorAll('aside.nav .tab').forEach(b => {
      b.classList.toggle('active', b.dataset.tabId === currentTabId);
    });
    document.querySelectorAll('aside.nav .subnav').forEach(sn => {
      sn.classList.toggle('open', sn.dataset.parent === currentTabId);
    });
    document.querySelectorAll('aside.nav .subnav a').forEach(a => {
      a.classList.toggle(
        'active',
        a.dataset.tabId === currentTabId && a.dataset.sectionId === currentSectionId
      );
    });
  }

  function updateBreadcrumb(tab, sectionId) {
    const sec = tab.sections.find(s => s.id === sectionId);
    const el = document.getElementById('breadcrumb');
    if (!el) return;
    const subgroup = sec?.subgroupLabel || (sec?.subgroup && tab.sections.find(s => s.subgroup === sec.subgroup && s.subgroupLabel)?.subgroupLabel);
    const subgroupHtml = subgroup ? `<span class="sep">/</span><span>${subgroup}</span>` : '';
    el.innerHTML = `
      <span class="breadcrumb-icon">${svgIcon(tab.icon, 14)}</span>
      <span>${tab.label}</span>
      ${subgroupHtml}
      ${sec ? `<span class="sep">/</span><span class="current">${sec.label}</span>` : ''}
    `;
  }

  // ----------- CONTENT LOAD -----------
  async function loadSection(tab, sectionId) {
    const main = document.getElementById('content');
    if (!main) return;
    main.dataset.loading = 'true';
    main.innerHTML = '';

    const sec = tab.sections.find(s => s.id === sectionId);

    if (tab.id === 'overview') {
      main.dataset.loading = 'false';
      main.innerHTML = renderOverview();
      attachOverviewLinks();
      return;
    }

    if (sec && sec.source && sec.source.startsWith('embed:')) {
      const file = sec.source.replace('embed:', '');
      const anchor = sec.anchor ? `#${sec.anchor}` : '';
      main.dataset.loading = 'false';
      // Iframe sem moldura — parece conteúdo nativo. Hash garante scroll pro anchor.
      // Usa key+timestamp pra forçar reload e respeitar a mudança de hash entre sub-abas
      main.innerHTML = `
        <iframe class="ds-frame" src="embed/${file}${anchor}" title="${sec.label}" loading="eager"></iframe>
      `;
      // Auto-resize: ajusta altura do iframe ao conteúdo (postMessage pelo DS ou observer)
      const frame = main.querySelector('.ds-frame');
      frame.addEventListener('load', () => {
        try {
          const adjust = () => {
            const docEl = frame.contentDocument && frame.contentDocument.documentElement;
            if (docEl) frame.style.height = docEl.scrollHeight + 'px';
          };
          adjust();
          // Re-ajusta após mudanças (theme toggle, etc.)
          if (frame.contentDocument) {
            const ro = new ResizeObserver(adjust);
            ro.observe(frame.contentDocument.documentElement);
          }
        } catch (e) {
          // Cross-origin não rola — usa altura fixa de fallback
          frame.style.height = 'calc(100vh - var(--topbar-height) - 64px)';
        }
      });
      return;
    }

    if (sec && sec.source && (sec.source.startsWith('gallery:') || sec.source.startsWith('archetypes:'))) {
      main.dataset.loading = 'false';
      try {
        const res = await fetch('data/photo-index.json');
        const data = await res.json();
        if (sec.source.startsWith('archetypes:')) {
          main.innerHTML = renderArchetypes(data);
        } else {
          main.innerHTML = renderGallery(data);
          attachGalleryHandlers(data);
        }
      } catch (e) {
        main.innerHTML = `<div class="placeholder"><h2>Galeria indisponível</h2><p>${e.message}</p></div>`;
      }
      return;
    }

    if (sec && sec.source && sec.source.startsWith('transcricoes-gallery:')) {
      const catId = sec.source.split(':')[1];
      main.dataset.loading = 'false';
      try {
        const idx = await getTranscricoesIndex();
        main.innerHTML = renderTranscricoesGallery(tab, catId, idx);
        attachTranscricoesGalleryHandlers(tab, catId, idx);
      } catch (e) {
        main.innerHTML = `<div class="placeholder"><h2>Biblioteca de transcrições indisponível</h2><p>${e.message}</p></div>`;
      }
      return;
    }

    if (sec && sec.source && sec.source.startsWith('icons-gallery:')) {
      main.dataset.loading = 'false';
      try {
        const idx = await getIconsIndex();
        main.innerHTML = renderIconsGallery(tab, idx);
        attachIconsGalleryHandlers(tab, idx);
      } catch (e) {
        main.innerHTML = `<div class="placeholder"><h2>Catálogo de ícones indisponível</h2><p>${e.message}</p><p>Rode o subagent de extração ou verifique <code>data/icons-index.json</code>.</p></div>`;
      }
      return;
    }

    if (sec && sec.source && sec.source.startsWith('applications-gallery:')) {
      main.dataset.loading = 'false';
      try {
        const idx = await getApplicationsIndex();
        main.innerHTML = renderApplicationsGallery(tab, idx);
        attachApplicationsGalleryHandlers(tab, idx);
      } catch (e) {
        main.innerHTML = `<div class="placeholder"><h2>Banco de aplicações indisponível</h2><p>${e.message}</p><p>Rode <code>node scripts/import-applications.mjs</code>.</p></div>`;
      }
      return;
    }

    if (sec && sec.placeholder) {
      main.dataset.loading = 'false';
      main.innerHTML = renderPlaceholder(tab, sec);
      return;
    }

    // Carrega resumo (ou full se não houver) + monta cabeçalho com ações
    const summaryPath = `content/${tab.id}/${sectionId}.html`;
    try {
      const res = await fetch(summaryPath);
      if (res.ok) {
        const html = await res.text();
        main.dataset.loading = 'false';
        main.innerHTML = renderSectionShell(tab, sec, html);
        attachActionHandlers();
        return;
      }
    } catch (e) {
      // fallback
    }

    main.dataset.loading = 'false';
    main.innerHTML = renderPlaceholder(tab, sec);
  }

  function renderSectionShell(tab, sec, html) {
    const mdPath = `content/${tab.id}/${sec.id}.md`;
    const fullUrl = `full.html#/${tab.id}/${sec.id}`;
    const updatedLabel = formatUpdatedAt(sec && sec.updatedAt);
    const updatedMeta = updatedLabel
      ? `<span class="updated-at" title="${sec.updatedAt}">${svgIcon('clock', 12)}<span>${updatedLabel}</span></span>`
      : '';
    const copyBtn = `<button type="button" class="action-mini ghost copy-link" title="Copiar link desta página">${svgIcon('link', 14)}<span>Copiar link</span></button>`;

    // Header customizado pra transcrição (categoria · meta · botão YouTube + voltar à biblioteca)
    if (sec && sec.transcricao) {
      const epBadge = sec.episode ? `<span class="trans-badge">EP #${String(sec.episode).padStart(2, '0')}</span>` : '';
      const reading = sec.readingMin ? `<span class="trans-meta-item">${svgIcon('clock', 12)} ${sec.readingMin} min</span>` : '';
      const ytBtn = sec.ytUrl ? `<a class="action-mini ghost" href="${sec.ytUrl}" target="_blank" rel="noopener" title="Ver no YouTube">${svgIcon('youtube', 14)}<span>YouTube</span></a>` : '';
      return `
        <div class="trans-back-bar">
          <a class="action-mini ghost" href="#/${tab.id}/biblioteca">${svgIcon('arrowLeft', 14)}<span>Biblioteca · ${escapeHtml(tab.label)}</span></a>
        </div>
        <div class="page-with-toc">
          <article class="prose trans-prose">
            <header class="trans-header">
              <div class="trans-cat">${escapeHtml(tab.label)}${updatedLabel ? ` · ${updatedLabel}` : ''}</div>
              <h1 class="trans-title">${epBadge}${escapeHtml(sec.label)}</h1>
              <div class="trans-meta">
                ${reading}
                ${ytBtn}
                ${copyBtn}
                <a class="action-mini ghost" href="${mdPath}" download title="Baixar .md original">${svgIcon('download', 12)}<span>.md</span></a>
              </div>
            </header>
            ${html}
          </article>
          <aside class="prose-toc" id="prose-toc"></aside>
        </div>
      `;
    }

    return `
      <div class="page-with-toc">
        <article class="prose">
          <div class="prose-actions">
            ${updatedMeta}
            <span class="prose-actions-spacer"></span>
            ${copyBtn}
            <a class="action-mini" href="${mdPath}" download title="Baixar .md original">
              ${svgIcon('download', 14)}<span>Baixar .md</span>
            </a>
            <a class="action-mini" href="${fullUrl}" target="_blank" rel="noopener" title="Abrir documentação técnica completa em nova aba">
              ${svgIcon('external', 14)}<span>Doc completa</span>
            </a>
          </div>
          ${html}
        </article>
        <aside class="prose-toc" id="prose-toc"></aside>
      </div>
    `;
  }

  function attachActionHandlers() {
    buildToc();
    attachTabGroups();
    attachSwatchCopy();
    attachMotionDemos();
    attachCopyLink();
  }

  // ----------- COPY LINK -----------
  function attachCopyLink() {
    document.querySelectorAll('.copy-link').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', async () => {
        // Se TOC tem item ativo, inclui o anchor; senão copia URL da seção
        const activeTocItem = document.querySelector('.prose-toc a.toc-item.is-active');
        const anchor = activeTocItem ? activeTocItem.dataset.target : null;
        const base = window.location.href.split('#')[0];
        const hash = `#/${currentTabId}/${currentSectionId}`;
        const url = `${base}${hash}${anchor ? `?h=${anchor}` : ''}`;
        try {
          await navigator.clipboard.writeText(url);
        } catch (_) {
          const ta = document.createElement('textarea');
          ta.value = url;
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand('copy'); } catch (_) {}
          ta.remove();
        }
        const original = btn.innerHTML;
        btn.classList.add('is-copied');
        btn.innerHTML = `${svgIcon('check', 14)}<span>Copiado</span>`;
        clearTimeout(btn._copyTimer);
        btn._copyTimer = setTimeout(() => {
          btn.classList.remove('is-copied');
          btn.innerHTML = original;
        }, 1600);
      });
    });
  }

  // ----------- SWATCH CLICK-TO-COPY -----------
  function attachSwatchCopy() {
    document.querySelectorAll('.swatch[data-hex]').forEach(sw => {
      if (sw.dataset.copyBound) return;
      sw.dataset.copyBound = '1';
      const copy = async () => {
        const hex = sw.dataset.hex;
        try {
          await navigator.clipboard.writeText(hex);
        } catch (e) {
          const ta = document.createElement('textarea');
          ta.value = hex;
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand('copy'); } catch (_) {}
          ta.remove();
        }
        sw.setAttribute('data-feedback', `${hex} copiado`);
        sw.classList.add('is-copied');
        clearTimeout(sw._copyTimer);
        sw._copyTimer = setTimeout(() => sw.classList.remove('is-copied'), 1100);
      };
      sw.addEventListener('click', copy);
      sw.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          copy();
        }
      });
    });
  }

  // ----------- MOTION DEMOS (página Movimento) -----------
  function attachMotionDemos() {
    // Reveal on scroll: elementos [data-motion="reveal"] dentro de uma página
    const revealEls = document.querySelectorAll('[data-motion="reveal"]');
    if (revealEls.length && 'IntersectionObserver' in window) {
      const io = new IntersectionObserver(entries => {
        entries.forEach(en => {
          if (en.isIntersecting) {
            en.target.classList.add('is-revealed');
            io.unobserve(en.target);
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
      revealEls.forEach(el => io.observe(el));
    }

    // Magnetic CTA
    document.querySelectorAll('[data-motion="magnetic"]').forEach(el => {
      if (el.dataset.magneticBound) return;
      el.dataset.magneticBound = '1';
      const max = 6;
      el.addEventListener('mousemove', e => {
        const r = el.getBoundingClientRect();
        const x = ((e.clientX - r.left) / r.width - 0.5) * max * 2;
        const y = ((e.clientY - r.top) / r.height - 0.5) * max * 2;
        el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });

    // Counter
    const counters = document.querySelectorAll('[data-motion="counter"]');
    if (counters.length && 'IntersectionObserver' in window) {
      const ioC = new IntersectionObserver(entries => {
        entries.forEach(en => {
          if (!en.isIntersecting) return;
          const el = en.target;
          ioC.unobserve(el);
          const target = parseFloat(el.dataset.to || '0');
          const suffix = el.dataset.suffix || '';
          const prefix = el.dataset.prefix || '';
          const dur = parseInt(el.dataset.duration || '700', 10);
          const start = performance.now();
          const tick = now => {
            const t = Math.min(1, (now - start) / dur);
            const eased = 1 - Math.pow(1 - t, 3);
            const v = target * eased;
            el.textContent = prefix + (Number.isInteger(target) ? Math.round(v) : v.toFixed(1)) + suffix;
            if (t < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        });
      }, { threshold: 0.5 });
      counters.forEach(el => ioC.observe(el));
    }

    // Tipo-machine
    document.querySelectorAll('[data-motion="typewriter"]').forEach(el => {
      if (el.dataset.typeBound) return;
      el.dataset.typeBound = '1';
      el.dataset.fullText = el.textContent;
      el.textContent = '';
      const speed = parseInt(el.dataset.speed || '38', 10);
      const run = () => {
        const text = el.dataset.fullText;
        el.textContent = '';
        let i = 0;
        const tick = () => {
          if (i > text.length) return;
          el.textContent = text.slice(0, i);
          const char = text[i - 1];
          const pause = (char === '.' || char === '—') ? speed * 8 : speed;
          i++;
          if (i <= text.length + 1) setTimeout(tick, pause);
        };
        tick();
      };
      el._motionRun = run;
      if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(entries => {
          entries.forEach(en => { if (en.isIntersecting) { run(); io.unobserve(el); } });
        }, { threshold: 0.5 });
        io.observe(el);
      } else { run(); }
    });

    // Replay buttons
    document.querySelectorAll('.motion-replay').forEach(btn => {
      if (btn.dataset.replayBound) return;
      btn.dataset.replayBound = '1';
      btn.addEventListener('click', () => {
        const kind = btn.dataset.rerun;
        const root = btn.closest('.motion-demo') || document;
        if (kind === 'block') {
          const el = root.querySelector('[data-motion-demo="block"]');
          if (!el) return;
          el.classList.remove('is-revealed');
          void el.offsetWidth;
          el.classList.add('is-revealed');
        } else if (kind === 'stagger') {
          const bars = root.querySelectorAll('[data-motion-demo="stagger"] [data-motion="reveal"]');
          bars.forEach(b => {
            b.classList.remove('is-revealed');
            void b.offsetWidth;
            b.classList.add('is-revealed');
          });
        } else if (kind === 'counter') {
          const c = root.querySelector('[data-motion="counter"]');
          if (!c) return;
          const target = parseFloat(c.dataset.to || '0');
          const suffix = c.dataset.suffix || '';
          const prefix = c.dataset.prefix || '';
          const dur = parseInt(c.dataset.duration || '1500', 10);
          const start = performance.now();
          const tick = now => {
            const t = Math.min(1, (now - start) / dur);
            const eased = 1 - Math.pow(1 - t, 3);
            const v = target * eased;
            c.textContent = prefix + (Number.isInteger(target) ? Math.round(v) : v.toFixed(1)) + suffix;
            if (t < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        } else if (kind === 'typewriter') {
          const tw = root.querySelector('[data-motion="typewriter"]');
          if (tw && tw._motionRun) tw._motionRun();
        }
      });
    });
  }

  // ----------- TABS COMPONENT -----------
  function attachTabGroups() {
    document.querySelectorAll('.tab-group').forEach(group => {
      const groupId = group.dataset.group;
      const buttons = group.querySelectorAll(`.tab-btn[data-group="${groupId}"]`);
      const panels = group.querySelectorAll(`.tab-panel[data-group="${groupId}"]`);
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          const targetTab = btn.dataset.tab;
          buttons.forEach(b => b.classList.toggle('active', b.dataset.tab === targetTab));
          panels.forEach(p => {
            if (p.dataset.tab === targetTab) p.removeAttribute('hidden');
            else p.setAttribute('hidden', '');
          });
        });
      });
    });
  }

  // ----------- INLINE EMBED (DS sem iframe) -----------
  let embedCache = null;
  async function loadInlineEmbed(file, anchor, container) {
    if (!embedCache || embedCache.file !== file) {
      const res = await fetch(`embed/${file}`);
      const html = await res.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const stylesText = Array.from(doc.querySelectorAll('style')).map(s => s.textContent).join('\n');
      const fontLinks = Array.from(doc.querySelectorAll('link[rel="stylesheet"][href*="googleapis"]')).map(l => l.outerHTML).join('\n');
      // Remove o aside.nav e o topbar interno do DS — quem navega é o brand system
      doc.querySelectorAll('aside.nav, .topbar').forEach(el => el.remove());
      const bodyHtml = doc.body.innerHTML;
      const scripts = Array.from(doc.querySelectorAll('script')).map(s => s.textContent);
      embedCache = { file, stylesText, fontLinks, bodyHtml, scripts };
    }

    // Injeta estilos uma vez (escopados em #ds-embed-host pra não vazar pro brand system)
    if (!document.getElementById('ds-embed-styles')) {
      const fontWrap = document.createElement('div');
      fontWrap.innerHTML = embedCache.fontLinks;
      Array.from(fontWrap.children).forEach(l => document.head.appendChild(l));

      const style = document.createElement('style');
      style.id = 'ds-embed-styles';
      // Escopa todos os seletores dentro de #ds-embed-host pra evitar conflito com brand system
      const scoped = embedCache.stylesText
        .replace(/(^|\})\s*([^@}{]+?)\s*\{/g, (m, brace, sel) => {
          if (!sel.trim() || sel.trim().startsWith('@') || sel.includes('keyframes')) return m;
          const scopedSel = sel.split(',').map(s => {
            const t = s.trim();
            if (t.startsWith(':root') || t.startsWith('html') || t === 'body' || t === '*') return `#ds-embed-host`;
            return `#ds-embed-host ${t}`;
          }).join(', ');
          return `${brace} ${scopedSel} {`;
        });
      style.textContent = scoped;
      document.head.appendChild(style);
    }

    container.innerHTML = `<div id="ds-embed-host" class="ds-embed-content">${embedCache.bodyHtml}</div>`;
    // Re-roda scripts (innerHTML não executa)
    embedCache.scripts.forEach(scriptText => {
      try {
        const script = document.createElement('script');
        script.textContent = scriptText;
        container.querySelector('#ds-embed-host').appendChild(script);
      } catch (e) {
        console.warn('Embed script error:', e);
      }
    });

    if (anchor) {
      setTimeout(() => {
        const target = container.querySelector(`#${anchor}`);
        if (target) target.scrollIntoView({ behavior: 'instant', block: 'start' });
      }, 50);
    } else {
      window.scrollTo({ top: 0 });
    }
  }

  // ----------- TOC LATERAL -----------
  function buildToc() {
    const tocEl = document.getElementById('prose-toc');
    const article = document.querySelector('.prose');
    if (!tocEl || !article) return;

    const headings = Array.from(article.querySelectorAll('h2[id], h3[id]'));
    if (headings.length < 2) {
      tocEl.style.display = 'none';
      return;
    }

    const items = headings.map(h => {
      const depth = h.tagName === 'H3' ? 3 : 2;
      const id = h.id;
      const label = h.textContent.trim();
      return `<a href="#${id}" class="toc-item toc-d${depth}" data-target="${id}">${escapeHtml(label)}</a>`;
    }).join('');

    tocEl.innerHTML = `<div class="toc-label">Nesta página</div>${items}`;

    // Smooth scroll + active state via IntersectionObserver
    tocEl.querySelectorAll('a.toc-item').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const id = a.dataset.target;
        const target = document.getElementById(id);
        if (target) {
          const top = target.getBoundingClientRect().top + window.scrollY - 100;
          window.scrollTo({ top, behavior: 'smooth' });
          history.replaceState(null, '', `#/${currentTabId}/${currentSectionId}#${id}`);
        }
      });
    });

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            tocEl.querySelectorAll('a.toc-item').forEach(a => {
              a.classList.toggle('active', a.dataset.target === id);
            });
          }
        });
      }, { rootMargin: '-100px 0px -60% 0px' });
      headings.forEach(h => observer.observe(h));
    }
  }

  function renderOverview() {
    const cards = nav.tabs
      .filter(t => t.id !== 'overview')
      .map(t => {
        const status = 'ready';
        const sectionsCount = t.sections.length;
        const statusLabel = `${sectionsCount} seçõe${sectionsCount === 1 ? '' : 's'}`;
        return `
          <a class="overview-card" data-status="${status}" href="#/${t.id}">
            <div class="icon">${svgIcon(t.icon, 28)}</div>
            <h3>${t.label}</h3>
            <p>${tabDescription(t.id)}</p>
            <div class="status">${statusLabel}</div>
          </a>
        `;
      })
      .join('');

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Brand<br><span class="accent">System.</span></h1>
        <p>Resumo institucional da marca Metta — para onboarding, alinhamento e referência rápida. Cada seção traz o essencial validado; documentações completas ficam a um clique de distância (abrir ou baixar).</p>
      </section>
      <div class="overview-grid">${cards}</div>
    `;
  }

  function tabDescription(id) {
    return {
      marca:        'Manifesto, história, plataforma, estratégia, narrativa.',
      audiencia:    'ICP estratégico, MQL, dossiês e banco de provas.',
      verbal:       'Tom, vocabulário, código de conteúdo, linha editorial.',
      visual:       'Resumo da identidade + Design System completo.',
      'direcao-arte': 'Princípios fotográficos, estilos de cena, galeria curada.',
      metodologia:  '6 Gestões da Meta Batida, aceleradores, FCA e CHA.',
      produtos:     'Mentoria SMTM (5 planos) e consultoria.',
      aplicacoes:   'Catálogo vivo de ads, carrosséis, slides, telas e posters canônicos.',
      transcricoes: '95 transcrições do Tiago classificadas por tema — banco vivo de discurso.'
    }[id] || '';
  }

  function attachOverviewLinks() {
    document.querySelectorAll('.overview-card').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = a.getAttribute('href').replace('#/', '');
        const tab = nav.tabs.find(t => t.id === tabId);
        navigate(tabId, tab.sections[0]?.id || null);
      });
    });
  }

  // ----------- APLICAÇÕES — banco de peças canônicas -----------
  let applicationsIndexCache = null;
  async function getApplicationsIndex() {
    if (!applicationsIndexCache) {
      const res = await fetch('data/applications-index.json');
      if (!res.ok) throw new Error('applications-index.json não encontrado');
      applicationsIndexCache = await res.json();
    }
    return applicationsIndexCache;
  }

  function renderApplicationsGallery(tab, idx) {
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const filterType     = params.get('type')      || 'all';
    const filterBrand    = params.get('brand')     || 'all';
    const filterIntent   = params.get('intent')    || 'all';
    const filterFormato  = params.get('formato')   || 'all';
    const filterSerie    = params.get('serie')     || 'all';
    const filterDensity  = params.get('densidade') || 'all';
    const search = (params.get('q') || '').toLowerCase();

    const all = idx.applications || [];
    const filtered = all.filter(a => {
      if (filterType     !== 'all' && a.type     !== filterType)     return false;
      if (filterBrand    !== 'all' && a.brand    !== filterBrand)    return false;
      if (filterIntent   !== 'all' && a.intent   !== filterIntent)   return false;
      if (filterFormato  !== 'all' && a.formato_canonico  !== filterFormato)  return false;
      if (filterSerie    !== 'all' && a.serie_id !== filterSerie)    return false;
      if (filterDensity  !== 'all' && a.densidade_texto   !== filterDensity)  return false;
      if (search && !(a.title?.toLowerCase().includes(search) || a.id.toLowerCase().includes(search))) return false;
      return true;
    });

    // Vocabulário controlado pra os filtros novos (lazy — só os valores presentes no banco filtrado por type)
    const fcValues = filterType === 'all'
      ? Array.from(new Set(all.map(a => a.formato_canonico).filter(Boolean))).sort()
      : (idx.formato_canonico_values?.[filterType] || []);
    const serieValues = Array.from(new Set(all.map(a => a.serie_id).filter(Boolean))).sort();
    const densityValues = idx.densidade_texto_values || ['baixa', 'media', 'alta'];

    const noFilters = filterType === 'all' && filterBrand === 'all' && filterIntent === 'all'
      && filterFormato === 'all' && filterSerie === 'all' && filterDensity === 'all' && !search;

    let gridHtml;
    if (noFilters) {
      // Modo agrupado: por type — prévia de 6 cards por group (resto via "Ver todos")
      const PREVIEW_PER_GROUP = 6;
      gridHtml = Object.keys(idx.types).map(typeId => {
        const list = filtered.filter(a => a.type === typeId);
        if (list.length === 0) return '';
        const preview = list.slice(0, PREVIEW_PER_GROUP);
        const cards = preview.map(a => renderAppCard(a, tab.id)).join('');
        const overflow = list.length > PREVIEW_PER_GROUP;
        return `
          <section class="app-cat-group">
            <header class="app-cat-header">
              <h2>${escapeHtml(idx.types[typeId])}</h2>
              <span class="app-cat-count">${list.length}</span>
              <a class="app-cat-link" href="#/${tab.id}/biblioteca?type=${typeId}">Ver ${overflow ? `todos os ${list.length}` : 'todos'} →</a>
            </header>
            <div class="app-grid">${cards}</div>
          </section>
        `;
      }).join('');
    } else {
      const cards = filtered.map(a => renderAppCard(a, tab.id)).join('');
      gridHtml = `<div class="app-grid">${cards || '<div class="placeholder small"><p>Nenhuma peça corresponde aos filtros.</p></div>'}</div>`;
    }

    const typeOptions     = Object.entries(idx.types).map(([k, v])   => `<option value="${k}" ${k === filterType    ? 'selected' : ''}>${escapeHtml(v)} (${all.filter(a => a.type    === k).length})</option>`).join('');
    const brandOptions    = Object.entries(idx.brands).map(([k, v])  => `<option value="${k}" ${k === filterBrand   ? 'selected' : ''}>${escapeHtml(v)} (${all.filter(a => a.brand   === k).length})</option>`).join('');
    const intentOptions   = Object.entries(idx.intents).map(([k, v]) => `<option value="${k}" ${k === filterIntent  ? 'selected' : ''}>${escapeHtml(v)} (${all.filter(a => a.intent  === k).length})</option>`).join('');
    const formatoOptions  = fcValues.map(k => `<option value="${k}" ${k === filterFormato ? 'selected' : ''}>${escapeHtml(k)} (${all.filter(a => a.formato_canonico === k).length})</option>`).join('');
    const serieOptions    = serieValues.map(k => `<option value="${k}" ${k === filterSerie ? 'selected' : ''}>${escapeHtml(k)} (${all.filter(a => a.serie_id === k).length})</option>`).join('');
    const densityOptions  = densityValues.map(k => `<option value="${k}" ${k === filterDensity ? 'selected' : ''}>${escapeHtml(k)} (${all.filter(a => a.densidade_texto === k).length})</option>`).join('');

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Catálogo.</h1>
        <p>${all.length} peças canônicas no banco — referência viva pra criar com consistência. Cada peça traz preview, copy quando houver, classificação por tipo/intenção e nota editorial. Filtre por tipo, brand ou intenção, ou busque pelo título.</p>
      </section>
      <div class="gallery-controls">
        <label>Tipo
          <select id="app-filter-type">
            <option value="all" ${filterType === 'all' ? 'selected' : ''}>Todos (${all.length})</option>
            ${typeOptions}
          </select>
        </label>
        <label>Intenção
          <select id="app-filter-intent">
            <option value="all" ${filterIntent === 'all' ? 'selected' : ''}>Todas</option>
            ${intentOptions}
          </select>
        </label>
        <span class="gallery-count">${filtered.length} de ${all.length}</span>
      </div>
      ${gridHtml}
    `;
  }

  function renderAppCard(a, tabId) {
    const intentLabel = ({ autoridade: 'autoridade', oferta: 'oferta', prova: 'prova', conversao: 'conversão' })[a.intent] || a.intent;
    const fmt = a.format ? a.format.replace(/-(\d+x\d+)$/, '') : '';
    const styleTag = a.style ? `<span class="app-tag app-tag-style">${escapeHtml(a.style)}</span>` : '';
    // Indicador de carrossel: nº de slides
    const slotsBadge = (a.type === 'carrossel' && a.slot_count) ? `<span class="app-card-slots">${a.slot_count} slides</span>` : '';
    return `
      <article class="app-card" data-id="${a.id}" data-type="${a.type}">
        <div class="app-card-frame app-frame-${a.type}">
          <img src="${a.src.thumb}" alt="${escapeAttr(a.title)}" loading="lazy">
          ${slotsBadge}
        </div>
        <div class="app-card-meta">
          <div class="app-card-tags">
            <span class="app-tag app-tag-type">${escapeHtml(a.type)}</span>
            ${styleTag}
            <span class="app-tag app-tag-intent">${escapeHtml(intentLabel)}</span>
          </div>
          <h3 class="app-card-title">${escapeHtml(a.title)}</h3>
          <div class="app-card-format">${escapeHtml(fmt)} · ${escapeHtml(a.brand)}</div>
        </div>
      </article>
    `;
  }

  function attachApplicationsGalleryHandlers(tab, idx) {
    const ALL_KEYS = ['type', 'brand', 'intent', 'formato', 'serie', 'densidade', 'q'];
    const buildHash = (overrides = {}) => {
      const cur = new URLSearchParams(location.hash.split('?')[1] || '');
      const params = new URLSearchParams();
      for (const k of ALL_KEYS) {
        const v = overrides[k] ?? cur.get(k);
        if (v && v !== 'all' && v.trim?.() !== '') params.set(k, v);
      }
      const qs = params.toString();
      return `#/${tab.id}/biblioteca${qs ? '?' + qs : ''}`;
    };

    ['type', 'intent'].forEach(key => {
      const el = document.getElementById(`app-filter-${key}`);
      if (el) el.addEventListener('change', () => location.hash = buildHash({ [key]: el.value }));
    });
    document.querySelectorAll('.app-card').forEach(card => {
      card.addEventListener('click', () => openApplicationDetail(card.dataset.id, idx));
    });
  }

  function openApplicationDetail(id, idx) {
    const a = idx.applications.find(x => x.id === id);
    if (!a) return;
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay app-detail';
    const copyBlock = (a.copy && (a.copy.headline || a.copy.subheadline || a.copy.cta)) ? `
      <h4>Copy</h4>
      <dl class="app-detail-copy">
        ${a.copy.headline    ? `<dt>Headline</dt><dd>${escapeHtml(a.copy.headline)}</dd>` : ''}
        ${a.copy.subheadline ? `<dt>Subheadline</dt><dd>${escapeHtml(a.copy.subheadline)}</dd>` : ''}
        ${a.copy.cta         ? `<dt>CTA</dt><dd>${escapeHtml(a.copy.cta)}</dd>` : ''}
      </dl>
    ` : '<p class="app-detail-empty">Copy ainda não preenchido — edite <code>data/applications-index.json</code></p>';
    const notesBlock = a.notes ? `<h4>Nota editorial</h4><p>${escapeHtml(a.notes)}</p>` : '<p class="app-detail-empty">Sem nota editorial. Adicione no índice pra ajudar a IA a entender por que essa peça funciona.</p>';

    // Preview: se for carrossel com slots, renderiza viewer multi-slide
    let previewHtml;
    if (a.type === 'carrossel' && Array.isArray(a.slots) && a.slots.length > 0) {
      const slidesHtml = a.slots.map((s, i) => `
        <figure class="carousel-slide" data-idx="${i}" ${i === 0 ? 'data-active' : ''}>
          <img src="${escapeAttr(s.src)}" alt="Slide ${s.n}" loading="lazy">
          <figcaption class="carousel-slide-caption">
            <span class="carousel-slide-num">${s.n}/${a.slots.length}</span>
            ${s.function ? `<span class="carousel-slide-function">${escapeHtml(s.function)}</span>` : ''}
          </figcaption>
        </figure>
      `).join('');
      const dotsHtml = a.slots.map((s, i) => `<button class="carousel-dot${i === 0 ? ' active' : ''}" data-goto="${i}" aria-label="Ir pro slide ${s.n}"></button>`).join('');
      previewHtml = `
        <div class="app-detail-preview carousel-viewer" data-current="0">
          <div class="carousel-track">${slidesHtml}</div>
          <button class="carousel-nav carousel-prev" aria-label="Slide anterior">‹</button>
          <button class="carousel-nav carousel-next" aria-label="Próximo slide">›</button>
          <div class="carousel-dots">${dotsHtml}</div>
        </div>
      `;
    } else {
      previewHtml = `
        <div class="app-detail-preview">
          <img src="${escapeAttr(a.src.mid)}" alt="${escapeAttr(a.title)}">
        </div>
      `;
    }

    overlay.innerHTML = `
      <div class="lightbox-content app-detail-content">
        <button class="lightbox-close" aria-label="Fechar">×</button>
        ${previewHtml}
        <div class="app-detail-meta">
          <div class="app-detail-id">${escapeHtml(a.type)}${a.style ? ` · estilo ${escapeHtml(a.style)}` : ''} · ${escapeHtml(a.format || '')}</div>
          <h3>${escapeHtml(a.title)}</h3>
          ${a.tese ? `<p class="app-detail-tese">${escapeHtml(a.tese)}</p>` : ''}
          <div class="app-detail-tags">
            <span class="app-tag">brand: ${escapeHtml(a.brand)}</span>
            <span class="app-tag">intent: ${escapeHtml(a.intent)}</span>
            ${a.formato_canonico ? `<span class="app-tag app-tag-formato">função: ${escapeHtml(a.formato_canonico)}</span>` : ''}
            ${a.mood ? `<span class="app-tag">mood: ${escapeHtml(a.mood)}</span>` : ''}
            ${a.densidade_texto ? `<span class="app-tag">densidade: ${escapeHtml(a.densidade_texto)}</span>` : ''}
            ${a.icp_target && a.icp_target.length ? `<span class="app-tag">ICP: ${a.icp_target.map(escapeHtml).join(' · ')}</span>` : ''}
            ${a.serie_id ? `<span class="app-tag app-tag-serie">série: ${escapeHtml(a.serie_id)}</span>` : ''}
            <span class="app-tag">status: ${escapeHtml(a.status || 'canonical')}</span>
            ${a.archetype_foto ? `<span class="app-tag">foto: ${escapeHtml(a.archetype_foto)}</span>` : ''}
          </div>
          ${copyBlock}
          ${notesBlock}
          ${a.tokens_used && a.tokens_used.length ? `<h4>Tokens aplicados</h4><div class="app-detail-tokens">${a.tokens_used.map(t => `<code>${escapeHtml(t)}</code>`).join(' ')}</div>` : ''}
          <div class="app-detail-actions">
            <a class="action-mini" href="${escapeAttr(a.src.mid)}" target="_blank" rel="noopener">${svgIcon('external', 12)}<span>Abrir preview</span></a>
            <button class="action-mini ghost" data-copy-id>${svgIcon('download', 12)}<span>Copiar id</span></button>
          </div>
          <pre class="app-detail-path">${escapeHtml(a.sourcePath || a.src.mid)}</pre>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = () => { overlay.classList.add('closing'); setTimeout(() => overlay.remove(), 200); };
    overlay.querySelector('.lightbox-close').addEventListener('click', close);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });
    overlay.querySelector('[data-copy-id]')?.addEventListener('click', e => {
      navigator.clipboard.writeText(a.id).then(() => {
        const span = e.currentTarget.querySelector('span');
        const orig = span.textContent;
        span.textContent = 'Copiado ✓';
        setTimeout(() => span.textContent = orig, 1400);
      });
    });

    // Carousel navigation handlers
    const viewer = overlay.querySelector('.carousel-viewer');
    if (viewer) {
      const slides = viewer.querySelectorAll('.carousel-slide');
      const dots = viewer.querySelectorAll('.carousel-dot');
      const goTo = (idx) => {
        const max = slides.length - 1;
        idx = Math.max(0, Math.min(max, idx));
        viewer.dataset.current = idx;
        slides.forEach((s, i) => s.toggleAttribute('data-active', i === idx));
        dots.forEach((d, i) => d.classList.toggle('active', i === idx));
      };
      viewer.querySelector('.carousel-prev').addEventListener('click', () => goTo(parseInt(viewer.dataset.current, 10) - 1));
      viewer.querySelector('.carousel-next').addEventListener('click', () => goTo(parseInt(viewer.dataset.current, 10) + 1));
      dots.forEach(d => d.addEventListener('click', () => goTo(parseInt(d.dataset.goto, 10))));
      // Keyboard nav
      const onKey = (e) => {
        if (e.key === 'ArrowLeft')  goTo(parseInt(viewer.dataset.current, 10) - 1);
        if (e.key === 'ArrowRight') goTo(parseInt(viewer.dataset.current, 10) + 1);
      };
      document.addEventListener('keydown', onKey);
      // Cleanup on close
      const origClose = close;
      const closeWithCleanup = () => { document.removeEventListener('keydown', onKey); origClose(); };
      overlay.querySelector('.lightbox-close').onclick = closeWithCleanup;
      overlay.onclick = (e) => { if (e.target === overlay) closeWithCleanup(); };
    }
  }

  // ----------- ÍCONES — galeria por categoria (DS) -----------
  let iconsIndexCache = null;
  async function getIconsIndex() {
    if (!iconsIndexCache) {
      const res = await fetch('data/icons-index.json');
      if (!res.ok) throw new Error('icons-index.json não encontrado');
      iconsIndexCache = await res.json();
    }
    return iconsIndexCache;
  }

  function renderIconsGallery(tab, idx) {
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const filterSection = params.get('cat') || 'all';
    const search = (params.get('q') || '').toLowerCase();

    const all = idx.icons || [];
    const filtered = all.filter(i => {
      if (filterSection !== 'all' && i.section !== filterSection) return false;
      if (search && !i.name.toLowerCase().includes(search) && !i.id.toLowerCase().includes(search)) return false;
      return true;
    });

    const sectionsList = idx.sections || [];

    let gridHtml;
    if (filterSection === 'all' && !search) {
      gridHtml = sectionsList.map(s => {
        const list = filtered.filter(i => i.section === s.id);
        if (list.length === 0) return '';
        const tiles = list.map(i => renderIconTile(i)).join('');
        return `
          <section class="ico-cat-group" data-cat="${s.id}">
            <header class="ico-cat-header">
              <h2>${escapeHtml(s.label)}</h2>
              <span class="ico-cat-count">${list.length}</span>
              <a class="ico-cat-link" href="#/${tab.id}/icones?cat=${s.id}">Ver só ${escapeHtml(s.label.toLowerCase())} →</a>
            </header>
            <div class="ico-grid">${tiles}</div>
          </section>
        `;
      }).join('');
    } else {
      const tiles = filtered.map(i => renderIconTile(i)).join('');
      gridHtml = `<div class="ico-grid">${tiles || '<div class="placeholder small"><p>Nenhum ícone corresponde aos filtros.</p></div>'}</div>`;
    }

    const sectionOptions = sectionsList
      .map(s => `<option value="${s.id}" ${s.id === filterSection ? 'selected' : ''}>${escapeHtml(s.label)} (${s.count})</option>`)
      .join('');

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Ícones.</h1>
        <p>${all.length} ícones do sistema de marca, organizados em ${sectionsList.length} categorias e exportados do Figma. Use a busca pelo nome ou filtre por categoria. Clique num ícone pra copiar nome ou SVG.</p>
      </section>
      <div class="gallery-controls">
        <label>Categoria
          <select id="ico-filter-cat">
            <option value="all" ${filterSection === 'all' ? 'selected' : ''}>Todas (${all.length})</option>
            ${sectionOptions}
          </select>
        </label>
        <label>Buscar
          <input type="search" id="ico-search-input" placeholder="Nome do ícone…" value="${escapeAttr(search)}">
        </label>
        <span class="gallery-count">${filtered.length} de ${all.length}</span>
      </div>
      ${gridHtml}
    `;
  }

  function renderIconTile(icon) {
    const tStyle = icon.transform ? ` style="transform:${escapeAttr(icon.transform)}"` : '';
    return `
      <button class="ico-tile" data-id="${icon.id}" data-name="${escapeAttr(icon.name)}" data-src="${escapeAttr(icon.src)}"${icon.transform ? ` data-transform="${escapeAttr(icon.transform)}"` : ''} title="${escapeAttr(icon.name)}">
        <span class="ico-tile-frame"><img src="${icon.src}" alt="${escapeAttr(icon.name)}" loading="lazy"${tStyle}></span>
        <span class="ico-tile-name">${escapeHtml(icon.name)}</span>
      </button>
    `;
  }

  function attachIconsGalleryHandlers(tab, idx) {
    const buildHash = (cat, q) => {
      const params = new URLSearchParams();
      if (cat && cat !== 'all') params.set('cat', cat);
      if (q && q.trim()) params.set('q', q.trim());
      const qs = params.toString();
      return `#/${tab.id}/icones${qs ? '?' + qs : ''}`;
    };

    const select = document.getElementById('ico-filter-cat');
    if (select) {
      select.addEventListener('change', () => {
        const q = document.getElementById('ico-search-input')?.value || '';
        location.hash = buildHash(select.value, q);
      });
    }

    const input = document.getElementById('ico-search-input');
    if (input) {
      let debounceTimer;
      input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const cat = document.getElementById('ico-filter-cat')?.value || 'all';
          location.hash = buildHash(cat, input.value);
        }, 250);
      });
    }

    document.querySelectorAll('.ico-tile').forEach(tile => {
      tile.addEventListener('click', () => openIconDetail(tile.dataset, idx));
    });
  }

  async function openIconDetail(data, idx) {
    const tStyle = data.transform ? ` style="transform:${escapeAttr(data.transform)}"` : '';
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay ico-detail';
    overlay.innerHTML = `
      <div class="lightbox-content ico-detail-content">
        <button class="lightbox-close" aria-label="Fechar">×</button>
        <div class="ico-detail-preview">
          <img src="${escapeAttr(data.src)}" alt="${escapeAttr(data.name)}"${tStyle}>
        </div>
        <div class="ico-detail-meta">
          <div class="ico-detail-id">${escapeHtml(data.id)}</div>
          <h3>${escapeHtml(data.name)}</h3>
          <div class="ico-detail-actions">
            <button class="action-mini" data-copy-name>${svgIcon('download', 12)}<span>Copiar nome</span></button>
            <button class="action-mini" data-copy-svg>${svgIcon('download', 12)}<span>Copiar SVG</span></button>
            <a class="action-mini ghost" href="${escapeAttr(data.src)}" download="${escapeAttr(data.name)}.svg">${svgIcon('download', 12)}<span>Baixar SVG</span></a>
          </div>
          <pre class="ico-detail-path">${escapeHtml(data.src)}</pre>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const close = () => { overlay.classList.add('closing'); setTimeout(() => overlay.remove(), 200); };
    overlay.querySelector('.lightbox-close').addEventListener('click', close);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });

    const flash = (btn, txt) => {
      const orig = btn.querySelector('span').textContent;
      btn.querySelector('span').textContent = txt;
      btn.classList.add('copied');
      setTimeout(() => { btn.querySelector('span').textContent = orig; btn.classList.remove('copied'); }, 1400);
    };

    overlay.querySelector('[data-copy-name]').addEventListener('click', e => {
      navigator.clipboard.writeText(data.name).then(() => flash(e.currentTarget, 'Copiado ✓'));
    });
    overlay.querySelector('[data-copy-svg]').addEventListener('click', async e => {
      try {
        const r = await fetch(data.src);
        const txt = await r.text();
        await navigator.clipboard.writeText(txt);
        flash(e.currentTarget, 'SVG copiado ✓');
      } catch (err) {
        flash(e.currentTarget, 'Erro');
      }
    });
  }

  // ----------- TRANSCRIÇÕES — galeria por categoria -----------
  let transcricoesIndexCache = null;
  async function getTranscricoesIndex() {
    if (!transcricoesIndexCache) {
      const res = await fetch('data/transcricoes-index.json');
      transcricoesIndexCache = await res.json();
    }
    return transcricoesIndexCache;
  }

  // Achata todas as transcrições do índice e enriquece com category/categoryLabel
  function flattenTranscricoes(idx) {
    const flat = [];
    for (const cat of idx.categories) {
      for (const t of idx.transcriptions[cat.id] || []) {
        flat.push({ ...t, category: cat.id, categoryLabel: cat.label });
      }
    }
    return flat;
  }

  function renderTranscricoesGallery(tab, _catId, idx) {
    const all = flattenTranscricoes(idx);
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const filterCat = params.get('cat') || 'all';
    const search = (params.get('q') || '').toLowerCase();

    const filtered = all.filter(t => {
      if (filterCat !== 'all' && t.category !== filterCat) return false;
      if (search && !(t.label.toLowerCase().includes(search) || t.shortLabel.toLowerCase().includes(search))) return false;
      return true;
    });

    const totalReading = all.reduce((s, t) => s + (t.readingMin || 0), 0);
    const epCount = all.filter(t => t.episode != null).length;

    // Cards agrupados por categoria quando filterCat === 'all'; senão grid plano
    let gridHtml;
    if (filterCat === 'all' && !search) {
      gridHtml = idx.categories.map(cat => {
        const list = filtered.filter(t => t.category === cat.id);
        if (list.length === 0) return '';
        const cards = list.map(t => renderTransCard(t, tab.id, true)).join('');
        return `
          <section class="trans-cat-group" data-cat="${cat.id}">
            <header class="trans-cat-header">
              <h2>${escapeHtml(cat.label)}</h2>
              <span class="trans-cat-count">${list.length}</span>
              <a class="trans-cat-link" href="#/${tab.id}/biblioteca?cat=${cat.id}">Ver só ${escapeHtml(cat.label.toLowerCase())} →</a>
            </header>
            <div class="trans-grid">${cards}</div>
          </section>
        `;
      }).join('');
    } else {
      const cards = filtered.map(t => renderTransCard(t, tab.id, false)).join('');
      gridHtml = `<div class="trans-grid">${cards || '<div class="placeholder small"><p>Nenhuma transcrição corresponde aos filtros.</p></div>'}</div>`;
    }

    const catOptions = idx.categories
      .map(c => `<option value="${c.id}" ${c.id === filterCat ? 'selected' : ''}>${escapeHtml(c.label)} (${idx.transcriptions[c.id].length})</option>`)
      .join('');

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Transcrições.</h1>
        <p>${all.length} aulas do Tiago classificadas em ${idx.categories.length} temas, com ${epCount} episódios numerados e ~${(totalReading / 60).toFixed(1)}h de leitura. Filtre por categoria ou busque no título.</p>
      </section>
      <div class="gallery-controls">
        <label>Categoria
          <select id="filter-cat">
            <option value="all" ${filterCat === 'all' ? 'selected' : ''}>Todas (${all.length})</option>
            ${catOptions}
          </select>
        </label>
        <label>Buscar
          <input type="search" id="trans-search-input" placeholder="No título…" value="${escapeAttr(search)}">
        </label>
        <span class="gallery-count">${filtered.length} de ${all.length}</span>
      </div>
      ${gridHtml}
    `;
  }

  function renderTransCard(t, tabId, showCat) {
    const epBadge = t.episode != null
      ? `<span class="trans-card-ep">EP #${String(t.episode).padStart(2, '0')}</span>`
      : '<span class="trans-card-ep avulso">avulso</span>';
    const yt = t.ytUrl
      ? `<a class="trans-card-yt" href="${t.ytUrl}" target="_blank" rel="noopener" title="Ver no YouTube" onclick="event.stopPropagation()">${svgIcon('youtube', 12)}</a>`
      : '';
    const catLabel = showCat ? '' : `<div class="trans-card-cat">${escapeHtml(t.categoryLabel)}</div>`;
    return `
      <article class="trans-card" data-tab="${tabId}" data-id="${t.id}">
        <div class="trans-card-head">
          ${epBadge}
          ${yt}
        </div>
        ${catLabel}
        <h3 class="trans-card-title">${escapeHtml(t.shortLabel)}</h3>
        <div class="trans-card-meta">
          <span>${svgIcon('clock', 11)} ${t.readingMin} min</span>
          <span class="trans-card-words">${t.wordCount.toLocaleString('pt-BR')} palavras</span>
        </div>
      </article>
    `;
  }

  function attachTranscricoesGalleryHandlers(tab) {
    document.querySelectorAll('.trans-card').forEach(card => {
      card.addEventListener('click', () => navigate(card.dataset.tab, card.dataset.id));
    });

    const buildHash = (cat, q) => {
      const params = new URLSearchParams();
      if (cat && cat !== 'all') params.set('cat', cat);
      if (q && q.trim()) params.set('q', q.trim());
      const qs = params.toString();
      return `#/${tab.id}/biblioteca${qs ? '?' + qs : ''}`;
    };

    const select = document.getElementById('filter-cat');
    if (select) {
      select.addEventListener('change', () => {
        const q = document.getElementById('trans-search-input')?.value || '';
        location.hash = buildHash(select.value, q);
      });
    }

    const input = document.getElementById('trans-search-input');
    if (input) {
      let debounceTimer;
      input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          const cat = document.getElementById('filter-cat')?.value || 'all';
          location.hash = buildHash(cat, input.value);
        }, 250);
      });
    }
  }

  // ----------- GALLERY / ARCHETYPES -----------
  function renderArchetypes(data) {
    const cats = data.categories || {};
    const grouped = {};
    data.archetypes.forEach(a => {
      const c = a.category;
      if (!grouped[c]) grouped[c] = [];
      grouped[c].push(a);
    });

    const groupHtml = Object.entries(grouped).map(([catId, list]) => {
      const items = list.map(a => `
        <article class="archetype-card" data-archetype="${a.id}">
          <header class="archetype-head">
            <h3>${a.label}</h3>
            <span class="archetype-count">${a.count} fotos</span>
          </header>
          <p class="archetype-desc">${a.description}</p>
          <details class="archetype-prompt">
            <summary>Prompt template</summary>
            <pre><code>${escapeHtml(a.promptTemplate)}</code></pre>
            <button class="copy-prompt" data-prompt="${escapeAttr(a.promptTemplate)}">Copiar prompt</button>
          </details>
          <div class="archetype-tags">
            ${Object.entries(a.tags).map(([k, v]) => `<span class="tag"><span class="k">${k}</span><span class="v">${v}</span></span>`).join('')}
          </div>
          <a class="archetype-link" href="#/direcao-arte/galeria?archetype=${a.id}">Ver fotos →</a>
        </article>
      `).join('');
      return `
        <section class="archetype-group">
          <h2 class="cat-label">${cats[catId] || catId}</h2>
          <div class="archetype-grid">${items}</div>
        </section>
      `;
    }).join('');

    const totalPhotos = (data.photos || []).length;
    const introCopy = totalPhotos > 0
      ? `${data.archetypes.length} estilos cobrindo 6 categorias, com ${totalPhotos} fotos curadas. Cada estilo traz prompt template em inglês profissional pronto pra alimentar gpt-image-1 via Codex CLI.`
      : `${data.archetypes.length} estilos cobrindo 6 categorias. Banco fotográfico em curadoria — use os prompt templates abaixo pra gerar novas imagens via gpt-image-1 (Codex CLI) e popular a galeria com fotos aprovadas pela direção de arte.`;

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Estilos<br><span class="accent">editoriais.</span></h1>
        <p>${introCopy}</p>
      </section>
      ${groupHtml}
    `;
  }

  function renderGallery(data) {
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const filterArchetype = params.get('archetype') || 'all';
    const filterCategory = params.get('category') || 'all';

    // Empty state — galeria sem fotos
    if (!data.photos || data.photos.length === 0) {
      return `
        <section class="hero">
          <div class="yellow-band"></div>
          <h1>Galeria<br><span class="accent">em curadoria.</span></h1>
          <p>O banco de imagens foi zerado para receber apenas fotos aprovadas pela direção de arte. Os estilos editoriais com prompts profissionais continuam disponíveis para gerar novas imagens via gpt-image-1.</p>
        </section>
        <div class="placeholder">
          <span class="badge">Galeria vazia</span>
          <h2>Sem fotos no momento</h2>
          <p>Quando houver imagens validadas, elas aparecerão aqui automaticamente. Por enquanto, consulte os estilos para gerar referências fotográficas alinhadas ao DNA Metta.</p>
          <div class="source-list" style="margin-top:24px;">
            <a href="#/direcao-arte/arquetipos" class="action-btn action-btn-primary" style="margin-top:8px;">Ver estilos</a>
          </div>
        </div>
      `;
    }

    const filtered = data.photos.filter(p => {
      if (filterArchetype !== 'all' && p.archetype !== filterArchetype) return false;
      if (filterCategory !== 'all' && p.category !== filterCategory) return false;
      return true;
    });

    const cards = filtered.map(p => `
      <figure class="photo-card" data-id="${p.id}">
        <div class="photo-frame">
          <img src="${p.src.thumb}" alt="${p.archetypeLabel}" loading="lazy">
        </div>
        <figcaption>
          <div class="photo-meta">
            <span class="photo-id">${p.id}</span>
            <span class="photo-archetype">${p.archetypeLabel}</span>
          </div>
          <button class="copy-prompt" data-prompt="${escapeAttr(p.prompt)}">Copiar prompt</button>
        </figcaption>
      </figure>
    `).join('');

    const archeOptions = data.archetypes.map(a => `<option value="${a.id}" ${a.id === filterArchetype ? 'selected' : ''}>${a.label} (${a.count})</option>`).join('');
    const catOptions = Object.entries(data.categories).map(([k, v]) => `<option value="${k}" ${k === filterCategory ? 'selected' : ''}>${v}</option>`).join('');

    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>Galeria<br><span class="accent">${filtered.length} fotos.</span></h1>
        <p>Banco curado de referências fotográficas. Cada foto tem prompt profissional em inglês pra gerar novas imagens via gpt-image-1 mantendo DNA Metta.</p>
      </section>
      <div class="gallery-controls">
        <label>Categoria
          <select id="filter-category">
            <option value="all" ${filterCategory === 'all' ? 'selected' : ''}>Todas</option>
            ${catOptions}
          </select>
        </label>
        <label>Estilo
          <select id="filter-archetype">
            <option value="all" ${filterArchetype === 'all' ? 'selected' : ''}>Todos</option>
            ${archeOptions}
          </select>
        </label>
        <span class="gallery-count">${filtered.length} de ${data.photos.length}</span>
      </div>
      <div class="photo-grid">${cards}</div>
    `;
  }

  function attachGalleryHandlers(data) {
    document.querySelectorAll('.copy-prompt').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.dataset.prompt;
        navigator.clipboard.writeText(text).then(() => {
          const orig = btn.textContent;
          btn.textContent = 'Copiado ✓';
          btn.classList.add('copied');
          setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1600);
        });
      });
    });

    document.querySelectorAll('.photo-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('.copy-prompt')) return;
        const id = card.dataset.id;
        const p = data.photos.find(ph => ph.id === id);
        if (p) openLightbox(p);
      });
    });

    const catSel = document.getElementById('filter-category');
    const archeSel = document.getElementById('filter-archetype');
    if (catSel) catSel.addEventListener('change', () => updateGalleryFilters(catSel.value, archeSel.value));
    if (archeSel) archeSel.addEventListener('change', () => updateGalleryFilters(catSel.value, archeSel.value));
  }

  function updateGalleryFilters(category, archetype) {
    const params = new URLSearchParams();
    if (category !== 'all') params.set('category', category);
    if (archetype !== 'all') params.set('archetype', archetype);
    const qs = params.toString();
    location.hash = `#/direcao-arte/galeria${qs ? '?' + qs : ''}`;
  }

  function openLightbox(photo) {
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.innerHTML = `
      <div class="lightbox-content">
        <button class="lightbox-close" aria-label="Fechar">×</button>
        <div class="lightbox-image-wrap">
          <img src="${photo.src.mid}" alt="${photo.archetypeLabel}">
        </div>
        <div class="lightbox-meta">
          <div class="lightbox-id">${photo.id}</div>
          <h3>${photo.archetypeLabel}</h3>
          <div class="lightbox-tags">
            ${Object.entries(photo.tags).map(([k, v]) => `<span class="tag"><span class="k">${k}</span><span class="v">${v}</span></span>`).join('')}
          </div>
          <h4>Prompt profissional</h4>
          <pre class="lightbox-prompt">${escapeHtml(photo.prompt)}</pre>
          <button class="copy-prompt" data-prompt="${escapeAttr(photo.prompt)}">Copiar prompt</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    function close() {
      overlay.classList.add('closing');
      setTimeout(() => overlay.remove(), 200);
    }
    overlay.querySelector('.lightbox-close').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });
    overlay.querySelector('.copy-prompt').addEventListener('click', (e) => {
      navigator.clipboard.writeText(photo.prompt).then(() => {
        const btn = e.target;
        const orig = btn.textContent;
        btn.textContent = 'Copiado ✓';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1600);
      });
    });
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }
  function escapeAttr(s) {
    return escapeHtml(s);
  }

  function renderPlaceholder(tab, sec) {
    return `
      <section class="hero">
        <div class="yellow-band"></div>
        <h1>${sec?.label || tab.label}</h1>
        <p>Esta seção está em construção. A documentação será preenchida em breve.</p>
      </section>
      <div class="placeholder">
        <span class="badge">${tab.label}</span>
        <h2>Em construção</h2>
        <p>Por enquanto, este espaço está reservado. Quando o conteúdo for produzido, ele aparecerá automaticamente aqui.</p>
      </div>
    `;
  }

  // ----------- SIDEBAR (collapse desktop + drawer mobile) -----------
  function initSidebar() {
    const app = document.querySelector('.app');
    const collapseBtn = document.querySelector('.app > .collapse-toggle');
    const mobileBtn = document.querySelector('.mobile-menu-toggle');
    const overlay = document.querySelector('.nav-overlay');
    if (!app) return;

    // Restaurar estado collapsed do localStorage (desktop)
    const savedCollapsed = localStorage.getItem('sidebar-collapsed') === '1';
    if (savedCollapsed) app.classList.add('sidebar-collapsed');

    if (collapseBtn) {
      collapseBtn.addEventListener('click', () => {
        const isCollapsed = app.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', isCollapsed ? '1' : '0');
        collapseBtn.setAttribute('aria-label', isCollapsed ? 'Abrir menu' : 'Recolher menu');
        collapseBtn.title = isCollapsed ? 'Abrir menu (Ctrl+\\)' : 'Recolher menu (Ctrl+\\)';
      });
      collapseBtn.setAttribute(
        'aria-label',
        savedCollapsed ? 'Abrir menu' : 'Recolher menu'
      );
    }

    if (mobileBtn) {
      mobileBtn.addEventListener('click', () => {
        app.classList.add('drawer-open');
      });
    }

    const closeDrawer = () => app.classList.remove('drawer-open');

    if (overlay) overlay.addEventListener('click', closeDrawer);

    // Em mobile, qualquer clique em tab/subnav-link fecha o drawer
    document.addEventListener('click', (e) => {
      const isTabOrLink = e.target.closest('aside.nav .tab, aside.nav .subnav a');
      if (isTabOrLink && window.matchMedia('(max-width: 880px)').matches) {
        closeDrawer();
      }
    });

    // Atalho de teclado (Ctrl+\) pra toggle no desktop
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '\\') {
        e.preventDefault();
        if (window.matchMedia('(min-width: 881px)').matches) {
          collapseBtn?.click();
        } else {
          app.classList.toggle('drawer-open');
        }
      }
      if (e.key === 'Escape' && app.classList.contains('drawer-open')) {
        closeDrawer();
      }
    });

    // Resize: se passar pra desktop com drawer aberto, fecha
    window.addEventListener('resize', () => {
      if (window.matchMedia('(min-width: 881px)').matches) {
        closeDrawer();
      }
    });
  }

  // ----------- SEARCH (lazy-loaded index + modal Ctrl+K) -----------
  let searchIndex = null;
  let searchLoading = null;
  let searchSelected = 0;
  let searchResults = [];

  function normalizeForSearch(s) {
    return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  async function ensureSearchIndex() {
    if (searchIndex) return searchIndex;
    if (searchLoading) return searchLoading;
    searchLoading = fetch('data/search-index.json').then(r => r.json()).then(data => {
      searchIndex = data.entries || [];
      return searchIndex;
    }).catch(err => {
      console.error('Falha ao carregar search-index:', err);
      return [];
    });
    return searchLoading;
  }

  function runSearch(query) {
    if (!searchIndex || !query.trim()) return [];
    const terms = normalizeForSearch(query).split(/\s+/).filter(Boolean);
    if (terms.length === 0) return [];
    const scored = [];
    for (const entry of searchIndex) {
      let score = 0;
      const labelNorm = normalizeForSearch(entry.label);
      for (const t of terms) {
        if (labelNorm.includes(t)) score += 10;          // match no título pesa mais
        const occurrences = entry.textNorm.split(t).length - 1;
        score += Math.min(occurrences, 8);
      }
      if (score > 0) scored.push({ entry, score });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 30).map(x => x.entry);
  }

  function highlightTerms(text, query) {
    const terms = query.trim().split(/\s+/).filter(t => t.length > 1);
    if (!terms.length) return escapeHtml(text);
    const norm = normalizeForSearch(text);
    let result = '';
    let i = 0;
    while (i < text.length) {
      let matched = false;
      for (const t of terms) {
        const tNorm = normalizeForSearch(t);
        if (norm.substring(i, i + tNorm.length) === tNorm) {
          result += `<mark>${escapeHtml(text.substr(i, tNorm.length))}</mark>`;
          i += tNorm.length;
          matched = true;
          break;
        }
      }
      if (!matched) {
        result += escapeHtml(text[i]);
        i++;
      }
    }
    return result;
  }

  function snippetAroundMatch(text, query, len = 160) {
    const norm = normalizeForSearch(text);
    const q = normalizeForSearch(query.trim().split(/\s+/)[0] || '');
    const pos = q ? norm.indexOf(q) : -1;
    if (pos < 0) return text.slice(0, len) + (text.length > len ? '…' : '');
    const start = Math.max(0, pos - 40);
    const end = Math.min(text.length, pos + len - 40);
    return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }

  function renderSearchResults(query) {
    const list = document.getElementById('search-results');
    const empty = document.getElementById('search-empty');
    if (!list) return;
    searchResults = runSearch(query);
    searchSelected = 0;
    if (!query.trim()) {
      list.innerHTML = '';
      if (empty) {
        empty.style.display = 'block';
        empty.innerHTML = `<div class="search-hint">Digite pra buscar em todo o Brand System (${(searchIndex || []).length} documentos)</div>`;
      }
      return;
    }
    if (empty) empty.style.display = searchResults.length ? 'none' : 'block';
    if (!searchResults.length) {
      if (empty) empty.innerHTML = `<div class="search-hint">Nenhum resultado para "${escapeHtml(query)}".</div>`;
      list.innerHTML = '';
      return;
    }
    list.innerHTML = searchResults.map((r, idx) => `
      <button class="search-result" data-idx="${idx}" data-tab="${r.tab}" data-section="${r.sectionId}">
        <div class="search-result-crumb">${escapeHtml(r.tabLabel)}</div>
        <div class="search-result-title">${highlightTerms(r.label, query)}</div>
        <div class="search-result-snippet">${highlightTerms(snippetAroundMatch(r.snippet, query), query)}</div>
      </button>
    `).join('');
    updateSelected();
    list.querySelectorAll('.search-result').forEach(el => {
      el.addEventListener('click', () => {
        const tab = el.dataset.tab;
        const sec = el.dataset.section;
        closeSearch();
        location.hash = `#/${tab}/${sec}`;
      });
      el.addEventListener('mouseenter', () => {
        searchSelected = parseInt(el.dataset.idx, 10);
        updateSelected();
      });
    });
  }

  function updateSelected() {
    document.querySelectorAll('.search-result').forEach((el, i) => {
      el.classList.toggle('is-selected', i === searchSelected);
      if (i === searchSelected) {
        el.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function openSearch() {
    let overlay = document.getElementById('search-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'search-overlay';
      overlay.className = 'search-overlay';
      overlay.innerHTML = `
        <div class="search-panel" role="dialog" aria-label="Busca">
          <div class="search-input-wrap">
            ${svgIcon('search', 18)}
            <input type="search" id="search-input" placeholder="Buscar manifesto, ICP, tom de voz..." autocomplete="off" spellcheck="false">
            <kbd class="search-esc">Esc</kbd>
          </div>
          <div id="search-empty" class="search-empty"></div>
          <div id="search-results" class="search-results"></div>
        </div>
      `;
      document.body.appendChild(overlay);
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeSearch();
      });
    }
    overlay.classList.add('is-open');
    document.body.classList.add('search-open');
    ensureSearchIndex().then(() => {
      renderSearchResults(document.getElementById('search-input').value);
    });
    const input = document.getElementById('search-input');
    input.focus();
    input.addEventListener('input', () => renderSearchResults(input.value));
  }

  function closeSearch() {
    const overlay = document.getElementById('search-overlay');
    if (overlay) overlay.classList.remove('is-open');
    document.body.classList.remove('search-open');
  }

  function initSearch() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+K / Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSearch();
        return;
      }
      const overlay = document.getElementById('search-overlay');
      if (!overlay || !overlay.classList.contains('is-open')) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeSearch();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (searchResults.length) {
          searchSelected = (searchSelected + 1) % searchResults.length;
          updateSelected();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (searchResults.length) {
          searchSelected = (searchSelected - 1 + searchResults.length) % searchResults.length;
          updateSelected();
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const target = searchResults[searchSelected];
        if (target) {
          closeSearch();
          location.hash = `#/${target.tab}/${target.sectionId}`;
        }
      }
    });
    const trigger = document.querySelector('.search-trigger');
    if (trigger) trigger.addEventListener('click', openSearch);
  }

  // ----------- TOPBAR MENU (dropdown compacto) -----------
  function formatZipSize(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) return null;
    const mb = bytes / 1024 / 1024;
    if (mb >= 100) return `${mb.toFixed(0)} MB`;
    if (mb >= 10)  return `${mb.toFixed(1)} MB`;
    return `${mb.toFixed(2)} MB`;
  }

  function formatZipDate(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return null;
    const meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
    return `atualizado ${d.getDate()} ${meses[d.getMonth()]}`;
  }

  async function initTopbarMenu() {
    const menu = document.querySelector('.topbar-menu');
    if (!menu) return;
    const trigger = menu.querySelector('.topbar-menu-trigger');
    const dropdown = menu.querySelector('.topbar-menu-dropdown');
    const zipMeta = menu.querySelector('[data-menu-meta="zip"]');
    const zipLink = menu.querySelector('[data-menu-item="download-zip"]');
    if (!trigger || !dropdown) return;

    function open() {
      menu.dataset.state = 'open';
      dropdown.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
    }
    function close() {
      menu.dataset.state = 'closed';
      dropdown.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
    }
    function toggle() {
      if (menu.dataset.state === 'open') close();
      else open();
    }

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      toggle();
    });
    document.addEventListener('click', (e) => {
      if (menu.dataset.state !== 'open') return;
      if (!menu.contains(e.target)) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && menu.dataset.state === 'open') {
        close();
        trigger.focus();
      }
    });
    dropdown.addEventListener('click', (e) => {
      const item = e.target.closest('.topbar-menu-item');
      if (item) close();
    });

    // Manifest pra mostrar tamanho + data do zip
    try {
      const res = await fetch('downloads/manifest.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('manifest 404');
      const m = await res.json();
      const size = formatZipSize(m.sizeBytes);
      const date = formatZipDate(m.generatedAt);
      if (zipMeta) {
        const parts = [size, date].filter(Boolean);
        zipMeta.textContent = parts.length ? parts.join(' · ') : 'pacote completo';
      }
    } catch (_) {
      if (zipMeta) zipMeta.textContent = 'pacote completo';
      // Se o manifest não existe ainda (dev sem build:zip), esconde o link
      if (zipLink) {
        zipLink.setAttribute('aria-disabled', 'true');
        zipLink.addEventListener('click', (e) => {
          e.preventDefault();
          if (zipMeta) zipMeta.textContent = 'rode npm run build:zip primeiro';
        });
      }
    }
  }

  // ----------- INIT -----------
  async function init() {
    initTheme();
    document.querySelectorAll('.theme-toggle button').forEach(btn => {
      btn.addEventListener('click', () => setTheme(btn.dataset.theme));
    });
    await loadNav();
    initSidebar();
    initSearch();
    initTopbarMenu();
    window.addEventListener('hashchange', onHashChange);
    onHashChange();
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', BrandSystem.init);
