// Solicitações do time: pedido de material, dúvida ou sugestão de melhoria.
// Cada envio vira um item no board "Solicitações Brand System" do Monday e
// notifica quem cuida da fila.
//
// Esta é uma função guarda-chuva, no mesmo desenho de api/auth.js: as URLs
// públicas são /api/solicitacoes/<acao>, mapeadas pelo rewrite do vercel.json,
// e um switch decide o que fazer. O motivo é o teto de 12 Serverless Functions
// do plano Hobby: com esta, chegamos a 12. Qualquer backend novo daqui pra
// frente entra como AÇÃO aqui dentro, não como arquivo novo em api/.
//
// Regra que não se negocia: o e-mail do autor vem SEMPRE da sessão assinada,
// nunca do corpo do request.
import { SESSION_COOKIE, verifySession, readCookie } from '../lib/auth.js';
import { lerPerfil, limpaTexto, nomeCompleto } from '../lib/perfil.js';

// Ids gerados por .scripts/monday-setup/setup-board-solicitacoes.mjs.
// São constantes e não variáveis de ambiente: não mudam, e no painel virariam
// mais um lugar pra esquecer de configurar.
const COLS = {
  categoria: 'color_mm6e8as1',
  solicitante: 'person',
  email: 'email_mm6ehypb',
  nome: 'text_mm6ewxt4',
  descricao: 'long_text_mm6ezy57',
  anexos: 'file_mm6ekga4',
  recebida: 'date4',
};
const GRUPO = 'topics';   // "Novas solicitações"

const CATEGORIAS = {
  material: 'Material novo',
  duvida: 'Dúvida',
  melhoria: 'Sugestão de melhoria',
};

const LIMITES = {
  titulo: 120,
  descricao: 5000,
  anexos: 3,
  bytesPorAnexo: 3 * 1024 * 1024,
  bytesTotal: Math.floor(3.5 * 1024 * 1024),   // folga sob os 4,5 MB de corpo da Vercel
};

const MIMES = new Set([
  'image/png', 'image/jpeg', 'image/webp', 'image/gif',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/plain', 'text/csv',
]);

const API = () => process.env.MONDAY_API_URL || 'https://api.monday.com/v2';
const API_ARQUIVO = 'https://api.monday.com/v2/file';
const BOARD = () => process.env.MONDAY_SOLICITACOES_BOARD || '18427667141';
const NOTIFICAR = () => (process.env.MONDAY_NOTIFICAR || '97060855,113582050')
  .split(',').map((s) => s.trim()).filter(Boolean);

function temMonday() { return Boolean(process.env.MONDAY_TOKEN); }

/** O rewrite manda `action`, mas o caminho original é a fonte mais confiável. */
function acaoDe(req) {
  const caminho = String(req.url || '').split('?')[0];
  if (caminho.endsWith('/criar')) return 'criar';
  if (caminho.endsWith('/config')) return 'config';
  return req.query?.action || 'config';
}

async function sessaoDe(req) {
  const secret = process.env.SESSION_SECRET;
  if (!secret) return null;
  return verifySession(readCookie(req.headers.cookie, SESSION_COOKIE), secret);
}

/**
 * Chamada GraphQL. O Monday responde 200 com os erros DENTRO do corpo, então
 * checar só o status HTTP não basta: quem faz isso acha que deu certo.
 */
async function gql(query, variables) {
  const resp = await fetch(API(), {
    method: 'POST',
    headers: {
      Authorization: process.env.MONDAY_TOKEN,
      'Content-Type': 'application/json',
      'API-Version': '2024-01',
    },
    body: JSON.stringify({ query, variables }),
  });
  const json = await resp.json().catch(() => ({}));
  if (json.errors) {
    const msg = json.errors.map((e) => e.message).join(' · ');
    throw new Error(msg.slice(0, 300));
  }
  if (!resp.ok) throw new Error(`monday http ${resp.status}`);
  return json.data;
}

function decodeDataUri(uri) {
  const m = /^data:([\w.+-]+\/[\w.+-]+);base64,(.+)$/s.exec(String(uri || ''));
  if (!m) return null;
  return { mime: m[1], buf: Buffer.from(m[2], 'base64') };
}

/**
 * Sobe um arquivo pra coluna de anexos do item.
 *
 * Usa endpoint próprio (/v2/file) e multipart no formato da spec "GraphQL
 * multipart request": campos `query`, `map` e o arquivo no campo que o map
 * aponta. Formato confirmado por teste contra a API real; a documentação
 * oficial não descreve os nomes dos campos.
 */
