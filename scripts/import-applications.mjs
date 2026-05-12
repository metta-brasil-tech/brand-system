#!/usr/bin/env node
/* ============================================================
   IMPORT-APPLICATIONS — banco de peças do BS
   - Lê classification JSON em C:\tmp\applications-classification.json
   - Pra cada peça: copia/redimensiona, gera thumb + mid
   - Atualiza data/applications-index.json com classificação editorial
   - Idempotente: preserva campos editoriais que o user editar manualmente
============================================================ */

import { readFile, writeFile, mkdir, copyFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join, basename, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const ASSETS = join(ROOT, 'assets', 'applications');
const INDEX = join(ROOT, 'data', 'applications-index.json');

const REF_BASE = 'C:\\Users\\Usuario\\Desktop\\Renan\\Clientes\\Metta\\Rebranding\\01. Assets de Marca\\Referências Design';
const CLASSIFICATION_FILES = [
  'C:\\tmp\\applications-classification.json',
  'C:\\tmp\\applications-classification-batch2.json'
];

// Mapeamento type → subpasta source (LP fica vazio — apontar quando subir LPs reais)
const SOURCE_FOLDER = {
  ad:     'Modelos de ADS',
  slide:  'Slides',
  tela:   'Telas Conceito',
  lp:     'LPs',
  poster: 'Posters'
};

const TYPE_DIR = { ad: 'ads', slide: 'slides', tela: 'telas', lp: 'lps', poster: 'posters' };

function detectFormatFromAspect(w, h) {
  const r = w / h;
  if (Math.abs(r - 1) < 0.05) return `square-${w}x${h}`;
  if (Math.abs(r - 9 / 16) < 0.06) return `story-${w}x${h}`;
  if (Math.abs(r - 4 / 5) < 0.05) return `feed-vertical-${w}x${h}`;
  if (Math.abs(r - 16 / 9) < 0.06) return `slide-${w}x${h}`;
  if (Math.abs(r - 3 / 2) < 0.05) return `landscape-${w}x${h}`;
  if (Math.abs(r - 2 / 3) < 0.05) return `portrait-${w}x${h}`;
  if (r > 1) return `landscape-${w}x${h}`;
  return `portrait-${w}x${h}`;
}

function parseSvgViewBox(svgText) {
  const m = svgText.match(/viewBox=["']([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)["']/);
  if (m) return { w: parseFloat(m[3]), h: parseFloat(m[4]) };
  return { w: 1080, h: 1920 };
}

async function getDimensions(filepath, ext) {
  if (ext === '.svg') {
    const txt = await readFile(filepath, 'utf8');
    return parseSvgViewBox(txt);
  }
  const m = await sharp(filepath).metadata();
  return { w: m.width, h: m.height };
}

function slugifyTitle(title) {
  return title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 60);
}

async function main() {
  for (const t of Object.values(TYPE_DIR)) {
    await mkdir(join(ASSETS, t, 'thumbs'), { recursive: true });
    await mkdir(join(ASSETS, t, 'mid'),    { recursive: true });
  }

  const classification = [];
  for (const cf of CLASSIFICATION_FILES) {
    if (existsSync(cf)) {
      const part = JSON.parse(await readFile(cf, 'utf8'));
      classification.push(...part);
      console.log(`Carregadas ${part.length} classificações de ${cf}`);
    }
  }
  console.log(`Total: ${classification.length} classificações`);

  let idx = {
    version: '1.0',
    generatedAt: new Date().toISOString(),
    types: {
      ad:     'Ads (anúncios)',
      slide:  'Slides (apresentações)',
      tela:   'Telas Conceito (posters, banners, editoriais)',
      lp:     'LPs (landing pages)',
      poster: 'Posters editoriais'
    },
    intents: {
      autoridade: 'Autoridade',
      oferta:     'Oferta',
      prova:      'Prova',
      conversao:  'Conversão direta'
    },
    brands: { metta: 'Metta', tiago: 'Tiago Alves' },
    icps: { acelera: 'Acelera', elite: 'Elite', premium: 'Premium', exclusive: 'Exclusive' },
    moods: ['confronto', 'provocacao', 'autoridade', 'aspiracional', 'analitico', 'acolhedor', 'urgencia'],
    applications: []
  };
  if (existsSync(INDEX)) {
    try {
      const prev = JSON.parse(await readFile(INDEX, 'utf8'));
      idx.applications = prev.applications || [];
    } catch {}
  }
  const existing = new Map(idx.applications.map(a => [a.id, a]));

  const log = { ok: 0, missing: [], errors: [] };

  for (const c of classification) {
    const folder = SOURCE_FOLDER[c.type];
    if (!folder) { log.errors.push(`type desconhecido: ${c.type}`); continue; }
    const src = join(REF_BASE, folder, c.filename);
    if (!existsSync(src)) { log.missing.push(c.filename); continue; }

    const ext = extname(src).toLowerCase();
    const buf = await readFile(src);
    let dims;
    try { dims = await getDimensions(src, ext); }
    catch (e) { log.errors.push(`${c.filename}: ${e.message}`); continue; }
    const format = detectFormatFromAspect(dims.w, dims.h);

    const baseSlug = slugifyTitle(c.title || basename(c.filename, ext));
    let id = `${c.type}-${baseSlug}`;
    // Inclui style no ID pra ads (desambigua quando 2 estilos têm tema parecido)
    if (c.type === 'ad' && c.style) {
      id = `${c.type}-${c.style.toLowerCase()}-${baseSlug}`;
    }
    const dirSeg = TYPE_DIR[c.type];
    const thumbPath = join(ASSETS, dirSeg, 'thumbs', `${id}.webp`);
    const midPathRaster = join(ASSETS, dirSeg, 'mid', `${id}.webp`);
    const midPathSvg = join(ASSETS, dirSeg, 'mid', `${id}.svg`);

    let midRel, thumbRel;
    try {
      if (ext === '.svg') {
        await copyFile(src, midPathSvg);
        midRel = `assets/applications/${dirSeg}/mid/${id}.svg`;
        // Tenta rasterizar SVG pra thumb webp; se falhar (SVG muito grande),
        // copia o próprio SVG como thumb (browser escala via CSS)
        try {
          await sharp(buf, { density: 72 })
            .resize({ width: 480, withoutEnlargement: false })
            .webp({ quality: 80 })
            .toFile(thumbPath);
          thumbRel = `assets/applications/${dirSeg}/thumbs/${id}.webp`;
        } catch {
          const thumbSvgPath = join(ASSETS, dirSeg, 'thumbs', `${id}.svg`);
          await copyFile(src, thumbSvgPath);
          thumbRel = `assets/applications/${dirSeg}/thumbs/${id}.svg`;
        }
      } else {
        await sharp(buf).resize({ width: 1280, withoutEnlargement: true }).webp({ quality: 85 }).toFile(midPathRaster);
        await sharp(buf).resize({ width: 480, withoutEnlargement: true }).webp({ quality: 80 }).toFile(thumbPath);
        midRel = `assets/applications/${dirSeg}/mid/${id}.webp`;
        thumbRel = `assets/applications/${dirSeg}/thumbs/${id}.webp`;
      }
    } catch (e) {
      log.errors.push(`${c.filename}: render ${e.message}`);
      continue;
    }

    const fileStat = await stat(src);
    const auto = {
      id,
      type: c.type,
      style: c.style || null,
      format,
      brand: c.brand || 'metta',
      intent: c.intent,
      icp_target: c.icp_target || [],
      title: c.title,
      tese: c.tese,
      mood: c.mood,
      src: { thumb: thumbRel, mid: midRel },
      dimensions: dims,
      sourcePath: src.replace(/\\/g, '/'),
      date: fileStat.mtime.toISOString().slice(0, 10),
      status: 'canonical',
      tokens_used: c.tokens_used || [],
      archetype_foto: c.archetype_foto || null,
      notes: c.notes || ''
    };

    // Merge: preserva edições manuais do usuário (campos abaixo são "editáveis")
    const prev = existing.get(id) || {};
    const editableFields = ['notes', 'tokens_used', 'archetype_foto', 'intent', 'mood', 'icp_target', 'title', 'tese', 'status', 'copy'];
    const merged = { ...auto };
    for (const f of editableFields) {
      if (prev[f] !== undefined && prev[f] !== null && (Array.isArray(prev[f]) ? prev[f].length > 0 : prev[f] !== '')) {
        merged[f] = prev[f];
      }
    }
    if (!merged.copy) merged.copy = { headline: '', subheadline: '', cta: '' };

    existing.set(id, merged);
    log.ok++;
  }

  idx.applications = Array.from(existing.values()).sort((a, b) => {
    if (a.type !== b.type) {
      const order = ['ad', 'slide', 'tela', 'poster'];
      return order.indexOf(a.type) - order.indexOf(b.type);
    }
    return a.id.localeCompare(b.id);
  });
  idx.totalApplications = idx.applications.length;
  idx.generatedAt = new Date().toISOString();

  await writeFile(INDEX, JSON.stringify(idx, null, 2) + '\n', 'utf8');

  console.log(`\n✓ ${log.ok} importados com sucesso`);
  if (log.missing.length) console.log(`✗ ${log.missing.length} arquivos não encontrados:\n  ${log.missing.slice(0, 5).join('\n  ')}${log.missing.length > 5 ? '\n  ...' : ''}`);
  if (log.errors.length) console.log(`! ${log.errors.length} erros:\n  ${log.errors.slice(0, 5).join('\n  ')}`);
  console.log(`\nTotal no índice: ${idx.totalApplications} peças`);
}

main().catch(e => { console.error(e); process.exit(1); });
