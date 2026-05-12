#!/usr/bin/env node
/* ============================================================
   IMPORT-CARROSSEL — importa carrosséis multi-slide
   - Aceita múltiplos jobs (array de configs)
   - Lê pasta com slides PNG/JPG numerados (1.png, 2.png, ...)
   - Pra cada slide: gera webp em assets/applications/carrosseis/<id>/
   - Capa (slide-1) também serve como thumb
   - Adiciona/atualiza entry no applications-index.json
   - Atualiza types{} com 'carrossel' se faltar
============================================================ */

import { readFile, writeFile, readdir, mkdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join, extname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const ASSETS = join(ROOT, 'assets', 'applications', 'carrosseis');
const INDEX = join(ROOT, 'data', 'applications-index.json');

// ===== CARROSSÉIS A IMPORTAR =====
const JOBS = [
  {
    id: 'carrossel-37-empresarios-em-burnout',
    sourcePath: 'C:\\Users\\Usuario\\Desktop\\Renan\\Clientes\\Metta\\Funis\\01. Social\\Metta\\37% dos empresarios estao em burnout',
    brand: 'metta',
    intent: 'autoridade',
    icp_target: ['acelera', 'premium'],
    title: '37% dos empresários estão em burnout',
    tese: 'Burnout do empresário não é falta de meditação — é falta de método. Empresa autônoma resolve.',
    mood: 'confronto-editorial',
    tokens_used: ['charcoal-dark-blue', 'yellow-50-sotaque', 'title-large-display', 'expanded-heavy', 'imagem-conceitual'],
    archetype_foto: 'imagem-conceitual-editorial',
    slot_functions: {
      1: 'capa-hook-dado',           // 37% empreendedores em burnout (cabeça aberta)
      2: 'pesquisa-empilhada',        // 94,1% saúde mental + 70% engajamento (Gallup)
      3: 'desenvolvimento',
      4: 'desenvolvimento',
      5: 'reframe-editorial',         // É o olho do dono que engorda o gado
      6: 'metodo',
      7: 'metodo',
      8: 'punchline-reframe',         // Burnout não se resolve com meditação (lâmpada na cabeça)
      9: 'fechamento-prova-cta'       // 72% qualidade de vida + Fale com a Metta
    },
    notes: 'Carrossel editorial Metta de prova-pesada. Estrutura: hook com dado externo (37% Gallup) → pesquisa empilhada → reframe editorial via metáforas (vaca, lâmpada na cabeça) → punchline → fechamento com prova interna (72% clientes Metta) + CTA. Estilo cinematográfico com imagens conceituais. Paleta charcoal/dark-blue + amarelo + claro nos slides de prova. Top of funnel pra empresário no limite.'
  },
  {
    id: 'carrossel-gestao-da-mudanca-time-3-vezes',
    sourcePath: 'C:\\Users\\Usuario\\Desktop\\Renan\\Clientes\\Metta\\Funis\\01. Social\\Metta\\Gestão da Mudança',
    brand: 'metta',
    intent: 'autoridade',
    icp_target: ['acelera', 'premium', 'elite'],
    title: 'Você já trocou o time 3 vezes',
    tese: 'O problema não está no time — está na ausência de gestão da mudança. Uma das 6 Gestões.',
    mood: 'provocacao-editorial',
    tokens_used: ['bege-papelao', 'charcoal-base', 'red-tag-mudanca', 'title-medium', 'expanded-heavy', 'imagem-conceitual'],
    archetype_foto: 'imagem-conceitual-editorial',
    slot_functions: {
      1: 'capa-provocacao',           // Você já trocou o time 3 vezes (cabeça peeking entre caixas)
      2: 'desenvolvimento',
      3: 'desenvolvimento',
      4: 'diagnostico',
      5: 'reframe',
      6: 'metodo-6-gestoes',
      7: 'metodo',
      8: 'metodo',
      9: 'prova',
      10: 'fechamento-cta'
    },
    notes: 'Carrossel da série "AS 6 GESTÕES" — pilar editorial Metta. Foco na Gestão da Mudança. Capa cinematográfica com cabeça peeking entre caixas/cubos bege simboliza "estar perdido no labirinto da gestão". Tags topo "AS 6 GESTÕES" + "MUDANÇA" (vermelho destaque). Reframe editorial: trocar time não resolve, é gestão. Funil: provocação → diagnóstico → método (6 Gestões da Meta Batida).'
  },
  {
    id: 'carrossel-post-fca-case-78-meta',
    sourcePath: 'C:\\Users\\Usuario\\Desktop\\Renan\\Clientes\\Metta\\Funis\\01. Social\\Metta\\Post FCA',
    brand: 'metta',
    intent: 'prova',
    icp_target: ['acelera', 'premium'],
    title: 'Case FCA — gestor saiu de 62% pra 78% da meta em 7 dias',
    tese: 'Com FCA (Ferramenta de Comportamento e Atitude), 15 min/dia bastam pra virar performance — sem demitir, sem contratar.',
    mood: 'prova-acolhedora',
    tokens_used: ['light-base', 'charcoal-base', 'yellow-50-sotaque', 'title-medium', 'expanded-heavy', 'foto-pessoa-real'],
    archetype_foto: 'retrato-individual-confiante',
    slot_functions: {
      1: 'capa-case-numero',          // 62% → 78% em 7 dias (gestor real com laptop)
      2: 'contexto-empresa',
      3: 'sintoma-diagnostico',
      4: 'metodo-fca',
      5: 'metodo-fca',
      6: 'aplicacao-pratica',
      7: 'resultado',
      8: 'resultado-detalhado',
      9: 'reframe',
      10: 'fechamento-cta'
    },
    notes: 'Case real do banco com método FCA. Capa: número da virada (62→78%) + foto gestor + tag CASES. Body: 7 dias, sem demitir, sem contratar, "uma ferramenta, 15 minutos por dia" — promessa de simplicidade. Estilo Metta de prova nominal acolhedora — não mostra confronto, mostra resultado e leveza do método. Bottom funnel pra ICP que já reconhece dor e está buscando solução.'
  }
];

// ===== HELPERS =====
function detectFormat(w, h) {
  const r = w / h;
  if (Math.abs(r - 4 / 5) < 0.05) return `carrossel-${w}x${h}`;
  if (Math.abs(r - 1) < 0.05) return `square-${w}x${h}`;
  if (Math.abs(r - 9 / 16) < 0.06) return `story-${w}x${h}`;
  return `carrossel-${w}x${h}`;
}

async function processJob(JOB, idx) {
  if (!existsSync(JOB.sourcePath)) {
    console.log(`✗ Pulando ${JOB.id}: pasta não encontrada`);
    return false;
  }

  const targetDir = join(ASSETS, JOB.id);
  await mkdir(targetDir, { recursive: true });

  const files = (await readdir(JOB.sourcePath))
    .filter(f => /\.(png|jpe?g)$/i.test(f))
    .map(f => {
      // extrai o número do final do nome (1, 2, 10) — robusto a prefixos tipo "cr7metta-1.png"
      const stem = basename(f, extname(f));
      const m = stem.match(/(\d+)$/);
      return { file: f, n: m ? parseInt(m[1], 10) : 999 };
    })
    .sort((a, b) => a.n - b.n);

  if (files.length === 0) { console.log(`✗ ${JOB.id}: nenhum slide encontrado`); return false; }
  console.log(`\n📚 ${JOB.id} · ${files.length} slides`);

  const slots = [];
  let firstDims = null;
  for (let i = 0; i < files.length; i++) {
    const { file, n } = files[i];
    const src = join(JOB.sourcePath, file);
    const buf = await readFile(src);
    if (i === 0) {
      const meta = await sharp(buf).metadata();
      firstDims = { w: meta.width, h: meta.height };
    }
    const out = join(targetDir, `slide-${n}.webp`);
    await sharp(buf).resize({ width: 1080, withoutEnlargement: true }).webp({ quality: 88 }).toFile(out);
    slots.push({
      n,
      function: JOB.slot_functions?.[n] || null,
      src: `assets/applications/carrosseis/${JOB.id}/slide-${n}.webp`
    });
  }
  console.log(`  ✓ ${slots.length} webps gerados`);

  // Capa → thumb
  const capaBuf = await readFile(join(JOB.sourcePath, files[0].file));
  await sharp(capaBuf).resize({ width: 480, withoutEnlargement: false }).webp({ quality: 80 })
    .toFile(join(targetDir, '_thumb.webp'));

  const format = detectFormat(firstDims.w, firstDims.h);
  const fileStat = await stat(join(JOB.sourcePath, files[0].file));

  const entry = {
    id: JOB.id,
    type: 'carrossel',
    style: null,
    format,
    brand: JOB.brand,
    intent: JOB.intent,
    icp_target: JOB.icp_target,
    title: JOB.title,
    tese: JOB.tese,
    mood: JOB.mood,
    src: {
      thumb: `assets/applications/carrosseis/${JOB.id}/_thumb.webp`,
      mid:   `assets/applications/carrosseis/${JOB.id}/slide-1.webp`
    },
    slot_count: slots.length,
    slots,
    dimensions: firstDims,
    sourcePath: JOB.sourcePath.replace(/\\/g, '/'),
    date: fileStat.mtime.toISOString().slice(0, 10),
    status: 'canonical',
    tokens_used: JOB.tokens_used,
    archetype_foto: JOB.archetype_foto,
    notes: JOB.notes,
    copy: { headline: '', subheadline: '', cta: '' }
  };

  const existing = idx.applications.findIndex(a => a.id === JOB.id);
  if (existing >= 0) idx.applications[existing] = entry;
  else idx.applications.push(entry);
  console.log(`  ✓ Entry no índice (${format})`);
  return true;
}

async function main() {
  const idx = JSON.parse(await readFile(INDEX, 'utf8'));

  // Garante 'carrossel' em types (na ordem certa: ad → carrossel → slide → ...)
  if (!idx.types.carrossel) {
    const ordered = {};
    const order = ['ad', 'carrossel', 'slide', 'tela', 'lp', 'poster'];
    for (const k of order) {
      if (k === 'carrossel') ordered[k] = 'Carrosséis (Instagram)';
      else if (idx.types[k]) ordered[k] = idx.types[k];
    }
    idx.types = ordered;
    console.log('✓ Tipo "carrossel" adicionado em types{}');
  }

  let okCount = 0;
  for (const job of JOBS) {
    if (await processJob(job, idx)) okCount++;
  }

  idx.totalApplications = idx.applications.length;
  idx.generatedAt = new Date().toISOString();
  await writeFile(INDEX, JSON.stringify(idx, null, 2) + '\n', 'utf8');

  console.log(`\n✓ ${okCount}/${JOBS.length} carrosséis importados`);
  console.log(`✓ Total no índice: ${idx.totalApplications} peças`);
}

main().catch(e => { console.error('✗', e.message); process.exit(1); });
