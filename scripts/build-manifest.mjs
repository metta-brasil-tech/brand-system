#!/usr/bin/env node
// ============================================================
// METTA BRAND SYSTEM — BUILD DOWNLOAD MANIFEST (v2)
// Lê:
//   - data/nav.json + content/ → grupo "docs"
//   - assets/ → grupos "galeria", "aplicacoes", "identidade-visual"
// Escreve data/download-manifest.json com tudo que o modal precisa
// pra render checkbox tree + size badges.
// ============================================================

import { readFile, writeFile, stat, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const NAV_PATH = join(ROOT, 'data', 'nav.json');
const CONTENT_DIR = join(ROOT, 'content');
const ASSETS_DIR = join(ROOT, 'assets');
const OUT_PATH = join(ROOT, 'data', 'download-manifest.json');

const VISUAL_SOURCE_RE = /^(embed|gallery|archetypes|scan|transcricoes-gallery|icons-gallery|applications-gallery):/;

const log = {
  info: (m) => console.log(`  ${m}`),
  ok:   (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  group:(m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

async function fileSize(absPath) {
  try { return (await stat(absPath)).size; } catch { return 0; }
}

async function walkFiles(dir) {
  const out = [];
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return out; }
  for (const e of entries) {
    const abs = join(dir, e.name);
    if (e.isDirectory()) out.push(...await walkFiles(abs));
    else if (e.isFile()) {
      const size = (await stat(abs)).size;
      out.push({ name: e.name, path: relative(ROOT, abs).split(sep).join('/'), sizeBytes: size });
    }
  }
  return out;
}

async function listImmediateSubdirs(dir) {
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return []; }
  return entries.filter(e => e.isDirectory()).map(e => e.name);
}

function sumSize(files) { return files.reduce((a, b) => a + b.sizeBytes, 0); }

// ----------- DOCS GROUP -----------
async function buildDocsGroup() {
  const nav = JSON.parse(await readFile(NAV_PATH, 'utf8'));
  const tabs = [];

  for (const tab of nav.tabs) {
    const sections = [];
    let totalBytes = 0;

    for (const sec of tab.sections) {
      if (!sec.source) continue;
      if (VISUAL_SOURCE_RE.test(sec.source)) continue;
      const mdPath = join(CONTENT_DIR, tab.id, `${sec.id}.md`);
      if (!existsSync(mdPath)) continue;
      const size = await fileSize(mdPath);
      sections.push({
        id: sec.id,
        label: sec.label,
        files: [{ name: `${sec.id}.md`, path: `content/${tab.id}/${sec.id}.md`, sizeBytes: size }],
        totalBytes: size,
        fileCount: 1
      });
      totalBytes += size;
    }
    if (sections.length === 0) continue;

    tabs.push({
      id: tab.id,
      label: tab.label,
      kind: 'docs',
      sections,
      totalBytes,
      fileCount: sections.length
    });
    log.ok(`[docs/${tab.id}] ${tab.label} — ${sections.length} docs, ${(totalBytes/1024).toFixed(1)} KB`);
  }
  return { id: 'docs', label: 'Documentação', tabs };
}

// ----------- ASSET TABS HELPERS -----------
function humanizeSlug(slug) {
  // carrossel-37-empresarios-em-burnout → "37 empresários em burnout"
  // carrossel-post-fca-case-78-meta → "Post FCA case 78 meta"
  return slug
    .replace(/^(carrossel|carrocel|poster|slide|tela|ad)-/i, '')
    .replace(/-/g, ' ')
    .replace(/^\s*([a-zà-ÿ])/, (_, c) => c.toUpperCase());
}

async function buildAssetTabFromSubfolders(opts) {
  // Tab cujas sections são as subpastas imediatas de dir
  const { id, label, dir, sectionLabels, gallery, previewFrom, humanize } = opts;
  // previewFrom: 'self' | 'thumbs-sibling' — pra HQ/mid usa thumb correspondente
  const subdirs = await listImmediateSubdirs(dir);
  const sections = [];
  const firstFileBySubdir = {};
  let totalBytes = 0;
  let fileCount = 0;
  for (const sub of subdirs) {
    const files = await walkFiles(join(dir, sub));
    if (files.length === 0) continue;
    const sorted = [...files].sort((a, b) => a.name.localeCompare(b.name));
    firstFileBySubdir[sub] = sorted[0];
    const size = sumSize(files);
    sections.push({
      id: sub,
      label: (sectionLabels && sectionLabels[sub]) || (humanize ? humanizeSlug(sub) : sub),
      files,
      totalBytes: size,
      fileCount: files.length
    });
    totalBytes += size;
    fileCount += files.length;
  }
  if (sections.length === 0) return null;

  if (gallery) {
    for (const section of sections) {
      let preview = firstFileBySubdir[section.id];
      if (previewFrom === 'thumbs-sibling' && (section.id === 'mid' || section.id === 'hq')) {
        if (firstFileBySubdir['thumbs']) preview = firstFileBySubdir['thumbs'];
      }
      if (preview) section.preview = preview.path;
    }
  }

  return {
    id, label, kind: 'assets',
    displayMode: gallery ? 'gallery' : undefined,
    sections, totalBytes, fileCount
  };
}

async function buildAssetTabFlat(opts) {
  // Tab sem subpastas: gera uma única section "tudo"
  const { id, label, dir } = opts;
  const files = await walkFiles(dir);
  if (files.length === 0) return null;
  return {
    id, label, kind: 'assets',
    sections: [{
      id: 'todos',
      label: 'Todos',
      files,
      totalBytes: sumSize(files),
      fileCount: files.length
    }],
    totalBytes: sumSize(files),
    fileCount: files.length
  };
}

// Cada arquivo de `primarySubdir` = 1 section selecionável. Preview usa o
// arquivo correspondente em `previewSubdir` (mesmo nome), pra performance.
// Download SEMPRE do primarySubdir (resolução original).
async function buildAssetTabPerFileMatched(opts) {
  const { id, label, dir, primarySubdir, previewSubdir, labelFn } = opts;
  const primaryFiles = await walkFiles(join(dir, primarySubdir));
  if (primaryFiles.length === 0) return null;
  const previewByName = {};
  if (previewSubdir) {
    const previewFiles = await walkFiles(join(dir, previewSubdir));
    for (const f of previewFiles) previewByName[f.name] = f.path;
  }
  const sections = primaryFiles
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }))
    .map(f => ({
      id: f.name.replace(/\.[^.]+$/, ''),
      label: labelFn ? labelFn(f.name) : f.name.replace(/\.[^.]+$/, ''),
      files: [f],
      preview: previewByName[f.name] || f.path,
      totalBytes: f.sizeBytes,
      fileCount: 1
    }));
  return {
    id, label, kind: 'assets', displayMode: 'gallery',
    sections,
    totalBytes: sumSize(primaryFiles),
    fileCount: primaryFiles.length
  };
}

