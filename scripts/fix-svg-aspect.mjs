#!/usr/bin/env node
/* ============================================================
   FIX-SVG-ASPECT — remove atributos do <svg> que quebram aspect-ratio
   quando renderizado via <img>:
     - preserveAspectRatio="none"  → faz esticar o conteúdo
     - width="100%" height="100%"  → conflita com o tamanho natural
     - overflow="visible"          → ícone pode vazar do tile
   Mantém apenas o viewBox como dimensão natural — assim object-fit:contain
   no CSS de <img> funciona corretamente.
============================================================ */

import { readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ICONS_DIR = join(resolve(__dirname, '..'), 'assets', 'icons');

async function* walk(dir) {
  for (const entry of await readdir(dir)) {
    const full = join(dir, entry);
    const st = await stat(full);
    if (st.isDirectory()) yield* walk(full);
    else if (entry.endsWith('.svg')) yield full;
  }
}

let processed = 0, modified = 0;
for await (const file of walk(ICONS_DIR)) {
  processed++;
  let svg = await readFile(file, 'utf8');
  const before = svg;

  svg = svg
    .replace(/\s+preserveAspectRatio="none"/g, '')
    .replace(/\s+width="100%"/g, '')
    .replace(/\s+height="100%"/g, '')
    .replace(/\s+overflow="visible"/g, '')
    .replace(/\s+style="display:\s*block;?"/g, '');

  if (svg !== before) {
    await writeFile(file, svg, 'utf8');
    modified++;
  }
}
console.log(`✓ ${processed} SVGs lidos · ${modified} normalizados`);
