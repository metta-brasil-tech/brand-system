#!/usr/bin/env node
/* ============================================================
   METTA BRAND SYSTEM — BUILD PIPELINE v2
   Lê .md do vault Obsidian → gera 3 artefatos por section:
     content/<tab>/<sec>.html       (RESUMO essencial)
     content/<tab>/<sec>.full.html  (CONTEÚDO COMPLETO)
     content/<tab>/<sec>.md         (cópia do .md original pra download)
============================================================ */

import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
import { existsSync, statSync } from 'node:fs';
import { dirname, resolve, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import matter from 'gray-matter';
import { marked } from 'marked';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const VAULT = resolve(ROOT, 'source');                 // fonte local (auto-contida pro repo Vercel)
const NAV_PATH = join(ROOT, 'data', 'nav.json');
const CONTENT_DIR = join(ROOT, 'content');

// ----------- LOG HELPERS -----------
const log = {
  info:  (m) => console.log(`  ${m}`),
  ok:    (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn:  (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  err:   (m) => console.error(`  \x1b[31m✗\x1b[0m ${m}`),
  group: (m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

// ----------- MARKDOWN PIPELINE -----------
marked.use({
  gfm: true,
  breaks: false,
  pedantic: false,
  renderer: {
    heading(text, level) {
      // Remove "§" (parágrafo) que aparece em headings tipo "§1 Quem é a Metta"
      const cleaned = String(text).replace(/§\s*/g, '');
      const id = slugify(stripTags(cleaned));
      return `<h${level} id="${id}">${cleaned}</h${level}>\n`;
    }
  }
});

function slugify(s) {
  return s.toString()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 80);
}

function stripTags(s) {
  return String(s).replace(/<[^>]*>/g, '');
}

function preprocessMd(md) {
  // Wikilinks
  md = md.replace(/\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]/g, (_, target, hash, alias) => {
    const label = (alias || target).trim();
    return `<span class="wikilink" data-target="${target.trim()}"${hash ? ` data-anchor="${hash.trim()}"` : ''}>${label}</span>`;
  });
  // Block IDs do Obsidian
  md = md.replace(/\s\^([a-z0-9-]+)\s*$/gim, (_, id) => ` <span id="${id}" class="block-anchor"></span>`);
  // Converte H1 "ETAPA N — NOME" (formato Narrativa) em H2 "Etapa N: Nome" pra TOC
  md = md.replace(/^# ETAPA (\d+)\s*[—–-]\s*(.+)$/gm, (_, n, name) => {
    const cleanName = name.trim()
      .toLowerCase()
      .replace(/\b([\wÀ-ÿ])([\wÀ-ÿ]*)/g, (_, head, tail) => head.toUpperCase() + tail)
      .replace(/\b(De|Do|Da|Dos|Das|E|A|O|Em|No|Na|Nos|Nas|Ou|Pra|Para|Pelo|Pela|Por|Sem|Sob|Sobre|Com)\b/g, (s) => s.toLowerCase());
    return `## Etapa ${n}: ${cleanName}`;
  });
  return md;
}

/**
 * Processa blocos de tabs no markdown e devolve HTML do componente.
 * Sintaxe:
 *   :::tabs Label1|Label2
 *   :::tab Label1
 *   conteúdo markdown da tab 1
 *   :::
 *   :::tab Label2
 *   conteúdo markdown da tab 2
 *   :::
 *   :::
 */
function processTabs(md) {
  // Marcadores explícitos: :::tabs LABELS ... :::endtabs com :::tab NAME ... :::endtab
  const tabsRe = /^:::tabs\s+([^\n]+)\n([\s\S]*?)\n:::endtabs\s*$/gm;
  return md.replace(tabsRe, (full, labelsLine, body) => {
    const labels = labelsLine.split('|').map(s => s.trim());
    const tabRe = /^:::tab\s+([^\n]+)\n([\s\S]*?)\n:::endtab\s*$/gm;
    const tabs = {};
    let m;
    while ((m = tabRe.exec(body)) !== null) {
      const name = m[1].trim();
      tabs[name] = m[2].trim();
    }
    const groupId = 'tabs-' + Math.random().toString(36).slice(2, 8);
    const headers = labels.map((label, i) => {
      const slug = slugify(label);
      const active = i === 0 ? ' active' : '';
      return `<button class="tab-btn${active}" data-tab="${slug}" data-group="${groupId}">${escapeHtml(label)}</button>`;
    }).join('');
    const panels = labels.map((label, i) => {
      const slug = slugify(label);
      const hidden = i === 0 ? '' : ' hidden';
      const tabBody = tabs[label] || '';
      const html = postprocessHtml(marked.parse(tabBody));
      return `<div class="tab-panel" data-tab="${slug}" data-group="${groupId}"${hidden}>${html}</div>`;
    }).join('');
    return `<div class="tab-group" data-group="${groupId}"><div class="tab-headers">${headers}</div>${panels}</div>`;
  });
}

function postprocessHtml(html) {
  html = html.replace(/<table>/g, '<div class="table-wrap"><table>').replace(/<\/table>/g, '</table></div>');
  return dedupeSeparadores(html);
}

/**
 * No máximo UMA linha de separação entre blocos de conteúdo.
 * O markdown do vault usa `---` antes de cada capítulo, mas H1 e H2 já desenham a
 * própria linha (`border-top` em prose.css). O `<hr>` vira uma segunda linha logo
 * acima da primeira. Aqui ele sai do HTML — o `---` segue no .md, que é do vault.
 * `<hr>` antes de H3 fica: H3 não tem borda, então ali a linha é única.
 */
function dedupeSeparadores(html) {
  return html
    .replace(/(?:<hr\s*\/?>\s*)+(?=<h[12][\s>])/gi, '')   // hr colado em H1/H2
    .replace(/(?:<hr\s*\/?>\s*){2,}/gi, '<hr>\n');        // hr repetido em sequência
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ----------- BLOG CLEANER -----------
/**
 * Limpa tokens markdown pra renderização "blog interno":
 * - Remove sections cuja H2/H3 contém: Documentos Relacionados, Documentos que Referenciam,
 *   🔗, 🎯 Quando consultar, Mapa de Conexão
 * - Remove comentários AUTO-RELATED-START / AUTO-RELATED-END
 * - Remove blockquotes vazias e separadores órfãos no fim
 *
 * Tudo o resto (TL;DR, capítulos, tabelas, referências científicas) é mantido.
 */
function isJunkHeading(text) {
  const t = String(text || '').toLowerCase().replace(/§/g, '').trim();
  // Metadados pra IA (TL;DR, Quando consultar) — não vão pro blog interno
  if (/^⚡?\s*tl;?dr/i.test(t)) return true;
  if (/^🎯?\s*quando consultar/i.test(t)) return true;
  // Referências/wikilinks de fim de doc
  if (/documentos relacionados|documentos que referenciam|🔗|mapa de conex/.test(t)) return true;
  if (/^🔗 documentos/.test(t)) return true;
  if (/^relacionados$/.test(t)) return true;
  // Artefatos de e-book: a página web não é o PDF. Some a ficha catalográfica
  // (o H2 de breadcrumb leva junto autor, obra e a navegação entre volumes que
  // vivem embaixo dele), o sumário com número de página e a bio de fim de livro.
  // Tudo isso continua no .md e na Doc completa.
  if (/\|\s*gest[aã]o\s*#\s*\d/.test(t)) return true;
  if (/^\d*\.?\s*sum[aá]rio\b/.test(t)) return true;
  if (/sobre (o autor|a metta|a empresa)|informa[cç][oõ]es sobre o autor/.test(t)) return true;
  return false;
}

// "3. Capitulo 1: O que e Metodo" → "3. O que e Metodo".
// Numerar seção e capítulo ao mesmo tempo é herança do livro impresso.
function limpaTituloDeCapitulo(md) {
  return md.replace(/^(#{2,3}\s*(?:§?\d+[.)]\s*)?)cap[ií]tulo\s*\d+\s*[:\-–—]\s*/gim, '$1');
}

// Título da página vem do nav.json (`tituloPagina`) pra que os 12 documentos de
// metodologia abram do mesmo jeito, com acento e sem "E-book Completo" no meio.
function aplicaTituloCanonico(md, titulo) {
  if (!titulo) return md;
  return md.replace(/^#\s+.+$/m, `# ${titulo}`);
}

function cleanForBlog(tokens) {
  const cleaned = [];
  let skip = false;
  let skipDepth = null;

  for (const tok of tokens) {
    // Pula comentários HTML AUTO-RELATED
    if (tok.type === 'html' && /<!--\s*AUTO-RELATED-(START|END)\s*-->/.test(tok.text)) {
      continue;
    }
    // Pula blocos de código markdown que sejam só anchors órfãos
    if (tok.type === 'html' && /^\s*<a id="[^"]+"><\/a>\s*$/.test(tok.text)) {
      continue;
    }

    if (tok.type === 'heading') {
      const txt = stripTags(tok.text || '');
      const isJunk = isJunkHeading(txt);
      if (isJunk) {
        skip = true;
        skipDepth = tok.depth;
        continue;
      }
      if (skip && tok.depth <= skipDepth) {
        skip = false;
        skipDepth = null;
      }
    }

    if (!skip) cleaned.push(tok);
  }

  // Remove separadores (hr) e linhas vazias finais
  while (cleaned.length > 0) {
    const last = cleaned[cleaned.length - 1];
    if (last.type === 'hr' || last.type === 'space') {
      cleaned.pop();
    } else {
      break;
    }
  }

  return cleaned;
}

// ----------- TRANSCRIÇÕES: formatador heurístico -----------
// Transforma texto corrido em parágrafos + H2s navegáveis.
// Detecta marcadores de transição ("primeiro", "agora", etc.) pra criar seções.

const TRANSITION_PATTERNS = [
  /^(Primeiro|Segundo|Terceiro|Quarto|Quinto|Sexto|S[ée]timo|Oitavo|Nono|D[eé]cimo)[\s,.]/,
  /^(Agora|Ent[ãa]o|Por[ée]m|Ent[ãa]o agora|Mas agora|Olha|Veja|Ent[ãa]o veja)[\s,]/,
  /^(Outra coisa|Outro ponto|A pr[óo]xima|A primeira|A segunda|Existe(m)? )/,
  /^(Vou te (falar|mostrar|dar|ensinar|explicar|contar|provar))[\s,.]/,
  /^(Deixa eu te (falar|mostrar|explicar|dar|contar))/,
  /^(Eu (preciso|quero|vou|posso) (te |de ))/,
  /^(O (segredo|primeiro|segundo|terceiro|importante|principal|que|maior))/,
  /^(O ponto|A chave|A questão|A diferença) /,
  /^(Bom,|Beleza,|T[áa] bom,|Ent[ãa]o,)/,
  /^(Em primeiro lugar|Em segundo lugar|Por fim)[\s,]/,
  /^(Voc[êe] (precisa|tem que|deve|vai)) /
];

const MAX_SENTENCE_WORDS = 60;

// Quebra forçada só quando uma sentença é absurdamente longa
function chunkLongSentence(s) {
  const words = s.split(/\s+/);
  if (words.length <= MAX_SENTENCE_WORDS) return [s];
  // Tenta quebrar em marcadores fortes (não em conjunções comuns)
  const STRONG = /\s+(?=(?:Ent[ãa]o|Agora|Por isso|Por exemplo|Inclusive|Veja|Olha)\b)/g;
  const tryBreak = s.split(STRONG);
  if (tryBreak.length > 1) {
    return tryBreak.flatMap(p => p.split(/\s+/).length > MAX_SENTENCE_WORDS ? chunkLongSentence(p) : [p]);
  }
  // Fatia hard a cada N palavras
  const out = [];
  const N = 45;
  for (let i = 0; i < words.length; i += N) {
    out.push(words.slice(i, i + N).join(' '));
  }
  return out;
}

// Splita texto em sentenças. Robusto pra transcrições mal-pontuadas do YouTube.
function splitSentences(text) {
  const cleaned = text.replace(/\s+/g, ' ').trim();
  let result = null;

  // Estratégia 1: split natural por . ! ? + espaço + maiúscula/dígito
  const matches = cleaned.match(/[^.!?]+[.!?]+(?=\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ\d]|$)/g);
  if (matches && matches.length >= 4) result = matches.map(s => s.trim()).filter(Boolean);

  // Estratégia 2: split por mudança de minúscula → maiúscula
  if (!result) {
    const split1 = cleaned.split(/(?<=[a-záéíóúâêôãõç])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])/g)
      .map(s => s.trim()).filter(Boolean);
    if (split1.length >= 4) result = split1;
  }

  // Estratégia 3: marcadores de discurso falado
  if (!result) {
    const DISCOURSE = /\s+(?=(?:Ent[ãa]o|Agora|Bem|Olha|Veja|Pessoal|Bom|Beleza|Ó|Cara|Vamos|Eu vou|A gente|N[óo]s|Ah,|Mas |Por[ée]m|Por isso|Por exemplo|Inclusive|Tipo|Ent[ãa]o,)\b)/g;
    const split2 = cleaned.split(DISCOURSE).map(s => s.trim()).filter(Boolean);
    if (split2.length >= 4) result = split2;
  }

  // Estratégia 4: chunk forçado
  if (!result) {
    const words = cleaned.split(/\s+/);
    if (words.length > 30) {
      const chunks = [];
      for (let i = 0; i < words.length; i += 22) {
        chunks.push(words.slice(i, i + 22).join(' '));
      }
      result = chunks;
    } else {
      result = [cleaned];
    }
  }

  // Pós-processo: quebra sentenças muito longas
  return result.flatMap(chunkLongSentence).map(s => s.trim()).filter(Boolean);
}

function isTransition(sentence) {
  return TRANSITION_PATTERNS.some(re => re.test(sentence));
}

// Gera heading curto a partir da primeira frase do bloco
function generateHeading(sentence, fallbackIdx) {
  const STOPWORDS_END = /^(de|do|da|dos|das|e|um|uma|o|a|em|que|para|pra|por|com|sem|na|no|nas|nos|à|ao|aos|às|se|sua|seu|tem|ter|ele|ela|eles|elas|eu|voc[êe]|n[óo]s|isso|isto|aquilo|mas|ou|j[áa]|ainda|tamb[ée]m|muito|mais|menos)$/i;
  const cleaned = sentence
    .replace(/[.!?,;:]+$/g, '')
    .replace(/^[^\wÁ-ÿ]+/, '')
    .replace(/\s+/g, ' ')
    .trim();
  const words = cleaned.split(/\s+/);
  let take = Math.min(words.length, 8);
  // Não termina em stopword
  while (take > 3 && STOPWORDS_END.test(words[take - 1])) take--;
  if (take < 3) take = Math.min(words.length, 7);
  let heading = words.slice(0, take).join(' ');
  // Capitaliza primeira letra
  if (heading) heading = heading[0].toUpperCase() + heading.slice(1);
  return heading || `Parte ${fallbackIdx + 1}`;
}

// Agrupa sentenças em parágrafos de 3-4 frases
function groupParagraphs(sentences, perParagraph = 4) {
  const paragraphs = [];
  for (let i = 0; i < sentences.length; i += perParagraph) {
    paragraphs.push(sentences.slice(i, i + perParagraph).join(' '));
  }
  return paragraphs;
}

function formatTranscricaoBody(rawContent) {
  // Separa header (linhas com # Título / # URL: / urls / vazios) do body
  // O header é DESCARTADO — app.js já renderiza título e link YouTube no shell.
  const lines = rawContent.split('\n');
  let bodyStart = 0;
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i].trim();
    if (i < 5 && (l.startsWith('#') || l.startsWith('URL:') || /^https?:\/\//.test(l) || l === '')) {
      bodyStart = i + 1;
    } else {
      break;
    }
  }
  const body = lines.slice(bodyStart).join(' ').replace(/\s+/g, ' ').trim();

  if (!body) return rawContent;

  const sentences = splitSentences(body);
  const total = sentences.length;

  // Muito curto: 1-2 parágrafos, sem H2 nem TOC
  if (total < 8) {
    const paragraphs = groupParagraphs(sentences, Math.max(3, Math.ceil(total / 2)));
    return paragraphs.join('\n\n');
  }

  // Quebra uniforme: alvo de 3-8 seções, ~12-18 frases por seção
  const targetSections = Math.min(8, Math.max(3, Math.ceil(total / 14)));
  const perSection = Math.ceil(total / targetSections);
  const blocks = [];
  for (let i = 0; i < total; i += perSection) {
    blocks.push(sentences.slice(i, i + perSection));
  }
  // Mescla último bloco se muito pequeno
  if (blocks.length > 1 && blocks[blocks.length - 1].length < Math.ceil(perSection / 3)) {
    const last = blocks.pop();
    blocks[blocks.length - 1] = blocks[blocks.length - 1].concat(last);
  }

  // Gera markdown — primeira frase vira H2 sumarizado; resto, parágrafos
  const sectionsMd = blocks.map((sents, idx) => {
    const heading = generateHeading(sents[0], idx);
    const remaining = sents.slice(1);
    if (remaining.length === 0) {
      // bloco com 1 só frase: não cria heading
      return sents[0];
    }
    const paragraphs = groupParagraphs(remaining, 4);
    return `## ${heading}\n\n${paragraphs.join('\n\n')}`;
  });

  return sectionsMd.join('\n\n');
}

function isTranscricaoSource(src) {
  return typeof src === 'string' && src.startsWith('transcricoes/');
}

// ----------- TIMESTAMP DA ÚLTIMA ATUALIZAÇÃO -----------
// Tenta git log primeiro (commit author date); se falhar (arquivo novo, sem git), usa mtime.
function getUpdatedAt(absPath) {
  try {
    const out = execSync(`git log -1 --format=%cI -- "${absPath}"`, {
      cwd: ROOT,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore']
    }).trim();
    if (out) return out;
  } catch (_) { /* fallback */ }
  try {
    return statSync(absPath).mtime.toISOString();
  } catch (_) {
    return null;
  }
}

// ----------- SEARCH INDEX -----------
function htmlToPlainText(html) {
  return String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#\d+;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function makeSnippet(text, maxLen = 200) {
  const t = text.length > maxLen ? text.slice(0, maxLen).replace(/\s\S*$/, '') + '…' : text;
  return t;
}

function normalizeForSearch(s) {
  return String(s)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '');
}

// ----------- BUILD CORE -----------
async function buildSection(tab, sec) {
  const src = sec.source;
  if (!src) return { skipped: 'sem source (placeholder)' };
  if (src.startsWith('embed:')) return { skipped: 'embed' };
  if (src.startsWith('gallery:')) return { skipped: 'gallery' };
  if (src.startsWith('archetypes:')) return { skipped: 'archetypes' };
  if (src.startsWith('scan:')) return { skipped: 'scan' };
  if (src.startsWith('transcricoes-gallery:')) return { skipped: 'transcricoes-gallery' };
  if (src.startsWith('icons-gallery:')) return { skipped: 'icons-gallery' };
  if (src.startsWith('applications-gallery:')) return { skipped: 'applications-gallery' };
  if (src.startsWith('downloads-gallery:')) return { skipped: 'downloads-gallery' };

  const absPath = join(VAULT, src);
  if (!existsSync(absPath)) {
    return { error: `arquivo não encontrado: ${src}` };
  }

  const raw = await readFile(absPath, 'utf8');
  const parsed = matter(raw);

  // Transcrições passam por formatador (texto corrido → parágrafos + H2s)
  const isTrans = isTranscricaoSource(src);
  let sourceContent = isTrans ? formatTranscricaoBody(parsed.content) : parsed.content;
  sourceContent = aplicaTituloCanonico(limpaTituloDeCapitulo(sourceContent), sec.tituloPagina);
  const body = preprocessMd(sourceContent);

  // Versão FULL — tudo do .md original (pra "abrir doc completa")
  let fullHtml = marked.parse(body);
  fullHtml = postprocessHtml(fullHtml);

  // Versão BLOG — pode vir de blog_source (override curado) ou ser limpa do original
  let blogHtml;
  if (sec.blog_source) {
    const blogPath = join(VAULT, sec.blog_source);
    if (existsSync(blogPath)) {
      const blogRaw = await readFile(blogPath, 'utf8');
      const blogParsed = matter(blogRaw);
      let blogBody = preprocessMd(blogParsed.content);
      // Processa tabs ANTES do marked (gera HTML que substitui o marker)
      blogBody = processTabs(blogBody);
      blogHtml = marked.parse(blogBody);
      blogHtml = postprocessHtml(blogHtml);
    } else {
      console.warn(`  blog_source não encontrado: ${sec.blog_source} — usando cleanup automático`);
    }
  }
  if (!blogHtml) {
    const tokens = marked.lexer(body);
    const blogTokens = cleanForBlog(tokens);
    blogHtml = marked.parser(blogTokens);
    blogHtml = postprocessHtml(blogHtml);
  }

  // Extrai H2 do conteúdo BLOG pra TOC lateral
  const h2s = [];
  const h2Re = /<h([23]) id="([^"]+)">([^<]+)<\/h[23]>/g;
  let m;
  while ((m = h2Re.exec(blogHtml)) !== null) {
    h2s.push({ id: m[2], label: stripTags(m[3]), depth: parseInt(m[1], 10) });
  }

  const outDir = join(CONTENT_DIR, tab.id);
  await mkdir(outDir, { recursive: true });

  // Escreve blog (default)
  const blogPath = join(outDir, `${sec.id}.html`);
  await writeFile(blogPath, blogHtml, 'utf8');

  // Escreve completo (pra "abrir doc completa")
  const fullPath = join(outDir, `${sec.id}.full.html`);
  await writeFile(fullPath, fullHtml, 'utf8');

  // Copia .md original pra download
  const mdPath = join(outDir, `${sec.id}.md`);
  await copyFile(absPath, mdPath);

  // Timestamp da última atualização — prioridade pra blog_source (se existir), senão source
  const tsPath = sec.blog_source && existsSync(join(VAULT, sec.blog_source))
    ? join(VAULT, sec.blog_source)
    : absPath;
  const updatedAt = getUpdatedAt(tsPath);

  // Plain text pro índice de busca
  const plainBlog = htmlToPlainText(blogHtml);

  const totalBytes = blogHtml.length + fullHtml.length;
  return {
    ok: true,
    bytes: totalBytes,
    h2s,
    updatedAt,
    plainBlog,
    outPath: relative(ROOT, blogPath)
  };
}