// Label humano genérico: remove prefixo conhecido, troca hífens, capitaliza
function makePieceLabel(filename, stripPrefixes = []) {
  let base = filename.replace(/\.[^.]+$/, '');
  for (const p of stripPrefixes) {
    const re = new RegExp(`^${p}-`, 'i');
    while (re.test(base)) base = base.replace(re, '');
  }
  // "ad-a-cliente-na-loja" → "ad a cliente na loja" → "Cliente na loja" (após strip)
  base = base.replace(/-/g, ' ').replace(/\s+/g, ' ').trim();
  // Capitaliza primeira letra
  return base.charAt(0).toUpperCase() + base.slice(1);
}

// Cada arquivo = 1 section selecionável (com preview visual no modal)
async function buildAssetTabPerFile(opts) {
  const { id, label, dir, labelFn } = opts;
  const files = await walkFiles(dir);
  if (files.length === 0) return null;
  const sections = files.map(f => ({
    id: f.name.replace(/\.[^.]+$/, ''),
    label: labelFn ? labelFn(f.name) : f.name,
    files: [f],
    preview: f.path,
    totalBytes: f.sizeBytes,
    fileCount: 1
  }));
  return {
    id, label, kind: 'assets', displayMode: 'gallery',
    sections,
    totalBytes: sumSize(files),
    fileCount: files.length
  };
}

