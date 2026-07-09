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
import unicodedata
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

# Afinidade PAPEL-NARRATIVO → archetype/id (a "ciência da copy" também é posicional:
# um slide de PROVA quer logo-wall/quote, um de REFRAME quer statement tipográfico).
# Bônus aditivo ao score de overlap textual — não substitui, complementa.
_ROLE_AFFINITY = {
    "hook":      {"object-center", "photo-fullbleed", "photo-top", "collage", "portrait", "surreal"},
    "desenvolve": {"photo-top", "photo-headline", "object-center", "news"},
    "develop":   {"photo-top", "photo-headline", "object-center", "news"},
    "reframe":   {"statement", "typo", "editorial-typo", "philosophical"},
    "prova":     {"logo-wall", "news", "portrait", "tweet-card", "social-proof"},
    "proof":     {"logo-wall", "news", "portrait", "tweet-card", "social-proof"},
    "cta":       {"closer", "urgency", "frame", "letter"},
    "fecho":     {"closer", "urgency", "frame", "letter"},
}
# ids conhecidos por papel (reforço quando o archetype do blueprint não bate o vocabulário)
_ROLE_IDS = {
    "reframe": {"LIGHT-TIPO", "YELLOW-EDITORIAL", "C-tipografia-pura-dark", "K-bold-dourado-urgencia", "TIAGO-TYPO-PURE"},
    "prova":   {"LOGO-WALL", "NEWS-CARD", "I-retrato-editorial-pb", "METTA-TWEET-CARD", "YELLOW-BLOCO"},
    "proof":   {"LOGO-WALL", "NEWS-CARD", "I-retrato-editorial-pb", "METTA-TWEET-CARD", "YELLOW-BLOCO"},
}

_STOP = set("""a o e de da do das dos que em no na nos nas um uma uns umas para pra por com sem
ao aos as os se sua seu suas seus the of to and is it você voce não nao mais já ja como
ele ela eles elas isso esse essa este esta num numa pelo pela ser ter tem foi são sao""".split())

_CACHE: dict[str, dict] | None = None


