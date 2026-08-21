// Login Google do Brand System, as três etapas numa função só.
//
// Por que juntas: o plano Hobby da Vercel permite no máximo 12 Serverless
// Functions por deployment em projeto sem framework, e a api/ já tinha 10.
// Três arquivos separados estouravam o limite e o deploy falhava inteiro.
//
// As URLs públicas continuam /api/auth/login, /callback e /logout, mapeadas
// pelos rewrites do vercel.json, então o Google Cloud não precisa saber disso.
import {
  SESSION_COOKIE, STATE_COOKIE,
  createSession, verifySession, serializeCookie, serializeUserCookie,
  clearCookie, clearUserCookie, readCookie, isAllowed, safeNext,
} from '../lib/auth.js';

function redirectUri(req) {
  if (process.env.OAUTH_REDIRECT_URI) return process.env.OAUTH_REDIRECT_URI;
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const proto = req.headers['x-forwarded-proto'] || 'https';
  return `${proto}://${host}/api/auth/callback`;
}

/** O rewrite manda `action`, mas o caminho original é a fonte mais confiável. */
function acaoDe(req) {
  const caminho = String(req.url || '').split('?')[0];
  if (caminho.endsWith('/callback')) return 'callback';
  if (caminho.endsWith('/logout')) return 'logout';
  if (caminho.endsWith('/login')) return 'login';
  if (caminho.endsWith('/me')) return 'me';
  if (caminho.endsWith('/perfil')) return 'perfil';
  return req.query?.action || 'login';
}

function recusa(res, motivo) {
  res.setHeader('Set-Cookie', clearCookie(STATE_COOKIE));
  res.redirect(302, `/login?erro=${encodeURIComponent(motivo)}`);
}

// ---------------------------------------------------------------- perfil
// Nome, sobrenome e foto de quem entrou. Fica no Vercel KV (o mesmo storage
// que a galeria de criativos já usa), acessado pela API REST em vez do SDK
// pra não engordar o bundle desta função. Chave: perfil:<email>.
//
// O e-mail nunca sai daqui alterado: ele vem da sessão assinada, não do corpo
// do request. Editar perfil não pode virar troca de identidade.
const FOTO_MAX = 700 * 1024;   // data URI; o KV aceita 1 MB por valor

function temKv() {
  return Boolean(process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN);
}

function chavePerfil(email) {
  return `perfil:${String(email).toLowerCase()}`;
}

async function kvLer(chave) {
  if (!temKv()) return null;
  const resp = await fetch(`${process.env.KV_REST_API_URL}/get/${encodeURIComponent(chave)}`, {
    headers: { Authorization: `Bearer ${process.env.KV_REST_API_TOKEN}` },
    cache: 'no-store',
  });
  if (!resp.ok) return null;
  const { result } = await resp.json();
  if (!result) return null;
  try { return JSON.parse(result); } catch { return null; }
}