// Label humano a partir do nome do arquivo, por padrão de família
function logoLabel(filename) {
  // logo_metta_colorido_escuro_h.svg → "Colorido escuro · Horizontal"
  const base = filename.replace(/^logo_metta_/, '').replace(/\.[^.]+$/, '');
  const parts = base.split('_');
  const last = parts[parts.length - 1];
  let orient = '';
  if (last === 'h' || last === 'v') {
    orient = last === 'h' ? ' · Horizontal' : ' · Vertical';
    parts.pop();
  }
  const color = parts.join(' ')
    .replace(/([a-zà-ÿ])(\d)/g, '$1 $2') // azul2 → azul 2
    .replace(/(^|\s)([a-zà-ÿ])/g, (_, s, c) => s + c.toUpperCase());
  return color + orient;
}
function symbolLabel(filename) {
  const base = filename.replace(/^simbolo_metta_/, '').replace(/\.[^.]+$/, '');
  return base.charAt(0).toUpperCase() + base.slice(1).replace(/(\d)/, ' $1');
}
function signatureLabel(filename) {
  const base = filename.replace(/^assinatura_metta_/, '').replace(/\.[^.]+$/, '');
  return base.charAt(0).toUpperCase() + base.slice(1).replace(/(\d)/, ' $1');
}

// ----------- MODELOS DE DOCUMENTOS (.docx editáveis) -----------
// label/category/description alimentam tanto o modal de download quanto a seção navegável
// "Modelos de Documentos" (source: downloads-gallery:modelos). Ordem das categorias na UI
// é controlada por MODELO_CATEGORIES.
const MODELO_CATEGORIES = ['Comercial', 'Projetos', 'Pessoas', 'Operação'];
const MODELO_META = {
  'Metta-Proposta-Comercial.docx':             { label: 'Proposta Comercial',              category: 'Comercial', description: 'Proposta de prestação de serviços com escopo, entregáveis e investimento.' },
  'Metta-Orcamento.docx':                       { label: 'Orçamento',                       category: 'Comercial', description: 'Orçamento itemizado com valores, prazos e condições de pagamento.' },
  'Metta-Contrato-Prestacao-Servicos.docx':     { label: 'Contrato de Prestação de Serviços', category: 'Comercial', description: 'Contrato padrão com cláusulas de escopo, prazos, confidencialidade e rescisão.' },
  'Metta-Carta-Comercial.docx':                 { label: 'Carta Comercial',                 category: 'Comercial', description: 'Carta formal de apresentação, comunicação ou cobrança institucional.' },
  'Metta-Briefing-Projeto.docx':                { label: 'Briefing de Projeto',             category: 'Projetos',  description: 'Briefing inicial: objetivo, contexto, escopo e critérios de sucesso.' },
  'Metta-Status-Report-Projeto.docx':           { label: 'Status Report de Projeto',        category: 'Projetos',  description: 'Acompanhamento periódico: progresso, riscos e próximos passos.' },
  'Metta-Ata-Reuniao.docx':                     { label: 'Ata de Reunião',                  category: 'Projetos',  description: 'Registro de pauta, decisões e encaminhamentos de reunião.' },
  'Metta-Plano-de-Acao-5W2H.docx':              { label: 'Plano de Ação (5W2H)',            category: 'Projetos',  description: 'Plano de ação no formato 5W2H — o quê, por quê, quem, quando, onde, como e quanto.' },
  'Metta-Relatorio-Diagnostico.docx':           { label: 'Relatório de Diagnóstico',        category: 'Projetos',  description: 'Diagnóstico estruturado com achados, análise e recomendações.' },
  'Metta-Manual-Onboarding.docx':               { label: 'Manual de Onboarding',            category: 'Pessoas',   description: 'Guia de integração de novos colaboradores à Metta.' },
  'Metta-PDI-Desenvolvimento-Individual.docx':  { label: 'PDI — Desenvolvimento Individual', category: 'Pessoas',  description: 'Plano de desenvolvimento individual com metas, ações e prazos.' },
  'Metta-Politica-Interna.docx':                { label: 'Política Interna',                category: 'Pessoas',   description: 'Norma ou política interna com regras, escopo e responsabilidades.' },
  'Metta-POP-Procedimento-Operacional.docx':    { label: 'POP — Procedimento Operacional',  category: 'Operação',  description: 'Procedimento operacional padrão passo a passo pra padronizar a execução.' }
};
function modeloCategoryRank(cat) {
  const i = MODELO_CATEGORIES.indexOf(cat);
  return i < 0 ? MODELO_CATEGORIES.length : i;
}
// fileObj relativo ao ROOT, no mesmo formato do walkFiles
async function fileObj(abs) {
  const size = (await stat(abs)).size;
  return { name: abs.split(sep).pop(), path: relative(ROOT, abs).split(sep).join('/'), sizeBytes: size };
}

