#!/usr/bin/env node
/* ============================================================
   NORMALIZE-ICONS v3 — pós-processa data/icons-index.json
   Resolve bugs de exportação do Figma onde múltiplos ícones
   compartilham o mesmo SVG (a rotação ficava no nó parent).

   Estratégia: mapeamento explícito de famílias direcionais.
   Cada família declara seu SVG canônico (verificado manualmente)
   e as 4 (ou mais) direções derivadas via transform CSS.
============================================================ */

import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const INDEX = join(ROOT, 'data', 'icons-index.json');

// ===== FAMÍLIAS DIRECIONAIS =====
// Declara, pra cada família, o canônico (SVG verificado no disco) e
// as direções derivadas. Direção `null` = sem transform (canônico).
const FAMILIES = [
  // Cardinal — chevron simples (chevron-up.svg verificado: aponta UP)
  {
    canonicalSrc: 'assets/icons/arrows/chevron-up.svg',
    canonicalSection: 'arrows',
    members: [
      { name: 'chevron-up',    transform: null },
      { name: 'chevron-right', transform: 'rotate(90deg)' },
      { name: 'chevron-down',  transform: 'rotate(180deg)' },
      { name: 'chevron-left',  transform: 'rotate(-90deg)' }
    ]
  },

  // Cardinal — chevron-double (chevron-double-down verificado: 2 V apontando DOWN)
  {
    canonicalSrc: 'assets/icons/arrows/chevron-double-down.svg',
    canonicalSection: 'arrows',
    members: [
      { name: 'chevron-double-down',  transform: null },
      { name: 'chevron-double-left',  transform: 'rotate(90deg)' },
      { name: 'chevron-double-up',    transform: 'rotate(180deg)' },
      { name: 'chevron-double-right', transform: 'rotate(-90deg)' }
    ]
  },

  // Arrow simples — quatro arquivos próprios MAS arrow-down faltando
  // (cada arquivo tem path próprio verificado, exceto arrow-down)
  {
    canonicalSrc: 'assets/icons/arrows/arrow-up.svg',
    canonicalSection: 'arrows',
    perDir: {
      up:    { src: 'assets/icons/arrows/arrow-up.svg',    transform: null },
      left:  { src: 'assets/icons/arrows/arrow-left.svg',  transform: null },
      right: { src: 'assets/icons/arrows/arrow-right.svg', transform: null },
      down:  { src: 'assets/icons/arrows/arrow-up.svg',    transform: 'rotate(180deg)' }
    },
    members: [
      { name: 'arrow-up' },    { name: 'arrow-down' },
      { name: 'arrow-left' },  { name: 'arrow-right' }
    ]
  },

  // Arrow -sm (sufixo small)
  {
    canonicalSrc: 'assets/icons/arrows/arrow-up-sm.svg',
    canonicalSection: 'arrows',
    perDir: {
      up:    { src: 'assets/icons/arrows/arrow-up-sm.svg',    transform: null },
      left:  { src: 'assets/icons/arrows/arrow-left-sm.svg',  transform: null },
      right: { src: 'assets/icons/arrows/arrow-right-sm.svg', transform: null },
      down:  { src: 'assets/icons/arrows/arrow-up-sm.svg',    transform: 'rotate(180deg)' }
    },
    members: [
      { name: 'arrow-up-sm' },    { name: 'arrow-down-sm' },
      { name: 'arrow-left-sm' },  { name: 'arrow-right-sm' }
    ]
  },

  // Arrow contained (cardinal) — usa arrow-up-contained-01 como base de "up"
  {
    canonicalSrc: 'assets/icons/arrows/arrow-up-contained-01.svg',
    canonicalSection: 'arrows',
    perDir: {
      up:    { src: 'assets/icons/arrows/arrow-up-contained-01.svg',    transform: null },
      left:  { src: 'assets/icons/arrows/arrow-left-contained-01.svg',  transform: null },
      right: { src: 'assets/icons/arrows/arrow-right-contained-01.svg', transform: null },
      down:  { src: 'assets/icons/arrows/arrow-down-contained-01.svg',  transform: null }
    },
    members: [
      { name: 'arrow-up-contained-01' },    { name: 'arrow-down-contained-01' },
      { name: 'arrow-left-contained-01' },  { name: 'arrow-right-contained-01' }
    ]
  },

  // Arrow square contained (cardinal)
  {
    canonicalSection: 'arrows',
    perDir: {
      up:    { src: 'assets/icons/arrows/arrow-up-square-contained.svg',    transform: null },
      left:  { src: 'assets/icons/arrows/arrow-left-square-contained.svg',  transform: null },
      right: { src: 'assets/icons/arrows/arrow-right-square-contained.svg', transform: null },
      down:  { src: 'assets/icons/arrows/arrow-down-square-contained.svg',  transform: null }
    },
    members: [
      { name: 'arrow-up-square-contained' },    { name: 'arrow-down-square-contained' },
      { name: 'arrow-left-square-contained' },  { name: 'arrow-right-square-contained' }
    ]
  },

  // Arrow-curve — Manter só 4 (vertical/horizontal × CW/CCW)
  // Canônico: arrow-curve-left-down (verificado)
  {
    canonicalSrc: 'assets/icons/arrows/arrow-curve-left-down.svg',
    canonicalSection: 'arrows',
    members: [
      { name: 'arrow-curve-left-down',  transform: null },
      { name: 'arrow-curve-right-down', transform: 'scaleX(-1)' },
      { name: 'arrow-curve-left-up',    transform: 'scaleY(-1)' },
      { name: 'arrow-curve-right-up',   transform: 'scale(-1, -1)' }
    ],
    // Remove os outros nomes redundantes do catálogo
    purge: ['arrow-curve-left-right', 'arrow-curve-up-left', 'arrow-curve-up-right']
  }
];

