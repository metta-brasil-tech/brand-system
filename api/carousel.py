"""Vercel serverless — gera um CARROSSEL PANORAMA coeso.

POST /api/carousel
Header: Authorization: Bearer <PIECES_API_TOKEN>
Body:
  {
    "marca": "metta",                 # metta (default) | tiago
    "format": "feed",                 # feed (default) | story | sqr
    "scene": "<cena EM INGLÊS que TRANSFORMA da esquerda p/ direita>",  # ex: caos→ordem
    "slides": [                        # 2 a 4 slides
      {"headline": "...", "subhead": "...", "cta": "...", "tag": "..."},
      ...
    ]
  }

Fluxo: UMA imagem ultra-wide (generate_panorama, Gemini) → fatiada em N → cada fatia
vira o fundo de um slide (D-foto-fullbleed-overlay) com a copy por cima + decoração de
série (ticks, seta, campo de anéis contínuo). Usa image_source="upload" + art_director
OFF → NÃO chama o art-director/Anthropic (roda só com crédito Gemini).

Princípio (validado): carrossel coeso = UMA linguagem só; a transformação visual É a
narrativa. Ver memória brand-system-carrossel-panorama-coeso.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Setup: torna o submodule engine/ e a própria api/ importáveis (igual generate.py)
ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("BRAND_KNOWLEDGE_PATH", str(ENGINE_DIR / "brand-knowledge"))
os.environ.setdefault("ARTIFACTS_DIR", "/tmp/artifacts")

_MODEL_PANORAMA = "D-foto-fullbleed-overlay"   # foto full-bleed + headline overlay
_FAMILY = {"metta": "A", "tiago": "TIAGO"}


def _check_auth(headers) -> bool:
    expected = os.environ.get("PIECES_API_TOKEN")
    if not expected:
        return False
    got = headers.get("Authorization", "")
    if not got.startswith("Bearer "):
        return False
    return got[len("Bearer "):].strip() == expected


def generate_panorama_carousel(payload: dict) -> dict:
    """Gera o carrossel-panorama. Retorna {status, ...}."""
    marca = str(payload.get("marca") or "metta").lower().strip()
    fmt = str(payload.get("format") or "feed").lower().strip()
    scene = str(payload.get("scene") or "").strip()
    slides = payload.get("slides")

    if not isinstance(slides, list) or not (2 <= len(slides) <= 4):
        return {"status": 400, "detail": "slides deve ser uma lista de 2 a 4 itens (limite do panorama)."}
    if not scene:
        return {"status": 400,
                "detail": "scene é obrigatório: descreva EM INGLÊS uma cena que TRANSFORMA "
                          "da esquerda p/ direita (ex: 'ultra-wide dark office that transforms "
                          "from chaos on the left to a clean lit doorway on the right')."}
    for i, sl in enumerate(slides, 1):
        if not str((sl or {}).get("headline", "")).strip():
            return {"status": 400, "detail": f"slide {i} sem headline."}

    n = len(slides)

    # 1) UMA imagem panorâmica (Gemini) → N fatias contínuas.
    try:
        from _nano_pipeline import generate_panorama
        raws, pmeta = generate_panorama(scene, n_slides=n, family=_FAMILY.get(marca, "A"))
    except Exception as exc:
        return {"status": 502, "detail": f"Falha ao gerar o panorama (Gemini): {exc.__class__.__name__}: {exc}"}
    if not raws or len(raws) < n:
        return {"status": 502, "detail": "Panorama não retornou fatias suficientes."}
    slice_uris = ["data:image/png;base64," + base64.b64encode(b).decode("ascii") for b in raws]

    # 2) Cada fatia vira um slide (foto full-bleed + copy + decor de série).
    import generate as gen
    out_slides = []
    for i, sl in enumerate(slides, 1):
        body = re.sub(r"(?m)^\s*[-•*]\s+", "", str((sl or {}).get("body", "")))
        try:
            res = gen._run_pipeline_inline(
                briefing_text="api-panorama", mock=False,
                forced_model_id=_MODEL_PANORAMA,
                image_source="upload", image_url=slice_uris[i - 1],
                user_headline=str(sl.get("headline", "")),
                user_subhead=str(sl.get("subhead", "")),
                user_body=body,
                user_cta_text=str(sl.get("cta", "")),
                user_tag=str(sl.get("tag", "")),
                wizard_format=fmt,
                render_png=True,
                art_director=False,   # imagem já pronta (fatia) → sem art-director/Anthropic
                vision_qa=False,
                serie_info={"i": i, "n": n, "last": i == n},
            )
            out_slides.append({
                "i": i, "ok": bool(res.get("ok")),
                "png_data_uri": res.get("png_data_uri"),
                "html": res.get("html"),
                "error": None if res.get("ok") else str(res.get("error"))[:200],
            })
        except Exception as exc:
            out_slides.append({"i": i, "ok": False, "png_data_uri": None, "html": None,
                               "error": f"{exc.__class__.__name__}: {exc}"[:200]})

    ok_count = sum(1 for s in out_slides if s["ok"])
    return {
        "status": 200 if ok_count == n else 207,
        "ok": ok_count == n,
        "panorama": True,
        "marca": marca, "format": fmt, "n": n,
        "generated": ok_count,
        "panorama_meta": {"size": pmeta.get("size"), "ref_id": pmeta.get("ref_id"),
                          "ms": pmeta.get("ms")},
        "slides": out_slides,
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _check_auth(self.headers):
                return self._json(401, {"detail": "Authorization Bearer token ausente ou inválido."})
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return self._json(400, {"detail": "Body não é JSON válido."})
            result = generate_panorama_carousel(data)
            status = result.pop("status")
            return self._json(status, result)
        except Exception as exc:
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        return self._json(200, {
            "ok": True, "endpoint": "/api/carousel", "mode": "panorama-coeso",
            "usage": "POST {marca, format, scene (EN, transformação left→right), slides:[{headline,...}] (2-4)}",
        })

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
