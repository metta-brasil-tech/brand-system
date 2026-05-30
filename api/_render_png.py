"""Render server-side de HTML -> PNG via Chromium REAL (substitui html2canvas).

Por que existe: html2canvas reimplementa CSS parcialmente e roda no browser do
usuário (não-determinístico, texto mole em scale:1). Aqui usamos Chromium de
verdade no servidor, a 2x DPI, esperando o auto-fit (data-engine-ready) e as
fontes carregarem, e fazemos screenshot do elemento .ad. Downscale supersampled
2x->1x dá texto display nítido (o que separa "designer" de "gerado").

Usa Playwright se disponível; senão cai pro Chrome/Edge via subprocess.

    render_png(html, width=1080, height=1350, scale=2, downscale=True) -> bytes
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_READY_JS = "() => document.documentElement.getAttribute('data-engine-ready') === '1'"


def _downscale(png_bytes: bytes, w: int, h: int) -> bytes:
    """Reduz 2x->1x com Lanczos (supersampling) pra nitidez de export profissional."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        if im.size != (w, h):
            im = im.resize((w, h), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "PNG")
        return out.getvalue()
    except Exception:
        return png_bytes


# ---------------------------------------------------------------------------
# Backend Playwright (preferido — waits determinísticos)
# ---------------------------------------------------------------------------
def _render_playwright(html: str, width: int, height: int, scale: int) -> bytes:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--force-color-profile=srgb"])
        page = browser.new_page(viewport={"width": width, "height": height},
                                device_scale_factor=scale)
        page.set_content(html, wait_until="networkidle")
        try:
            page.wait_for_function(_READY_JS, timeout=8000)
        except Exception:
            pass
        try:
            page.evaluate("async () => { if (document.fonts) await document.fonts.ready; }")
        except Exception:
            pass
        el = page.query_selector(".ad-canvas") or page.query_selector(".ad")
        png = el.screenshot(type="png") if el else page.screenshot(type="png")
        browser.close()
        return png


# ---------------------------------------------------------------------------
# Backend Chrome subprocess (fallback)
# ---------------------------------------------------------------------------
def _find_chrome() -> str | None:
    for p in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.exists(p):
            return p
    return shutil.which("chrome") or shutil.which("chromium") or shutil.which("msedge")


def _render_chrome(html: str, width: int, height: int, scale: int) -> bytes:
    chrome = _find_chrome()
    if not chrome:
        raise RuntimeError("Nenhum Chromium encontrado pro render server-side.")
    with tempfile.TemporaryDirectory() as td:
        html_path = Path(td) / "ad.html"
        png_path = Path(td) / "ad.png"
        html_path.write_text(html, encoding="utf-8")
        url = "file:///" + str(html_path).replace("\\", "/")
        subprocess.run([
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--force-device-scale-factor={scale}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=7000", "--run-all-compositor-stages-before-draw",
            f"--screenshot={png_path}", url,
        ], check=False, timeout=60, capture_output=True)
        if not png_path.exists():
            raise RuntimeError("Chrome não gerou o PNG.")
        return png_path.read_bytes()


def render_png(html: str, width: int = 1080, height: int = 1350,
               scale: int = 2, downscale: bool = True, backend: str = "auto") -> bytes:
    """HTML -> PNG bytes. scale=2 + downscale=True => 1080xH supersampled (nítido)."""
    raw = None
    err = None
    if backend in ("auto", "playwright"):
        try:
            raw = _render_playwright(html, width, height, scale)
        except Exception as e:
            err = e
            if backend == "playwright":
                raise
    if raw is None:
        raw = _render_chrome(html, width, height, scale)
    return _downscale(raw, width, height) if downscale else raw


# Dimensões por formato
FORMAT_DIMS = {"story": (1080, 1920), "feed": (1080, 1350), "sqr": (1080, 1080)}


def render_format(html: str, fmt: str = "feed", **kw) -> bytes:
    w, h = FORMAT_DIMS.get(fmt, (1080, 1350))
    return render_png(html, width=w, height=h, **kw)