async function buildModelosTab() {
  const dir = join(ASSETS_DIR, 'modelos-documentos');
  // só os .docx de template no TOPO da pasta (ignora previews/ e examples/)
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return null; }
  const templates = entries.filter(e => e.isFile() && e.name.toLowerCase().endsWith('.docx'));
  if (templates.length === 0) return null;

  const sections = [];
  for (const e of templates) {
    const f = await fileObj(join(dir, e.name));
    const meta = MODELO_META[f.name] || {};
    const id = f.name.replace(/\.[^.]+$/, '');                       // Metta-Proposta-Comercial

    // preview: assets/modelos-documentos/previews/<id>/p1.png, p2.png, ...
    let previewPages = [];
    const prevDir = join(dir, 'previews', id);
    if (existsSync(prevDir)) {
      // .webp após optimize-images; .png como fallback antes da otimização
      const imgs = (await readdir(prevDir)).filter(n => /\.(webp|png)$/i.test(n))
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      previewPages = imgs.map(n => relative(ROOT, join(prevDir, n)).split(sep).join('/'));
    }

    // exemplo preenchido: assets/modelos-documentos/examples/<id>-exemplo.docx
    let exampleFile = null;
    const exAbs = join(dir, 'examples', `${id}-exemplo.docx`);
    if (existsSync(exAbs)) exampleFile = await fileObj(exAbs);

    sections.push({
      id,
      label: meta.label || f.name.replace(/\.docx$/, '').replace(/^Metta-/, '').replace(/-/g, ' '),
      category: meta.category || 'Outros',
      description: meta.description || '',
      files: [f],
      previewPages,
      exampleFile,
      totalBytes: f.sizeBytes,
      fileCount: 1
    });
  }
  sections.sort((a, b) =>
    modeloCategoryRank(a.category) - modeloCategoryRank(b.category) ||
    a.label.localeCompare(b.label, 'pt-BR', { sensitivity: 'base' })
  );
  return {
    id: 'documentos', label: 'Documentos editáveis (.docx)', kind: 'assets',
    sections, totalBytes: sumSize(sections.map(s => s.files[0])), fileCount: sections.length
  };
}

