// Vercel serverless function — lista os criativos pra galeria.
//
// GET /api/creatives            -> galeria VISÍVEL:
//     índice curado (data/generated-index.json) + salvos clicados (KV 'creatives:index').
// GET /api/creatives?scope=archive -> galeria INVISÍVEL (auto-arquivo):
//     TODA peça gerada (KV 'creatives:archive'), com pipeline + avaliação do QA.
//     Não é linkada em lugar nenhum da UI — acesso só por quem souber a URL.
//
// KV (dinâmico, mais novo) vem primeiro; depois o curado. Dedup por id.
// Degradação segura: sem KV configurado, o escopo visível devolve só o curado
// (a galeria segue funcionando como antes); o archive volta vazio.
import { readFileSync } from 'fs';
import { join } from 'path';
import { kv } from '@vercel/kv';

const KEY_PUBLIC = 'creatives:index';
const KEY_ARCHIVE = 'creatives:archive';

function readCurated() {
  try {
    const raw = readFileSync(join(process.cwd(), 'data', 'generated-index.json'), 'utf-8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.items) ? parsed.items : [];
  } catch {
    return [];
  }
}

async function readKv(key) {
  if (!process.env.KV_REST_API_URL) return [];
  try {
    const rows = await kv.lrange(key, 0, -1);
    return (rows || []).map(r => {
      try { return typeof r === 'string' ? JSON.parse(r) : r; } catch { return null; }
    }).filter(Boolean);
  } catch {
    return [];
  }
}

function dedupSort(lists) {
  const seen = new Set();
  const items = [];
  for (const it of [].concat(...lists)) {
    if (!it || !it.id || seen.has(it.id)) continue;
    seen.add(it.id);
    items.push(it);
  }
  items.sort((a, b) => String(b.savedAt || b.date || '').localeCompare(String(a.savedAt || a.date || '')));
  return items;
}

export default async function handler(req, res) {
  if (req.method !== 'GET') { res.status(405).json({ ok: false, error: 'GET only' }); return; }

  const url = new URL(req.url, 'http://x');
  const scope = url.searchParams.get('scope') === 'archive' ? 'archive' : 'public';
  res.setHeader('Cache-Control', 'no-store');

  if (scope === 'archive') {
    const archive = await readKv(KEY_ARCHIVE);
    res.status(200).json({ ok: true, scope, items: dedupSort([archive]), count: archive.length });
    return;
  }

  const curated = readCurated();
  const dynamic = await readKv(KEY_PUBLIC);
  const items = dedupSort([dynamic, curated]);
  res.status(200).json({ ok: true, scope, items, dynamic: dynamic.length, curated: curated.length });
}
