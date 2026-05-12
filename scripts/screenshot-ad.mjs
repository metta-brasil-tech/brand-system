#!/usr/bin/env node
/* Captura screenshot 1080x1920 de um ad HTML via Chrome headless,
   salva como webp (mid + thumb) em assets/applications/ads/, e adiciona
   entry no applications-index.json */
import { readFile, writeFile, copyFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SOURCE_HTML = resolve(ROOT, '..', 'ad-yellow-bloco-mentoria-metodologia-lucro.html');
const TMP_HTML = resolve(ROOT, '..', '_export-ad.html');
const TMP_PNG = resolve(ROOT, '..', '_export-ad.png');

// Override do transform: scale pra renderizar 1:1
const OVERRIDE_CSS = `
<style id="export-override">
  body { padding: 0 !important; background: transparent !important; }
  .ad { transform: none !important; box-shadow: none !important; }
  .meta { display: none !important; }
</style>
`;

async function main() {
  // 1. Cria HTML override
  let html = await readFile(SOURCE_HTML, 'utf8');
  html = html.replace('</head>', `${OVERRIDE_CSS}</head>`);
  await writeFile(TMP_HTML, html, 'utf8');

  // 2. Screenshot via Chrome headless
  console.log('📷 Capturando screenshot 1080x1920...');
  const cmd = `"${CHROME}" --headless --disable-gpu --no-sandbox --hide-scrollbars --window-size=1080,1920 --screenshot="${TMP_PNG}" "file:///${TMP_HTML.replace(/\\/g, '/')}"`;
  execSync(cmd, { stdio: 'inherit' });

  if (!existsSync(TMP_PNG)) throw new Error('Screenshot não foi gerado');
  console.log('✓ Screenshot capturado');

  // 3. Define ID + paths
  const id = 'ad-yellow-bloco-mentoria-metodologia-lucro';
  const dirSeg = 'ads';
  await mkdir(join(ROOT, 'assets', 'applications', dirSeg, 'thumbs'), { recursive: true });
  await mkdir(join(ROOT, 'assets', 'applications', dirSeg, 'mid'),    { recursive: true });

  const midPath = join(ROOT, 'assets', 'applications', dirSeg, 'mid', `${id}.webp`);
  const thumbPath = join(ROOT, 'assets', 'applications', dirSeg, 'thumbs', `${id}.webp`);

  // 4. Converte PNG → webp (mid 1280, thumb 480)
  const buf = await readFile(TMP_PNG);
  await sharp(buf).resize({ width: 1280 }).webp({ quality: 88 }).toFile(midPath);
  await sharp(buf).resize({ width: 480 }).webp({ quality: 80 }).toFile(thumbPath);
  console.log(`✓ Webp gerados: mid + thumb`);

  // 5. Adiciona entry no applications-index.json
  const INDEX = join(ROOT, 'data', 'applications-index.json');
  const idx = JSON.parse(await readFile(INDEX, 'utf8'));
  const existing = idx.applications.findIndex(a => a.id === id);

  const entry = {
    id,
    type: 'ad',
    style: 'YELLOW-BLOCO',
    format: 'story-1080x1920',
    brand: 'metta',
    intent: 'oferta',
    icp_target: ['acelera', 'premium'],
    title: 'Metodologia de vendas que constrói lucro na sua operação',
    tese: 'Mentoria SMTM com método testado em escala destrava lucro na operação do empresário',
    mood: 'autoridade',
    src: {
      thumb: `assets/applications/${dirSeg}/thumbs/${id}.webp`,
      mid:   `assets/applications/${dirSeg}/mid/${id}.webp`
    },
    dimensions: { w: 1080, h: 1920 },
    sourcePath: SOURCE_HTML.replace(/\\/g, '/'),
    date: new Date().toISOString().slice(0, 10),
    status: 'canonical',
    tokens_used: ['charcoal-base', 'yellow-50-sotaque', 'title-large', 'expanded-heavy', 'expanded-bold-cta'],
    archetype_foto: 'retrato-individual-confiante',
    notes: 'YELLOW-BLOCO no Padrão A (foto BG full + card overlay). Foto pes-011 (executivo brasileiro 35-45, mood approachable authority). Headline com palavra "lucro" destacada via underline-marker. Logo bar de clientes carrega prova social agregada (+1000). CTA pill preto com seta amarela. Quando brilha: convite de mentoria pra ICP que já tem operação ativa mas estagnou — combina prova institucional + oferta sem dor pessoal.',
    copy: {
      headline: 'Metodologia de vendas que constrói lucro na sua operação.',
      subheadline: 'Faça parte da mentoria que escalou +1.000 operações comerciais no Brasil.',
      cta: 'Aplicar para mentoria'
    }
  };

  if (existing >= 0) {
    idx.applications[existing] = entry;
    console.log(`✓ Entry atualizada: ${id}`);
  } else {
    idx.applications.push(entry);
    console.log(`✓ Entry adicionada: ${id}`);
  }
  // Recalcula contagens
  const counts = {};
  for (const a of idx.applications) counts[a.type] = (counts[a.type] || 0) + 1;
  for (const t of Object.keys(idx.types)) {
    // só atualiza se houver
  }
  idx.totalApplications = idx.applications.length;
  idx.generatedAt = new Date().toISOString();
  await writeFile(INDEX, JSON.stringify(idx, null, 2) + '\n', 'utf8');
  console.log(`✓ applications-index.json atualizado · ${idx.totalApplications} peças total`);

  // 6. Cleanup
  for (const f of [TMP_HTML, TMP_PNG]) {
    try { await import('node:fs/promises').then(m => m.unlink(f)); } catch {}
  }
  console.log('✓ Cleanup feito.');
}

main().catch(e => { console.error('✗', e.message); process.exit(1); });