// ----------- MODELOS DE EBOOK (kits HTML+CSS zipados) -----------
// Cada kit: HTML do modelo + ebook-base.css + fontes + imagens de exemplo + guia PDF
// próprio (documentação autossuficiente por modelo). Exemplo = PDF renderizado.
const EBOOK_META = {
  'Metta-Ebook-V1-Editorial-Noite.zip': { label: 'Ebook V1 · Editorial Noite', category: 'Ebooks', description: 'Capa escura tipográfica, miolo claro com cabeçalho e rodapé institucionais. A versão mais formal. Kit editável + guia do modelo.' },
  'Metta-Ebook-V2-Gelo-Minimal.zip':    { label: 'Ebook V2 · Gelo Minimal',    category: 'Ebooks', description: 'Capa branca, coluna de leitura estreita e máximo respiro. A versão mais limpa. Kit editável + guia do modelo.' },
  'Metta-Ebook-V3-Revista-Bold.zip':    { label: 'Ebook V3 · Revista Bold',    category: 'Ebooks', description: 'Capa com foto sangrada, sumário escuro e miolo em duas colunas. A versão mais visual. Kit editável + guia do modelo.' }
};

async function buildEbooksTab() {
  const dir = join(ASSETS_DIR, 'modelos-ebook');
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return null; }
  const kits = entries.filter(e => e.isFile() && e.name.toLowerCase().endsWith('.zip'));
  if (kits.length === 0) return null;

  const sections = [];
  for (const e of kits) {
    const f = await fileObj(join(dir, e.name));
    const meta = EBOOK_META[f.name] || {};
    const id = f.name.replace(/\.[^.]+$/, '');

    let previewPages = [];
    const prevDir = join(dir, 'previews', id);
    if (existsSync(prevDir)) {
      const imgs = (await readdir(prevDir)).filter(n => /\.(webp|png)$/i.test(n))
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      previewPages = imgs.map(n => relative(ROOT, join(prevDir, n)).split(sep).join('/'));
    }

    let exampleFile = null;
    const exAbs = join(dir, 'examples', `${id}-exemplo.pdf`);
    if (existsSync(exAbs)) exampleFile = await fileObj(exAbs);

    sections.push({
      id,
      label: meta.label || id.replace(/^Metta-/, '').replace(/-/g, ' '),
      category: meta.category || 'Ebooks',
      description: meta.description || '',
      files: [f],
      previewPages,
      exampleFile,
      totalBytes: f.sizeBytes,
      fileCount: 1
    });
  }
  sections.sort((a, b) => a.label.localeCompare(b.label, 'pt-BR', { sensitivity: 'base' }));
  return {
    id: 'ebooks', label: 'Modelos de Ebook (kit editável)', kind: 'assets',
    sections, totalBytes: sumSize(sections.map(s => s.files[0])), fileCount: sections.length
  };
}

// ----------- FUNDOS DE VIDEOCHAMADA (uso do time) -----------
// Imagens 1920x1080 prontas pra subir como plano de fundo no Google Meet e no Zoom.
// Ficam em JPG de propósito: nenhuma das duas plataformas aceita WebP no upload
// (ver KEEP_ORIGINAL_DIRS em scripts/optimize-images.mjs). Preview é WebP normal.
const FUNDO_META = {
  'Metta-Fundo-Videochamada-01-Poster-Bora-Bater-Meta.jpg': { label: 'Sala com poster · Bora bater meta', description: 'Sala clara com o poster "Superar metas para viver". Clima de casa, boa pra reunião interna e daily.' },
  'Metta-Fundo-Videochamada-02-Sala-Parede-Metta.jpg':      { label: 'Sala de reunião · Parede metta',     description: 'Sala ampla com a parede amarela assinada ao fundo. Institucional sem pesar, serve pra call com cliente.' },
  'Metta-Fundo-Videochamada-03-Arcos-Gelo.jpg':             { label: 'Arcos · Fundo gelo',                 description: 'Fundo neutro claro com arcos e símbolo nos cantos. O mais discreto do conjunto: não briga com a sua imagem.' },
  'Metta-Fundo-Videochamada-04-Superar-Metas.jpg':          { label: 'Superar metas é o que nos move',     description: 'Amarelo cheio com a frase em tipografia grande. Presença forte, melhor pra gravação, evento e webinar.' },
  'Metta-Fundo-Videochamada-05-Sala-Logo-Parede.jpg':       { label: 'Sala de reunião · Logo na parede',   description: 'Sala com o logo aplicado na parede e mesa amarela. A leitura mais corporativa, boa pra reunião externa.' }
};

