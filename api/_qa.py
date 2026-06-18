"""QA validator do render blueprint-driven.

Checagem estática (rápida, sem browser) + leitura opcional do flag data-overflow
que o _engine.js seta no browser. Use no pipeline antes de entregar, ou no teste.

    qa(front_matter, copy, image_url, html) -> {"status","issues","warnings"}
"""
from __future__ import annotations

ARCHETYPES = {"typo", "photo-side", "photo-full", "photo-band", "object-center",
              "card-mock", "logo-wall", "framed", "split", "number-hero"}
# Marca Tiago tem design system próprio (Inter, off-white, accent #FFCC00) e não
# usa o mecanismo de theme/token Metta — validado à parte.
TIAGO_ARCHETYPES = {
    "tiago-editorial-hero", "tiago-editorial-dark", "tiago-editorial-card",
    "tiago-editorial-cta", "tiago-typo", "tiago-dark-surreal", "tiago-photo-raw",
    "tiago-notes", "tiago-story-hero", "tiago-story-yellow", "tiago-story-minimal",
    "tiago-twitter",
}
THEMES = {"dark", "light", "yellow", "paper"}


def qa(front_matter: dict, copy: dict, image_url: str, html: str) -> dict:
    issues: list[str] = []
    warnings: list[str] = []
    fm = front_matter or {}
    copy = copy or {}
    params = fm.get("params", {}) or {}

    arch = fm.get("archetype")
    is_tiago = isinstance(arch, str) and arch.startswith("tiago")
    if arch not in ARCHETYPES and not (is_tiago and arch in TIAGO_ARCHETYPES):
        issues.append(f"archetype inválido: '{arch}' (esperado um de {sorted(ARCHETYPES | TIAGO_ARCHETYPES)})")
    # Theme só vale pro sistema Metta; Tiago define seu próprio bg por archetype.
    if not is_tiago:
        theme = params.get("theme", "dark")
        if theme not in THEMES:
            issues.append(f"theme inválido: '{theme}'")

    # Estilos imagem-pura (text:none — ex. tiago-photo-raw, tiago-dark-surreal) NÃO
    # têm texto por design: a peça é só a foto. Headline vazia neles é esperado.
    image_only = str(params.get("text", "")).strip().lower() == "none"

    # Slots de conteúdo
    if not (copy.get("headline") or "").strip():
        if not image_only:
            issues.append("headline vazia (slot obrigatório)")
    elif len(copy["headline"]) > 90:
        warnings.append(f"headline longa ({len(copy['headline'])}ch) — auto-fit reduz, mas considere encurtar")
    if not (copy.get("cta") or "").strip() and not image_only:
        warnings.append("sem CTA (recomendado: CTA no fim)")

    # Tweet/notes precisam de CORPO — sem body o card sai 'pelado' (lição da sessão).
    _TWEET_LIKE = {"card-mock", "tiago-twitter", "tiago-notes"}
    if arch in _TWEET_LIKE and not (copy.get("body") or "").strip():
        warnings.append("estilo tweet/notes sem corpo (body) — card fica vazio; preencha o body")

    # Imagem
    img_req = bool((fm.get("image") or {}).get("required"))
    if img_req and not image_url:
        warnings.append("modelo pede imagem (image.required) mas nenhuma foi fornecida — render sai sem foto")

    # Réguas duras no HTML
    if 'class="ad"' not in html:
        issues.append("HTML não contém o canvas .ad")
    if "Zalando Sans Expanded" not in html:
        issues.append("fonte display Zalando Sans Expanded ausente no HTML")
    if copy.get("headline") and copy["headline"].replace("*", "")[:12] not in html.replace("*", ""):
        warnings.append("headline pode não ter sido injetada no HTML")

    # Overflow / colisão (se o html já passou pelo browser e o _engine.js marcou).
    # data-collision="1" = texto ainda ficaria embaixo do CTA mesmo no piso de
    # fonte → copy longa demais pro estilo (sinal pra encurtar ou trocar de estilo).
    if 'data-collision="1"' in html:
        issues.append("colisão texto×CTA: copy não cabe acima do botão nem no menor tamanho — encurte a copy ou troque de estilo")
    elif 'data-overflow="1"' in html:
        issues.append("overflow detectado: conteúdo excede o canvas")

    status = "FAIL" if issues else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {"status": status, "issues": issues, "warnings": warnings}