async function kvGravar(chave, valor) {
  if (!temKv()) return false;
  const resp = await fetch(`${process.env.KV_REST_API_URL}/set/${encodeURIComponent(chave)}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.KV_REST_API_TOKEN}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify(valor),
  });
  return resp.ok;
}

function limpaNome(valor, max = 40) {
  return String(valor ?? '')
    .replace(/[\x00-\x1f\x7f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

/** Devolve a foto normalizada, '' pra "sem foto" ou null se veio coisa estranha. */
function limpaFoto(valor) {
  const foto = String(valor ?? '').trim();
  if (!foto) return '';
  if (foto.startsWith('https://')) return foto.length <= 500 ? foto : null;
  if (/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(foto)) {
    return foto.length <= FOTO_MAX ? foto : null;
  }
  return null;
}

/** Primeiro palpite de nome quando ainda não há nada salvo: o próprio e-mail. */
function perfilPadrao(email) {
  const local = String(email || '').split('@')[0] || '';
  const partes = local.split(/[._-]+/).filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1));
  return { nome: partes[0] || local, sobrenome: partes.slice(1).join(' '), foto: '' };
}

async function lerPerfil(email) {
  let salvo = null;
  try {
    salvo = await kvLer(chavePerfil(email));
  } catch (e) {
    console.error('[perfil] falha lendo do KV', e);
  }
  const base = perfilPadrao(email);
  return {
    nome: salvo?.nome || base.nome,
    sobrenome: salvo?.sobrenome ?? base.sobrenome,
    foto: salvo?.foto ?? base.foto,
  };
}

async function sessaoDe(req) {
  const secret = process.env.SESSION_SECRET;
  if (!secret) return null;
  return verifySession(readCookie(req.headers.cookie, SESSION_COOKIE), secret);
}

// GET /api/auth/me -> quem está logado neste navegador (401 se ninguém).
async function quemSou(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const sessao = await sessaoDe(req);
  if (!sessao) { res.status(401).json({ ok: false, error: 'nao_autenticado' }); return; }
  const perfil = await lerPerfil(sessao.email);
  res.status(200).json({ ok: true, email: sessao.email, ...perfil, servidor: temKv() });
}

// POST /api/auth/perfil -> altera nome, sobrenome e foto. E-mail é imutável.
async function salvarPerfil(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') { res.status(405).json({ ok: false, error: 'metodo_invalido' }); return; }

  const sessao = await sessaoDe(req);
  if (!sessao) { res.status(401).json({ ok: false, error: 'nao_autenticado' }); return; }

  let corpo = req.body;
  if (typeof corpo === 'string') { try { corpo = JSON.parse(corpo); } catch { corpo = null; } }
  if (!corpo || typeof corpo !== 'object') { res.status(400).json({ ok: false, error: 'corpo_invalido' }); return; }

  const nome = limpaNome(corpo.nome);
  if (!nome) { res.status(400).json({ ok: false, error: 'nome_vazio' }); return; }
  const sobrenome = limpaNome(corpo.sobrenome);

  const atual = await lerPerfil(sessao.email);
  let foto = atual.foto;
  if (corpo.foto !== undefined) {
    foto = limpaFoto(corpo.foto);
    if (foto === null) { res.status(400).json({ ok: false, error: 'foto_invalida' }); return; }
  }

  const perfil = { nome, sobrenome, foto };

  if (!temKv()) {
    // Storage não configurado: a UI cai pro modo "só neste navegador".
    res.status(501).json({ ok: false, error: 'sem_armazenamento', email: sessao.email, ...perfil });
    return;
  }

  let gravou = false;
  try {
    gravou = await kvGravar(chavePerfil(sessao.email), { ...perfil, atualizado_em: new Date().toISOString() });
  } catch (e) {
    console.error('[perfil] falha gravando no KV', e);
  }
  if (!gravou) { res.status(502).json({ ok: false, error: 'gravacao_falhou' }); return; }

  res.status(200).json({ ok: true, email: sessao.email, ...perfil, servidor: true });
}

/** Primeiro login: aproveita nome e foto que o Google já devolveu. Best effort. */
async function semeiaPerfil(email, claims) {
  if (!temKv()) return;
  try {
    if (await kvLer(chavePerfil(email))) return;
    await kvGravar(chavePerfil(email), {
      nome: limpaNome(claims.given_name) || perfilPadrao(email).nome,
      sobrenome: limpaNome(claims.family_name),
      foto: limpaFoto(claims.picture) || '',
      atualizado_em: new Date().toISOString(),
    });
  } catch (e) {
    console.error('[perfil] nao consegui semear o perfil de', email, e);
  }
}

// ---------------------------------------------------------------- login
function entrar(req, res) {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId) { res.status(503).send('GOOGLE_CLIENT_ID não configurado na Vercel.'); return; }

  const destino = safeNext(req.query?.next || '/');
  const nonce = crypto.randomUUID().replace(/-/g, '');
  const state = `${nonce}.${Buffer.from(destino, 'utf8').toString('base64url')}`;

  const auth = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  auth.searchParams.set('client_id', clientId);
  auth.searchParams.set('redirect_uri', redirectUri(req));
  auth.searchParams.set('response_type', 'code');
  auth.searchParams.set('scope', 'openid email profile');
  auth.searchParams.set('state', state);
  auth.searchParams.set('prompt', 'select_account');
  // `hd` só filtra o seletor de contas. Fica opt-in porque num Workspace
  // multi-domínio ele pode esconder justamente as contas certas.
  if (process.env.LOGIN_HD) auth.searchParams.set('hd', process.env.LOGIN_HD);

  // Cookie curto (10 min) só pra provar, no callback, que o state é nosso.
  res.setHeader('Set-Cookie', serializeCookie(STATE_COOKIE, nonce, { maxAge: 600 }));
  res.redirect(302, auth.toString());
}

// ------------------------------------------------------------- callback
async function voltarDoGoogle(req, res) {
  const { GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET } = process.env;
  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !SESSION_SECRET) {
    res.status(503).send('Auth não configurada (falta client id/secret ou SESSION_SECRET).');
    return;
  }

  if (req.query?.error) return recusa(res, req.query.error);

  const code = req.query?.code;
  const nonceCookie = readCookie(req.headers.cookie, STATE_COOKIE);
  const [nonce, destinoB64] = String(req.query?.state || '').split('.');

  if (!code || !nonce || !nonceCookie || nonce !== nonceCookie) {
    return recusa(res, 'state_invalido');
  }

  // 1) Troca o code por tokens (servidor -> servidor, com o client secret).
  let tokens;
  try {
    const resp = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
        redirect_uri: redirectUri(req),
        grant_type: 'authorization_code',
      }),
    });
    tokens = await resp.json();
    if (!resp.ok || !tokens.id_token) {
      console.error('[auth] falha na troca do code', tokens);
      return recusa(res, 'token_falhou');
    }
  } catch (e) {
    console.error('[auth] erro de rede na troca do code', e);
    return recusa(res, 'token_falhou');
  }

  // 2) Lê o id_token. A assinatura não precisa ser reconferida porque ele veio
  //    direto do Google por HTTPS nesta requisição (recomendação do próprio Google
  //    pro fluxo de authorization code). O que precisa ser conferido são os claims.
  let claims;
  try {
    claims = JSON.parse(Buffer.from(tokens.id_token.split('.')[1], 'base64url').toString('utf8'));
  } catch {
    return recusa(res, 'token_ilegivel');
  }

  const agora = Math.floor(Date.now() / 1000);
  const emissorOk = claims.iss === 'https://accounts.google.com' || claims.iss === 'accounts.google.com';
  if (!emissorOk || claims.aud !== GOOGLE_CLIENT_ID || !claims.exp || claims.exp < agora) {
    return recusa(res, 'token_invalido');
  }
  if (claims.email_verified !== true && claims.email_verified !== 'true') {
    return recusa(res, 'email_nao_verificado');
  }

  // 3) A regra: conta do Workspace da Metta (claim `hd`) ou allowlist.
  if (!isAllowed({ email: claims.email, hd: claims.hd }, process.env)) {
    console.warn('[auth] acesso negado para', claims.email, 'hd=', claims.hd);
    return recusa(res, 'dominio');
  }

  const email = String(claims.email).toLowerCase();
  await semeiaPerfil(email, claims);
  const sessao = await createSession(email, SESSION_SECRET);
  const destino = safeNext(destinoB64 ? Buffer.from(destinoB64, 'base64url').toString('utf8') : '/');

  res.setHeader('Set-Cookie', [
    serializeCookie(SESSION_COOKIE, sessao),
    serializeUserCookie(email),
    clearCookie(STATE_COOKIE),
  ]);
  res.redirect(302, destino);
}

// --------------------------------------------------------------- logout
function sair(req, res) {
  res.setHeader('Set-Cookie', [clearCookie(SESSION_COOKIE), clearUserCookie()]);
  res.redirect(302, '/login?saiu=1');
}

export default async function handler(req, res) {
  switch (acaoDe(req)) {
    case 'callback': return voltarDoGoogle(req, res);
    case 'logout':   return sair(req, res);
    case 'me':       return quemSou(req, res);
    case 'perfil':   return salvarPerfil(req, res);
    default:         return entrar(req, res);
  }
}
