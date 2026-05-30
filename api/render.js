// Render server-side de HTML -> PNG via Chromium real no Vercel.
// Substitui o html2canvas do browser do usuário (rasterização infiel/mole).
// Padrão Vercel pra headless Chrome: @sparticuz/chromium + puppeteer-core.
// Renderiza a 2x DPI e reduz pra 1080xH com sharp (supersampling = texto nítido).
import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import sharp from 'sharp';

const DIMS = { story: [1080, 1920], feed: [1080, 1350], sqr: [1080, 1080] };

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'POST only' });
    return;
  }
  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = {}; } }
  const html = body && body.html;
  const fmt = (body && body.format) || 'feed';
  if (!html) { res.status(400).json({ error: 'missing html' }); return; }
  const [w, h] = DIMS[fmt] || DIMS.feed;

  let browser;
  try {
    browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: { width: w, height: h, deviceScaleFactor: 2 },
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
    });
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0', timeout: 20000 });
    // espera o auto-fit do engine sinalizar pronto + fontes carregarem
    try {
      await page.waitForFunction(
        "document.documentElement.getAttribute('data-engine-ready') === '1'",
        { timeout: 8000 });
    } catch (_) {}
    try { await page.evaluate('document.fonts && document.fonts.ready'); } catch (_) {}

    const el = (await page.$('.ad-canvas')) || (await page.$('.ad'));
    const raw = el ? await el.screenshot({ type: 'png' })
                   : await page.screenshot({ type: 'png' });
    // 2x -> 1x com Lanczos (sharp) = export nítido no tamanho de spec
    const out = await sharp(raw).resize(w, h, { fit: 'fill' }).png().toBuffer();

    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Cache-Control', 'no-store');
    res.status(200).send(out);
  } catch (e) {
    res.status(500).json({ error: String((e && e.message) || e) });
  } finally {
    if (browser) { try { await browser.close(); } catch (_) {} }
  }
}
