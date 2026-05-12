#!/usr/bin/env node
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const NAV = join(ROOT, 'data', 'nav.json');
const TAB_FILE = join(ROOT, 'data', '_transcricoes-tab.json');

const nav = JSON.parse(await readFile(NAV, 'utf8'));
const newTabs = JSON.parse(await readFile(TAB_FILE, 'utf8'));
const newIds = new Set(newTabs.map(t => t.id));

// IDs de categorias antigas (caso tenha rodado a versão de 8 abas antes)
const OLD_CATEGORY_IDS = ['depoimentos-anuncios', 'estrategia-mensal', 'lideranca', 'pilares-metodo', 'equipe-engajamento', 'vendedores', 'lucro', 'empresario-cultura'];

const before = nav.tabs.length;
nav.tabs = nav.tabs.filter(t => t.id !== 'transcricoes' && !newIds.has(t.id) && !OLD_CATEGORY_IDS.includes(t.id));
const removed = before - nav.tabs.length;
if (removed > 0) console.log(`🗑️  Removeu ${removed} aba(s) antiga(s)`);

nav.tabs.push(...newTabs);
console.log(`➕ Adicionou aba "${newTabs[0].label}" (${newTabs[0].sections.length - 1} transcrições)`);

await writeFile(NAV, JSON.stringify(nav, null, 2) + '\n', 'utf8');
console.log(`✅ nav.json atualizado — ${nav.tabs.length} abas total`);
