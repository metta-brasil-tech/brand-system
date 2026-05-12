#!/usr/bin/env node
/* Reclassifica:
   - Adiciona tipo `lp` (vazio inicialmente — pra futuras Landing Pages)
   - Mantém `tela` mas redefine como "Telas Conceito" (posters/banners/editoriais)
   - Muda intent das 9 telas conceito existentes de `conversao` → `autoridade`
     (LP = conversão; tela conceito = peça editorial sem captura direta)
*/
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const INDEX = join(resolve(__dirname, '..'), 'data', 'applications-index.json');

const idx = JSON.parse(await readFile(INDEX, 'utf8'));

// Atualiza dicionário de types
idx.types = {
  ad:     'Ads (anúncios)',
  slide:  'Slides (apresentações)',
  tela:   'Telas Conceito (posters, banners, editoriais)',
  lp:     'LPs (landing pages)',
  poster: 'Posters editoriais'
};

let movedToAuthority = 0;
for (const a of idx.applications) {
  if (a.type === 'tela' && a.intent === 'conversao') {
    a.intent = 'autoridade';
    movedToAuthority++;
  }
}

idx.generatedAt = new Date().toISOString();
await writeFile(INDEX, JSON.stringify(idx, null, 2) + '\n', 'utf8');

console.log(`✓ types atualizado (5 categorias agora: ad/slide/tela/lp/poster)`);
console.log(`✓ ${movedToAuthority} telas conceito reclassificadas: conversao → autoridade`);
console.log(`  (LP fica reservado pra Landing Pages reais quando você subir)`);