async function buildFundosTab() {
  const dir = join(ASSETS_DIR, 'fundos-videochamada');
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return null; }
  const imagens = entries.filter(e => e.isFile() && /\.(jpe?g|png)$/i.test(e.name));
  if (imagens.length === 0) return null;

  const sections = [];
  for (const e of imagens) {
    const f = await fileObj(join(dir, e.name));
    const meta = FUNDO_META[f.name] || {};
    const id = f.name.replace(/\.[^.]+$/, '');

    // resolução real do arquivo — vira badge no card ("1920×1080")
    let dim = '';
    try {
      const m = await sharp(join(dir, e.name)).metadata();
      if (m.width && m.height) dim = `${m.width}×${m.height}`;
    } catch { /* sem sharp disponível: card fica só com formato e peso */ }

    let previewPages = [];
    const prevDir = join(dir, 'previews', id);
    if (existsSync(prevDir)) {
      const imgs = (await readdir(prevDir)).filter(n => /\.(webp|png|jpe?g)$/i.test(n))
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      previewPages = imgs.map(n => relative(ROOT, join(prevDir, n)).split(sep).join('/'));
    }

    sections.push({
      id,
      label: meta.label || id.replace(/^Metta-Fundo-Videochamada-\d+-/, '').replace(/-/g, ' '),
      category: 'Fundos de videochamada',
      description: meta.description || '',
      files: [f],
      previewPages,
      exampleFile: null,
      // sinaliza pro app.js: card de imagem, não de documento paginado
      previewKind: 'imagem',
      resolucao: dim,
      previewEyebrow: `Fundo de videochamada${dim ? ' · ' + dim : ''}`,
      totalBytes: f.sizeBytes,
      fileCount: 1
    });
  }
  // ordem = numeração do arquivo (01..05), que é a ordem editorial do conjunto
  sections.sort((a, b) => a.id.localeCompare(b.id, 'pt-BR', { numeric: true }));
  return {
    id: 'fundos-videochamada', label: 'Fundos de videochamada', kind: 'assets',
    sections, totalBytes: sumSize(sections.map(s => s.files[0])), fileCount: sections.length
  };
}

async function buildGroup(id, label, tabSpecs) {
  const tabs = [];
  for (const t of tabSpecs) {
    const tab = await t.builder();
    if (!tab) { log.info(`[${id}/${t.id}] vazio, pulado`); continue; }
    tabs.push(tab);
    log.ok(`[${id}/${tab.id}] ${tab.label} — ${tab.fileCount} arq, ${(tab.totalBytes/1024/1024).toFixed(2)} MB`);
  }
  return { id, label, tabs };
}

