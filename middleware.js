// Portão de entrada do Brand System.
// Roda antes de qualquer arquivo ser servido (inclusive HTML estático e /content),
// então nada vaza por URL direta. Quem não tem sessão válida vai pra /login.
//
// Liga/desliga por env var: só bloqueia com AUTH_ENABLED=1 na Vercel.
// Isso evita trancar o site antes de o OAuth estar configurado.
import { next } from '@vercel/functions';
import {
  SESSION_COOKIE, RENEW_WHEN_UNDER, SESSION_MAX_AGE,
  verifySession, createSession, serializeCookie, readCookie,
} from './lib/auth.js';

export const config = {
  // Tudo, menos as rotas de auth, a tela de login e os internos da Vercel.
  matcher: '/((?!api/auth|login|_vercel|favicon\.ico).*)',
};

export default async function middleware(request) {
  const env = process.env;
  if (env.AUTH_ENABLED !== '1') return next();

  const secret = env.SESSION_SECRET;
  if (!secret || !env.GOOGLE_CLIENT_ID || !env.GOOGLE_CLIENT_SECRET) {
    // Fail-closed: com auth ligada e config faltando, não serve o conteúdo.
    return new Response(
      'Brand System: autenticação ligada mas mal configurada (falta SESSION_SECRET ou credenciais do Google).',
      { status: 503, headers: { 'content-type': 'text/plain; charset=utf-8' } }
    );
  }

  const url = new URL(request.url);
  const token = readCookie(request.headers.get('cookie'), SESSION_COOKIE);
  const session = await verifySession(token, secret);

  if (session) {
    const restante = session.exp - Math.floor(Date.now() / 1000);
    if (restante < RENEW_WHEN_UNDER) {
      const novo = await createSession(session.email, secret);
      return next({ headers: { 'set-cookie': serializeCookie(SESSION_COOKIE, novo, { maxAge: SESSION_MAX_AGE }) } });
    }
    return next();
  }

  // Chamada de dados (fetch do app.js, /api/*) recebe 401 em vez de HTML de login.
  const querHtml = (request.headers.get('accept') || '').includes('text/html');
  if (!querHtml) {
    return Response.json({ ok: false, error: 'nao_autenticado' }, { status: 401 });
  }

  const destino = new URL('/login', url.origin);
  const voltarPara = url.pathname + url.search;
  if (voltarPara && voltarPara !== '/') destino.searchParams.set('next', voltarPara);
  return Response.redirect(destino, 302);
}
