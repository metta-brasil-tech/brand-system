"""Vercel serverless function — recebe peças de copy prontas de um agente externo
(agente-copy, github.com/metta-brasil-tech/agente-copy) e as expõe pra exibição
no brand-system.

POST /api/pieces
Header: Authorization: Bearer <PIECES_API_TOKEN>
Body: {
  "brand": "metta" | "tiago",           # opcional, default "metta"
  "copy_type": "carrossel" | "post_unico" | "descricao_post" | "stories"
               | "reels" | "criativos" | <outro>,   # opcional, informativo
  "hook": "string",
  "corpo": "string",
  "cta": "string",
  "full_text": "string",
  "hook_variations": ["string", "string", "string"],
  "pilar_conteudo": "string",
  "icp_alvo": "string",
  "platform": "instagram" | "linkedin",
  "linkedin_adaptation": "string ou null"
}
Resposta 201: { "ok": true, "id": "...", "piece": {...} }

GET /api/pieces
Lista as peças recebidas (sem auth — leitura pública, consumida pela própria UI
do brand-system pra exibir/entregar as peças).
Resposta 200: { "ok": true, "pieces": [...] }

AUTENTICAÇÃO: token compartilhado simples via env var PIECES_API_TOKEN (setado
no Vercel). Sem essa env var configurada, o endpoint recusa todo POST (fail
closed) — não existe modo "sem auth" em produção.

LIMITAÇÃO CONHECIDA (mesma do _bank.py/flywheel): fora do diretório /tmp, o
filesystem da Vercel é read-only em produção — a escrita em data/pieces-index.json
só persiste rodando localmente (vercel dev / npm start) ou num runtime com disco
gravável. Pra persistência real em produção na Vercel, plugar Vercel Blob/KV ou
um banco externo (não configurado neste repo ainda). Até lá, isso cobre o fluxo
de MVP (dev local dos dois repos) e deixa o contrato HTTP definitivo.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_INDEX = _ROOT / "data" / "pieces-index.json"

_VALID_PLATFORMS = {"instagram", "linkedin"}
_VALID_BRANDS = {"metta", "tiago"}

_REQUIRED_STRING_FIELDS = ("hook", "corpo", "cta", "full_text", "pilar_conteudo", "icp_alvo")


def _slug(text: str, n: int = 50) -> str:
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n] or "peca"


def _atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _read_index() -> list[dict]:
    if not _INDEX.exists():
        return []
    try:
        raw = json.loads(_INDEX.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return raw if isinstance(raw, list) else []


def _validate_payload(data: dict) -> str | None:
    """Retorna a mensagem de erro (str) se o payload for inválido, senão None."""
    if not isinstance(data, dict):
        return "corpo precisa ser um objeto JSON"

    for field in _REQUIRED_STRING_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return f"campo obrigatório ausente ou vazio: {field}"

    hook_variations = data.get("hook_variations")
    if not isinstance(hook_variations, list) or not all(isinstance(h, str) for h in hook_variations):
        return "hook_variations precisa ser uma lista de strings"

    platform = data.get("platform")
    if platform not in _VALID_PLATFORMS:
        return f"platform precisa ser um de {sorted(_VALID_PLATFORMS)}"

    brand = data.get("brand", "metta")
    if brand not in _VALID_BRANDS:
        return f"brand precisa ser um de {sorted(_VALID_BRANDS)}"

    linkedin_adaptation = data.get("linkedin_adaptation")
    if linkedin_adaptation is not None and not isinstance(linkedin_adaptation, str):
        return "linkedin_adaptation precisa ser string ou null"

    return None


def _build_entry(data: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": f"piece-{_slug(data['hook'])}-{uuid.uuid4().hex[:8]}",
        "received_at": now,
        "status": "recebido",
        "brand": data.get("brand", "metta"),
        "copy_type": data.get("copy_type"),
        "hook": data["hook"],
        "corpo": data["corpo"],
        "cta": data["cta"],
        "full_text": data["full_text"],
        "hook_variations": data["hook_variations"],
        "pilar_conteudo": data["pilar_conteudo"],
        "icp_alvo": data["icp_alvo"],
        "platform": data["platform"],
        "linkedin_adaptation": data.get("linkedin_adaptation"),
    }


def _check_auth(headers) -> bool:
    expected = os.environ.get("PIECES_API_TOKEN")
    if not expected:
        return False
    got = headers.get("Authorization", "")
    if not got.startswith("Bearer "):
        return False
    return got[len("Bearer "):].strip() == expected


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

            error = _validate_payload(data)
            if error:
                return self._json(400, {"detail": error})

            entry = _build_entry(data)
            pieces = _read_index()
            pieces.append(entry)
            _atomic_write_json(_INDEX, pieces)

            return self._json(201, {"ok": True, "id": entry["id"], "piece": entry})

        except Exception as exc:
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        try:
            return self._json(200, {"ok": True, "pieces": _read_index()})
        except Exception as exc:
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