def _norm(s: str) -> str:
    """minúsculo + sem acento (pra casar 'método' com 'metodo')."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", _norm(s)) if len(w) > 2 and w not in _STOP}


def _section(body: str, header: str) -> str:
    m = re.search(rf"^##\s*{re.escape(header)}\s*\n(.+?)(?=\n##\s|\Z)", body, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _load_models() -> dict[str, dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    out: dict[str, dict] = {}
    for p in glob.glob(str(_BP / "metta" / "*.md")) + glob.glob(str(_BP / "tiago" / "*.md")):
        t = Path(p).read_text(encoding="utf-8")
        m = re.search(r"^---\n(.*?)\n---", t, re.DOTALL)
        fm = m.group(1) if m else ""
        body = t[m.end():] if m else t
        mid = Path(p).stem
        theme = (re.search(r"theme:\s*(\w+)", fm) or [None, "dark"])[1]
        typo = not re.search(r"required:\s*true", fm)
        marca = (re.search(r"marca:\s*(\w+)", fm) or [None, "metta"])[1]
        archetype = (re.search(r"archetype:\s*([\w-]+)", fm) or [None, ""])[1]
        # intenção POSITIVA (quando este modelo brilha) e NEGATIVA (anti-padrões).
        pos = " ".join([_section(body, "Intenção"), _section(body, "Quando brilha")])
        neg = _section(body, "Anti-padrões")
        out[mid] = {
            "marca": marca, "theme": theme,
            "family": _FAMILY_OVERRIDE.get(mid) or _THEME_FAMILY.get(theme, "DARK"),
            "typographic": typo,
            "is_closer": mid in _CLOSERS,
            "archetype": archetype,
            "intent_pos": _tokens(pos),
            "intent_neg": _tokens(neg),
        }
    _CACHE = out
    return out


def _slide_text(slide) -> str:
    """texto do slide que importa pra escolher o modelo: papel + headline + direção visual."""
    if isinstance(slide, str):
        return slide
    return " ".join(str(slide.get(k, "")) for k in ("role", "headline", "subhead", "visual", "body"))


def score_model(model_id: str, slide) -> float:
    """Quão bem ESTE modelo serve ESTE slide (copy-aware). Maior = melhor.

    = overlap(copy do slide, intenção do modelo) − overlap(copy, anti-padrões)
      + bônus de afinidade PAPEL→archetype/id. Determinístico, sem LLM.
    """
    info = model_info(model_id)
    if info.get("family") == "?":
        return 0.0
    toks = _tokens(_slide_text(slide))
    pos = info.get("intent_pos") or set()
    neg = info.get("intent_neg") or set()
    score = 2.0 * len(toks & pos) - 1.5 * len(toks & neg)
    role = _norm(slide.get("role", "")) if isinstance(slide, dict) else ""
    if role:
        arche = info.get("archetype", "")
        if arche and any(_norm(a) in _norm(arche) or _norm(arche) in _norm(a)
                         for a in _ROLE_AFFINITY.get(role, ())):
            score += 3.0
        if model_id in _ROLE_IDS.get(role, set()):
            score += 2.5
    return score


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


def _best_family(slides: list, pool: list[str], models: dict) -> str:
    """Escolhe a família cujos modelos, no total, melhor servem ESTA série (copy-aware).

    Se os slides não têm copy (só headlines), não há sinal → cai no DARK editorial.
    """
    fams = {models[m]["family"] for m in pool} - {"?"}
    have_copy = any(isinstance(s, dict) and (s.get("visual") or s.get("role") or s.get("headline")) for s in slides)
    if not have_copy or not fams:
        return "DARK"
    best, best_score = "DARK", float("-inf")
    for fam in sorted(fams):
        fam_models = [m for m in pool if models[m]["family"] == fam]
        # soma do MELHOR modelo da família por slide → quão bem a família cobre a narrativa
        total = sum(max((score_model(m, s) for m in fam_models), default=0.0) for s in slides)
        if total > best_score:
            best, best_score = fam, total
    return best


def plan_serie(slides: list, marca: str = "metta", fmt: str = "feed") -> dict:
    """Direção de série coerente pra N slides — CIENTE DA COPY (v2).

    `slides` aceita:
      - list[str]            → só headlines (retrocompat; cai na heurística posicional)
      - list[dict]           → {role, headline, subhead, body, cta, visual} por slide
                               → escolhe o modelo pelo CONTEÚDO de cada slide.

    Trava UMA família (C4), capa visual pelo hook (C1), fecho com CTA (C2), sem
    repetição (C3 + anti-repetição total), máx 2 tipográficos (C6). Não gera nada.
    """
    if isinstance(slides, str):
        slides = [slides]
    # normaliza: tudo vira dict (headline mínimo) pra uniformizar o scorer
    slides = [{"headline": s} if isinstance(s, str) else dict(s) for s in (slides or [{"headline": ""}])]
    n = len(slides)
    models = _load_models()
    pool = [m for m, i in models.items() if i["marca"] == (marca or "metta").lower()]
    family = _best_family(slides, pool, models)

    # C4: TUDO travado na família escolhida.
    in_fam = lambda m: models[m]["family"] == family
    visual = [m for m in pool if not models[m]["typographic"] and in_fam(m)]
    typo = [m for m in pool if models[m]["typographic"] and in_fam(m)]
    closers = [m for m in pool if models[m]["is_closer"] and in_fam(m)] or typo or visual
    fam_pool = [m for m in pool if in_fam(m)] or pool

    seq: list[str] = []
    n_typo = 0
    rationale: list[dict] = []
    for idx, slide in enumerate(slides):
        if idx == 0:                       # C1: capa SEMPRE visual (stop-scroll)
            cand = visual or fam_pool
        elif idx == n - 1:                 # C2: fechamento/CTA
            cand = closers or visual or fam_pool
        else:                              # miolo: qualquer da família…
            cand = fam_pool
            if n_typo >= 2:                # …mas respeita C6 (máx 2 tipográficos)
                cand = [m for m in cand if not models[m]["typographic"]] or cand
        # anti-repetição TOTAL (nada já usado) + nunca igual ao anterior
        cand = [m for m in cand if m not in seq] or [m for m in cand if not seq or m != seq[-1]] or cand
        # escolhe o de MAIOR score pra ESTE slide (ciente da copy); desempate estável
        pick = max(cand, key=lambda m: (score_model(m, slide), m in (visual if idx == 0 else cand), -seq.count(m)))
        seq.append(pick)
        if models[pick]["typographic"]:
            n_typo += 1
        rationale.append({"slide": idx + 1, "model": pick, "score": round(score_model(pick, slide), 1),
                          "role": slide.get("role", ""), "foto": not models[pick]["typographic"]})

    # capa: a direção visual do hook vira a CENA da capa (briefing_text forte, não "carrossel")
    cover = slides[0]
    cover_direction = (cover.get("visual") or cover.get("headline") or "").strip()

    return {
        "family": family,
        "format": fmt,
        "preset": _FAMILY_PRESET.get(family, "fotorrealista"),  # tratamento de foto uniforme
        "treatments_por_slide": seq,
        "cover_direction": cover_direction,                     # capa mais forte (cena derivada da copy)
        "briefs_por_slide": [(s.get("visual") or s.get("headline") or "").strip() for s in slides],
        "selecao": rationale,                                   # por que cada modelo (copy-aware)
        "motivos": ["amarelo cirúrgico recorrente", "tipografia display consistente",
                    "tratamento de foto uniforme"][:3],
        "validacao": validate_serie([{"style": m, "cta": slides[i].get("cta", "")}
                                     for i, m in enumerate(seq)], fmt),
    }
