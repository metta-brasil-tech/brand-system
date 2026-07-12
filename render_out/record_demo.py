#!/usr/bin/env python3
"""Grava um walkthrough do Brand System em vídeo (Playwright + Chromium headless).
Navega por hash routing direto (mais confiável que clicar em seletores da UI).
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5300"
OUT_DIR = Path(__file__).resolve().parent / "demo-video"
OUT_DIR.mkdir(exist_ok=True)

# (hash, tempo em segundos parado na tela, ação extra)
STEPS = [
    ("#/overview/intro", 4.0, None),
    ("#/visual/ds-cores", 3.5, None),
    ("#/criar/novo", 3.0, "scroll_criar"),
    ("#/criativos/galeria", 3.0, None),
    ("#/criativos/galeria", 3.0, "filtro_metta"),
    ("#/criativos/galeria", 2.5, "filtro_tiago"),
    ("#/aplicacoes/biblioteca", 3.5, "scroll_down"),
    ("#/overview/intro", 2.5, None),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=str(OUT_DIR),
        record_video_size={"width": 1440, "height": 900},
        device_scale_factor=2,
    )
    page = context.new_page()
    page.goto(f"{BASE}/index.html", wait_until="networkidle")
    time.sleep(1.5)

    for hash_, dwell, action in STEPS:
        page.evaluate(f"location.hash = '{hash_}'")
        time.sleep(1.2)  # tempo do router renderizar
        if action == "scroll_criar":
            try:
                frame = page.frame_locator("iframe.ds-frame")
                for _ in range(3):
                    frame.locator("body").hover()
                    page.mouse.wheel(0, 500)
                    time.sleep(0.5)
            except Exception:
                pass
        elif action == "filtro_metta":
            try:
                frame = page.frame_locator("iframe.ds-frame")
                frame.get_by_role("button", name="Metta", exact=True).click(timeout=3000)
            except Exception:
                pass
        elif action == "filtro_tiago":
            try:
                frame = page.frame_locator("iframe.ds-frame")
                frame.get_by_role("button", name="Tiago", exact=True).click(timeout=3000)
            except Exception:
                pass
        elif action == "scroll_down":
            for _ in range(4):
                page.mouse.wheel(0, 400)
                time.sleep(0.4)
        time.sleep(dwell)

    context.close()
    browser.close()

# Playwright salva com nome hash aleatório — renomeia pro nome final
webms = sorted(OUT_DIR.glob("*.webm"), key=lambda f: f.stat().st_mtime, reverse=True)
if webms:
    final = OUT_DIR / "brand-system-walkthrough.webm"
    webms[0].rename(final)
    print("VIDEO:", final)
else:
    print("Nenhum vídeo gerado")