async function subirAnexo(itemId, nomeArquivo, mime, buf) {
  const form = new FormData();
  form.append('query', `mutation ($file: File!) { add_file_to_column (item_id: ${itemId}, column_id: "${COLS.anexos}", file: $file) { id } }`);
  form.append('map', JSON.stringify({ image: ['variables.file'] }));
  form.append('image', new Blob([buf], { type: mime }), nomeArquivo);
  // Sem Content-Type manual: o fetch monta o boundary.
  const resp = await fetch(API_ARQUIVO, {
    method: 'POST',
    headers: { Authorization: process.env.MONDAY_TOKEN },
    body: form,
  });
  const json = await resp.json().catch(() => ({}));
  if (json.errors) throw new Error(json.errors.map((e) => e.message).join(' · ').slice(0, 200));
  if (!json.data?.add_file_to_column?.id) throw new Error('upload sem id de retorno');
  return json.data.add_file_to_column.id;
}

/** Nome de arquivo seguro: sem caminho, sem caractere de controle. */
function nomeSeguro(nome, mime) {
  const limpo = String(nome || '').split(/[\\/]/).pop().replace(/[\x00-\x1f\x7f"]/g, '').trim();
  if (limpo) return limpo.slice(0, 100);
  const ext = (mime.split('/')[1] || 'bin').replace(/[^a-z0-9]/gi, '');
  return `anexo.${ext}`;
}

/** Descobre o id do usuário no Monday pelo e-mail, pra atribuir o card a ele. */
async function idNoMonday(email) {
  try {
    const d = await gql(`{ users(emails: ["${email.replace(/"/g, '')}"]) { id } }`);
    return d?.users?.[0]?.id || null;
  } catch (e) {
    console.warn('[solicitacoes] não consegui resolver o usuário', e.message);
    return null;
  }
}

// ------------------------------------------------------------------ config
// A interface pergunta antes de abrir o formulário: se a integração não está
// configurada, é melhor avisar do que deixar a pessoa escrever à toa.
function configuracao(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({
    ok: true,
    configurado: temMonday(),
    categorias: Object.entries(CATEGORIAS).map(([id, label]) => ({ id, label })),
    limites: {
      titulo: LIMITES.titulo,
      descricao: LIMITES.descricao,
      anexos: LIMITES.anexos,
      bytesTotal: LIMITES.bytesTotal,
      tipos: Array.from(MIMES),
    },
  });
}

// ------------------------------------------------------------------- criar
async function criar(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.status(405).json({ ok: false, error: 'metodo_invalido' }); return; }

  const sessao = await sessaoDe(req);
  if (!sessao) { res.status(401).json({ ok: false, error: 'nao_autenticado' }); return; }

  if (!temMonday()) {
    res.status(501).json({
      ok: false,
      error: 'sem_integracao',
      detalhe: 'Falta a variável MONDAY_TOKEN no projeto da Vercel.',
    });
    return;
  }

  let corpo = req.body;
  if (typeof corpo === 'string') { try { corpo = JSON.parse(corpo); } catch { corpo = null; } }
  if (!corpo || typeof corpo !== 'object') { res.status(400).json({ ok: false, error: 'corpo_invalido' }); return; }

  const categoria = String(corpo.categoria || '').trim();
  if (!CATEGORIAS[categoria]) { res.status(400).json({ ok: false, error: 'categoria_invalida', campo: 'categoria' }); return; }

  const titulo = limpaTexto(corpo.titulo, LIMITES.titulo);
  if (titulo.length < 3) { res.status(400).json({ ok: false, error: 'titulo_curto', campo: 'titulo' }); return; }

  const descricao = String(corpo.descricao ?? '')
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '')   // mantém quebra de linha
    .trim()
    .slice(0, LIMITES.descricao);
  if (descricao.length < 10) { res.status(400).json({ ok: false, error: 'descricao_curta', campo: 'descricao' }); return; }

  // --- anexos
  const brutos = Array.isArray(corpo.anexos) ? corpo.anexos : [];
  if (brutos.length > LIMITES.anexos) { res.status(400).json({ ok: false, error: 'anexos_demais', campo: 'anexos' }); return; }
  const anexos = [];
  let somaBytes = 0;
  for (const a of brutos) {
    const dec = decodeDataUri(a?.data_uri);
    if (!dec) { res.status(400).json({ ok: false, error: 'anexo_ilegivel', campo: 'anexos' }); return; }
    if (!MIMES.has(dec.mime)) { res.status(400).json({ ok: false, error: 'tipo_nao_aceito', campo: 'anexos', detalhe: dec.mime }); return; }
    if (dec.buf.length > LIMITES.bytesPorAnexo) { res.status(413).json({ ok: false, error: 'anexo_grande', campo: 'anexos' }); return; }
    somaBytes += dec.buf.length;
    if (somaBytes > LIMITES.bytesTotal) { res.status(413).json({ ok: false, error: 'anexos_grandes', campo: 'anexos' }); return; }
    anexos.push({ nome: nomeSeguro(a?.nome, dec.mime), mime: dec.mime, buf: dec.buf });
  }

  // --- autor, sempre da sessão
  const email = sessao.email;
  const perfil = await lerPerfil(email);
  const autor = nomeCompleto(perfil, email);
  const pessoaId = await idNoMonday(email);

  const hoje = new Date().toISOString().slice(0, 10);
  const colunas = {
    [COLS.categoria]: { label: CATEGORIAS[categoria] },
    [COLS.email]: { email, text: email },
    [COLS.nome]: autor,
    [COLS.descricao]: descricao,
    [COLS.recebida]: { date: hoje },
  };
  if (pessoaId) colunas[COLS.solicitante] = { personsAndTeams: [{ id: Number(pessoaId), kind: 'person' }] };

  // --- cria o item
  let itemId;
  try {
    const d = await gql(
      `mutation ($board: ID!, $grupo: String!, $nome: String!, $colunas: JSON!) {
         create_item(board_id: $board, group_id: $grupo, item_name: $nome, column_values: $colunas) { id }
       }`,
      { board: String(BOARD()), grupo: GRUPO, nome: titulo, colunas: JSON.stringify(colunas) }
    );
    itemId = d?.create_item?.id;
    if (!itemId) throw new Error('resposta sem id de item');
  } catch (e) {
    console.error('[solicitacoes] create_item falhou', e);
    res.status(502).json({ ok: false, error: 'monday_falhou', detalhe: e.message });
    return;
  }

  // Daqui pra frente o pedido JÁ existe. Nada que falhe abaixo pode fazer o
  // envio parecer perdido: vira aviso na resposta e comentário no próprio card.
  const avisos = [];

  for (const anexo of anexos) {
    try {
      await subirAnexo(itemId, anexo.nome, anexo.mime, anexo.buf);
    } catch (e) {
      console.error('[solicitacoes] anexo falhou', anexo.nome, e);
      avisos.push(`O anexo "${anexo.nome}" não subiu.`);
    }
  }

  const resumo = `Enviado por ${autor} (${email}) pelo Brand System.`;
  try {
    const texto = avisos.length ? `${resumo}\n\nAtenção: ${avisos.join(' ')}` : resumo;
    await gql(
      `mutation ($item: ID!, $texto: String!) { create_update(item_id: $item, body: $texto) { id } }`,
      { item: String(itemId), texto }
    );
  } catch (e) {
    console.warn('[solicitacoes] não consegui comentar no card', e.message);
  }

  for (const userId of NOTIFICAR()) {
    try {
      await gql(
        `mutation ($user: ID!, $item: ID!, $texto: String!) {
           create_notification(user_id: $user, target_id: $item, text: $texto, target_type: Project) { id }
         }`,
        { user: String(userId), item: String(itemId), texto: `Nova solicitação de ${autor}: ${titulo}` }
      );
    } catch (e) {
      console.warn('[solicitacoes] notificação falhou para', userId, e.message);
      avisos.push('A notificação da equipe não saiu, mas o pedido foi registrado.');
    }
  }

  res.status(201).json({
    ok: true,
    id: itemId,
    url: `https://mettabrasil.monday.com/boards/${BOARD()}/pulses/${itemId}`,
    avisos,
  });
}

export default async function handler(req, res) {
  try {
    switch (acaoDe(req)) {
      case 'criar':  return await criar(req, res);
      default:       return configuracao(req, res);
    }
  } catch (e) {
    console.error('[solicitacoes] erro inesperado', e);
    if (!res.headersSent) res.status(500).json({ ok: false, error: String(e?.message || e) });
  }
}
