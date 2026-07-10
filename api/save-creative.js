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
// Body (post):     { type:"post", visibility, brand, model_id, format, headline, cta,
//                    image_data_uri:"data:image/png;base64,...", run_id?, pipeline?, evaluation? }
// Body (carrossel):{ type:"carousel", visibility, brand, model_id, format, headline, cta,
//                    slides:[{ image_data_uri, headline }], run_id?, pipeline?, evaluation? }
//   visibility: "public"  -> galeria VISÍVEL (a pessoa clicou "Salvar")
//               "archive" -> galeria INVISÍVEL (auto-arquivo de toda peça gerada)
//   pipeline:   diagnóstico/etapas do pipeline (array de strings)
//   evaluation: avaliação do QA { qa, vision_qa, critic, evaluation }
// Resposta 201: { ok:true, item:{...}, visibility }
import { put } from '@vercel/blob';
import { kv } from '@vercel/kv';

// Dois "baldes" no KV:
//   creatives:index   -> galeria VISÍVEL (só o que a pessoa clicou pra salvar)
//   creatives:archive -> galeria INVISÍVEL (TODA peça gerada, auto-arquivada,
//                        com criativo + pipeline + avaliação do QA)
const KEY_PUBLIC = 'creatives:index';
const KEY_ARCHIVE = 'creatives:archive';

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
  // 'public' = a pessoa clicou "Salvar na galeria"; 'archive' = auto-arquivo silencioso.
  const visibility = body.visibility === 'public' ? 'public' : 'archive';
  const targetKey = visibility === 'public' ? KEY_PUBLIC : KEY_ARCHIVE;

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
      run_id: String(body.run_id || ''),
      qa: String(body.qa || (visibility === 'public' ? 'Salvo pela ferramenta' : 'Auto-arquivado')),
      nota: String(body.nota || ''),
      engine: String(body.engine || 'ferramenta /criar'),
      visibility,
      source: visibility === 'public' ? 'clicado' : 'auto-arquivo',
      // registro completo pra análise: o pipeline (etapas/diagnóstico) e a
      // avaliação do QA (qa + vision_qa + crítico + nota final).
      pipeline: Array.isArray(body.pipeline) ? body.pipeline.slice(0, 200).map(String) : [],
      evaluation: (body.evaluation && typeof body.evaluation === 'object') ? body.evaluation : null,
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

    await kv.lpush(targetKey, JSON.stringify(record));
    res.status(201).json({ ok: true, item: record, visibility });
  } catch (e) {
    res.status(500).json({ ok: false, error: String((e && e.message) || e) });
  }
}