// ===== EXECUTA =====
const idx = JSON.parse(await readFile(INDEX, 'utf8'));

// Limpa estado anterior
for (const ic of idx.icons) {
  delete ic.transform;
  delete ic.transformKind;
  delete ic.duplicateOf;
  delete ic.duplicateRole;
  delete ic.duplicateGroup;
  delete ic.virtual;
  delete ic.virtualOf;
}

const byId = new Map(idx.icons.map(ic => [ic.id, ic]));

// 1. Aplica famílias declaradas
let updated = 0, virtualAdded = 0, purged = 0;
const purgeIds = new Set();

for (const fam of FAMILIES) {
  for (const m of fam.members) {
    const id = `${fam.canonicalSection}/${m.name}`;
    let existing = byId.get(id);

    // Determina src e transform pra esse membro
    let src, transform;
    if (fam.perDir) {
      // Detecta direção pelo nome
      const dirMatch = m.name.match(/-(up|down|left|right)(-|$)/);
      const dir = dirMatch ? dirMatch[1] : 'up';
      const cfg = fam.perDir[dir];
      if (!cfg) continue;
      src = cfg.src;
      transform = cfg.transform;
    } else {
      src = fam.canonicalSrc;
      transform = m.transform;
    }

    // Converte transform pra string ou null
    const t = transform || null;

    if (existing) {
      // Override: atualiza src e transform
      const changed = existing.src !== src || (existing.transform || null) !== t;
      if (changed) {
        existing.src = src;
        if (t) existing.transform = t; else delete existing.transform;
        updated++;
      }
    } else {
      // Cria entry virtual
      const newEntry = {
        id,
        section: fam.canonicalSection,
        name: m.name,
        nodeId: 'virtual',
        src,
        virtual: true
      };
      if (t) newEntry.transform = t;
      idx.icons.push(newEntry);
      byId.set(id, newEntry);
      virtualAdded++;
    }
  }
  // Marca pra remoção
  if (fam.purge) {
    for (const purgeName of fam.purge) {
      purgeIds.add(`${fam.canonicalSection}/${purgeName}`);
    }
  }
}

// 2. Detecta duplicatas restantes via MD5 e remove (mantém alfabético primeiro)
//    IGNORA ícones com `transform` ou `virtual` — são variações intencionais
//    que compartilham SVG fonte por design.
const groups = new Map();
for (const ic of idx.icons) {
  if (ic.virtual) continue;
  if (ic.transform) continue;
  if (purgeIds.has(ic.id)) continue;
  try {
    const buf = await readFile(join(ROOT, ic.src));
    const h = createHash('md5').update(buf).digest('hex');
    if (!groups.has(h)) groups.set(h, []);
    groups.get(h).push(ic);
  } catch {}
}

const remaining = [];
for (const [hash, list] of groups) {
  if (list.length > 1) {
    list.sort((a, b) => a.name.localeCompare(b.name));
    // Mantém canônico (primeiro), descarta o resto
    for (const dup of list.slice(1)) {
      remaining.push({ canonical: list[0].id, duplicate: dup.id });
      purgeIds.add(dup.id);
    }
  }
}

// 3. Aplica purge
const before = idx.icons.length;
idx.icons = idx.icons.filter(ic => !purgeIds.has(ic.id));
purged = before - idx.icons.length;

// 4. Recalcula counts
const sectionCounts = {};
for (const ic of idx.icons) sectionCounts[ic.section] = (sectionCounts[ic.section] || 0) + 1;
for (const s of idx.sections) s.count = sectionCounts[s.id] || 0;
idx.totalIcons = idx.icons.length;

// 5. Ordena
idx.icons.sort((a, b) => {
  if (a.section !== b.section) return a.section.localeCompare(b.section);
  return a.name.localeCompare(b.name, 'pt-BR');
});

idx.normalizedAt = new Date().toISOString();
await writeFile(INDEX, JSON.stringify(idx, null, 2) + '\n', 'utf8');

console.log(`✓ Famílias direcionais aplicadas: ${FAMILIES.length}`);
console.log(`  Ícones atualizados (src/transform corrigido): ${updated}`);
console.log(`  Ícones virtuais criados (direções faltantes): ${virtualAdded}`);
console.log(`  Ícones purgados (duplicatas/redundantes): ${purged}`);
console.log(`\nDuplicatas removidas:`);
for (const r of remaining.slice(0, 30)) console.log(`  ${r.duplicate}  (=  ${r.canonical})`);
if (remaining.length > 30) console.log(`  ... +${remaining.length - 30}`);
console.log(`\nCatálogo final: ${idx.icons.length} ícones`);
