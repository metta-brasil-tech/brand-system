"""Fase 5 — entrada no banco (F8 do plugin). O motor do flywheel.

Quando uma peça é **aprovada (SHIP) pelo usuário**, ela vira repertório: entra no
banco (`data/applications-index.json` + thumb raster). Aí o crítico (_critic) passa a
poder escolhê-la como referência e a geração reference-aware fica mais afiada → melhora
composta. É o que faz o sistema melhorar COM O TEMPO, não só por peça.

SEGURANÇA (inegociável):
  - Só entra peça com verdict=SHIP E approved=True (aprovação humana explícita). Banco
    poluído com peça ruim envenena TODAS as gerações futuras.
  - Escrita ATÔMICA (tmp+rename) — nunca deixa o índice meio-escrito (o crítico lê ele
    ao vivo durante geração).
  - NÃO rodar enquanto um batch estiver gerando (o batch lê o índice). Rodar com a
    máquina ociosa.

A ficha é escrita OLHANDO O PNG (vision tagging, como o F8 do plugin), com fallback no
decision-log quando a visão não está disponível.

A auditoria do efeito NÃO é por-entrada: ela acontece no próximo batch, quando o
_ledger compara as métricas antes→depois de o banco ter crescido.
"""
from __future__ import annotations

import base64
import json
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_INDEX = _ROOT / "data" / "applications-index.json"
_THUMBS = _ROOT / "assets" / "applications" / "ads" / "thumbs"


def _slug(text: str, n: int = 50) -> str:
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n] or "peca"


def _atomic_write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)  # rename atômico


def _append_to_index(entry: dict) -> None:
    raw = json.loads(_INDEX.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        # dedup por id
        raw = [x for x in raw if not (isinstance(x, dict) and x.get("id") == entry["id"])]
        raw.append(entry)
        _atomic_write_json(_INDEX, raw)
        return
    if isinstance(raw, dict):
        key = next((k for k, v in raw.items() if isinstance(v, list)), None) or "items"
        lst = raw.setdefault(key, [])
        raw[key] = [x for x in lst if not (isinstance(x, dict) and x.get("id") == entry["id"])]
        raw[key].append(entry)
        _atomic_write_json(_INDEX, raw)
        return
    raise ValueError("formato inesperado de applications-index.json")


def _vision_tag(png_bytes: bytes, copy: dict, marca: str) -> dict:
    """Olha o PNG e devolve mood/intent/archetype_foto/tokens (best-effort)."""
    try:
        from openai import OpenAI
    except Exception:
        return {}
    model = os.getenv("BANK_TAG_MODEL") or os.getenv("VISION_QA_MODEL", "gpt-4.1")
    sys_p = (
        "Você cataloga um anúncio aprovado pro banco de referências. Olhe a peça e "
        "devolve APENAS JSON: {\"mood\":\"confronto|analitico|autoridade|aspiracional|"
        "provocacao|acolhedor|diagnostico|urgencia\",\"intent\":\"autoridade|oferta|"
        "prova\",\"archetype_foto\":\"<tipo de foto curto, ex: executivo-em-decisao, "
        "objeto-conceitual, retrato-individual-confiante>\",\"tokens\":[\"2-4 tokens "
        "visuais, ex: charcoal-base, yellow-50-sotaque\"]}"
    )
    try:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        r = OpenAI().chat.completions.create(
            model=model, max_tokens=200,
            messages=[{"role": "system", "content": sys_p},
                      {"role": "user", "content": [
                          {"type": "text", "text": f"marca={marca}. Catalogue:"},
                          {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}])
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (r.choices[0].message.content or "").strip())
        m = re.search(r"\{.*\}", t, re.DOTALL)
        return json.loads(m.group(0) if m else t)
    except Exception:
        return {}


def ingest_to_bank(png_bytes: bytes, copy: dict, model_id: str, marca: str,
                   verdict: str | None = None, approved: bool = False,
                   decision_log: dict | None = None, tag_with_vision: bool = True) -> dict:
    """Entra com uma peça APROVADA no banco. Retorna {ok, id|reason}.

    Gate duro: approved=True E verdict=SHIP. Sem isso, recusa (protege o banco).
    """
    if not approved:
        return {"ok": False, "reason": "entrada no banco exige aprovação humana explícita (approved=True)"}
    if (verdict or "").upper() != "SHIP":
        return {"ok": False, "reason": f"só peça SHIP entra no banco (recebido: {verdict})"}
    if not png_bytes:
        return {"ok": False, "reason": "sem PNG"}

    headline = (copy.get("headline") or "").replace("*", "")
    _id = f"ad-{_slug(headline)}"
    _THUMBS.mkdir(parents=True, exist_ok=True)
    thumb_rel = f"assets/applications/ads/thumbs/{_id}.png"
    (_ROOT / thumb_rel).write_bytes(png_bytes)

    tags = _vision_tag(png_bytes, copy, marca) if tag_with_vision else {}
    dl = decision_log or {}
    av = (dl.get("avatar") or {}) if isinstance(dl, dict) else {}

    entry = {
        "id": _id,
        "brand": marca,
        "type": "ad",
        "status": "canonical",
        "date": date.today().isoformat(),
        "model_id": model_id,
        "mood": tags.get("mood"),
        "intent": tags.get("intent"),
        "archetype_foto": tags.get("archetype_foto"),
        "tokens_used": tags.get("tokens") or [],
        "copy": {"headline": headline, "subheadline": copy.get("subhead", ""),
                 "cta": copy.get("cta", "")},
        "avatar_segment": av.get("segment"),
        "src": {"thumb": thumb_rel, "mid": thumb_rel},
        "notes": "Aprovado pelo usuário e ingerido via flywheel (Fase 5).",
        "_provenance": (dl.get("knowledge_provenance") if isinstance(dl, dict) else None),
    }
    _append_to_index(entry)
    return {"ok": True, "id": _id, "entry": entry, "tagged_by_vision": bool(tags)}
