#!/usr/bin/env node
/* Restaura pes-012 e esc-001 a partir dos originais do Desktop */
import { readFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const THUMBS = join(ROOT, 'assets', 'fotografia', 'thumbs');
const MID = join(ROOT, 'assets', 'fotografia', 'mid');

const REF_BASE = 'C:\\Users\\Usuario\\Desktop\\Renan\\Clientes\\Metta\\Rebranding\\01. Assets de Marca\\Referências Design';

const JOBS = [
  {
    id: 'pes-012',
    source: `${REF_BASE}\\Imagens Pessoas\\Professional Coffee Break 1.png`
  },
  {
    id: 'esc-001',
    source: `${REF_BASE}\\Imagens Escritório\\conference-room-in-office-2026-01-09-12-17-24-utc 1.png`
  }
];

for (const job of JOBS) {
  const buf = await readFile(job.source);
  await sharp(buf).resize({ width: 1280, withoutEnlargement: true }).webp({ quality: 85 }).toFile(join(MID, `${job.id}.webp`));
  await sharp(buf).resize({ width: 480, withoutEnlargement: true }).webp({ quality: 80 }).toFile(join(THUMBS, `${job.id}.webp`));
  console.log(`✓ ${job.id} restaurado`);
}
console.log('\n✅ Originais reaplicados em pes-012 e esc-001.');
