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
    # --- 3 modelos que existiam mas eram ÓRFÃOS do planner (nunca escolhidos há
    # meses). Agora no vocabulário, ligados às estruturas de copy que eles servem. ---
    "T-STAT-DADOS": {  # números empilhados gigantes (pesquisa/resultado)
        "models": ["METTA-STAT-STACK"],
        "capa_ok": False, "tipografico": True, "needs_image": False,
    },
    "T-EQUACAO": {  # headline com "=" vira termos + sinal amarelo
        "models": ["METTA-EQUACAO"],
        "capa_ok": True, "tipografico": True, "needs_image": False,
    },
    "T-CHAT-DEF": {  # palavra-definição + balão de chat "escrevendo…" (hook)
        "models": ["METTA-CHAT-DEF"],
        "capa_ok": True, "tipografico": True, "needs_image": False,
    },
}

# Regra C9 — MÁX 1 foto de PESSOA por carrossel. Pessoas geradas por IA em slides
# consecutivos saem sósias (mesmo homem/loja) e o conjunto lê como "foto repetida"
# (feedback do Nathan). Estes tratamentos põem PESSOA no quadro; objeto/tipografia
# não têm o risco. A partir da 1ª foto de pessoa, o planner rebaixa as próximas pra
# tratamento sem-pessoa (objeto/tipográfico). "menos foto, mais conceito."
_PERSON_TREATMENTS = {"T-FOTO-CENA", "T-SPLIT-DUAL", "T-MOCKUP-NEWS"}

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
    "METTA-STAT-STACK": "DARK", "METTA-EQUACAO": "DARK", "METTA-CHAT-DEF": "DARK",
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
    # "=" na headline vira METTA-EQUACAO (termos empilhados + sinal amarelo).
    has_equation = "=" in text
    # definição-dicionário: 1ª palavra curta seguida de "·"/"—"/":" (ex: "Método ·
    # substantivo...") OU pergunta muito curta → hook de definição (METTA-CHAT-DEF).
    has_definition = bool(re.search(r"^\s*[\wÀ-ÿ]+\.?\s*[·:—-]", text))
    return {
        "word_count": word_count,
        "has_list": has_list,
        "has_question": has_question,
        "has_number": has_number,
        "has_quote": has_quote,
        "has_equation": has_equation,
        "has_definition": has_definition,
        "is_very_short": word_count <= 8,
        "is_long": word_count >= 50,
    }


def _candidates(cls: dict, position: str) -> list[str]:
    """Tratamentos compatíveis por estrutura (mapa da seção 4 do plugin)."""
    if position == "fim":
        return ["T-CTA-FINAL"]  # Rule C2
    if cls["has_list"]:
        cands = ["T-BULLETS-DARK"]
    elif cls.get("has_equation"):        # "=" na headline → equação (só modelo certo)
        cands = ["T-EQUACAO", "T-HIGHLIGHT-XL", "T-AMARELO-STATEMENT"]
    elif cls.get("has_definition"):      # "palavra · definição" → hook de chat-def
        cands = ["T-CHAT-DEF", "T-DEFINICAO", "T-HIGHLIGHT-XL"]
    elif cls["has_quote"]:
        cands = ["T-TWEET-CARD", "T-FOTO-CENA"]
    elif cls["is_very_short"] and cls["has_question"]:
        cands = ["T-CHAT-DEF", "T-FOTO-CENA", "T-HIGHLIGHT-XL", "T-AMARELO-STATEMENT"]
    elif cls["is_very_short"]:
        cands = ["T-AMARELO-STATEMENT", "T-HIGHLIGHT-XL", "T-OBJ-ESCURO"]
    elif cls["has_number"]:
        cands = ["T-STAT-DADOS", "T-MOCKUP-NEWS", "T-FOTO-CENA", "T-HIGHLIGHT-XL"]
    elif cls["is_long"]:
        cands = ["T-FOTO-CENA", "T-TWEET-CARD", "T-OBJ-ESCURO"]
    else:
        cands = ["T-FOTO-CENA", "T-OBJ-ESCURO", "T-DEFINICAO"]
    if position == "capa":  # Rule C1
        cands = [t for t in cands if TREATMENTS[t]["capa_ok"]] or ["T-FOTO-CENA"]
    return cands


