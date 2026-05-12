#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const NAV = join(resolve(__dirname, '..'), 'data', 'nav.json');

const nav = JSON.parse(await readFile(NAV, 'utf8'));
const visual = nav.tabs.find(t => t.id === 'visual');
if (!visual) throw new Error('Aba visual não encontrada');

// Remove section "icones" prévia se houver
const before = visual.sections.length;
visual.sections = visual.sections.filter(s => s.id !== 'icones');

// Adiciona section "icones" antes da última (geralmente ds-tecnico) ou no fim
const newSection = {
  id: 'icones',
  label: 'Ícones',
  source: 'icons-gallery:all',
  description: 'Catálogo dos ícones do sistema — extraídos do Figma e classificados por contexto de uso.'
};

// Insere antes do ds-tecnico se existir, senão no fim
const dsIdx = visual.sections.findIndex(s => s.id === 'ds-tecnico' || s.source?.startsWith('embed:'));
if (dsIdx >= 0) visual.sections.splice(dsIdx, 0, newSection);
else visual.sections.push(newSection);

await writeFile(NAV, JSON.stringify(nav, null, 2) + '\n', 'utf8');
console.log(`✓ Section "icones" ${before === visual.sections.length ? 'substituída' : 'adicionada'} na aba Identidade Visual.`);
console.log(`  Total de sections em visual: ${visual.sections.length}`);
