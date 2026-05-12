#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const NAV = join(resolve(__dirname, '..'), 'data', 'nav.json');

const nav = JSON.parse(await readFile(NAV, 'utf8'));

// Remove aba antiga (caso exista)
nav.tabs = nav.tabs.filter(t => t.id !== 'aplicacoes');

const tab = {
  id: 'aplicacoes',
  icon: 'layers',
  label: 'Aplicações',
  group: 'negócio',
  description: 'Banco vivo de peças canônicas — referência pra criar com consistência.',
  sections: [
    {
      id: 'biblioteca',
      label: 'Biblioteca',
      source: 'applications-gallery:all',
      description: 'Ads, slides, telas e posters classificados por tipo, brand e intenção.'
    }
  ]
};

// Insere antes de transcrições (último grupo) se existir, senão no fim
const transIdx = nav.tabs.findIndex(t => t.id === 'transcricoes');
if (transIdx >= 0) nav.tabs.splice(transIdx, 0, tab);
else nav.tabs.push(tab);

await writeFile(NAV, JSON.stringify(nav, null, 2) + '\n', 'utf8');
console.log(`✓ Aba "Aplicações" adicionada · total ${nav.tabs.length} abas`);
