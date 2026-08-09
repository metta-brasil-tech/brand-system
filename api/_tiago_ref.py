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


# --------------------------------------------------------------------------
# Regra: quando uma peça METTA usa o Tiago no lugar de pessoa genérica.
# Decisão (Nathan delegou os contextos): usar o Tiago quando a figura representa
# AUTORIDADE/EXPERT — o Tiago é a cara/especialista da Metta. Manter pessoa
# genérica quando a figura é o CLIENTE/ICP (o dono sufocado com quem o espectador
# se identifica) — não faz sentido o Tiago ser "o cliente sofrendo".
# --------------------------------------------------------------------------
_METTA_TIAGO_ALWAYS = {"I-retrato-editorial-pb"}            # retrato de autoridade P&B
_METTA_TIAGO_IF_AUTHORITY = {                               # autoridade quando intent pede
    "A-headline-foto-dark", "D-foto-fullbleed-overlay",
    "YELLOW-SPLIT", "YELLOW-BLOCO", "NEWS-CARD",
}
_METTA_TIAGO_NEVER = {"FOTO-PILL-CASUAL", "B-foto-top-headline-mixed"}  # cliente/ICP


def should_use_tiago_for_metta(model_id: str, intent: str | None = "") -> bool:
    """True se a peça METTA deve usar o Tiago real (contexto de autoridade)."""
    if model_id in _METTA_TIAGO_NEVER:
        return False
    if model_id in _METTA_TIAGO_ALWAYS:
        return True
    if model_id in _METTA_TIAGO_IF_AUTHORITY:
        return str(intent or "").strip().lower() in ("autoridade", "prova")
    return False


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
