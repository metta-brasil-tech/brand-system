"""Vercel serverless function — busca de imagens via Google Custom Search API.

GET /api/image-search?q=<termo>
Resposta: { results: [{ url, thumbnail, title, width, height }] }

Lê GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX_ID de env vars (setup em
arquitetura/engine-no-brand-system.md). Free tier: 100 buscas/dia.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
MAX_RESULTS = 10  # Google CSE retorna no máximo 10 por request


def _search(query: str) -> dict:
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cx_id = os.getenv("GOOGLE_CSE_CX_ID")

    if not api_key or not cx_id:
        return {
            "error": "Busca de imagens não configurada. Faltam GOOGLE_CSE_API_KEY e/ou GOOGLE_CSE_CX_ID nas env vars do Vercel."
        }

    params = {
        "key": api_key,
        "cx": cx_id,
        "q": query,
        "searchType": "image",
        "num": MAX_RESULTS,
        "safe": "active",
    }
    url = f"{GOOGLE_CSE_ENDPOINT}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "metta-brand-system/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        if e.code == 403 and "Custom Search" in body:
            # Chave existe mas o projeto Google Cloud dela não tem a API habilitada.
            return {"error": (
                "A chave do Google ainda não tem a Custom Search API ativada. "
                "Ativar em console.cloud.google.com → APIs e serviços → Biblioteca → "
                "'Custom Search API' → Ativar (no MESMO projeto da GOOGLE_CSE_API_KEY). "
                "Leva 1 minuto e não precisa de redeploy.")}
        if e.code == 429:
            return {"error": "Cota diária da busca esgotou (100/dia no plano grátis). Use 'Gerar com IA' ou 'Enviar foto' por hoje."}
        return {"error": f"Google CSE HTTP {e.code}: {body[:300]}"}
    except Exception as e:
        return {"error": f"{e.__class__.__name__}: {e}"}

    items = data.get("items", [])
    results = []
    for it in items:
        image_info = it.get("image", {}) or {}
        results.append({
            "url": it.get("link", ""),
            "thumbnail": image_info.get("thumbnailLink", it.get("link", "")),
            "title": it.get("title", ""),
            "width": image_info.get("width"),
            "height": image_info.get("height"),
            "context_url": image_info.get("contextLink", ""),
        })
    return {"results": results, "total": len(results), "query": query}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            query = (qs.get("q") or [""])[0].strip()

            if not query:
                return self._json(400, {"detail": "Parâmetro q (query) é obrigatório."})

            result = _search(query)
            if "error" in result:
                return self._json(502, {"detail": result["error"], "query": query})
            return self._json(200, result)

        except Exception as e:
            return self._json(500, {"detail": f"Erro interno: {e.__class__.__name__}: {e}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=300")  # 5min cache
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