// ----------- MAIN -----------
async function main() {
  log.group('Metta Brand System — Build Download Manifest v2');

  log.group('Grupo: Documentação');
  const docsGroup = await buildDocsGroup();

  log.group('Grupo: Galeria');
  const galeriaGroup = await buildGroup('galeria', 'Galeria', [
    { id: 'fotografia', builder: () => buildAssetTabPerFileMatched({
      id: 'fotografia', label: 'Fotografia',
      dir: join(ASSETS_DIR, 'fotografia'),
      primarySubdir: 'mid',
      previewSubdir: 'thumbs'
    })}
  ]);

  log.group('Grupo: Catálogo de Aplicações');
  const appsGroup = await buildGroup('aplicacoes', 'Catálogo de Aplicações', [
    { id: 'ads', builder: () => buildAssetTabPerFileMatched({
      id: 'ads', label: 'Anúncios',
      dir: join(ASSETS_DIR, 'applications', 'ads'),
      primarySubdir: 'mid', previewSubdir: 'thumbs',
      labelFn: (n) => makePieceLabel(n, ['ad-a', 'ad-b', 'ad-c', 'ad-d', 'ad-e', 'ad-f', 'ad-g', 'ad-h', 'ad-i', 'ad-j', 'ad'])
    })},
    { id: 'carrosseis', builder: () => buildAssetTabFromSubfolders({
      id: 'carrosseis', label: 'Carrosséis',
      dir: join(ASSETS_DIR, 'applications', 'carrosseis'),
      gallery: true, humanize: true
    })},
    { id: 'posters', builder: () => buildAssetTabPerFileMatched({
      id: 'posters', label: 'Posters',
      dir: join(ASSETS_DIR, 'applications', 'posters'),
      primarySubdir: 'mid', previewSubdir: 'thumbs',
      labelFn: (n) => makePieceLabel(n, ['poster-poster', 'poster'])
    })},
    { id: 'slides', builder: () => buildAssetTabPerFileMatched({
      id: 'slides', label: 'Slides',
      dir: join(ASSETS_DIR, 'applications', 'slides'),
      primarySubdir: 'mid', previewSubdir: 'thumbs',
      labelFn: (n) => makePieceLabel(n, ['slide-slide', 'slide'])
    })},
    { id: 'telas', builder: () => buildAssetTabPerFileMatched({
      id: 'telas', label: 'Telas / LPs',
      dir: join(ASSETS_DIR, 'applications', 'telas'),
      primarySubdir: 'mid', previewSubdir: 'thumbs',
      labelFn: (n) => makePieceLabel(n, ['tela-tela', 'tela'])
    })}
  ]);

  log.group('Grupo: Identidade Visual');
  const dsGroup = await buildGroup('identidade-visual', 'Identidade Visual', [
    { id: 'logos', builder: () => buildAssetTabPerFile({
      id: 'logos', label: 'Logos', dir: join(ASSETS_DIR, 'logos'),
      labelFn: logoLabel
    })},
    { id: 'symbols', builder: () => buildAssetTabPerFile({
      id: 'symbols', label: 'Símbolos', dir: join(ASSETS_DIR, 'symbols'),
      labelFn: symbolLabel
    })},
    { id: 'signatures', builder: () => buildAssetTabPerFile({
      id: 'signatures', label: 'Assinaturas', dir: join(ASSETS_DIR, 'signatures'),
      labelFn: signatureLabel
    })},
    { id: 'icons', builder: () => buildAssetTabFromSubfolders({
      id: 'icons', label: 'Ícones', dir: join(ASSETS_DIR, 'icons')
    })}
  ]);

  log.group('Grupo: Modelos e Kits');
  const modelosGroup = await buildGroup('modelos', 'Modelos e Kits', [
    { id: 'documentos', builder: () => buildModelosTab() },
    { id: 'ebooks', builder: () => buildEbooksTab() },
    { id: 'fundos-videochamada', builder: () => buildFundosTab() }
  ]);

  const groups = [docsGroup, modelosGroup, galeriaGroup, appsGroup, dsGroup].filter(g => g.tabs.length > 0);

  // Totals globais
  let totalBytes = 0, totalFiles = 0, totalTabs = 0;
  for (const g of groups) {
    for (const t of g.tabs) {
      totalBytes += t.totalBytes;
      totalFiles += t.fileCount;
      totalTabs++;
    }
  }

  const manifest = {
    generatedAt: new Date().toISOString(),
    grandTotalBytes: totalBytes,
    grandTotalFiles: totalFiles,
    grandTotalTabs: totalTabs,
    groups
  };
  await writeFile(OUT_PATH, JSON.stringify(manifest, null, 2), 'utf8');

  console.log('');
  log.ok(`Manifest: ${relative(ROOT, OUT_PATH)} — ${groups.length} grupos, ${totalTabs} abas, ${totalFiles} arquivos, ${(totalBytes/1024/1024).toFixed(1)} MB total`);
}

main().catch(err => {
  console.error('\nFalha ao gerar manifest:', err);
  process.exit(2);
});
