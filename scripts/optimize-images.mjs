#!/usr/bin/env node
// ============================================================
// METTA BRAND SYSTEM — OPTIMIZE IMAGES
// Walks assets/ recursivo, acha qualquer raster não-WebP (JPG, PNG,
// GIF, BMP, TIFF, AVIF) e converte pra WebP via Sharp. Apaga o
// original. SVG é vector, fica intacto.
//
// Roda automaticamente no início de `npm run build`, então é só
// dropar a imagem em assets/<pasta-certa>/ e o build cuida do
// resto. Idempotente: rodar 2x não faz nada da segunda vez.
// ============================================================

import { readdir, stat, unlink } from 'node:fs/promises';
import { dirname, resolve, join, relative, sep, basename, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const ASSETS_DIR = join(ROOT, 'assets');

// Formatos raster que convertemos pra WebP. SVG fica de fora.
const CONVERTIBLE = new Set(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.avif']);
// Pastas cujo arquivo final é BAIXADO e usado fora do navegador, onde WebP não serve.
// Ex.: fundos de videochamada — Google Meet e Zoom só aceitam JPG/PNG no upload de
// plano de fundo. Preview dentro dessas pastas (previews/) segue convertendo.
// - assets/tiago/recortadas e /recortes: embed/criar.html referencia esses arquivos
//   por caminho .png fixo; converter pra WebP derruba os recortes do wizard.
const KEEP_ORIGINAL_DIRS = ['assets/fundos-videochamada', 'assets/tiago/recortadas', 'assets/tiago/recortes'];
function keepOriginal(relPath) {
  return KEEP_ORIGINAL_DIRS.some(d => relPath.startsWith(d + '/') && !relPath.startsWith(d + '/previews/'));
}
const WEBP_QUALITY = 85;       // bom equilíbrio fidelidade/peso pra brand assets
const PNG_LOSSLESS_QUALITY = 90; // se o PNG é UI/screenshot, eleva qualidade

const log = {
  info: (m) => console.log(`  ${m}`),
  ok:   (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  err:  (m) => console.error(`  \x1b[31m✗\x1b[0m ${m}`),
  group:(m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

async function* walk(dir) {
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); }
  catch { return; }
  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const abs = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(abs);
    else if (entry.isFile()) yield abs;
  }
}

function fmtKB(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

async function convertToWebp(srcPath) {
  const ext = extname(srcPath).toLowerCase();
  const dstPath = srcPath.slice(0, -ext.length) + '.webp';
  const srcStat = await stat(srcPath);
  const srcSize = srcStat.size;

  // Decide qualidade baseado no formato origem
  const quality = ext === '.png' ? PNG_LOSSLESS_QUALITY : WEBP_QUALITY;

  const pipeline = sharp(srcPath, { animated: ext === '.gif' });
  // .webp() com quality apropriada; preserva alpha automaticamente
  await pipeline.webp({ quality, effort: 5 }).toFile(dstPath);

  const dstStat = await stat(dstPath);
  const dstSize = dstStat.size;

  // Se WebP ficou MAIOR (raro mas possível em imagens já bem comprimidas),
  // ainda assim preferimos WebP pra padronização. Reporta a diferença.
  await unlink(srcPath);

  return { srcPath, dstPath, srcSize, dstSize };
}

async function main() {
  log.group('Metta Brand System — Optimize Images (→ WebP)');

  let scanned = 0, converted = 0, errors = 0;
  let totalSrc = 0, totalDst = 0;

  for await (const file of walk(ASSETS_DIR)) {
    scanned++;
    const ext = extname(file).toLowerCase();
    if (!CONVERTIBLE.has(ext)) continue;
    const rel = relative(ROOT, file).split(sep).join('/');
    if (keepOriginal(rel)) { log.info(`${rel} — mantido no formato original (KEEP_ORIGINAL_DIRS)`); continue; }
    try {
      const r = await convertToWebp(file);
      converted++;
      totalSrc += r.srcSize;
      totalDst += r.dstSize;
      const delta = r.dstSize - r.srcSize;
      const pct = ((1 - r.dstSize / r.srcSize) * 100).toFixed(0);
      const sign = delta < 0 ? '−' : '+';
      log.ok(`${rel} → .webp  (${fmtKB(r.srcSize)} → ${fmtKB(r.dstSize)} · ${sign}${Math.abs(parseInt(pct))}%)`);
    } catch (err) {
      errors++;
      log.err(`${rel}: ${err.message}`);
    }
  }

  console.log('');
  if (converted === 0) {
    log.info(`${scanned} arquivos escaneados — nada pra converter, tudo já está em WebP/SVG.`);
  } else {
    const saved = totalSrc - totalDst;
    const savedPct = ((saved / totalSrc) * 100).toFixed(0);
    log.ok(`${converted} convertido(s) · ${fmtKB(totalSrc)} → ${fmtKB(totalDst)} · economizou ${fmtKB(saved)} (${savedPct}%)`);
  }
  if (errors > 0) {
    log.warn(`${errors} erro(s) — arquivo(s) mantido(s) no formato original`);
    process.exit(1);
  }
}

main().catch(err => {
  console.error('\nFalha ao otimizar imagens:', err);
  process.exit(2);
});
