#!/usr/bin/env node
/* ============================================================
   Gera 8 abas (uma por categoria) + index das transcrições.
   - data/_transcricoes-tabs.json  → array de tabs pra mergear no nav
   - data/transcricoes-index.json  → metadata das 95 transcrições
============================================================ */

import { readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const VAULT = resolve(ROOT, '..', '..', '..');
const TRANS_DIR = join(VAULT, 'transcricoes');

// Categorias (ordem importa — primeira regex que casar vence)
// Ordem de checagem: específico → genérico
const CATEGORIES = [
  {
    id: 'depoimentos-anuncios',
    label: 'Depoimentos & Anúncios',
    icon: 'quote',
    desc: 'Cases de alunos, anúncios e masterclasses.',
    test: (t) => /depoimento|^\[?an[úu]ncio|\[an[úu]ncio|masterclass|perp/i.test(t)
  },
  {
    id: 'estrategia-mensal',
    label: 'Estratégia Mensal',
    icon: 'calendar',
    desc: 'Como bater meta em cada mês — janeiro a dezembro, datas-chave e semanas finais.',
    test: (t) => /(em|de|do m[êe]s de|no m[êe]s de)\s+(janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)|black friday|dia das m[ãa]es|[úu]ltima semana|faltam 2 dias|primeira semana do m[êe]s|meta de setembro/i.test(t)
  },
  {
    id: 'lideranca',
    label: 'Liderança & Gestão',
    icon: 'compass',
    desc: 'Líder, gerente, gestor — atitude, motivação, liberar tempo e persuasão.',
    test: (t) => /lideran[çc]a|l[íi]der|liberando tempo|gestor de vendas|ex-vendedores fracassam|altitude|motiva[çc][ãa]o como lider|reconhecido da sua empresa|seu gestor sabe|seu gerente sabe/i.test(t)
  },
  {
    id: 'pilares-metodo',
    label: 'Pilares & Método',
    icon: 'package',
    desc: 'Pilares da Meta Batida, CHA, 50 em 5h, diagnóstico e princípios.',
    test: (t) => /pilares|\bcha\b|50.{0,3}em.{0,3}5h|diagn[óo]stico|receita de sucesso|frequência ideal de treinamento|intelig[êe]ncia artificial|baixo fluxo|aumentar 30.?.? de vendas|venda mais com as 5 emo|definir metas de vendas|superar as metas do m[êe]s|supere meta|sua equipe bate meta|bater meta\.?$|seu neg[óo]cio est[áa] superando/i.test(t)
  },
  {
    id: 'equipe-engajamento',
    label: 'Equipe & Engajamento',
    icon: 'users',
    desc: 'Engajamento, motivar o time, recuperar desmotivados e dono no funcionário.',
    test: (t) => /engajamento|motivar.{0,5}(o\s+)?(seu\s+)?time|time desmotivado|aumente.{0,10}performance|performance do seu time|colaboradores|m[ée]qui|funcion[áa]rio.{0,5}dono|perguntas ao seu gerente|acreditar na meta|focado na meta|sem depender de voc[êe]/i.test(t)
  },
  {
    id: 'vendedores',
    label: 'Vendedores',
    icon: 'target',
    desc: 'Clonar o melhor vendedor, contratar, demitir, performance e preço.',
    test: (t) => /vendedor|clone|contratar bons|reter talentos|laranja podre|selecionar.{0,5}vendedores|tipos de vendedores|pre[çc]o|acelerar.{0,5}performance.{0,5}novos|domine o atendimento/i.test(t)
  },
  {
    id: 'lucro',
    label: 'Lucro & Resultado',
    icon: 'trending-up',
    desc: 'Lucro, escala e jogo do lucro — como o resultado se constrói.',
    test: (t) => /^lucro\b|\blucro$|lucro de verdade|lucro na veia|jogo do lucro|escala se constr[óo]i|rouba 21|quer mais lucro/i.test(t)
  },
  {
    id: 'empresario-cultura',
    label: 'Empresário & Cultura',
    icon: 'briefcase',
    desc: 'Mindset do dono, erros, cobrança, atendimento e perfis a seguir.',
    test: (t) => /empres[áa]rio|empres[áa]rio.{0,5}preso|erros na empresa|s[óo] pode cobrar|culpa.{0,5}dono|siga este perfil|seu problema nunca foram|coach/i.test(t)
  }
];

const OVERRIDES = {
  'iU8W2Lsmm7w - Bater meta.md': 'pilares-metodo',
  'WmftUO1KUf4 - clone.md': 'vendedores',
  'XCczg86SE7A - CLONE.md': 'vendedores',
  'xGVW57h669A - lucro.md': 'lucro',
  'u6hsUnIqeY4 - o jogo do lucro.md': 'lucro',
  'eLxQJEx_3r4 - masterclass.md': 'depoimentos-anuncios',
  'bYftJ6nqbpA - COACH-.md': 'empresario-cultura'
};

function slugify(s, max = 60) {
  return s.toString()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, max);
}

function cleanLabel(title) {
  let s = title.replace(/^#\s*/, '').trim();
  s = s.replace(/^#?\d{1,3}\s*[-—]\s*/, '');
  s = s.replace(/\s+-\s+#\d{1,3}\s*$/, '');
  s = s.replace(/^\[?\s*AN[ÚU]NCIO\s*[-—:]\s*([^\]]+?)\]?$/i, 'Anúncio · $1');
  s = s.replace(/^DEPOIMENTO\s*[-—]\s*/i, 'Depoimento · ');
  s = s.replace(/\bACAD[ÊE]MICA\s*[-—]\s*UNIDEP\b/i, '(UNIDEP)');
  s = s.replace(/-\s*$/, '?');
  return s.trim();
}

function extractEpisode(filename, title) {
  const m = (filename + ' ' + title).match(/#\s*(\d{1,3})\b/);
  return m ? parseInt(m[1], 10) : null;
}

function extractYouTubeId(filename, content) {
  // Filename pattern: "{ytId} - title.md" — youtube id é 11 chars alfanuméricos
  const fnMatch = filename.match(/^([A-Za-z0-9_-]{11})\s*-/);
  if (fnMatch) return fnMatch[1];
  // Fallback: procura url no conteúdo
  const urlMatch = content.match(/youtube\.com\/watch\?v=([A-Za-z0-9_-]{11})/);
  return urlMatch ? urlMatch[1] : null;
}

function wordCount(text) {
  return text.split(/\s+/).filter(Boolean).length;
}

async function main() {
  const files = (await readdir(TRANS_DIR)).filter(f => f.endsWith('.md')).sort();
  console.log(`📚 ${files.length} transcrições encontradas`);

  const grouped = Object.fromEntries(CATEGORIES.map(c => [c.id, []]));

  for (const file of files) {
    const full = join(TRANS_DIR, file);
    const raw = await readFile(full, 'utf8');
    const parsed = matter(raw);
    let title = parsed.data?.title;
    if (!title) {
      const firstLine = parsed.content.split('\n').find(l => l.trim()) || '';
      title = firstLine.replace(/^#\s*/, '').trim();
    }
    title = (title || file.replace(/\.md$/, ''))
      .replace(/^Transcri[çc][ãa]o\s*[—–-]\s*/i, '');

    let catId = OVERRIDES[file];
    if (!catId) {
      for (const cat of CATEGORIES) {
        if (cat.test(title, file)) { catId = cat.id; break; }
      }
    }
    if (!catId) catId = 'empresario-cultura';

    const episode = extractEpisode(file, title);
    const baseLabel = cleanLabel(title);
    const label = episode ? `#${String(episode).padStart(2, '0')} · ${baseLabel}` : baseLabel;
    const sourceSlug = slugify(baseLabel, 50) || slugify(file.replace(/\.md$/, ''), 50);
    const id = episode ? `ep-${String(episode).padStart(2, '0')}-${sourceSlug.slice(0, 30)}` : sourceSlug;

    const ytId = extractYouTubeId(file, raw);
    const ytUrl = ytId ? `https://youtube.com/watch?v=${ytId}` : null;
    const wc = wordCount(parsed.content);

    grouped[catId].push({
      id,
      label,
      shortLabel: baseLabel,
      episode,
      file,
      source: `transcricoes/${file}`,
      ytId,
      ytUrl,
      wordCount: wc,
      readingMin: Math.max(1, Math.round(wc / 180)) // ~180 wpm
    });
  }

  // Ordena dentro de cada categoria: episódios crescentes primeiro, depois alfabético
  for (const cat of CATEGORIES) {
    grouped[cat.id].sort((a, b) => {
      if (a.episode != null && b.episode != null) return a.episode - b.episode;
      if (a.episode != null) return -1;
      if (b.episode != null) return 1;
      return a.label.localeCompare(b.label, 'pt-BR');
    });
  }

  // Garante IDs únicos GLOBAIS (entre todas as categorias)
  const seenGlobal = new Map();
  for (const cat of CATEGORIES) {
    for (const sec of grouped[cat.id]) {
      const base = sec.id;
      const n = (seenGlobal.get(base) || 0) + 1;
      if (n > 1) sec.id = `${base}-${n}`;
      seenGlobal.set(base, n);
    }
  }

  // ABA ÚNICA "Transcrições" com section "biblioteca" + 95 sections ocultas
  const bibliotecaSection = {
    id: 'biblioteca',
    label: 'Biblioteca',
    source: 'transcricoes-gallery:all',
    description: '95 transcrições do Tiago classificadas por tema.'
  };
  const allHiddenSections = [];
  for (const cat of CATEGORIES) {
    for (const t of grouped[cat.id]) {
      allHiddenSections.push({
        id: t.id,
        label: t.shortLabel,
        source: t.source,
        hidden: true,
        transcricao: true,
        ytUrl: t.ytUrl,
        ytId: t.ytId,
        episode: t.episode,
        readingMin: t.readingMin,
        wordCount: t.wordCount,
        category: cat.id,
        categoryLabel: cat.label
      });
    }
  }
  const tabs = [{
    id: 'transcricoes',
    icon: 'mic',
    label: 'Transcrições',
    group: 'biblioteca',
    description: 'Banco completo de transcrições do Tiago — classificadas por tema.',
    sections: [bibliotecaSection, ...allHiddenSections]
  }];

  // Index global pra galeria + roteamento
  const index = {
    generatedAt: new Date().toISOString(),
    categories: CATEGORIES.map(c => ({
      id: c.id,
      label: c.label,
      icon: c.icon,
      description: c.desc,
      count: grouped[c.id].length
    })),
    transcriptions: {}
  };
  for (const cat of CATEGORIES) {
    index.transcriptions[cat.id] = grouped[cat.id].map(t => ({
      id: t.id,
      label: t.label,
      shortLabel: t.shortLabel,
      episode: t.episode,
      file: t.file,
      ytId: t.ytId,
      ytUrl: t.ytUrl,
      wordCount: t.wordCount,
      readingMin: t.readingMin
    }));
  }

  // Resumo
  console.log('\n📊 Distribuição por categoria:');
  for (const cat of CATEGORIES) {
    console.log(`  ${cat.label}: ${grouped[cat.id].length}`);
  }
  const total = Object.values(grouped).reduce((s, a) => s + a.length, 0);
  console.log(`\n  TOTAL: ${total} transcrições em ${CATEGORIES.length} categorias (1 aba "Transcrições")`);

  await writeFile(join(ROOT, 'data', '_transcricoes-tab.json'), JSON.stringify(tabs, null, 2), 'utf8');
  await writeFile(join(ROOT, 'data', 'transcricoes-index.json'), JSON.stringify(index, null, 2), 'utf8');
  console.log(`\n✅ data/_transcricoes-tab.json e data/transcricoes-index.json gerados`);
}

main().catch(e => { console.error(e); process.exit(1); });
