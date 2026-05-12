#!/usr/bin/env node
/* Adiciona 3 sections faltantes na aba Identidade Visual:
   - logos (design/metta-logos.md)
   - ui-kit (design/metta-ui-kit.md)
   - ds-tecnico (embed:design-system-2.0.html)
   Posiciona em ordem editorial coerente. */
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const NAV = join(resolve(__dirname, '..'), 'data', 'nav.json');

const nav = JSON.parse(await readFile(NAV, 'utf8'));
const visual = nav.tabs.find(t => t.id === 'visual');
if (!visual) throw new Error('Aba visual não encontrada');

const NEW_SECTIONS = [
  {
    id: 'logos',
    label: 'Logos',
    source: 'design/metta-logos.md',
    description: 'Variações oficiais do logo Metta — regras de uso por fundo, IDs Drive, paths SVG.',
    insertAfter: 'ds-movimento'
  },
  {
    id: 'ui-kit',
    label: 'UI Kit',
    source: 'design/metta-ui-kit.md',
    description: '10 componentes JSX editoriais (CTAPill, SectionOpener, StrategyTechRow, QuoteBlock).',
    insertAfter: 'ds-componentes'
  },
  {
    id: 'ds-tecnico',
    label: 'DS Técnico',
    source: 'embed:design-system-2.0.html',
    description: 'Design System v2 técnico completo — embed interativo (tokens, componentes, motion).',
    insertAfter: 'icones'
  }
];

let added = 0;
let replaced = 0;
for (const newSec of NEW_SECTIONS) {
  // Remove se já existir (idempotente)
  const existingIdx = visual.sections.findIndex(s => s.id === newSec.id);
  if (existingIdx >= 0) {
    visual.sections.splice(existingIdx, 1);
    replaced++;
  }
  // Insere após section indicada
  const anchorIdx = visual.sections.findIndex(s => s.id === newSec.insertAfter);
  const { insertAfter, ...sec } = newSec;
  if (anchorIdx >= 0) {
    visual.sections.splice(anchorIdx + 1, 0, sec);
  } else {
    visual.sections.push(sec);
  }
  added++;
}

await writeFile(NAV, JSON.stringify(nav, null, 2) + '\n', 'utf8');
console.log(`✓ ${added - replaced} sections novas adicionadas (${replaced} substituídas)`);
console.log(`  Aba Identidade Visual agora tem ${visual.sections.length} sections`);
console.log(`\nOrdem final:`);
visual.sections.forEach((s, i) => console.log(`  ${i + 1}. ${s.id} — ${s.label}`));
