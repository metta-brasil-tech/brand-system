// Vercel serverless function — lista os criativos pra galeria.
// Junta duas fontes:
//   1) o índice curado, versionado no repo (data/generated-index.json)
//   2) os salvos automaticamente pela ferramenta, no Vercel KV ('creatives:index')
// KV (dinâmico, mais novo) vem primeiro; depois o curado. Dedup por id.
//
// Degradação segura: se o KV não estiver configurado, devolve só o índice curado
// (a galeria continua funcionando exatamente como antes).
//
// GET /api/creatives  ->  { ok:true, items:[...], dynamic:<n>, curated:<n> }
import { readFileSync } from 'fs';
import { join } from 'path';
import { kv } from '@vercel/kv';

const KEY = 'creatives:index';

function readCurated() {
  try {
    const raw = readFileSync(join(process.cwd(), 'data', 'generated-index.json'), 'utf-8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.items) ? parsed.items : [];
  } catch {
    return [];
  }
}

async function readDynamic() {
  if (!process.env.KV_REST_API_URL) return [];
  try {
    const rows = await kv.lrange(KEY, 0, -1);
    return (rows || []).map(r => {
      try { return typeof r === 'string' ? JSON.parse(r) : r; } catch { return null; }
    }).filter(Boolean);
  } catch {
    return [];
  }
}

export default async function handler(req, res) {
  if (req.method !== 'GET') { res.status(405).json({ ok: false, error: 'GET only' }); return; }

  const curated = readCurated();
  const dynamic = await readDynamic();

  const seen = new Set();
  const items = [];
  for (const it of [...dynamic, ...curated]) {
    if (!it || !it.id || seen.has(it.id)) continue;
    seen.add(it.id);
    items.push(it);
  }
  items.sort((a, b) =>
    String(b.savedAt || b.date || '').localeCompare(String(a.savedAt || a.date || '')));

  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ ok: true, items, dynamic: dynamic.length, curated: curated.length });
}
