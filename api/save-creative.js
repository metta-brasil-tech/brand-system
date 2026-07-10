// Vercel serverless function — salva um criativo (post único ou carrossel)
// gerado pela ferramenta, de forma PERSISTENTE:
//   - imagem(ns) -> Vercel Blob (URL pública permanente)
//   - registro   -> Vercel KV (lista 'creatives:index', mais novo primeiro)
//
// Só funciona com as env vars da Vercel setadas:
//   BLOB_READ_WRITE_TOKEN  (Storage -> Blob)
//   KV_REST_API_URL + KV_REST_API_TOKEN  (Storage -> KV)
// Sem elas, responde 501 com instrução clara (fail-safe, não quebra a UI).
//
// POST /api/save-creative
// Body (post):     { type:"post", brand, model_id, format, headline, cta,
//                    image_data_uri:"data:image/png;base64,..." , qa?, nota? }
// Body (carrossel):{ type:"carousel", brand, model_id, format, headline, cta,
//                    slides:[{ image_data_uri, headline }], qa?, nota? }
// Resposta 201: { ok:true, item:{...} }
import { put } from '@vercel/blob';
import { kv } from '@vercel/kv';

const KEY = 'creatives:index';

function slug(s, n = 48) {
  return String(s || 'peca')
    .normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, n) || 'peca';
}

function dataUriToBuffer(uri) {
  const m = /^data:(image\/\w+);base64,(.+)$/s.exec(uri || '');
  if (!m) return null;
  return { mime: m[1], buf: Buffer.from(m[2], 'base64') };
}

async function uploadImage(dataUri, pathname) {
  const dec = dataUriToBuffer(dataUri);
  if (!dec) throw new Error('image_data_uri inválida (esperado data:image/*;base64,...)');
  const { url } = await put(pathname, dec.buf, {
    access: 'public',
    contentType: dec.mime,
    addRandomSuffix: true,
  });
  return url;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ ok: false, error: 'POST only' }); return; }

  if (!process.env.BLOB_READ_WRITE_TOKEN || !process.env.KV_REST_API_URL) {
    res.status(501).json({
      ok: false,
      error: 'Armazenamento não configurado. Habilite Vercel Blob + KV no projeto e defina ' +
             'BLOB_READ_WRITE_TOKEN, KV_REST_API_URL e KV_REST_API_TOKEN nas Environment Variables.',
    });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = {}; } }
  body = body || {};

  const type = body.type === 'carousel' ? 'carousel' : 'post';
  const brand = body.brand === 'tiago' ? 'tiago' : 'metta';
  const headline = String(body.headline || '').slice(0, 300);
  const base = slug(headline || body.model_id || 'peca');
  const stamp = Date.now().toString(36);

  try {
    const record = {
      id: `${brand}-${type}-${base}-${stamp}`,
      type,
      brand,
      model_id: String(body.model_id || ''),
      format: String(body.format || 'feed'),
      headline,
      cta: String(body.cta || ''),
      date: new Date().toISOString().slice(0, 10),
      savedAt: new Date().toISOString(),
      qa: String(body.qa || 'Salvo automaticamente pela ferramenta'),
      nota: String(body.nota || ''),
      engine: String(body.engine || 'ferramenta /criar'),
      source: 'auto',
    };

    if (type === 'carousel') {
      const slides = Array.isArray(body.slides) ? body.slides : [];
      if (slides.length < 2) throw new Error('carrossel precisa de ao menos 2 slides');
      record.slides = [];
      for (let i = 0; i < slides.length; i++) {
        const url = await uploadImage(slides[i].image_data_uri, `creatives/${record.id}-${i + 1}.png`);
        record.slides.push({ src: url, headline: String(slides[i].headline || '') });
      }
      record.src = record.slides[0].src;
    } else {
      record.src = await uploadImage(body.image_data_uri, `creatives/${record.id}.png`);
    }

    await kv.lpush(KEY, JSON.stringify(record));
    res.status(201).json({ ok: true, item: record });
  } catch (e) {
    res.status(500).json({ ok: false, error: String((e && e.message) || e) });
  }
}
