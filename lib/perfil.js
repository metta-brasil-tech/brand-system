// Perfil de quem está logado, guardado no Vercel KV.
//
// Vive em lib/ porque duas funções precisam do mesmo dado: api/auth.js (que lê
// e grava) e api/solicitacoes.js (que só lê, pra carimbar o autor do pedido).
// lib/ não conta no teto de 12 Serverless Functions do plano Hobby.
//
// O acesso ao KV é pela API REST do Upstash, não pelo SDK: o SDK entraria no
// bundle de toda função que importar isto, e aqui o que se faz é um GET e um
// SET simples.

const FOTO_MAX = 700 * 1024;   // data URI; o KV aceita 1 MB por valor

export function temKv() {
  return Boolean(process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN);
}

export function chavePerfil(email) {
  return `perfil:${String(email).toLowerCase()}`;
}

export async function kvLer(chave) {
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

export async function kvGravar(chave, valor) {
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

/** Tira caracteres de controle, junta espaços e corta no limite. */
export function limpaTexto(valor, max = 40) {
  return String(valor ?? '')
    .replace(/[\x00-\x1f\x7f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

/** Devolve a foto normalizada, '' pra "sem foto" ou null se veio coisa estranha. */
export function limpaFoto(valor) {
  const foto = String(valor ?? '').trim();
  if (!foto) return '';
  if (foto.startsWith('https://')) return foto.length <= 500 ? foto : null;
  if (/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(foto)) {
    return foto.length <= FOTO_MAX ? foto : null;
  }
  return null;
}

/** Primeiro palpite de nome quando ainda não há nada salvo: o próprio e-mail. */
export function perfilPadrao(email) {
  const local = String(email || '').split('@')[0] || '';
  const partes = local.split(/[._-]+/).filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1));
  return { nome: partes[0] || local, sobrenome: partes.slice(1).join(' '), foto: '' };
}

export async function lerPerfil(email) {
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

/** Nome completo pra exibição, com o e-mail como último recurso. */
export function nomeCompleto(perfil, email) {
  return [perfil?.nome, perfil?.sobrenome].filter(Boolean).join(' ').trim() || email;
}

export { FOTO_MAX };
