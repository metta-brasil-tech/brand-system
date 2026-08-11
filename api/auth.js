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
  createSession, serializeCookie, serializeUserCookie,
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
  return req.query?.action || 'login';
}

function recusa(res, motivo) {
  res.setHeader('Set-Cookie', clearCookie(STATE_COOKIE));
  res.redirect(302, `/login?erro=${encodeURIComponent(motivo)}`);
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
    default:         return entrar(req, res);
  }
}
