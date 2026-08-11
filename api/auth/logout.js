// Encerra a sessão local. Não desloga a conta Google do navegador, só o Brand System.
import { SESSION_COOKIE, clearCookie, clearUserCookie } from '../../lib/auth.js';

export default async function handler(req, res) {
  res.setHeader('Set-Cookie', [clearCookie(SESSION_COOKIE), clearUserCookie()]);
  res.redirect(302, '/login?saiu=1');
}
