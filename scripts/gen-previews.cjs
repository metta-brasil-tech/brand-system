#!/usr/bin/env node
/**
 * gen-previews.js — Gera WebP de preview para os 3 templates Metta faltantes.
 * Usa Playwright (Chromium) para renderizar o template HTML real.
 *
 * Uso: node scripts/gen-previews.js
 */

const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const FONT_PATH = path.join(ROOT, 'assets/fonts/SF-Pro-Variable-Official.ttf');
const OUT_DIR = path.join(ROOT, 'assets/style-previews/metta');

// Read CSS files
const sharedCss = fs.readFileSync(path.join(ROOT, 'source/ad-templates/_shared.css'), 'utf8');

function fixFontPath(css) {
  // Replace relative font url with file:// absolute path
  return css.replace(
    /url\('?\/assets\/fonts\/SF-Pro-Variable-Official\.ttf'?\)/g,
    `url('file://${FONT_PATH}')`
  );
}

const fixedSharedCss = fixFontPath(sharedCss);

// Template definitions
const templates = [
  {
    name: 'yellow-bloco',
    templateCssFile: 'source/ad-templates/metta/YELLOW-BLOCO.css',
    html: `
      <div class="ad-canvas ad-yellow-bloco" data-format="feed" data-model="YELLOW-BLOCO">
        <!-- Foto simulada com gradiente escuro (preview sem pessoa real) -->
        <div class="yb-photo" style="background: linear-gradient(160deg, #1a2a35 0%, #0c161b 40%, #2e3e47 100%);"></div>
        <div class="yb-block">
          <h1 class="yb-headline ad-text-expanded-heavy">O time que bate meta não é motivado.</h1>
          <p class="yb-subhead ad-text-regular">Método Metta aplicado em +1.000 operações no Brasil.</p>
        </div>
        <div class="yb-cta-wrap">
          <button class="ad-cta ad-cta--dark">Saiba mais</button>
        </div>
      </div>
    `,
    format: 'feed',
  },
  {
    name: 'yellow-frame',
    templateCssFile: 'source/ad-templates/metta/YELLOW-FRAME.css',
    html: `
      <div class="ad-canvas ad-yellow-frame" data-format="feed" data-model="YELLOW-FRAME">
        <div class="yf-frame">
          <div class="yf-content">
            <h1 class="yf-headline ad-text-expanded-heavy">Vender sem método é perder dinheiro todo dia.</h1>
            <p class="yf-subhead ad-text-regular">Método Metta — estrutura que escala.</p>
            <div class="yf-cta-wrap">
              <button class="ad-cta ad-cta--yellow">Conhecer</button>
            </div>
          </div>
        </div>
      </div>
    `,
    format: 'feed',
  },
  {
    name: 'tweet-card',
    templateCssFile: 'source/ad-templates/metta/METTA-TWEET-CARD.css',
    html: `
      <div class="ad-canvas ad-metta-tweet" data-format="feed" data-model="METTA-TWEET-CARD">
        <header class="mt-header">
          <div class="mt-avatar">M</div>
          <div class="mt-user">
            <div class="mt-name-row">
              <span class="mt-name ad-text-bold">Metta</span>
              <span class="mt-verified">✓</span>
            </div>
            <span class="mt-handle ad-text-regular">@metta.brasil</span>
          </div>
        </header>
        <div class="mt-text">
          <h1 class="mt-headline ad-text-bold">Gestor de vendas não nasce — é formado com método, não com motivação.</h1>
          <p class="mt-subhead ad-text-regular">Estrutura bate inspiração toda semana.</p>
        </div>
        <p class="mt-cta ad-text-regular">Descubra o Método Metta 👉</p>
      </div>
    `,
    format: 'feed',
  },
];

async function generatePreview(browser, tpl) {
  const templateCss = fs.readFileSync(path.join(ROOT, tpl.templateCssFile), 'utf8');

  const htmlContent = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
${fixedSharedCss}
${templateCss}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { margin: 0; padding: 0; background: transparent; }
</style>
</head>
<body>
${tpl.html}
</body>
</html>`;

  const page = await browser.newPage();
  await page.setViewportSize({ width: 1080, height: 1350 });
  await page.setContent(htmlContent, { waitUntil: 'networkidle' });

  // Wait for font to load
  await page.waitForTimeout(800);

  const element = await page.$('.ad-canvas');
  if (!element) throw new Error('No .ad-canvas found');

  const box = await element.boundingBox();

  // Screenshot the canvas element
  const screenshotBuffer = await element.screenshot({
    type: 'png',
    clip: { x: 0, y: 0, width: Math.round(box.width), height: Math.round(box.height) },
  });

  await page.close();

  // Scale down to 560px wide for preview
  return screenshotBuffer;
}

async function main() {
  console.log('Starting preview generation...');

  const browser = await chromium.launch({ headless: true });

  for (const tpl of templates) {
    const outPath = path.join(OUT_DIR, `${tpl.name}.png`);
    console.log(`\nGenerating: ${tpl.name}...`);

    try {
      const buf = await generatePreview(browser, tpl);
      fs.writeFileSync(outPath, buf);
      console.log(`  ✅ Saved ${outPath} (${Math.round(buf.length / 1024)}KB)`);
    } catch (err) {
      console.error(`  ❌ Failed: ${err.message}`);
    }
  }

  await browser.close();
  console.log('\nDone!');
}

main().catch(e => { console.error(e); process.exit(1); });
