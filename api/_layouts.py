"""Layout templates determinísticos por modelo.

Cada modelo tem uma função `build_*(briefing, headline, subhead, cta, image_url) -> dict`
que retorna o `layout_spec` JSON pronto pro assembler — sem passar pelo LLM.

Por que: skill 03 (layout-composer LLM) era estocástica — variava posição/hierarquia
a cada geração, quebrava o look do modelo. Templates Python são 100% previsíveis,
respeitam o YAML do modelo literalmente, e o LLM só gera conteúdo (headline/subhead).

Cada função recebe:
- briefing: dict do skill 01
- copy: dict { headline, subhead?, cta }
- image_url: URL (file://) ou None

Retorna: layout_spec compatível com layout-spec.schema.json
"""
from __future__ import annotations


# ============================================================
# TIAGO — STORY 1080x1920 (9:16)
# ============================================================

def build_tiago_story_cover_hero(briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Capa de story Tiago — foto bleed + headline grande centrada + subhead + CTA + signature.

    Hierarquia visual:
    1. Foto bleed full (background)
    2. Gradient scrim vertical (legibilidade do texto)
    3. Headline GRANDE SF Pro Condensed Semibold center-vertical center-horizontal
    4. Subhead abaixo, SF Pro Light arredondado, menor
    5. CTA pill amarelo bottom-center
    6. (Assinatura aplicada DEPOIS pelo post-processing — não está aqui)
    """
    W, H = 1080, 1920
    elements: list[dict] = []

    # 1) Foto bleed full (quando há image_url)
    if image_url:
        elements.append({
            "type": "image_slot",
            "slot_name": "foto_bleed",
            "x": 0, "y": 0, "width": W, "height": H,
            "image_prompt_ref": "image-prompts/tiago/style-story-cover-hero.md",
            "url_placeholder": "pending",
            # Gradient overlay top→bottom escurece pros textos ficarem legíveis
            "overlay": "gradient-fade-to-black-bottom-60%",
        })
    else:
        elements.append({
            "type": "rect",
            "slot_name": "bg_fallback",
            "x": 0, "y": 0, "width": W, "height": H,
            "fill": "#0C161B",
        })

    headline = copy.get("headline", "").strip() or "Sua tese aqui"
    subhead = copy.get("subhead", "").strip()
    cta_text = (copy.get("cta", "").strip() or "Saiba mais").upper()

    # 2) Headline — centralizada, grande, SF Pro Condensed Semibold
    # Tamanho: 90px caber em ~3 linhas de até 30 chars cada
    elements.append({
        "type": "text",
        "slot_name": "headline",
        "text": headline,
        "x": 80, "y": 700, "width": W - 160, "height": "auto",
        "font": {
            "family": "SF Pro Condensed",
            "style": "Semibold",
            "weight": 600,
            "stretch_pct": 75,
            "size": 90,
            "line_height_pct": 100,
            "letter_spacing_pct": -1,
            "text_case": "sentence",
        },
        "color": "#FFFFFF",
        "align": "center",
    })

    # 3) Subhead opcional — abaixo do headline, SF Pro Light, ~40% do tamanho
    if subhead:
        elements.append({
            "type": "text",
            "slot_name": "subhead",
            "text": subhead,
            "x": 120, "y": 1200, "width": W - 240, "height": "auto",
            "font": {
                "family": "SF Pro",
                "style": "Light",
                "weight": 300,
                "stretch_pct": 100,
                "size": 38,
                "line_height_pct": 130,
                "letter_spacing_pct": 0,
                "text_case": "sentence",
            },
            "color": "#E5E5E5",
            "align": "center",
        })

    # 4) CTA pill amarelo bottom-center
    # Calcular largura aproximada pra centralizar (estimativa: 18px por char + padding)
    cta_width_est = min(700, max(280, len(cta_text) * 18 + 56))
    elements.append({
        "type": "pill_cta",
        "slot_name": "cta",
        "text": cta_text,
        "x": (W - cta_width_est) // 2, "y": H - 220, "width": cta_width_est, "height": 80,
        "padding_x": 28, "padding_y": 24,
        "background": "#FFCC00",
        "text_color": "#0F1419",
        "font": {
            "family": "SF Pro",
            "style": "Semibold",
            "weight": 600,
            "stretch_pct": 100,
            "size": 26,
            "letter_spacing_pct": 4,
            "text_case": "UPPER",
        },
    })

    return {
        "model_id": "TIAGO-STORY-COVER-HERO",
        "frame": {"width": W, "height": H, "background": {"type": "solid", "value": "#000000"}},
        "elements": elements,
    }


# ============================================================
# Registry — modelos com template determinístico
# ============================================================
TEMPLATES = {
    "TIAGO-STORY-COVER-HERO": build_tiago_story_cover_hero,
    # TODO: adicionar restantes (TIAGO-STORY-YELLOW-BLOCK, TIAGO-STORY-MINIMAL-QUESTION,
    # TIAGO-TYPO-PURE, TIAGO-NOTES-MOCKUP, TIAGO-TWITTER-CARD, TIAGO-EDITORIAL-*, etc.
    # + 6 Metta) — uma função por modelo, calibradas individualmente.
}


def has_template(model_id: str) -> bool:
    return model_id in TEMPLATES


def build_layout(model_id: str, briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Constrói layout-spec determinístico pra modelo. Raise KeyError se model_id não tem template."""
    return TEMPLATES[model_id](briefing, copy, image_url)
