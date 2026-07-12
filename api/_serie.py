"""Direção de série de carrossel — parte MECÂNICA (sem LLM).

Porta as serie-rules do plugin-metta-ads (lib/serie-rules.md v0.6) pro pipeline
blueprint-driven: classificação copy→tratamento, ponte tratamento→blueprint,
trava de família visual e validação das regras C1/C2/C3/C6.
Fonte canônica: content/direcao-arte/serie-carrossel.md.

O que fica de fora (julgamento, não mecânica): motivos recorrentes (C5) e
reconhecibilidade de marca (C7) — olho do critic/vision-qa, não deste módulo.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Vocabulário fechado de tratamentos (IDs do plugin) → blueprints Metta.
# "tipografico" conta pro teto C6; "capa_ok" habilita o slide 1 (C1);
# "needs_image" decide se o slide gera foto via IA.
# ---------------------------------------------------------------------------
TREATMENTS: dict[str, dict] = {
    "T-FOTO-CENA": {
        "models": ["A-headline-foto-dark", "B-foto-top-headline-mixed",
                   "D-foto-fullbleed-overlay", "I-retrato-editorial-pb",
                   "FOTO-PILL-CASUAL"],
        "capa_ok": True, "tipografico": False, "needs_image": True,
    },
    "T-SPLIT-DUAL": {
        "models": ["YELLOW-SPLIT"],
        "capa_ok": True, "tipografico": False, "needs_image": True,
    },
    "T-OBJ-ESCURO": {
        "models": ["DARK-OBJETO", "DARK-COLAGEM"],
        "capa_ok": True, "tipografico": False, "needs_image": True,
    },
    "T-TWEET-CARD": {
        "models": ["METTA-TWEET-CARD"],
        "capa_ok": False, "tipografico": False, "needs_image": False,
    },
    "T-MOCKUP-NEWS": {
        "models": ["NEWS-CARD"],
        "capa_ok": False, "tipografico": False, "needs_image": True,
    },
    "T-BULLETS-DARK": {  # id do plugin; aqui o modelo de bullets é o YELLOW-BLOCO
        "models": ["YELLOW-BLOCO"],
        "capa_ok": False, "tipografico": True, "needs_image": False,
    },
    "T-AMARELO-STATEMENT": {
        "models": ["YELLOW-DRAW", "YELLOW-EDITORIAL", "YELLOW-FRAME",
                   "YELLOW-OBJETO"],
        "capa_ok": True, "tipografico": False, "needs_image": True,
    },
    "T-DEFINICAO": {
        "models": ["LIGHT-TIPO", "H-fundo-branco-headline-gigante", "DARK-CARTA"],
        "capa_ok": False, "tipografico": True, "needs_image": False,
    },
    "T-HIGHLIGHT-XL": {
        "models": ["C-tipografia-pura-dark", "K-bold-dourado-urgencia"],
        "capa_ok": True, "tipografico": True, "needs_image": False,
    },
    "T-CTA-FINAL": {
        "models": ["K-bold-dourado-urgencia", "D-foto-fullbleed-overlay",
                   "YELLOW-EDITORIAL"],
        "capa_ok": False, "tipografico": False, "needs_image": False,
    },
}

# Família visual por blueprint (anti-monotonia e trava C4 operam sobre FAMÍLIA).
# Derivada do params.theme do blueprint, com overrides onde o theme engana.
_FAMILIA_OVERRIDE = {
    "DARK-CARTA": "DARK",      # theme=paper, mas a peça lê dark/confidencial
    "YELLOW-SPLIT": "YELLOW",  # theme=dark, mas o split é amarelo dominante
    "YELLOW-BLOCO": "YELLOW",  # theme=light, mas o bloco é amarelo dominante
}
_FAMILIA_BY_THEME = {"dark": "DARK", "light": "LIGHT", "yellow": "YELLOW",
                     "paper": "LIGHT"}
_FAMILIA_BY_MODEL = {
    "A-headline-foto-dark": "DARK", "B-foto-top-headline-mixed": "DARK",
    "C-tipografia-pura-dark": "DARK", "D-foto-fullbleed-overlay": "DARK",
    "DARK-COLAGEM": "DARK", "DARK-OBJETO": "DARK", "I-retrato-editorial-pb": "DARK",
    "K-bold-dourado-urgencia": "DARK", "LOGO-WALL": "DARK",
    "METTA-TWEET-CARD": "DARK",
    "FOTO-PILL-CASUAL": "LIGHT", "H-fundo-branco-headline-gigante": "LIGHT",
    "LIGHT-SURREAL": "LIGHT", "LIGHT-TIPO": "LIGHT", "NEWS-CARD": "LIGHT",
    "YELLOW-DRAW": "YELLOW", "YELLOW-EDITORIAL": "YELLOW",
    "YELLOW-FRAME": "YELLOW", "YELLOW-OBJETO": "YELLOW",
}
_FAMILIA_BY_MODEL.update(_FAMILIA_OVERRIDE)


def familia_of(model_id: str) -> str:
    return _FAMILIA_BY_MODEL.get(model_id, "DARK")


# ---------------------------------------------------------------------------
# Classificação mecânica da copy do slide (porta direta do plugin, seção 4).
# ---------------------------------------------------------------------------
def classify_slide(copy_text: str) -> dict:
    text = copy_text or ""
    word_count = len(text.split())
    has_list = bool(re.search(r"(?:^|\n)\s*[-•*]\s|\n\s*\d+[.)]\s", text))
    has_question = "?" in text
    has_number = bool(re.search(r"\b\d+(?:[.,]\d+)?\s*%?|R\$\s*\d", text))
    has_quote = any(q in text for q in ('"', "“", "”"))
    return {
        "word_count": word_count,
        "has_list": has_list,
        "has_question": has_question,
        "has_number": has_number,
        "has_quote": has_quote,
        "is_very_short": word_count <= 8,
        "is_long": word_count >= 50,
    }


def _candidates(cls: dict, position: str) -> list[str]:
    """Tratamentos compatíveis por estrutura (mapa da seção 4 do plugin)."""
    if position == "fim":
        return ["T-CTA-FINAL"]  # Rule C2
    if cls["has_list"]:
        cands = ["T-BULLETS-DARK"]
    elif cls["has_quote"]:
        cands = ["T-TWEET-CARD", "T-FOTO-CENA"]
    elif cls["is_very_short"] and cls["has_question"]:
        cands = ["T-FOTO-CENA", "T-HIGHLIGHT-XL", "T-AMARELO-STATEMENT"]
    elif cls["is_very_short"]:
        cands = ["T-AMARELO-STATEMENT", "T-HIGHLIGHT-XL", "T-OBJ-ESCURO"]
    elif cls["has_number"]:
        cands = ["T-MOCKUP-NEWS", "T-FOTO-CENA", "T-HIGHLIGHT-XL"]
    elif cls["is_long"]:
        cands = ["T-FOTO-CENA", "T-TWEET-CARD", "T-OBJ-ESCURO"]
    else:
        cands = ["T-FOTO-CENA", "T-OBJ-ESCURO", "T-DEFINICAO"]
    if position == "capa":  # Rule C1
        cands = [t for t in cands if TREATMENTS[t]["capa_ok"]] or ["T-FOTO-CENA"]
    return cands


def _pick_model(treatment: str, familia_lock: str | None) -> str:
    """Escolhe o blueprint do tratamento, preferindo a família travada."""
    models = TREATMENTS[treatment]["models"]
    if familia_lock:
        same = [m for m in models if familia_of(m) == familia_lock]
        if same:
            return same[0]
    return models[0]


def plan_serie(slides: list[dict]) -> dict:
    """Monta o plano da série: tratamento + blueprint + família por slide.

    slides: [{"headline":..., "subhead":..., "body":..., "cta":...}, ...]
    Aplica C1 (capa), C2 (fim), C3 (anti-repetição), C6 (máx 2 tipográficos)
    e trava de família (análogo mecânico da C4 — paleta nomeada é do plugin;
    aqui a paleta vive no blueprint, então trava-se a FAMÍLIA dominante).
    """
    n = len(slides)
    if n < 2:
        raise ValueError("série exige >= 2 slides (default Metta: 6-8)")
    plan: list[dict] = []
    familia_lock: str | None = None
    tipograficos = 0
    prev_treatment = ""
    for i, sl in enumerate(slides):
        position = "capa" if i == 0 else ("fim" if i == n - 1 else "meio")
        text = "\n".join(x for x in [sl.get("headline", ""), sl.get("subhead", ""),
                                     sl.get("body", "")] if x)
        cls = classify_slide(text)
        cands = _candidates(cls, position)
        # Rule C3 — não repetir o tratamento do slide anterior
        cands = [t for t in cands if t != prev_treatment] or cands
        # Análogo C4 — com a família travada, preferir tratamento que tem
        # blueprint na família (sort estável preserva a prioridade estrutural;
        # tratamento sem opção na família vira inversão pontual, permitida)
        if familia_lock:
            cands = sorted(cands, key=lambda t: 0 if any(
                familia_of(m) == familia_lock for m in TREATMENTS[t]["models"]) else 1)
        # Rule C6 — teto de 2 tipográficos na série
        if tipograficos >= 2:
            nao_tipo = [t for t in cands if not TREATMENTS[t]["tipografico"]]
            cands = nao_tipo or cands
        treatment = cands[0]
        model = _pick_model(treatment, familia_lock)
        familia = familia_of(model)
        if i == 0:
            familia_lock = familia  # trava no slide 1 (análogo C4)
        if TREATMENTS[treatment]["tipografico"]:
            tipograficos += 1
        prev_treatment = treatment
        plan.append({
            "slide": i + 1, "position": position, "treatment": treatment,
            "model": model, "familia": familia,
            "needs_image": TREATMENTS[treatment]["needs_image"],
            "classify": cls,
        })
    return {"n_slides": n, "familia": familia_lock, "slides": plan}


def validate_serie(plan: dict) -> list[str]:
    """Valida as regras mecânicas sobre um plano (ou plano editado à mão)."""
    issues: list[str] = []
    slides = plan.get("slides") or []
    n = len(slides)
    if n < 2:
        return ["C0: série exige >= 2 slides"]
    if not TREATMENTS.get(slides[0]["treatment"], {}).get("capa_ok"):
        issues.append(f"C1: capa não pode ser {slides[0]['treatment']} "
                      "(tipográfica pura perde o stop-scroll)")
    if slides[-1]["treatment"] != "T-CTA-FINAL":
        issues.append(f"C2: último slide deve ser T-CTA-FINAL, veio "
                      f"{slides[-1]['treatment']}")
    for a, b in zip(slides, slides[1:]):
        if a["treatment"] == b["treatment"] and not b.get("continued"):
            issues.append(f"C3: slides {a['slide']}-{b['slide']} repetem "
                          f"{a['treatment']} (marque continued pra lista que continua)")
    tipograficos = sum(1 for s in slides
                       if TREATMENTS.get(s["treatment"], {}).get("tipografico"))
    if tipograficos > 2:
        issues.append(f"C6: {tipograficos} slides tipográficos (máx 2)")
    familias = [s["familia"] for s in slides]
    dominante = plan.get("familia") or familias[0]
    fora = sum(1 for f in familias if f != dominante)
    if len(set(familias)) > 2 or fora > len(familias) // 2:
        issues.append(f"C4: família não travada — dominante {dominante}, "
                      f"série tem {sorted(set(familias))} ({fora}/{len(familias)} fora)")
    return issues