def _pick_model(treatment: str, familia_lock: str | None,
                avoid: str | None = None) -> str:
    """Escolhe o blueprint do tratamento, preferindo a família travada
    (ou, na capa, evitando a família das últimas séries — anti-monotonia)."""
    models = TREATMENTS[treatment]["models"]
    if familia_lock:
        same = [m for m in models if familia_of(m) == familia_lock]
        if same:
            return same[0]
    if avoid:
        other = [m for m in models if familia_of(m) != avoid]
        if other:
            return other[0]
    return models[0]


def familia_hint_from(root) -> str | None:
    """Anti-monotonia ENTRE séries (plugin, seção 3.5): olha os últimos
    serie-config.json sob `root`; se as 2 séries mais recentes foram da mesma
    família, retorna essa família para ser EVITADA na próxima capa."""
    import json
    from pathlib import Path
    try:
        configs = sorted(Path(root).rglob("serie-config.json"),
                         key=lambda p: p.stat().st_mtime, reverse=True)[:2]
    except OSError:
        return None
    familias = []
    for c in configs:
        try:
            familias.append(json.loads(c.read_text(encoding="utf-8")).get("familia"))
        except Exception:
            pass
    if len(familias) == 2 and familias[0] and familias[0] == familias[1]:
        return familias[0]
    return None


