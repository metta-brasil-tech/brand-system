// Passo 1 do login: manda a pessoa pro Google.
// O parâmetro `hd` só filtra o seletor de contas (conveniência); a regra de
// verdade é conferida no callback, no servidor.
import { STATE_COOKIE, serializeCookie, safeNext } from '../../lib/auth.js';

export function redirectUri(req) {
  if (process.env.OAUTH_REDIRECT_URI) return process.env.OAUTH_REDIRECT_URI;
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const proto = req.headers['x-forwarded-proto'] || 'https';
  return `${proto}://${host}/api/auth/callback`;
}

export default async function handler(req, res) {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId) {
    res.status(503).send('GOOGLE_CLIENT_ID não configurado na Vercel.');
    return;
  }

  const destino = safeNext(req.query?.next || '/');
  const nonce = crypto.randomUUID().replace(/-/g, '');
  const state = `${nonce}.${Buffer.from(destino, 'utf8').toString('base64url')}`;

  const auth = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  auth.searchParams.set('client_id', clientId);
  auth.searchParams.set('redirect_uri', redirectUri(req));
  auth.searchParams.set('response_type', 'code');
  auth.searchParams.set('scope', 'openid email profile');
  auth.searchParams.set('state', state);
  // `hd` só filtra o seletor de contas. Fica opt-in porque num Workspace
  // multi-domínio ele pode esconder justamente as contas certas.
  if (process.env.LOGIN_HD) auth.searchParams.set('hd', process.env.LOGIN_HD);
  auth.searchParams.set('prompt', 'select_account');

  // Cookie curto (10 min) só pra provar, no callback, que o state é nosso.
  res.setHeader('Set-Cookie', serializeCookie(STATE_COOKIE, nonce, { maxAge: 600 }));
  res.redirect(302, auth.toString());
}
