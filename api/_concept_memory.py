"""Memória de conceitos visuais — pra garantir VARIAÇÃO entre anúncios.

Guarda uma lista rolante de conceitos já usados (tipo de cena + nota de sujeito)
pra o Diretor Visual evitar repetir a mesma imagem/pessoa anúncio após anúncio.

Persistência: arquivo JSON. Local: env CONCEPT_MEMORY_PATH ou ARTIFACTS_DIR/
concept_memory.json. ATENÇÃO PROD: em serverless o disco é efêmero (/tmp) — pra
memória durável em produção, trocar por um KV (Vercel KV / Upstash) mantendo
esta mesma interface.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_CAP = 40  # quantos conceitos manter no histórico


def _path() -> Path:
    p = os.getenv("CONCEPT_MEMORY_PATH")
    if p:
        return Path(p)
    base = os.getenv("ARTIFACTS_DIR", "/tmp/artifacts")
    return Path(base) / "concept_memory.json"


def read_recent(n: int = 12) -> list[dict]:
    """Últimos N conceitos usados (mais recentes primeiro)."""
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data[-n:][::-1]
    except Exception:
        pass
    return []


def remember(concept: dict) -> None:
    """Acrescenta um conceito ao histórico (cap em _CAP)."""
    if not concept:
        return
    try:
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
        entry = {
            "scene_type": str(concept.get("scene_type", ""))[:40],
            "subject_note": str(concept.get("subject_note", ""))[:120],
        }
        data.append(entry)
        path.write_text(json.dumps(data[-_CAP:], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
