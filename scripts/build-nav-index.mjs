#!/usr/bin/env node
// ============================================================
// METTA BRAND SYSTEM — BUILD NAV INDEX
// Gera data/nav-index.json: um índice LEVE (só título + caminho + destino),
// pensado pra busca instantânea de "qualquer coisa que existe na plataforma"
// (página, assunto dentro de página, material pra baixar, ícone, foto, logo,
// transcrição). Diferente de data/search-index.json (o índice pesado, com
// texto integral dos documentos), esse aqui não guarda corpo de texto —
// só o necessário pra casar a busca e montar o caminho de navegação.
//
// Lê:
//   - data/nav.json                → páginas + assuntos (h2s)
//   - data/download-manifest.json  → materiais pra baixar (grupo "modelos")
//   - data/icons-index.json        → ícones
//   - data/photo-index.json        → fotos (por estilo/arquétipo)
//   - data/transcricoes-index.json → transcrições (categorias)
//   - assets/logos|symbols|signatures → arquivos de logo
// Escreve data/nav-index.json.
// ============================================================

import { readFile, writeFile, readdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const DATA_DIR = join(ROOT, 'data');
const ASSETS_DIR = join(ROOT, 'assets');
const OUT_PATH = join(DATA_DIR, 'nav-index.json');

const log = {
  info: (m) => console.log(`  ${m}`),
  ok:   (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  group:(m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

// Mesma normalização usada em app.js (runSearch) — minúsculas + sem acento.
// Precisa ficar idêntica pros dois lados (build e client) casarem o texto.
function normalizeForSearch(s) {
  return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function juntaTexto(...partes) {
  return normalizeForSearch(partes.filter(Boolean).join(' '));
}

const entries = [];

function addEntry(tipo, titulo, caminho, hash, textoExtra) {
  if (!titulo || !hash) return;
  entries.push({
    tipo,
    titulo,
    caminho,
    hash,
    texto: juntaTexto(titulo, textoExtra)
  });
}

// ----------- 1. PÁGINAS + ASSUNTOS (data/nav.json) -----------
// Regra: tab ou seção com hidden:true fica fora (não é conteúdo "de propósito"),
// com a exceção das seções de transcrição, tratadas à parte no passo 6 — elas
// são indexadas ali porque cada uma tem link direto próprio (#/transcricoes/<id>),
// diferente de uma seção de doc normal.
async function indexarPaginasEAssuntos(nav) {
  let paginas = 0, assuntos = 0;
  for (const tab of nav.tabs) {
    if (tab.hidden || tab.dev_only) continue; // dev_only some da nav em produção — indexar quebraria o link
    for (const sec of tab.sections) {
      if (sec.hidden) continue; // cobre também as 95 seções de transcrição (tratadas no passo 6)

      const caminho = tab.label === sec.label ? [tab.label] : [tab.label, sec.label];
      // Texto de match fica só em título+caminho (não entra a description em
      // prosa): frases soltas geram falso positivo por substring — ex.:
      // "Catálogo" contém "logo" como substring e poluía a busca por "logo".
      addEntry('pagina', sec.label, caminho, `#/${tab.id}/${sec.id}`, tab.label);
      paginas++;

      // Assuntos = os h2 de dentro da página. O anchor (?h=) leva direto pro
      // trecho — ver scrollToAnchorFromHash() em app.js.
      for (const h2 of sec.h2s || []) {
        addEntry('assunto', h2.label, caminho, `#/${tab.id}/${sec.id}?h=${h2.id}`, null);
        assuntos++;
      }
    }
  }
  log.ok(`Páginas: ${paginas} · Assuntos (h2): ${assuntos}`);
}

// ----------- 2. MATERIAIS PRA BAIXAR (data/download-manifest.json) -----------
// Só o grupo "modelos" (documentos, ebooks, fundos de tela). O resto do
// manifest (docs, galeria, aplicações, identidade visual) já vem de outra fonte.
//
// Os rótulos do manifest são internos e técnicos ("Documentos editáveis (.docx)").
// Na página eles já aparecem em português comum, então o caminho da busca usa os
// mesmos nomes: caminho e página têm que dizer a mesma coisa.
const ROTULO_AMIGAVEL = {
  documentos: 'Documentos do Word',
  ebooks: 'Ebooks',
  'fundos-videochamada': 'Fundos de tela',
};

async function indexarMateriais(manifest) {
  const grupo = manifest.groups.find(g => g.id === 'modelos');
  if (!grupo) { log.warn('Grupo "modelos" não encontrado em download-manifest.json'); return; }
  let tabs = 0, itens = 0;
  for (const tab of grupo.tabs) {
    const rotulo = ROTULO_AMIGAVEL[tab.id] || tab.label;
    // O nome interno continua no texto de match: quem procurar por "docx" acha.
    addEntry('material', rotulo, ['Materiais para baixar'], `#/modelos/documentos?cat=${tab.id}`, tab.label);
    tabs++;
    for (const sec of tab.sections) {
      const q = encodeURIComponent(sec.id);
      addEntry('material', sec.label, ['Materiais para baixar', rotulo], `#/modelos/documentos?cat=${tab.id}&q=${q}`, [sec.category, sec.description].join(' '));
      itens++;
    }
  }
  log.ok(`Materiais: ${tabs} categorias · ${itens} itens`);
}

// ----------- 3. ÍCONES (data/icons-index.json) -----------
// 839 ícones é gente demais pra indexar com texto rico — cada item entra só
// com o próprio nome + a categoria. As 19 categorias entram também, pra quem
// busca "ícone" ou o nome de uma categoria (ex: "setas") cair direto nela.
async function indexarIcones(idx) {
  const labelPorSecao = new Map((idx.sections || []).map(s => [s.id, s.label]));
  for (const s of idx.sections || []) {
    addEntry('icone', s.label, ['Identidade Visual', 'Ícones'], `#/visual/icones?cat=${s.id}`, null);
  }
  for (const icon of idx.icons || []) {
    const secLabel = labelPorSecao.get(icon.section) || '';
    addEntry('icone', icon.name, ['Identidade Visual', 'Ícones', secLabel], `#/visual/icones?q=${encodeURIComponent(icon.name)}`, secLabel);
  }
  log.ok(`Ícones: ${(idx.sections || []).length} categorias · ${(idx.icons || []).length} itens`);
}

// ----------- 4. FOTOS (data/photo-index.json) -----------
// Indexa por ARQUÉTIPO (estilo), não por foto individual: a galeria só filtra
// por ?category=/?archetype=, então várias fotos do mesmo estilo cairiam no
// mesmo resultado repetido. Só entram arquétipos com pelo menos 1 foto real
// (count > 0) — os demais não têm pra onde levar (a página de Estilos é hidden).
async function indexarFotos(idx) {
  const categorias = idx.categories || {};
  const comFoto = (idx.archetypes || []).filter(a => a.count > 0);
  for (const a of comFoto) {
    const catLabel = categorias[a.category] || a.category;
    addEntry('foto', a.label, ['Galeria de imagens', catLabel], `#/direcao-arte/galeria?archetype=${a.id}`, [catLabel, a.description].join(' '));
  }
  log.ok(`Fotos (arquétipos com foto): ${comFoto.length}`);
}

// ----------- 5. LOGOS (assets/logos, assets/symbols, assets/signatures) -----------
// Nomes amigáveis vêm de um mapa fixo (bate com o texto que já existe em
// content/visual/logos.html). Arquivo novo que não estiver no mapa cai no
// fallback genérico — pra não sumir do índice, só sem o nome bonito.
// Pra ADICIONAR um logo novo ao mapa: acrescente "nome-do-arquivo.svg": "Nome amigável".
const NOMES_LOGO = {
  'logo_metta_colorido_escuro_h.svg': 'Logo horizontal, fundo claro',
  'logo_metta_colorido_h.svg': 'Logo horizontal, fundo escuro',
  'logo_metta_colorido_escuro_v.svg': 'Logo vertical, fundo claro',
  'logo_metta_colorido_v.svg': 'Logo vertical, fundo escuro',
  'logo_metta_azul_h.svg': 'Logo horizontal, sobre fundo amarelo',
  'logo_metta_azul_v.svg': 'Logo vertical, sobre fundo amarelo',
  'logo_metta_azul2_h.svg': 'Logo horizontal, azul alternativo',
  'logo_metta_azul2_v.svg': 'Logo vertical, azul alternativo',
  'logo_metta_branco_h.svg': 'Logo horizontal, branco sobre foto',
  'logo_metta_branco_v.svg': 'Logo vertical, branco sobre foto',
  'logo_metta_cinza_h.svg': 'Logo horizontal, cinza discreto',
  'logo_metta_cinza_v.svg': 'Logo vertical, cinza discreto',
  'logo_metta_tagline_colorida_h.svg': 'Logo com a frase da marca, fundo escuro',
  'logo_metta_tagline_colorida_escura_h.svg': 'Logo com a frase da marca, fundo claro',
  'simbolo_metta_amarelo.svg': 'Símbolo, amarelo',
  'simbolo_metta_azul.svg': 'Símbolo, azul noite',
  'simbolo_metta_azul2.svg': 'Símbolo, azul alternativo',
  'simbolo_metta_branco.svg': 'Símbolo, branco',
  'simbolo_metta_cinza.svg': 'Símbolo, cinza',
  'assinatura_metta_amarelo.svg': 'Assinatura, amarela',
  'assinatura_metta_azul.svg': 'Assinatura, azul noite',
  'assinatura_metta_azul2.svg': 'Assinatura, azul alternativa',
  'assinatura_metta_branco.svg': 'Assinatura, branca',
  'assinatura_metta_cinza.svg': 'Assinatura, cinza'
};

function nomeAmigavelDeArquivo(tipoPasta, arquivo) {
  if (NOMES_LOGO[arquivo]) return NOMES_LOGO[arquivo];
  // Fallback genérico: "logo_metta_x_h.svg" → "Logo x horizontal"
  const stem = arquivo.replace(/\.svg$/i, '');
  const partes = stem.split('_').filter(p => p && p.toLowerCase() !== 'metta');
  const rotuloTipo = { logo: 'Logo', simbolo: 'Símbolo', assinatura: 'Assinatura' }[tipoPasta] || 'Logo';
  const resto = partes.slice(1).map(p => (p === 'h' ? 'horizontal' : p === 'v' ? 'vertical' : p));
  return [rotuloTipo, ...resto].join(' ');
}

async function indexarLogos() {
  const pastas = [
    { dir: 'logos', tipo: 'logo' },
    { dir: 'symbols', tipo: 'simbolo' },
    { dir: 'signatures', tipo: 'assinatura' }
  ];
  let total = 0;
  for (const { dir, tipo } of pastas) {
    let arquivos = [];
    try { arquivos = (await readdir(join(ASSETS_DIR, dir))).filter(f => f.toLowerCase().endsWith('.svg')); }
    catch { continue; }
    for (const arquivo of arquivos) {
      const titulo = nomeAmigavelDeArquivo(tipo, arquivo);
      addEntry('logo', titulo, ['Identidade Visual', 'Logos'], '#/visual/logos', null);
      total++;
    }
  }
  log.ok(`Logos: ${total} arquivos (logos + símbolos + assinaturas)`);
}

// ----------- 6. TRANSCRIÇÕES (data/transcricoes-index.json + data/nav.json) -----------
// Cada transcrição tem seção própria em nav.json (hidden:true, transcricao:true)
// com rota direta #/transcricoes/<id> — usamos isso em vez do filtro da galeria,
// porque leva direto pro conteúdo, não só pra lista filtrada.
async function indexarTranscricoes(transIdx, nav) {
  for (const cat of transIdx.categories || []) {
    addEntry('transcricao', cat.label, ['Transcrições', 'Biblioteca'], `#/transcricoes/biblioteca?cat=${cat.id}`, cat.description);
  }
  const tab = nav.tabs.find(t => t.id === 'transcricoes');
  const itens = (tab?.sections || []).filter(s => s.transcricao);
  for (const sec of itens) {
    addEntry('transcricao', sec.label, ['Transcrições', 'Biblioteca', sec.categoryLabel || ''], `#/transcricoes/${sec.id}`, null);
  }
  log.ok(`Transcrições: ${(transIdx.categories || []).length} categorias · ${itens.length} itens`);
}

async function main() {
  log.group('Metta Brand System — Nav Index');

  const [nav, manifest, icons, photos, transcricoes] = await Promise.all([
    readJson(join(DATA_DIR, 'nav.json')),
    readJson(join(DATA_DIR, 'download-manifest.json')).catch(() => null),
    readJson(join(DATA_DIR, 'icons-index.json')).catch(() => null),
    readJson(join(DATA_DIR, 'photo-index.json')).catch(() => null),
    readJson(join(DATA_DIR, 'transcricoes-index.json')).catch(() => null)
  ]);

  await indexarPaginasEAssuntos(nav);
  if (manifest) await indexarMateriais(manifest); else log.warn('download-manifest.json ausente — rode build:manifest antes.');
  if (icons) await indexarIcones(icons); else log.warn('icons-index.json ausente.');
  if (photos) await indexarFotos(photos); else log.warn('photo-index.json ausente.');
  await indexarLogos();
  if (transcricoes) await indexarTranscricoes(transcricoes, nav); else log.warn('transcricoes-index.json ausente.');

  const payload = { generatedAt: new Date().toISOString(), entries };
  const json = JSON.stringify(payload);
  await writeFile(OUT_PATH, json, 'utf8');

  const porTipo = {};
  for (const e of entries) porTipo[e.tipo] = (porTipo[e.tipo] || 0) + 1;

  console.log('');
  log.group('Resumo');
  log.info(`total: ${entries.length} entradas`);
  for (const [tipo, n] of Object.entries(porTipo)) log.info(`  ${tipo}: ${n}`);
  const kb = (Buffer.byteLength(json, 'utf8') / 1024).toFixed(1);
  log.ok(`data/nav-index.json → ${kb} KB`);
  if (Number(kb) > 400) log.warn(`Acima do orçamento de ~400 KB — considere agrupar mais (ex: ícones por categoria só).`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
