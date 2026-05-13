#!/usr/bin/env node
// ============================================================
// METTA BRAND SYSTEM — BUILD DOCS MANIFEST
// Lê data/nav.json + os arquivos .md em content/ e escreve
// data/documents-manifest.json com a árvore tab→sections→file/size
// que alimenta o modal "Baixar documentação" no topbar.
//
// MVP: somente .md (documentação). Galerias, ícones e aplicações
// visuais ficam fora — usuário pediu explicitamente.
// ============================================================

import { readFile, writeFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const NAV_PATH = join(ROOT, 'data', 'nav.json');
const CONTENT_DIR = join(ROOT, 'content');
const OUT_PATH = join(ROOT, 'data', 'documents-manifest.json');

const VISUAL_SOURCE_RE = /^(embed|gallery|archetypes|scan|transcricoes-gallery|icons-gallery|applications-gallery):/;

const log = {
  info: (m) => console.log(`  ${m}`),
  ok:   (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  group:(m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

async function fileSize(absPath) {
  try {
    const s = await stat(absPath);
    return s.size;
  } catch {
    return 0;
  }
}

async function main() {
  log.group('Metta Brand System — Build Docs Manifest');

  const nav = JSON.parse(await readFile(NAV_PATH, 'utf8'));
  const tabs = [];
  let grandTotalBytes = 0;
  let grandTotalDocs = 0;

  for (const tab of nav.tabs) {
    const sections = [];
    let totalBytes = 0;

    for (const sec of tab.sections) {
      if (!sec.source) continue;
      if (VISUAL_SOURCE_RE.test(sec.source)) continue;

      const mdPath = join(CONTENT_DIR, tab.id, `${sec.id}.md`);
      if (!existsSync(mdPath)) {
        log.warn(`[${tab.id}/${sec.id}] sem .md em content/ — rode build:content`);
        continue;
      }
      const size = await fileSize(mdPath);
      sections.push({
        id: sec.id,
        label: sec.label,
        path: `content/${tab.id}/${sec.id}.md`,
        sizeBytes: size
      });
      totalBytes += size;
    }

    if (sections.length === 0) {
      log.info(`[${tab.id}] ${tab.label} — sem docs, pulado`);
      continue;
    }

    tabs.push({
      id: tab.id,
      label: tab.label,
      sections,
      totalBytes,
      docCount: sections.length
    });
    grandTotalBytes += totalBytes;
    grandTotalDocs += sections.length;
    log.ok(`[${tab.id}] ${tab.label} — ${sections.length} docs, ${(totalBytes/1024).toFixed(1)} KB`);
  }

  const manifest = {
    generatedAt: new Date().toISOString(),
    grandTotalBytes,
    grandTotalDocs,
    tabs
  };
  await writeFile(OUT_PATH, JSON.stringify(manifest, null, 2), 'utf8');

  console.log('');
  log.ok(`Manifest: ${relative(ROOT, OUT_PATH)} — ${tabs.length} abas, ${grandTotalDocs} docs, ${(grandTotalBytes/1024).toFixed(1)} KB total`);
}

main().catch(err => {
  console.error('\nFalha ao gerar manifest:', err);
  process.exit(2);
});