async function copyDsEmbed() {
  const dsSrc = resolve(VAULT, 'embed', 'design-system-2.0.html');
  if (!existsSync(dsSrc)) {
    log.warn(`DS source não encontrado em ${dsSrc} — pulando embed`);
    return;
  }
  const dsRaw = await readFile(dsSrc, 'utf8');
  // Fonte Inter vive na raiz do brand-system; do output em embed/ o caminho relativo é ../Inter-* (já correto no source).
  const dsOut = join(ROOT, 'embed', 'design-system-2.0.html');
  await mkdir(dirname(dsOut), { recursive: true });
  await writeFile(dsOut, dsRaw, 'utf8');
  log.ok(`DS técnico copiado para embed/design-system-2.0.html (${dsRaw.length} bytes)`);
}

async function copyCriarEmbed() {
  const criarSrc = resolve(VAULT, 'embed', 'criar.html');
  if (!existsSync(criarSrc)) {
    log.warn(`Criar source não encontrado em ${criarSrc} — pulando embed`);
    return;
  }
  const criarRaw = await readFile(criarSrc, 'utf8');
  const criarOut = join(ROOT, 'embed', 'criar.html');
  await mkdir(dirname(criarOut), { recursive: true });
  await writeFile(criarOut, criarRaw, 'utf8');
  log.ok(`Criar UI copiado para embed/criar.html (${criarRaw.length} bytes)`);
}

