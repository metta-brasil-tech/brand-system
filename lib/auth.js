// Sessão assinada (HMAC-SHA256) para o login Google do Brand System.
// Sem banco: o cookie carrega o e-mail + validade e a assinatura garante que
// ninguém forjou nada. Roda igual no Edge (middleware) e no Node 20 (functions),
// porque usa só WebCrypto global.

export const SESSION_COOKIE = 'mbs_sess';
export const STATE_COOKIE = 'mbs_state';
export const SESSION_MAX_AGE = 60 * 60 * 24 * 7;      // 7 dias
export const RENEW_WHEN_UNDER = 60 * 60 * 24 * 3;     // renova silenciosamente nos últimos 3 dias

const enc = new TextEncoder();

function b64urlEncode(bytes) {
  let bin = '';
  for (const b of new Uint8Array(bytes)) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(str) {
  const pad = str.length % 4 ? '='.repeat(4 - (str.length % 4)) : '';
  const bin = atob(str.replace(/-/g, '+').replace(/_/g, '/') + pad);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function sign(secret, data) {
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  return b64urlEncode(await crypto.subtle.sign('HMAC', key, enc.encode(data)));
}

// Comparação em tempo constante (evita timing attack na assinatura).
function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** Cria o token de sessão: <payload>.<assinatura> */
export async function createSession(email, secret, maxAgeSec = SESSION_MAX_AGE) {
  const payload = { e: email, x: Math.floor(Date.now() / 1000) + maxAgeSec };
  const body = b64urlEncode(enc.encode(JSON.stringify(payload)));
  return `${body}.${await sign(secret, body)}`;
}

/** Devolve { email, exp } se o token for válido e não expirado, senão null. */
export async function verifySession(token, secret) {
  if (!token || !secret) return null;
  const dot = token.lastIndexOf('.');
  if (dot < 1) return null;
  const body = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  if (!safeEqual(sig, await sign(secret, body))) return null;
  try {
    const payload = JSON.parse(new TextDecoder().decode(b64urlDecode(body)));
    if (!payload.e || !payload.x) return null;
    if (payload.x < Math.floor(Date.now() / 1000)) return null;
    return { email: payload.e, exp: payload.x };
  } catch {
    return null;
  }
}

export function serializeCookie(name, value, { maxAge = SESSION_MAX_AGE, path = '/' } = {}) {
  const parts = [
    `${name}=${value}`,
    `Path=${path}`,
    `Max-Age=${maxAge}`,
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
  ];
  return parts.join('; ');
}

export const USER_COOKIE = 'mbs_user';

/** Cookie legível pelo JS, só pra UI mostrar quem entrou. Não vale como credencial. */
export function serializeUserCookie(email, maxAge = SESSION_MAX_AGE) {
  return `${USER_COOKIE}=${encodeURIComponent(email)}; Path=/; Max-Age=${maxAge}; Secure; SameSite=Lax`;
}

export function clearUserCookie() {
  return `${USER_COOKIE}=; Path=/; Max-Age=0; Secure; SameSite=Lax`;
}

export function clearCookie(name) {
  return `${name}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`;
}

export function readCookie(cookieHeader, name) {
  if (!cookieHeader) return null;
  for (const part of cookieHeader.split(';')) {
    const eq = part.indexOf('=');
    if (eq < 0) continue;
    if (part.slice(0, eq).trim() === name) return part.slice(eq + 1).trim();
  }
  return null;
}

/**
 * Regra de acesso. Domínio vem do claim `hd` do token do Google (verificado no
 * servidor); a allowlist é a válvula pra convidado de fora sem virar deploy.
 */
export function isAllowed({ email, hd }, env) {
  const domains = (env.ALLOWED_DOMAINS || 'mettabrasil.com.br')
    .split(',').map((d) => d.trim().toLowerCase()).filter(Boolean);
  const extras = (env.ALLOWED_EMAILS || '')
    .split(',').map((e) => e.trim().toLowerCase()).filter(Boolean);

  const mail = String(email || '').toLowerCase();
  if (!mail) return false;
  if (extras.includes(mail)) return true;

  const emailDomain = mail.split('@')[1] || '';
  const hdDomain = String(hd || '').toLowerCase();

  // Sem `hd` = conta Google comum (gmail pessoal), nunca passa pela regra de domínio.
  if (!hdDomain) return false;

  // Workspace multi-domínio: a organização da Metta é metabatida.com.br, mas os
  // e-mails são @mettabrasil.com.br. Dependendo do caso o `hd` volta com o domínio
  // da organização, não com o do e-mail, então basta um dos dois estar liberado.
  // Isso não afrouxa nada: o app é Interno, só quem é da organização chega aqui.
  return domains.includes(emailDomain) || domains.includes(hdDomain);
}

/** Só aceita caminho interno, pra não virar open redirect. */
export function safeNext(value) {
  if (typeof value !== 'string') return '/';
  if (!value.startsWith('/') || value.startsWith('//')) return '/';
  return value;
}
