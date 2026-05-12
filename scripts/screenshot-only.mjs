#!/usr/bin/env node
/* Screenshot-only — captura preview do ad sem adicionar ao índice */
import { readFile, writeFile } from 'node:fs/promises';
import { existsSync, unlinkSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const SOURCE = process.argv[2];
const OUT_PNG = process.argv[3];
if (!SOURCE || !OUT_PNG) { console.error('Uso: node screenshot-only.mjs <ad.html> <out.png>'); process.exit(1); }

const HTML_PATH = resolve(ROOT, '..', SOURCE);
const TMP_HTML = resolve(ROOT, '..', '_export-tmp.html');
const TMP_PNG = resolve(ROOT, '..', '_export-tmp.png');
const OUT = resolve(ROOT, '..', OUT_PNG);

const OVERRIDE = `<style>body{padding:0!important;background:transparent!important}.ad{transform:none!important;box-shadow:none!important}.meta{display:none!important}</style>`;

let html = await readFile(HTML_PATH, 'utf8');
html = html.replace('</head>', `${OVERRIDE}</head>`);
await writeFile(TMP_HTML, html, 'utf8');

const cmd = `"${CHROME}" --headless --disable-gpu --no-sandbox --hide-scrollbars --window-size=1080,1920 --screenshot="${TMP_PNG}" "file:///${TMP_HTML.replace(/\\/g, '/')}"`;
execSync(cmd, { stdio: 'inherit' });

const buf = await readFile(TMP_PNG);
await sharp(buf).resize({ width: 720 }).webp({ quality: 88 }).toFile(OUT.replace(/\.png$/, '.webp'));
console.log(`✓ ${OUT.replace(/\.png$/, '.webp')}`);

try { unlinkSync(TMP_HTML); unlinkSync(TMP_PNG); } catch {}
