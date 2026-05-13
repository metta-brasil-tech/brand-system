#!/usr/bin/env node
/* ============================================================
   METTA BRAND SYSTEM — BUILD ZIP
   Empacota o site estático em downloads/brand-system.zip
   e escreve downloads/manifest.json {sizeBytes, fileCount, generatedAt}.
============================================================ */

import { createWriteStream, statSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { dirname, resolve, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const archiver = require('archiver');

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const OUT_DIR = join(ROOT, 'downloads');
const ZIP_PATH = join(OUT_DIR, 'brand-system.zip');
const MANIFEST_PATH = join(OUT_DIR, 'manifest.json');

// Caminhos relativos à raiz que NÃO entram no zip
const EXCLUDE_DIRS = new Set([
  'node_modules',
  '.git',
  '.vercel',
  'scripts',
  'source',
  'downloads'
]);
const EXCLUDE_FILES = new Set([
  'package.json',
  'package-lock.json',
  'vercel.json',
  'serve.json',
  '.gitignore',
  '.gitattributes'
]);

const log = {
  info: (m) => console.log(`  ${m}`),
  ok:   (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  group:(m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

function shouldInclude(absPath) {
  const rel = relative(ROOT, absPath).split(sep);
  if (rel.length === 0) return false;
  const top = rel[0];
  if (EXCLUDE_DIRS.has(top)) return false;
  if (rel.length === 1 && EXCLUDE_FILES.has(top)) return false;
  return true;
}

function countFiles(dir) {
  let count = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const abs = join(dir, entry.name);
    if (!shouldInclude(abs)) continue;
    if (entry.isDirectory()) count += countFiles(abs);
    else if (entry.isFile()) count += 1;
  }
  return count;
}

async function main() {
  log.group('Metta Brand System — Build ZIP');

  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });

  const fileCount = countFiles(ROOT);
  log.info(`Arquivos a empacotar: ${fileCount}`);

  await new Promise((resolveZip, rejectZip) => {
    const output = createWriteStream(ZIP_PATH);
    const archive = archiver('zip', { zlib: { level: 6 } });

    output.on('close', resolveZip);
    archive.on('warning', (err) => {
      if (err.code === 'ENOENT') log.warn(String(err));
      else rejectZip(err);
    });
    archive.on('error', rejectZip);

    archive.pipe(output);

    archive.glob('**/*', {
      cwd: ROOT,
      dot: false,
      nodir: false,
      ignore: [
        'node_modules/**',
        '.git/**',
        '.vercel/**',
        'scripts/**',
        'source/**',
        'downloads/**',
        'package.json',
        'package-lock.json',
        'vercel.json',
        'serve.json',
        '.gitignore',
        '.gitattributes'
      ]
    }, { prefix: 'brand-system/' });

    archive.finalize();
  });

  const zipStat = statSync(ZIP_PATH);
  const manifest = {
    generatedAt: new Date().toISOString(),
    fileCount,
    sizeBytes: zipStat.size,
    filename: 'brand-system.zip'
  };
  await writeFile(MANIFEST_PATH, JSON.stringify(manifest, null, 2), 'utf8');

  const mb = (zipStat.size / 1024 / 1024).toFixed(2);
  log.ok(`Zip gerado: ${relative(ROOT, ZIP_PATH)} (${mb} MB · ${fileCount} arquivos)`);
  log.ok(`Manifest: ${relative(ROOT, MANIFEST_PATH)}`);
}

main().catch(err => {
  console.error('\nFalha ao gerar zip:', err);
  process.exit(2);
});
