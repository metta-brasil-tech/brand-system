"""Inferência de AVATAR/ICP pela copy — conserta o erro "ICP só se passado".

Bug encontrado na auditoria: o `generate.py` só usa `avatar_segment` se ele for
passado (CLI/wizard). Sem isso, o avatar fica vazio e a persona volta pra heurística
"use mulheres" — mesmo com o bloco de conhecimento presente. O handoff dizia
"segmento inferido pela copy", mas a inferência não existia.

Este módulo infere o segmento do ICP a partir da copy:
- casa a copy contra os segmentos do `avatars.json` (label/ui_desc/case_anchor/env);
- com sinal setorial forte → segmento específico (varejo-farmacia, servico-profissional…);
- sem sinal → cai no ICP estratégico (`generico` / variante `padrao` = empresário em
  ponto de inflexão). NUNCA fica vazio → a persona sempre nasce do ICP.

Brand-aware: para **Tiago** retorna (None, None) — nos anúncios do Tiago o sujeito é
ele/uma metáfora, não o avatar do ICP; injetar o empresário ali seria um bug novo.

    seg, var = infer_segment(copy, marca)   # ex: ("varejo-farmacia", "padrao")
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AVATARS = _ROOT / "engine" / "brand-knowledge" / "audience" / "avatars.json"

_DEFAULT = ("generico", "padrao")  # ICP estratégico — empresário em ponto de inflexão
_MIN_SCORE = 1  # 1 pista setorial forte já basta (os hints abaixo são inequívocos)

# Pistas setoriais explícitas — o texto do avatars.json é magro; aqui garantimos que
# os termos óbvios de cada setor casem mesmo sem aparecer na ficha do segmento.
_SECTOR_HINTS = {
    "varejo-farmacia": {"farmacia", "farmacias", "drogaria", "drogarias", "balcao"},
    "varejo-pet": {"pet", "petshop", "agropet", "veterinaria", "veterinario", "racao"},
    "varejo-otica-joias": {"otica", "oticas", "joia", "joias", "joalheria", "relojoaria", "oculos"},
    "varejo-construcao-deco": {"construcao", "reforma", "deco", "decoracao", "moveis", "ferragem", "materiais"},
    "servico-profissional": {"clinica", "consultorio", "dentista", "odonto", "medico", "medica",
                              "estetica", "fisioterapia", "salao", "academia", "terapeuta", "spa"},
    "industria-b2b": {"industria", "fabrica", "distribuidora", "atacado", "fornecedor"},
}

_STOP = {"que", "com", "para", "uma", "voce", "seu", "sua", "tem", "nao", "como",
         "dos", "das", "por", "mais", "isso", "dono", "empresa", "time", "vendas",
         "venda", "meta", "operacao", "negocio", "cliente", "equipe"}


def _words(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]{4,}", s)} - _STOP


def _segment_text(seg: dict) -> str:
    return " ".join(str(seg.get(k, "")) for k in
                    ("id", "label", "ui_desc", "case_anchor", "environment"))


def infer_segment(copy: dict, marca: str = "metta") -> tuple[str | None, str | None]:
    """Infere (segmento, variante) do ICP pela copy. Nunca vazio para Metta."""
    if (marca or "").lower() == "tiago":
        return (None, None)
    try:
        data = json.loads(_AVATARS.read_text(encoding="utf-8"))
        segs = [s for s in data.get("segments", []) if s.get("id") not in (None, "generico")]
    except Exception:
        return _DEFAULT

    q = _words(" ".join(str(copy.get(k, "")) for k in ("headline", "subhead", "body")))
    best, best_score = None, 0
    for s in segs:
        sid = s.get("id")
        score = len(q & _words(_segment_text(s))) + len(q & _SECTOR_HINTS.get(sid, set()))
        if score > best_score:
            best, best_score = s, score
    if best and best_score >= _MIN_SCORE:
        return (best["id"], "padrao")
    return _DEFAULT
