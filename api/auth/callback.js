// Passo 2 do login: o Google volta com um `code`, trocamos por tokens e decidimos
// se a pessoa entra. Aqui mora a regra de acesso.
import {
  SESSION_COOKIE, STATE_COOKIE,
  createSession, serializeCookie, clearCookie, readCookie, isAllowed, safeNext,
  serializeUserCookie,
} from '../../lib/auth.js';
import { redirectUri } from './login.js';

function recusa(res, motivo) {
  res.setHeader('Set-Cookie', clearCookie(STATE_COOKIE));
  res.redirect(302, `/login?erro=${encodeURIComponent(motivo)}`);
}

export default async function handler(req, res) {
  const { GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET } = process.env;
  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !SESSION_SECRET) {
    res.status(503).send('Auth não configurada (falta client id/secret ou SESSION_SECRET).');
    return;
  }

  if (req.query?.error) return recusa(res, req.query.error);

  const code = req.query?.code;
  const state = req.query?.state || '';
  const nonceCookie = readCookie(req.headers.cookie, STATE_COOKIE);
  const [nonce, destinoB64] = String(state).split('.');

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

  // 3) A regra: precisa ser conta do Workspace da Metta (claim `hd`) ou estar na allowlist.
  if (!isAllowed({ email: claims.email, hd: claims.hd }, process.env)) {
    console.warn('[auth] acesso negado para', claims.email, 'hd=', claims.hd);
    return recusa(res, 'dominio');
  }

  const sessao = await createSession(String(claims.email).toLowerCase(), SESSION_SECRET);
  const destino = safeNext(destinoB64 ? Buffer.from(destinoB64, 'base64url').toString('utf8') : '/');

  const email = String(claims.email).toLowerCase();
  res.setHeader('Set-Cookie', [
    serializeCookie(SESSION_COOKIE, sessao),
    serializeUserCookie(email),
    clearCookie(STATE_COOKIE),
  ]);
  res.redirect(302, destino);
}
