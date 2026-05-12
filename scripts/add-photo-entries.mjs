#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const INDEX = join(resolve(__dirname, '..'), 'data', 'photo-index.json');

const data = JSON.parse(await readFile(INDEX, 'utf8'));

// Pega os entries pes-012 e esc-001 como template (mesmo prompt + tags conforme user permitiu)
const pes012 = data.photos.find(p => p.id === 'pes-012');
const esc001 = data.photos.find(p => p.id === 'esc-001');

const newEntries = [
  {
    ...pes012,
    id: 'pes-018',
    src: {
      thumb: 'assets/fotografia/thumbs/pes-018.webp',
      mid:   'assets/fotografia/mid/pes-018.webp'
    }
  },
  {
    ...esc001,
    id: 'esc-007',
    src: {
      thumb: 'assets/fotografia/thumbs/esc-007.webp',
      mid:   'assets/fotografia/mid/esc-007.webp'
    }
  }
];

// Remove entries existentes pra ser idempotente
const newIds = new Set(newEntries.map(e => e.id));
data.photos = data.photos.filter(p => !newIds.has(p.id));

// Adiciona no fim
data.photos.push(...newEntries);

await writeFile(INDEX, JSON.stringify(data, null, 2) + '\n', 'utf8');
console.log(`✓ Adicionadas ${newEntries.length} entries: ${newEntries.map(e => e.id).join(', ')}`);
console.log(`  Total photos: ${data.photos.length}`);
