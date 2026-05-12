#!/usr/bin/env node
/* ============================================================
   IMPORTA fotos aprovadas do Desktop pra brand-system/assets/fotografia
   - Renomeia esc-NNN, pes-NNN
   - Gera webp mid (max 1000w q=82) + thumb (max 400w q=78)
   - Imprime mapping original → novo
============================================================ */
import { readdir, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, join, extname, basename } from 'node:path';
import sharp from 'sharp';

const ROOT = resolve(import.meta.dirname, '..');
const SRC_BASE = String.raw`C:\Users\Usuario\Desktop\Renan\Clientes\Metta\Rebranding\01. Assets de Marca\Referências Design`;
const OUT_MID = join(ROOT, 'assets', 'fotografia', 'mid');
const OUT_THUMB = join(ROOT, 'assets', 'fotografia', 'thumbs');
const MAP_PATH = join(ROOT, 'data', 'photo-import-map.json');

const FOLDERS = [
  { src: 'Imagens Escritório', prefix: 'esc' },
  { src: 'Imagens Pessoas',    prefix: 'pes' }
];

await mkdir(OUT_MID, { recursive: true });
await mkdir(OUT_THUMB, { recursive: true });

const map = [];
for (const folder of FOLDERS) {
  const dir = join(SRC_BASE, folder.src);
  if (!existsSync(dir)) {
    console.error(`! pasta não encontrada: ${dir}`);
    continue;
  }
  const files = (await readdir(dir))
    .filter(f => /\.(png|jpe?g|webp)$/i.test(f))
    .sort((a, b) => a.localeCompare(b, 'pt-BR'));

  console.log(`\n[${folder.src}] ${files.length} arquivos`);
  let i = 1;
  for (const f of files) {
    const id = `${folder.prefix}-${String(i).padStart(3, '0')}`;
    const fullPath = join(dir, f);
    const midPath = join(OUT_MID, `${id}.webp`);
    const thumbPath = join(OUT_THUMB, `${id}.webp`);

    try {
      await sharp(fullPath)
        .resize({ width: 1000, withoutEnlargement: true })
        .webp({ quality: 82 })
        .toFile(midPath);
      await sharp(fullPath)
        .resize({ width: 400, withoutEnlargement: true })
        .webp({ quality: 78 })
        .toFile(thumbPath);
      map.push({ id, original: f, folder: folder.src });
      console.log(`  ✓ ${id} ← ${f}`);
      i++;
    } catch (e) {
      console.error(`  ✗ ${f} — ${e.message}`);
    }
  }
}

await writeFile(MAP_PATH, JSON.stringify(map, null, 2), 'utf8');
console.log(`\n✓ ${map.length} fotos importadas. Mapping em data/photo-import-map.json`);
