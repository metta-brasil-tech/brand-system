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
    .sort((a, b) => a.name.localeCompare(b.name))
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
    { id: 'ads', builder: () => buildAssetTabFromSubfolders({
      id: 'ads', label: 'Anúncios',
      dir: join(ASSETS_DIR, 'applications', 'ads'),
      sectionLabels: { mid: 'HQ', thumbs: 'Thumbs' },
      gallery: true, previewFrom: 'thumbs-sibling'
    })},
    { id: 'carrosseis', builder: () => buildAssetTabFromSubfolders({
      id: 'carrosseis', label: 'Carrosséis',
      dir: join(ASSETS_DIR, 'applications', 'carrosseis'),
      gallery: true, humanize: true
    })},
    { id: 'posters', builder: () => buildAssetTabFromSubfolders({
      id: 'posters', label: 'Posters',
      dir: join(ASSETS_DIR, 'applications', 'posters'),
      sectionLabels: { mid: 'HQ', thumbs: 'Thumbs' },
      gallery: true, previewFrom: 'thumbs-sibling'
    })},
    { id: 'slides', builder: () => buildAssetTabFromSubfolders({
      id: 'slides', label: 'Slides',
      dir: join(ASSETS_DIR, 'applications', 'slides'),
      sectionLabels: { mid: 'HQ', thumbs: 'Thumbs' },
      gallery: true, previewFrom: 'thumbs-sibling'
    })},
    { id: 'telas', builder: () => buildAssetTabFromSubfolders({
      id: 'telas', label: 'Telas / LPs',
      dir: join(ASSETS_DIR, 'applications', 'telas'),
      sectionLabels: { mid: 'HQ', thumbs: 'Thumbs' },
      gallery: true, previewFrom: 'thumbs-sibling'
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

  const groups = [docsGroup, galeriaGroup, appsGroup, dsGroup].filter(g => g.tabs.length > 0);

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
