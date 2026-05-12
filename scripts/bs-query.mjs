#!/usr/bin/env node
/* ============================================================
   BS-QUERY — CLI pra consultar o Brand System programaticamente
   Uso típico (humano ou agente IA):

     node scripts/bs-query.mjs --type ad --intent oferta --formato captacao-fb --limit 5

     node scripts/bs-query.mjs --serie deck-performance-leve --json
     node scripts/bs-query.mjs --search "burnout"
     node scripts/bs-query.mjs --type ad --style YELLOW-BLOCO --densidade media
     node scripts/bs-query.mjs --list-vocab        # mostra vocabulários controlados

   Output default: tabela compacta com id · type · style · intent · title.
   Com --json: array JSON estruturado pronto pra próximo passo (briefing rico).
============================================================ */

import { readFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const INDEX = join(ROOT, 'data', 'applications-index.json');

// ===== PARSER DE ARGUMENTOS =====
function parseArgs(argv) {
  const args = {};
  const flags = ['json', 'list-vocab', 'help', 'h', 'verbose', 'count'];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--') && !a.startsWith('-')) continue;
    const k = a.replace(/^-+/, '');
    if (flags.includes(k)) { args[k] = true; continue; }
    const v = argv[i + 1];
    if (v === undefined || v.startsWith('--')) { args[k] = true; continue; }
    args[k] = v;
    i++;
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));

if (args.help || args.h) {
  console.log(`
bs-query — consulta o Brand System

Filtros (combine livremente):
  --type        ad | carrossel | slide | tela | lp | poster
  --style       (pra ads) A, B, C, D, YELLOW-BLOCO, DARK-CARTA, etc.
  --brand       metta | tiago
  --intent      autoridade | oferta | prova | conversao
  --formato     formato_canonico (captacao-fb, hero-lp, capa-deck, etc.)
  --serie       serie_id (deck-performance-leve, pp-se-captacao-fb, etc.)
  --densidade   baixa | media | alta
  --mood        confronto, autoridade, aspiracional, etc.
  --icp         acelera | premium | elite | exclusive
  --search      texto livre (busca em title, tese, notes)
  --limit       N (default: 20)

Output:
  (default)     tabela compacta — id · type · style · intent · title
  --json        array JSON pronto pra briefing (id, type, style, intent, formato_canonico,
                serie_id, densidade_texto, tese, notes, src, copy)
  --count       só retorna o número de matches
  --verbose     inclui notes editoriais completas no output

Utility:
  --list-vocab  imprime vocabulários controlados (types, formato_canonico, etc.)
  --help, -h    esta ajuda

Exemplos:
  node scripts/bs-query.mjs --type ad --intent oferta --formato captacao-fb --limit 5
  node scripts/bs-query.mjs --serie deck-performance-leve --json
  node scripts/bs-query.mjs --search "burnout" --json
`);
  process.exit(0);
}

// ===== LÊ ÍNDICE =====
const idx = JSON.parse(await readFile(INDEX, 'utf8'));

// ===== LIST VOCAB =====
if (args['list-vocab']) {
  console.log('=== Vocabulários controlados ===\n');
  console.log('types:', JSON.stringify(idx.types, null, 2));
  console.log('\nintents:', JSON.stringify(idx.intents, null, 2));
  console.log('\nbrands:', JSON.stringify(idx.brands, null, 2));
  console.log('\nformato_canonico_values:', JSON.stringify(idx.formato_canonico_values, null, 2));
  console.log('\ndensidade_texto_values:', JSON.stringify(idx.densidade_texto_values, null, 2));
  console.log('\nmoods (vistos no banco):');
  const moods = [...new Set(idx.applications.map(a => a.mood).filter(Boolean))].sort();
  for (const m of moods) console.log(`  ${m}`);
  console.log('\nstyles de ad (vistos no banco):');
  const styles = [...new Set(idx.applications.filter(a => a.type === 'ad').map(a => a.style).filter(Boolean))].sort();
  for (const s of styles) console.log(`  ${s}`);
  console.log('\nséries (vistos no banco):');
  const series = [...new Set(idx.applications.map(a => a.serie_id).filter(Boolean))].sort();
  for (const s of series) console.log(`  ${s}`);
  process.exit(0);
}

// ===== APLICA FILTROS =====
let results = idx.applications;

const FIELD_MAP = {
  type:       a => a.type,
  style:      a => a.style,
  brand:      a => a.brand,
  intent:     a => a.intent,
  formato:    a => a.formato_canonico,
  serie:      a => a.serie_id,
  densidade:  a => a.densidade_texto,
  mood:       a => a.mood
};

for (const [key, getter] of Object.entries(FIELD_MAP)) {
  if (args[key]) {
    results = results.filter(a => getter(a) === args[key]);
  }
}

if (args.icp) {
  const icp = args.icp.toLowerCase();
  results = results.filter(a => Array.isArray(a.icp_target) && a.icp_target.includes(icp));
}

if (args.search) {
  const q = args.search.toLowerCase();
  results = results.filter(a =>
    (a.title || '').toLowerCase().includes(q) ||
    (a.tese || '').toLowerCase().includes(q) ||
    (a.notes || '').toLowerCase().includes(q) ||
    a.id.toLowerCase().includes(q)
  );
}

// ===== LIMIT =====
const limit = args.limit ? parseInt(args.limit, 10) : 20;
const total = results.length;
const limited = results.slice(0, limit);

// ===== OUTPUT =====
if (args.count) {
  console.log(total);
  process.exit(0);
}

if (args.json) {
  const out = limited.map(a => ({
    id: a.id,
    type: a.type,
    style: a.style,
    brand: a.brand,
    intent: a.intent,
    formato_canonico: a.formato_canonico,
    serie_id: a.serie_id,
    densidade_texto: a.densidade_texto,
    icp_target: a.icp_target,
    mood: a.mood,
    title: a.title,
    tese: a.tese,
    notes: a.notes,
    tokens_used: a.tokens_used,
    archetype_foto: a.archetype_foto,
    src: a.src,
    copy: a.copy,
    sourcePath: a.sourcePath
  }));
  console.log(JSON.stringify({ total, returned: limited.length, results: out }, null, 2));
  process.exit(0);
}

// Tabela default
const fmt = (s, n) => (s || '').toString().padEnd(n).slice(0, n);
console.log(fmt('id', 50), fmt('type', 11), fmt('style', 14), fmt('intent', 11), fmt('formato', 22), 'title');
console.log('─'.repeat(150));
for (const a of limited) {
  const title = (a.title || '').replace(/\s+/g, ' ');
  console.log(
    fmt(a.id, 50),
    fmt(a.type, 11),
    fmt(a.style, 14),
    fmt(a.intent, 11),
    fmt(a.formato_canonico, 22),
    title.slice(0, 60)
  );
  if (args.verbose && a.notes) {
    console.log(`    ${a.notes}`);
  }
}
console.log('─'.repeat(150));
console.log(`${limited.length} de ${total} matches${total > limit ? ' (use --limit pra ajustar)' : ''}`);
