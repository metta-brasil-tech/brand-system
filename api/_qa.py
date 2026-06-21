"""QA validator do render blueprint-driven.

Checagem estática (rápida, sem browser) + leitura opcional do flag data-overflow
que o _engine.js seta no browser. Use no pipeline antes de entregar, ou no teste.

    qa(front_matter, copy, image_url, html) -> {"status","issues","warnings"}
"""
from __future__ import annotations

import html as _htmllib
import re
import unicodedata

# Chrome de marca que aparece no render mas NÃO vem da copy (whitelist embutida).
# É BRAND-AWARE: cada marca tem o seu chrome fixo (eyebrow/assinatura/tagline).
_CHROME_SHARED = {"metta"}
_CHROME_METTA = {"inteligencia", "comercial"}        # eyebrow automático dos covers Metta
_CHROME_TIAGO = {"estrategias", "gestao", "vendas",  # assinatura/tagline do Tiago Alves
                 "ciencia", "tiago", "alves"}


def _norm_words(s: str) -> list[str]:
    """Tokens alfanuméricos, lowercase, sem acento — robusto a markup e pontuação."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", s)


def _visible_text(html_str: str) -> str:
    """Texto visível do HTML (tira script/style/head, tags, desescapa entidades)."""
    h = re.sub(r"(?is)<(script|style|head|title|noscript)\b.*?</\1>", " ", html_str or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _htmllib.unescape(h)).strip()


def _is_subseq(needle: list[str], hay: list[str]) -> bool:
    """needle aparece como sequência CONTÍGUA de tokens em hay."""
    if not needle:
        return True
    for i in range(len(hay) - len(needle) + 1):
        if hay[i:i + len(needle)] == needle:
            return True
    return False


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

    # ── Guardrails de COPY LITERAL + TEXTO INVENTADO (portados do gate.py do plugin) ──
    # A copy é propriedade do brief — o render não pode trocar/perder/cortar palavra,
    # nem injetar texto fora da copy + whitelist. Comparação por SEQUÊNCIA de palavras
    # (não byte-a-byte) pra ser robusta a <br>/<span> do auto-quebra e à pontuação.
    if not image_only:
        vis_tokens = _norm_words(_visible_text(html))
        hl = (copy.get("headline") or "").replace("*", "")
        if hl.strip() and not _is_subseq(_norm_words(hl), vis_tokens):
            issues.append("copy_headline_literal: headline renderizada não bate com o brief "
                          "(palavra trocada/perdida/cortada)")
        sub = (copy.get("subhead") or "").replace("*", "")
        if sub.strip() and not _is_subseq(_norm_words(sub), vis_tokens):
            warnings.append("copy_subheadline_literal: subhead renderizada diverge do brief")
        cta = (copy.get("cta") or "").replace("*", "")
        if cta.strip() and not _is_subseq(_norm_words(cta), vis_tokens):
            warnings.append("copy_cta_literal: CTA renderizado diverge do brief")

        # no_invented_text: todo texto visível ∈ copy ∪ chrome da marca ∪ tag/whitelist.
        allowed: set[str] = set(_CHROME_SHARED) | (_CHROME_TIAGO if is_tiago else _CHROME_METTA)
        for k in ("headline", "subhead", "body", "cta", "tag"):
            allowed |= set(_norm_words((copy.get(k) or "").replace("*", "")))
        for w in (copy.get("whitelist") or []):
            allowed |= set(_norm_words(str(w)))
        invented = sorted({w for w in vis_tokens
                           if w not in allowed and len(w) > 2 and not w.isdigit()})
        if invented:
            warnings.append(f"no_invented_text: texto visível fora da copy/whitelist: {invented[:10]}")
    else:
        # ── Guard text:none ──────────────────────────────────────────────────────
        # Modelo só-foto (text:none): a peça NÃO deve renderizar texto de copy — só o
        # chrome da marca (logo/assinatura). A foto já leva o negative anti-texto no
        # prompt da skill 04; este guard cobre o lado HTML/template, que antes era
        # pulado por inteiro pra image_only (qualquer texto vazava silencioso).
        vis_tokens = _norm_words(_visible_text(html))
        allowed: set[str] = set(_CHROME_SHARED) | (_CHROME_TIAGO if is_tiago else _CHROME_METTA)
        stray = sorted({w for w in vis_tokens
                        if w not in allowed and len(w) > 2 and not w.isdigit()})
        if stray:
            warnings.append(f"text_none_guard: modelo text:none deveria ser só-foto, mas há "
                            f"texto renderizado fora do chrome da marca: {stray[:10]}")

    status = "FAIL" if issues else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {"status": status, "issues": issues, "warnings": warnings}
