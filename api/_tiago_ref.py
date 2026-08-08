"""Tiago REAL via REFERÊNCIA de imagem (Gemini image-to-image).

Modelos de foto do Tiago (prefer_upload) devem usar o ROSTO REAL dele, não um
humano inventado. Este módulo passa uma foto real recortada do Tiago como
referência (`inlineData`) + uma cena, e o Gemini gera o Tiago naquela cena
preservando o rosto. Bypassa o art-director (que depende da Anthropic) — a cena
vem de um mapa por modelo aqui, então funciona mesmo com a Anthropic sem crédito.

Uso (no generate.py): gen_tiago_scene(model_id, format_key, headline) -> png|None.
Falha silenciosa (retorna None) → o caller cai no fallback antigo, sem quebrar.
"""
from __future__ import annotations
import base64
import time
from pathlib import Path

import httpx
import _nano_pipeline as np

_ROOT = Path(__file__).resolve().parent.parent
_TIAGO_DIR = _ROOT / "assets" / "tiago"

# Recorte real por modelo (fallback = tiago-31, braços cruzados, rosto nítido).
_CUTOUTS = {
    "TIAGO-STORY-COVER-HERO": "recortadas/tiago-31.png",
    "TIAGO-PHOTO-RAW": "recortadas/tiago-11.png",
    "TIAGO-EDITORIAL-DARK": "recortadas/tiago-17.png",
    "TIAGO-EDITORIAL-HERO": "recortadas/tiago-31.png",
    "TIAGO-DARK-SURREAL": "recortadas/tiago-gen-01.png",
    "TIAGO-TWITTER-CARD-IMAGE": "recortadas/tiago-16.png",
    "TIAGO-EDITORIAL-CARD": "recortadas/tiago-17.png",
    "TIAGO-EDITORIAL-CTA": "recortadas/tiago-31.png",
    "TIAGO-STORY-YELLOW-BLOCK": "recortadas/tiago-11.png",
}
_DEFAULT_CUTOUT = "recortadas/tiago-31.png"

# Cena por modelo (validadas na sessão de 2026-08-07). {hl} = headline do slide.
_SCENES = {
    "TIAGO-STORY-COVER-HERO": (
        "this same man standing confidently in a sleek modern glass office at golden hour, "
        "arms relaxed, warm side light, looking calmly at the camera, candid editorial"),
    "TIAGO-PHOTO-RAW": (
        "this same man in a candid lo-fi moment at his desk in a busy office, mid-gesture "
        "while talking, natural window light, looks like a real phone photo, unposed"),
    "TIAGO-EDITORIAL-DARK": (
        "this same man in dramatic dark editorial lighting, half of his face lit by a warm "
        "rim light against a near-black background, serious reflective expression, cinematic"),
    "TIAGO-EDITORIAL-HERO": (
        "this same man on a modern conference stage giving a keynote talk, confident open body "
        "language, dramatic warm spotlight, dark auditorium with softly blurred audience and "
        "stage screens glowing behind him, cinematic depth of field"),
    "TIAGO-DARK-SURREAL": (
        "this same man standing calm and centered, while behind and above him a chaotic storm "
        "of flying papers reorganizes into a clean orderly glowing geometric grid, dark surreal "
        "editorial, dramatic cinematic light, symbolic"),
    "TIAGO-TWITTER-CARD-IMAGE": (
        "this same man smiling warmly, relaxed casual portrait in a bright modern office, "
        "friendly approachable, natural light"),
}
_DEFAULT_SCENE = (
    "this same man, confident business mentor, in a modern office with warm cinematic "
    "lighting, editorial portrait, calm authoritative expression")


def _aspect(format_key: str) -> str:
    f = (format_key or "").lower()
    if "story" in f or "1920" in f:
        return "9:16"
    if "sqr" in f or "1080x1080" in f:
        return "1:1"
    return "4:5"


def gen_tiago_scene(model_id: str, format_key: str = "feed",
                    headline: str = "", tries: int = 4) -> bytes | None:
    """Gera o Tiago REAL numa cena nova (rosto preservado). None em falha."""
    cut = _TIAGO_DIR / _CUTOUTS.get(model_id, _DEFAULT_CUTOUT)
    if not cut.is_file():
        # tenta qualquer recorte disponível
        cand = sorted((_TIAGO_DIR / "recortadas").glob("*.png"))
        if not cand:
            return None
        cut = cand[0]
    try:
        b64 = base64.b64encode(cut.read_bytes()).decode()
        key = np._api_key(None)
    except Exception:
        return None
    scene = _SCENES.get(model_id, _DEFAULT_SCENE)
    aspect = _aspect(format_key)
    prompt = (
        "Use the man in the ATTACHED photo as the EXACT reference for the person: keep his FACE, "
        "glasses, greying short hair, stubble and likeness IDENTICAL and clearly recognizable — it "
        f"must obviously be the same man. Create a new cinematic image. Scene: {scene}. "
        "Composition: the man sits in the LOWER portion; the ENTIRE UPPER 40% is calm empty space. "
        "Photoreal, editorial, dramatic lighting, high quality. Keep his real face unchanged. "
        "ABSOLUTELY NO TEXT, letters, numbers, logos or watermarks in the image.")

    def _call(with_cfg: bool):
        pl = {"contents": [{"parts": [{"text": prompt},
              {"inlineData": {"mimeType": "image/png", "data": b64}}]}],
              "generationConfig": {"responseModalities": ["IMAGE"]}}
        if with_cfg:
            pl["generationConfig"]["imageConfig"] = {"aspectRatio": aspect}
        return httpx.post(np._GEMINI_URL.format(model=np._MODEL, key=key), json=pl, timeout=240)

    for a in range(1, tries + 1):
        try:
            r = _call(True)
            if r.status_code != 200:
                r = _call(False)
            if r.status_code == 200:
                for c in r.json().get("candidates", []):
                    for p in c.get("content", {}).get("parts", []):
                        inl = p.get("inlineData") or p.get("inline_data")
                        if inl and inl.get("data"):
                            return base64.b64decode(inl["data"])
                return None
            if r.status_code in (429, 500, 503) and a < tries:
                time.sleep(6 * a); continue
            return None
        except Exception:
            if a < tries:
                time.sleep(6 * a); continue
            return None
    return None