async function main() {
  log.group('Metta Brand System — Build Pipeline v2');
  log.info(`Vault: ${VAULT}`);
  log.info(`Output: ${relative(process.cwd(), CONTENT_DIR)}`);

  log.group('Embed');
  await copyDsEmbed();
  await copyCriarEmbed();

  const navRaw = await readFile(NAV_PATH, 'utf8');
  const nav = JSON.parse(navRaw);

  let total = 0, ok = 0, errors = 0, skipped = 0;
  const errorList = [];
  const searchIndex = [];

  for (const tab of nav.tabs) {
    log.group(`[${tab.id}] ${tab.label}`);
    for (const sec of tab.sections) {
      total++;
      const result = await buildSection(tab, sec);
      if (result.ok) {
        ok++;
        log.ok(`${sec.id} → resumo + .full + .md (${result.bytes} bytes total)`);
        if (result.h2s.length > 0) {
          sec.h2s = result.h2s;
        }
        if (result.updatedAt) {
          sec.updatedAt = result.updatedAt;
        }
        // Indexa pra busca global.
        // Seção oculta não entra: se ela saiu do menu de propósito, não faz sentido
        // reaparecer numa busca. Exceção: transcrição, que é hidden só porque a lista
        // vive na galeria da aba, mas continua sendo conteúdo que se procura pelo nome.
        const foraDoMenu = sec.hidden && !sec.transcricao;
        if (!foraDoMenu) searchIndex.push({
          tab: tab.id,
          tabLabel: tab.label,
          sectionId: sec.id,
          label: sec.label,
          snippet: makeSnippet(result.plainBlog),
          textNorm: normalizeForSearch(`${tab.label} ${sec.label} ${result.plainBlog}`),
          h2s: (result.h2s || []).map(h => ({ id: h.id, label: h.label }))
        });
      } else if (result.skipped) {
        skipped++;
        log.info(`${sec.id} — pulado (${result.skipped})`);
      } else if (result.error) {
        errors++;
        errorList.push(`[${tab.id}/${sec.id}] ${result.error}`);
        log.err(`${sec.id} — ${result.error}`);
      }
    }
  }

  // Atualiza nav.json com h2s extraídos + timestamps + timestamp do build
  nav.generatedAt = new Date().toISOString();
  await writeFile(NAV_PATH, JSON.stringify(nav, null, 2), 'utf8');

  // Salva índice de busca
  const searchPath = join(ROOT, 'data', 'search-index.json');
  await writeFile(searchPath, JSON.stringify({ generatedAt: nav.generatedAt, entries: searchIndex }), 'utf8');
  log.ok(`Índice de busca: ${searchIndex.length} entradas → data/search-index.json`);

  console.log('');
  log.group('Resumo');
  log.info(`total: ${total}  ·  ok: ${ok}  ·  pulados: ${skipped}  ·  erros: ${errors}`);
  if (errors > 0) {
    log.warn(`Erros:`);
    errorList.forEach(e => log.warn(`  - ${e}`));
    process.exit(1);
  }
  console.log('');
  log.ok('Build concluído.');
}

main().catch(err => {
  console.error('\nFalha catastrófica:', err);
  process.exit(2);
});
