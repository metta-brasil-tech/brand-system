"""Fase 9/10 — direção e coerência de SÉRIE pra carrossel (portado do plugin-metta-ads).

Hoje cada slide do carrossel é gerado INDEPENDENTE (embed/criar.html → POST /generate
por slide). Não há coesão: paleta pode pular de dark→light, dois slides iguais em
sequência, capa tipográfica que não para o scroll, etc. Este módulo traz a disciplina de
série do plugin (regras C1–C8 do serie-rules.md), adaptada aos NOSSOS 34 modelos.

Classificação derivada dos blueprints em runtime (theme + image.required) — não
hardcoda, então não dessincroniza quando um modelo muda.

    from _serie import validate_serie, plan_serie
    issues = validate_serie([{"style":"DARK-OBJETO"}, {"style":"C-tipografia-pura-dark"}, ...])
    cfg    = plan_serie(["headline1","headline2",...], "metta")  # sugere a direção

Regras (mecânicas aqui; C5 motivos e C7 marca = julgamento do crítico de série):
  C1 capa (slide 1) NÃO-tipográfica (stop-scroll)
  C2 último slide = fechamento com CTA
  C3 anti-repetição: nada de 2 slides com o MESMO estilo em sequência
  C4 paleta travada: todos os slides na mesma FAMÍLIA (DARK/LIGHT/YELLOW/PHOTO)
  C6 no máx 2 slides tipográficos
  C8 um formato por série
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BP = _ROOT / "source" / "ad-blueprints"

# theme do blueprint → família de paleta (pra C4 "paleta travada")
_THEME_FAMILY = {
    "dark": "DARK", "paper": "LIGHT", "light": "LIGHT", "offwhite": "LIGHT",
    "white": "LIGHT", "yellow": "YELLOW", "photo": "PHOTO",
}
# fechadores conhecidos (C2) — estilos de CTA/fechamento de carrossel
_CLOSERS = {"TIAGO-EDITORIAL-CTA", "K-bold-dourado-urgencia", "YELLOW-FRAME", "DARK-CARTA"}

# Override de família: modelos cujo RENDER não bate com o `theme` do blueprint.
# Ex: YELLOW-SPLIT/YELLOW-BLOCO têm theme=dark/light mas renderizam AMARELO dominante
# → na série eles só combinam com outros amarelos, nunca numa série dark. (O `theme`
# sozinho engana o C4 "paleta travada" — visto no carrossel de teste.)
_FAMILY_OVERRIDE = {"YELLOW-SPLIT": "YELLOW", "YELLOW-BLOCO": "YELLOW"}

# Preset de foto POR FAMÍLIA — todos os slides da série usam o MESMO tratamento,
# senão a série parece peças avulsas (slide dark moody + slide cor-natural = quebra).
# É o motivo "tratamento de foto uniforme" aplicado de verdade.
_FAMILY_PRESET = {"DARK": "cinematic-dark", "LIGHT": "fotorrealista",
                  "YELLOW": "bw-yellow", "PHOTO": "fotorrealista"}

_CACHE: dict[str, dict] | None = None


def _load_models() -> dict[str, dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    out: dict[str, dict] = {}
    for p in glob.glob(str(_BP / "metta" / "*.md")) + glob.glob(str(_BP / "tiago" / "*.md")):
        t = Path(p).read_text(encoding="utf-8")
        m = re.search(r"^---\n(.*?)\n---", t, re.DOTALL)
        fm = m.group(1) if m else ""
        mid = Path(p).stem
        theme = (re.search(r"theme:\s*(\w+)", fm) or [None, "dark"])[1]
        typo = not re.search(r"required:\s*true", fm)
        marca = (re.search(r"marca:\s*(\w+)", fm) or [None, "metta"])[1]
        out[mid] = {
            "marca": marca, "theme": theme,
            "family": _FAMILY_OVERRIDE.get(mid) or _THEME_FAMILY.get(theme, "DARK"),
            "typographic": typo,
            "is_closer": mid in _CLOSERS,
        }
    _CACHE = out
    return out


def model_info(model_id: str) -> dict:
    return _load_models().get(model_id, {"family": "?", "typographic": False, "is_closer": False})


def _style(slide) -> str:
    if isinstance(slide, str):
        return slide
    return slide.get("style") or slide.get("model") or slide.get("model_id") or ""


def validate_serie(slides: list, fmt: str | None = None) -> dict:
    """Valida coerência serial (C1–C8). slides = lista de model_ids OU dicts {style,...}.

    Retorna {ok, issues, warnings, families, n_typographic}.
    """
    issues: list[str] = []
    warnings: list[str] = []
    if not slides:
        return {"ok": False, "issues": ["série vazia"], "warnings": [], "families": [], "n_typographic": 0}

    infos = [model_info(_style(s)) for s in slides]
    fams = [i["family"] for i in infos]
    n_typo = sum(1 for i in infos if i["typographic"])

    # C1 — capa não-tipográfica
    if infos[0]["typographic"]:
        issues.append(f"C1: capa (slide 1, '{_style(slides[0])}') é TIPOGRÁFICA — capa precisa parar o scroll (foto/objeto/statement visual)")

    # C2 — último = fechamento/CTA
    last_style = _style(slides[-1])
    last_cta = (slides[-1].get("cta") or slides[-1].get("copyCta") or "").strip() if isinstance(slides[-1], dict) else ""
    if not infos[-1]["is_closer"] and not last_cta:
        warnings.append(f"C2: último slide ('{last_style}') não parece fechamento com CTA — carrossel deve terminar chamando à ação")

    # C3 — anti-repetição consecutiva
    for a in range(len(slides) - 1):
        if _style(slides[a]) and _style(slides[a]) == _style(slides[a + 1]):
            issues.append(f"C3: slides {a+1} e {a+2} usam o MESMO estilo ('{_style(slides[a])}') em sequência")

    # C4 — paleta travada (mesma família)
    fam_set = {f for f in fams if f != "?"}
    if len(fam_set) > 1:
        issues.append(f"C4: paleta NÃO travada — famílias misturadas na série: {sorted(fam_set)} (escolha uma: DARK | LIGHT | YELLOW | PHOTO)")

    # C6 — máx 2 tipográficos
    if n_typo > 2:
        warnings.append(f"C6: {n_typo} slides tipográficos (máx recomendado 2) — carrossel fica monótono sem foto")

    # C8 — um formato por série (só checável se fmt informado por slide)
    if isinstance(slides[0], dict):
        formats = {(s.get("format") or fmt) for s in slides if isinstance(s, dict) and (s.get("format") or fmt)}
        if len(formats) > 1:
            issues.append(f"C8: mais de um formato na série: {sorted(formats)} — carrossel é UM formato (feed OU story)")

    return {"ok": not issues, "issues": issues, "warnings": warnings,
            "families": fams, "n_typographic": n_typo}


def plan_serie(headlines: list[str], marca: str = "metta", fmt: str = "feed") -> dict:
    """Sugere uma direção de série coerente pra N slides (heurística v1).

    Trava UMA família, escolhe capa visual + miolo variado + fechamento CTA, sem
    repetição consecutiva, e define 2-3 motivos. Não gera nada — só a direção.
    """
    models = _load_models()
    pool = [m for m, i in models.items() if i["marca"] == (marca or "metta").lower()]
    n = max(1, len(headlines))
    family = "DARK" if marca != "tiago" else "DARK"  # default editorial; ajustável

    # C4: TUDO travado na mesma família (visual, tipográfico e fechador).
    in_fam = lambda m: models[m]["family"] == family
    visual = [m for m in pool if not models[m]["typographic"] and in_fam(m)]
    typo = [m for m in pool if models[m]["typographic"] and in_fam(m)]
    closers = [m for m in pool if models[m]["is_closer"] and in_fam(m)] or typo or visual

    seq: list[str] = []
    for idx in range(n):
        if idx == 0:                      # C1: capa visual
            cand = visual or pool
        elif idx == n - 1:                # C2: fechamento
            cand = closers or visual
        else:                             # miolo: alterna visual/tipográfico, sem repetir
            cand = (typo if idx % 3 == 0 and typo else visual) or pool
        # prefere modelo AINDA não usado (variedade real, não só anti-consecutivo);
        # senão um != do anterior; senão qualquer um.
        pick = (next((m for m in cand if m not in seq), None)
                or next((m for m in cand if not seq or m != seq[-1]), None)
                or (cand[0] if cand else ""))
        seq.append(pick)

    return {
        "family": family,
        "format": fmt,
        "preset": _FAMILY_PRESET.get(family, "fotorrealista"),  # tratamento de foto uniforme
        "treatments_por_slide": seq,
        "motivos": ["amarelo cirúrgico recorrente", "tipografia display consistente",
                    "tratamento de foto uniforme"][:3],
        "validacao": validate_serie([{"style": s} for s in seq], fmt),
    }