def plan_serie(slides: list[dict], avoid_familia: str | None = None,
               no_image: bool = False) -> dict:
    """Monta o plano da série: tratamento + blueprint + família por slide.

    slides: [{"headline":..., "subhead":..., "body":..., "cta":...}, ...]
    Campos opcionais por slide: "treatment" (força um T-* do vocabulário) e
    "continued": true (exceção da C3 pra lista/thread que continua).
    Aplica C1 (capa), C2 (fim), C3 (anti-repetição), C6 (máx 2 tipográficos)
    e trava de família (análogo mecânico da C4 — paleta nomeada é do plugin;
    aqui a paleta vive no blueprint, então trava-se a FAMÍLIA dominante).
    avoid_familia: família a evitar na capa (anti-monotonia entre séries).
    """
    n = len(slides)
    if n < 2:
        raise ValueError("série exige >= 2 slides (default Metta: 6-8)")
    plan: list[dict] = []
    familia_lock: str | None = None
    tipograficos = 0
    person_photos = 0   # C9: conta fotos de PESSOA já usadas (teto = 1)
    prev_treatment = ""
    for i, sl in enumerate(slides):
        position = "capa" if i == 0 else ("fim" if i == n - 1 else "meio")
        text = "\n".join(x for x in [sl.get("headline", ""), sl.get("subhead", ""),
                                     sl.get("body", "")] if x)
        cls = classify_slide(text)
        forced = sl.get("treatment")
        if forced:
            if forced not in TREATMENTS:
                raise ValueError(f"slide {i + 1}: tratamento desconhecido {forced!r} "
                                 f"(vocabulário: {sorted(TREATMENTS)})")
            cands = [forced]
        else:
            cands = _candidates(cls, position)
            # Sem imagem, blueprint de FOTO vira vazio morto (metade do canvas
            # em branco) — só tratamentos sem foto entram, com o leque
            # tipográfico completo pra não virar 5x o mesmo molde (anti-padrão
            # A1). Modo degradado: produção real é com imagem.
            if no_image:
                sem_foto = [t for t in cands if not TREATMENTS[t]["needs_image"]]
                if sem_foto and (cls["has_list"] or cls["has_quote"]):
                    # sinal estrutural forte (lista/citação) mantém o tratamento
                    # certo — não dilui com alternativas nem cede à família
                    cands = sem_foto
                else:
                    extras = (["T-HIGHLIGHT-XL"] if position == "capa" else
                              ["T-DEFINICAO", "T-TWEET-CARD", "T-HIGHLIGHT-XL"])
                    cands = sem_foto + [t for t in extras if t not in sem_foto]
            # Rule C3 — não repetir o tratamento do slide anterior
            cands = [t for t in cands if t != prev_treatment] or cands
            # Análogo C4 — com a família travada, preferir tratamento que tem
            # blueprint na família (sort estável preserva a prioridade
            # estrutural; sem opção na família vira inversão pontual).
            # Sem imagem a série é toda tipográfica: a preferência de família
            # NÃO se aplica — variedade de fundo (dark/light/yellow) é o que
            # separa carrossel real de 5x o mesmo slide (banco: burnout).
            if familia_lock and not no_image:
                cands = sorted(cands, key=lambda t: 0 if any(
                    familia_of(m) == familia_lock for m in TREATMENTS[t]["models"]) else 1)
            elif avoid_familia and familia_lock is None:  # só a capa, antes da trava
                # capa com anti-monotonia: preferir tratamento com opção FORA
                # da família das últimas séries
                cands = sorted(cands, key=lambda t: 0 if any(
                    familia_of(m) != avoid_familia for m in TREATMENTS[t]["models"]) else 1)
            # Rule C6 — teto de 2 tipográficos na série (não se aplica no modo
            # sem-imagem: ali a série é tipográfica por definição)
            if tipograficos >= 2 and not no_image:
                nao_tipo = [t for t in cands if not TREATMENTS[t]["tipografico"]]
                cands = nao_tipo or cands
            # Rule C9 — já tem 1 foto de PESSOA: rebaixa as próximas pra
            # tratamento sem-pessoa (evita sósias). Se só sobrar pessoa, mantém
            # (não trava a série); a capa foto-âncora costuma ser a única.
            if person_photos >= 1:
                sem_pessoa = [t for t in cands if t not in _PERSON_TREATMENTS]
                cands = sem_pessoa or cands
        treatment = cands[0]
        if treatment in _PERSON_TREATMENTS:
            person_photos += 1
        forced_model = sl.get("model")
        if forced_model:
            # recriação/direção manual: usa o blueprint pedido (o pipeline
            # valida a existência); família vem da tabela (default DARK)
            model = forced_model
        else:
            model = _pick_model(treatment, None if no_image else familia_lock,
                                avoid=avoid_familia if familia_lock is None else None)
        familia = familia_of(model)
        if i == 0:
            familia_lock = familia  # trava no slide 1 (análogo C4)
        if TREATMENTS[treatment]["tipografico"]:
            tipograficos += 1
        prev_treatment = treatment
        entry = {
            "slide": i + 1, "position": position, "treatment": treatment,
            "model": model, "familia": familia,
            "needs_image": TREATMENTS[treatment]["needs_image"],
            "classify": cls,
        }
        if sl.get("continued"):
            entry["continued"] = True
        plan.append(entry)
    out = {"n_slides": n, "familia": familia_lock, "slides": plan}
    if no_image:
        out["no_image"] = True
    return out


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
    if tipograficos > 2 and not plan.get("no_image"):
        issues.append(f"C6: {tipograficos} slides tipográficos (máx 2)")
    familias = [s["familia"] for s in slides]
    dominante = plan.get("familia") or familias[0]
    fora = sum(1 for f in familias if f != dominante)
    if (len(set(familias)) > 2 or fora > len(familias) // 2) and not plan.get("no_image"):
        # no_image: série tipográfica varia fundo de propósito (banco real faz)
        issues.append(f"C4: família não travada — dominante {dominante}, "
                      f"série tem {sorted(set(familias))} ({fora}/{len(familias)} fora)")
    return issues
