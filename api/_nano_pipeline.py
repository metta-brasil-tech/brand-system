"""Pipeline Nano Banana + referência do banco → motor de layout real.

Núcleo da Fase C (agente de imagem). Gera o FUNDO com o Nano Banana Pro SEMPRE
alimentando a peça real do banco como referência visual (o fundo herda a
linguagem Metta — colagem/editorial/grão/amarelo cirúrgico — em vez de sair
foto cinematográfica genérica), e monta o criativo final pelo motor de layout
real (`_blueprint_render` + `_render_png`).

REGRA DE OURO: nunca gerar só por texto. A referência é o que puxa pra
linguagem Metta (provado em 2026-07-10). A referência sai do
`engine/brand-knowledge/exemplars/metta/_curated-references.json`, filtrada
pela família do blueprint.

Uso:
    from _nano_pipeline import generate_creative
    png, meta = generate_creative("metta", "LIGHT-SURREAL", copy, scene, format="feed")

Latência ~20s (Nano Banana Pro) — cabe na Vercel Pro (maxDuration). Custo ~$0.03-0.05.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import httpx

_ROOT = Path(__file__).resolve().parent.parent
_CURATED = _ROOT / "data/curated-references.json"
_MODEL = os.getenv("NANO_MODEL", "gemini-3-pro-image-preview")
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# Tratamento Metta explícito — instrui a casar o tratamento fotográfico da
# referência (não a copiar texto/layout). É o que transfere a linguagem da marca.
_METTA_TREAT = (
    "CRITICAL — match the EXACT photographic visual language of the reference image: its "
    "editorial magazine art-direction, its colour grade, its film-grain/print texture, its mood, "
    "and its DISCIPLINED single surgical yellow (#FFBE18) accent. This is Metta's language: "
    "editorial-documentary or surreal-collage, NOT glossy cinematic Hollywood stock, NOT dramatic "
    "movie-still lighting. IGNORE any text, logos or graphic overlays present in the reference — "
    "use ONLY its photographic treatment. Invent a COMPLETELY NEW scene as described. "
    "No text, no words, no letters, no layout copied."
)

# blueprint model_id → família no banco de referências curado.
_FAMILY = {
    "A-headline-foto-dark": "A", "FOTO-PILL-CASUAL": "A", "I-retrato-editorial-pb": "A",
    "B-foto-top-headline-mixed": "B",
    "C-tipografia-pura-dark": "C",
    "D-foto-fullbleed-overlay": "D",
    "DARK-CARTA": "DARK", "DARK-COLAGEM": "DARK", "DARK-OBJETO": "DARK",
    "LIGHT-SURREAL": "LIGHT", "LIGHT-TIPO": "LIGHT",
    "NEWS-CARD": "NEWS",
    "YELLOW-BLOCO": "YELLOW", "YELLOW-DRAW": "YELLOW", "YELLOW-EDITORIAL": "YELLOW",
    "YELLOW-FRAME": "YELLOW", "YELLOW-OBJETO": "YELLOW", "YELLOW-SPLIT": "YELLOW",
    "H-fundo-branco-headline-gigante": "OUTROS", "K-bold-dourado-urgencia": "OUTROS",
}

# formato do canvas → proporção nativa que o Nano Banana entrega (sem letterbox).
_ASPECT = {"feed": "4:5", "story": "9:16", "sqr": "1:1"}

# Blueprints puramente tipográficos / sem foto — não geram fundo.
_NO_PHOTO = {"C-tipografia-pura-dark", "H-fundo-branco-headline-gigante",
             "METTA-TWEET-CARD", "LOGO-WALL", "LIGHT-TIPO"}


class NanoPipelineError(RuntimeError):
    pass


def _load_curated() -> dict:
    try:
        return json.loads(_CURATED.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover
        raise NanoPipelineError(f"não consegui ler _curated-references.json: {e}")


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"\w{3,}", (s or "").lower()))


def pick_reference(model_id: str, copy: dict) -> dict | None:
    """Referência visual do banco pra este blueprint: filtra pela FAMÍLIA e
    desempata por overlap de tokens com a copy. Retorna {family, id, path, motor}
    ou None se a família não tiver referência utilizável em disco.
    """
    fam = _FAMILY.get(model_id, "OUTROS")
    cur = _load_curated()
    refs = (cur.get("by_family", {}).get(fam, {}) or {}).get("refs", [])
    refs = [r for r in refs if (_ROOT / r.get("path", "")).is_file()]
    if not refs:
        return None
    q = _tokens(f"{copy.get('headline','')} {copy.get('subhead','')}")
    best = max(refs, key=lambda r: len(q & _tokens(
        f"{r.get('title','')} {r.get('mood','')} {r.get('archetype_foto','')}")))
    return {
        "family": fam,
        "id": best["id"],
        "path": str(_ROOT / best["path"]),
        "motor": (cur["by_family"][fam] or {}).get("motor", "nano-banana-2"),
    }


def _api_key(explicit: str | None) -> str:
    key = explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GK") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise NanoPipelineError("GEMINI_API_KEY ausente (defina no ambiente / .env.local / Vercel).")
    return key


def generate_background(model_id: str, copy: dict, scene: str,
                        format: str = "feed", api_key: str | None = None) -> tuple[bytes, dict]:
    """Gera o FUNDO via Nano Banana Pro com a referência do banco injetada.

    `scene` = descrição EM INGLÊS da cena/conceito (idealmente vinda do diretor de
    arte). Retorna (png_bytes, meta). Levanta NanoPipelineError em falha.
    """
    ref = pick_reference(model_id, copy)
    if not ref:
        raise NanoPipelineError(
            f"sem referência de banco pra '{model_id}' — NÃO gerar só por texto "
            f"(regra de ouro). Adicione refs da família no _curated-references.json.")
    key = _api_key(api_key)
    aspect = _ASPECT.get(format, "4:5")

    refp = Path(ref["path"])
    b64ref = base64.b64encode(refp.read_bytes()).decode("ascii")
    mime = "image/webp" if refp.suffix.lower() == ".webp" else "image/png"
    prompt = f"Invent a new image. Scene: {scene.strip()} {_METTA_TREAT}"

    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inlineData": {"mimeType": mime, "data": b64ref}},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": aspect}},
    }
    url = _GEMINI_URL.format(model=_MODEL, key=key)
    t0 = time.time()
    for attempt in (1, 2):
        r = httpx.post(url, json=payload, timeout=240)
        if r.status_code == 200:
            break
        if attempt == 1:  # alguns modelos recusam imageConfig — tenta sem
            payload["generationConfig"].pop("imageConfig", None)
            continue
        raise NanoPipelineError(f"Nano Banana {r.status_code}: {r.text[:200]}")
    for c in r.json().get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            inl = p.get("inlineData") or p.get("inline_data")
            if inl and inl.get("data"):
                png = base64.b64decode(inl["data"])
                meta = {"model": _MODEL, "ref_id": ref["id"], "family": ref["family"],
                        "aspect": aspect, "ms": int((time.time() - t0) * 1000),
                        "bytes": len(png)}
                return png, meta
    raise NanoPipelineError("Nano Banana não retornou imagem.")


def generate_creative(marca: str, model_id: str, copy: dict, scene: str,
                      format: str = "feed", api_key: str | None = None) -> tuple[bytes, dict]:
    """Criativo PRONTO: fundo (Nano Banana + referência) → motor de layout real.

    Retorna (png_final, meta). Requer Chromium (Playwright) pro render — o mesmo
    que o resto do pipeline já usa.
    """
    if model_id in _NO_PHOTO:
        raise NanoPipelineError(f"'{model_id}' é tipográfico/sem foto — não usa Nano Banana.")
    from _blueprint_render import render
    from _render_png import render_format

    bg, meta = generate_background(model_id, copy, scene, format=format, api_key=api_key)
    data_uri = "data:image/png;base64," + base64.b64encode(bg).decode("ascii")
    res = render(marca, model_id, copy, image_url=data_uri, format=format)
    if res.get("missing"):
        raise NanoPipelineError(f"blueprint '{model_id}' não encontrado pro motor de layout.")
    png = render_format(res["html"], fmt=format)
    meta["final_bytes"] = len(png)
    return png, meta


# ---------------------------------------------------------------------------
# Carrossel panorâmico: 1 imagem larga → fatiada em N slides que se completam.
# É 1 geração só (cabe na Vercel ~20s) + fatiamento local (PIL). Resolve o
# limite de timeout: metade da imagem no slide 1, metade no 2 (o que a Sofia pediu).
# ---------------------------------------------------------------------------
_PANO_ASPECT = {2: "3:2", 3: "21:9", 4: "21:9"}


def generate_panorama(scene: str, n_slides: int = 2, family: str = "A",
                      api_key: str | None = None) -> tuple[list[bytes], dict]:
    """Gera UMA imagem panorâmica (Nano Banana Pro, com referência da família pra
    herdar a linguagem Metta) e FATIA em n_slides verticais que se completam.

    Retorna (lista_de_png_por_slide, meta). O texto por cima fica a cargo do
    render/front — aqui são só os fundos contínuos. n_slides ∈ [2,4].
    """
    import io

    from PIL import Image

    n_slides = max(2, min(4, int(n_slides)))
    aspect = _PANO_ASPECT.get(n_slides, "3:2")
    key = _api_key(api_key)

    # referência de coerência: 1ª peça da família (charcoal/editorial) do banco.
    cur = _load_curated()
    refs = [r for r in (cur.get("by_family", {}).get(family, {}) or {}).get("refs", [])
            if (_ROOT / r.get("path", "")).is_file()]
    parts: list[dict] = [{"text": (
        f"Invent ONE single continuous ultra-wide image. Scene: {scene.strip()} {_METTA_TREAT}")}]
    ref_id = None
    if refs:
        refp = _ROOT / refs[0]["path"]
        ref_id = refs[0]["id"]
        parts.append({"inlineData": {
            "mimeType": "image/webp" if refp.suffix.lower() == ".webp" else "image/png",
            "data": base64.b64encode(refp.read_bytes()).decode("ascii")}})

    payload = {"contents": [{"parts": parts}],
               "generationConfig": {"responseModalities": ["IMAGE"],
                                    "imageConfig": {"aspectRatio": aspect}}}
    url = _GEMINI_URL.format(model=_MODEL, key=key)
    t0 = time.time()
    for attempt in (1, 2):
        r = httpx.post(url, json=payload, timeout=300)
        if r.status_code == 200:
            break
        if attempt == 1:
            payload["generationConfig"].pop("imageConfig", None)
            continue
        raise NanoPipelineError(f"Nano Banana panorama {r.status_code}: {r.text[:200]}")

    raw = None
    for c in r.json().get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            inl = p.get("inlineData") or p.get("inline_data")
            if inl and inl.get("data"):
                raw = base64.b64decode(inl["data"])
                break
        if raw:
            break
    if not raw:
        raise NanoPipelineError("Nano Banana não retornou panorama.")

    img = Image.open(io.BytesIO(raw))
    W, H = img.size
    step = W // n_slides
    slices: list[bytes] = []
    for i in range(n_slides):
        x0 = i * step
        x1 = W if i == n_slides - 1 else (i + 1) * step
        buf = io.BytesIO()
        img.crop((x0, 0, x1, H)).save(buf, format="PNG")
        slices.append(buf.getvalue())
    meta = {"model": _MODEL, "aspect": aspect, "n_slides": n_slides,
            "ref_id": ref_id, "size": [W, H], "ms": int((time.time() - t0) * 1000)}
    return slices, meta
