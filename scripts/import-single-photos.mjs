#!/usr/bin/env node
/* Importa imagens novas/atualizadas pra galeria — gera thumb + mid em webp */
import { readFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const DOWNLOADS = 'C:\\Users\\Usuario\\Downloads';
const THUMBS = join(ROOT, 'assets', 'fotografia', 'thumbs');
const MID = join(ROOT, 'assets', 'fotografia', 'mid');

const JOBS = [
  { id: 'pes-018', source: 'Woman_laughing_at_meeting_table_202605091107.jpeg' },
  { id: 'esc-007', source: 'Empty_boardroom_at_golden_hour_202605091107.jpeg' }
];

for (const job of JOBS) {
  const src = join(DOWNLOADS, job.source);
  const buf = await readFile(src);
  // Mid: 1280px wide, webp q85
  await sharp(buf).resize({ width: 1280, withoutEnlargement: true }).webp({ quality: 85 }).toFile(join(MID, `${job.id}.webp`));
  // Thumb: 480px wide, webp q80
  await sharp(buf).resize({ width: 480, withoutEnlargement: true }).webp({ quality: 80 }).toFile(join(THUMBS, `${job.id}.webp`));
  console.log(`✓ ${job.id}  ←  ${job.source}`);
}
console.log('\n✅ Imagens importadas. Galeria já reflete (sem rebuild necessário).');
