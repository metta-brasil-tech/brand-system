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

    # 1) Foto bleed full — SEMPRE inclui image_slot (skill 04 gera a foto DEPOIS,
    # template não recebe url ainda). Quando image_source='none' a skill 04 pula
    # e o assembler desenha placeholder. Frame.background cobre vazio.
    elements.append({
        "type": "image_slot",
        "slot_name": "foto_bleed",
        "x": 0, "y": 0, "width": W, "height": H,
        "image_prompt_ref": "image-prompts/tiago/style-story-cover-hero.md",
        "url_placeholder": "pending",
        # Gradient overlay escurece a base pros textos ficarem legíveis
        "overlay": "gradient-fade-to-black-bottom-60%",
    })

    headline = copy.get("headline", "").strip() or "Sua tese aqui"
    subhead = copy.get("subhead", "").strip()
    cta_text = (copy.get("cta", "").strip() or "Saiba mais").upper()

    # Hierarquia adaptativa: agrupa headline + subhead + CTA num bloco vertical
    # centralizado em y=1100 (ligeiramente abaixo do meio). Quando há foto, o
    # bloco fica visualmente "respirando" sobre ela. Sem foto, evita CTA órfão
    # lá no bottom enquanto o texto fica no meio.
    block_top = 720

    # 2) Headline — centralizada, grande, SF Pro Condensed Semibold
    elements.append({
        "type": "text",
        "slot_name": "headline",
        "text": headline,
        "x": 80, "y": block_top, "width": W - 160, "height": "auto",
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

    # Estima quantas linhas do headline (cada linha ~95px de altura com line-height 100%)
    # 90px size × 1.0 line-height. ~32 chars/linha em 920px width.
    headline_lines = max(1, (len(headline) // 32) + 1)
    headline_height_est = headline_lines * 95
    cursor_y = block_top + headline_height_est + 40

    # 3) Subhead opcional — logo abaixo do headline, SF Pro Light
    if subhead:
        elements.append({
            "type": "text",
            "slot_name": "subhead",
            "text": subhead,
            "x": 120, "y": cursor_y, "width": W - 240, "height": "auto",
            "font": {
                "family": "SF Pro",
                "style": "Light",
                "weight": 300,
                "stretch_pct": 100,
                "size": 40,
                "line_height_pct": 130,
                "letter_spacing_pct": 0,
                "text_case": "sentence",
            },
            "color": "#E5E5E5",
            "align": "center",
        })
        subhead_lines = max(1, (len(subhead) // 40) + 1)
        cursor_y += subhead_lines * 52 + 56
    else:
        cursor_y += 32

    # 4) CTA pill amarelo — LOGO ABAIXO do bloco de texto (não no bottom da peça)
    cta_width_est = min(700, max(280, len(cta_text) * 18 + 56))
    elements.append({
        "type": "pill_cta",
        "slot_name": "cta",
        "text": cta_text,
        "x": (W - cta_width_est) // 2, "y": cursor_y, "width": cta_width_est, "height": 80,
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
# TIAGO — FEED 1080x1350 EDITORIAL HERO
# ============================================================

def build_tiago_editorial_hero(briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Capa editorial Tiago tipo-revista — feed 4:5, bg claro com foto bleed atrás.

    Camadas (z-order do assembler):
    1. Foto bleed full (image_slot collage_main) — sempre presente
    2. Gradient overlay top→middle pra legibilidade do header e headline
    3. Eyebrows top-left/right (UPPER tracked)
    4. Assinatura Tiago entre eyebrows (post-processing via SIGNATURE_MODELS, cor escura)
    5. Headline GIGANTE Bold sentence ~y=580 (centro vertical), width 920 (não full)
    6. CTA pill amarelo bottom-left com texto do user
    """
    W, H = 1080, 1350
    elements: list[dict] = []

    # 1) Foto bleed FULL — image_slot pra skill 04 + image-gen preencher
    elements.append({
        "type": "image_slot",
        "slot_name": "collage_main",
        "x": 0, "y": 0, "width": W, "height": H,
        "image_prompt_ref": "image-prompts/tiago/style-editorial-collage.md",
        "url_placeholder": "pending",
        # Gradient escurece top + bottom pra legibilidade do header e CTA
        "overlay": "gradient-fade-to-white-top-25%",
    })

    headline = copy.get("headline", "").strip() or "Sua manchete editorial"
    cta_text = (copy.get("cta", "").strip() or "Arrasta pro lado").upper()

    # 2-3) Eyebrows top-left e top-right (fixos, identidade editorial)
    eyebrow_font = {
        "family": "SF Pro",
        "style": "Bold",
        "weight": 700,
        "stretch_pct": 100,
        "size": 22,
        "line_height_pct": 110,
        "letter_spacing_pct": 8,
        "text_case": "UPPER",
    }
    elements.append({
        "type": "text",
        "slot_name": "header_eyebrow_left",
        "text": "ESTRATÉGIAS DE GESTÃO DE VENDAS",
        "x": 64, "y": 56, "width": 480, "height": "auto",
        "font": eyebrow_font,
        "color": "#0F1419",
        "align": "left",
    })
    elements.append({
        "type": "text",
        "slot_name": "header_eyebrow_right",
        "text": "VENDAS É CIÊNCIA",
        "x": W - 64 - 320, "y": 56, "width": 320, "height": "auto",
        "font": eyebrow_font,
        "color": "#0F1419",
        "align": "right",
    })

    # (A assinatura header é aplicada pelo post-processing 06-signature
    # — config SIGNATURE_MODELS no api/generate.py: cor escura, top-center, y=40)

    # 4) Headline GIGANTE sentence case, centro vertical, largura controlada
    elements.append({
        "type": "text",
        "slot_name": "headline",
        "text": headline,
        "x": 80, "y": 560, "width": 920, "height": "auto",
        "font": {
            "family": "SF Pro",
            "style": "Bold",
            "weight": 800,
            "stretch_pct": 100,
            "size": 84,
            "line_height_pct": 95,
            "letter_spacing_pct": -2,
            "text_case": "sentence",
        },
        "color": "#0F1419",
        "align": "left",
    })

    # 5) CTA pill amarelo bottom-left
    cta_width_est = min(700, max(280, len(cta_text) * 18 + 56))
    elements.append({
        "type": "pill_cta",
        "slot_name": "cta",
        "text": cta_text,
        "x": 64, "y": H - 150, "width": cta_width_est, "height": 72,
        "padding_x": 28, "padding_y": 22,
        "background": "#FFCC00",
        "text_color": "#0F1419",
        "font": {
            "family": "SF Pro",
            "style": "Bold",
            "weight": 700,
            "stretch_pct": 100,
            "size": 24,
            "letter_spacing_pct": 4,
            "text_case": "UPPER",
        },
    })

    return {
        "model_id": "TIAGO-EDITORIAL-HERO",
        "frame": {"width": W, "height": H, "background": {"type": "solid", "value": "#EDEEEE"}},
        "elements": elements,
    }


# ============================================================
# TIAGO — TWITTER CARD (mock feed X/Twitter, FEED 1080×1350)
# ============================================================

import os as _os
from pathlib import Path as _Path

# Caminho do header mock como asset PNG (commitado no submodule engine/assets/).
# Quando existe: 1 image_slot com static_asset preenchido (pipeline pula skill 04).
# Quando NÃO existe: fallback pros 6 elements primitivos (placeholder "T").
_TWITTER_HEADER_ASSET = _Path(__file__).resolve().parent.parent / "engine" / "assets" / "twitter-header-tiago.png"


def _twitter_header_elements() -> list[dict]:
    """Header mock topo: avatar ring amarelo + foto Tiago + 'Tiago Alves' + verified + handle.

    Se o asset PNG existe em engine/assets/twitter-header-tiago.png, usa ele direto
    via image_slot com static_asset (renderizado fiel ao SVG do user). Senão, fallback
    pra primitivos Pillow (círculo amarelo + 'T' central + texto) — visual menos rico
    mas funcional.
    """
    if _TWITTER_HEADER_ASSET.exists():
        return [{
            "type": "image_slot",
            "slot_name": "twitter_header",
            "x": 0, "y": 60, "width": 1080, "height": 280,
            "static_asset": f"file://{_TWITTER_HEADER_ASSET}",
        }]
    # Fallback: primitivos quando o asset não foi commitado ainda
    return [
        {"type": "rect", "slot_name": "avatar_ring", "x": 64, "y": 80,
         "width": 160, "height": 160, "fill": "#FFCC00", "corner_radius": 80},
        {"type": "rect", "slot_name": "avatar_inner", "x": 74, "y": 90,
         "width": 140, "height": 140, "fill": "#0F1419", "corner_radius": 70},
        {"type": "text", "slot_name": "avatar_initial", "text": "T",
         "x": 74, "y": 105, "width": 140, "height": "auto",
         "font": {"family": "SF Pro", "style": "Bold", "weight": 800,
                  "stretch_pct": 100, "size": 88, "line_height_pct": 100,
                  "letter_spacing_pct": 0, "text_case": "sentence"},
         "color": "#FFCC00", "align": "center"},
        {"type": "text", "slot_name": "header_name", "text": "Tiago Alves",
         "x": 250, "y": 100, "width": 500, "height": "auto",
         "font": {"family": "SF Pro", "style": "Bold", "weight": 700,
                  "stretch_pct": 100, "size": 42, "line_height_pct": 110,
                  "letter_spacing_pct": -0.5, "text_case": "sentence"},
         "color": "#0F1419", "align": "left"},
        {"type": "rect", "slot_name": "verified_bg", "x": 530, "y": 105,
         "width": 36, "height": 36, "fill": "#1D9BF0", "corner_radius": 18},
        {"type": "text", "slot_name": "verified_check", "text": "✓",
         "x": 530, "y": 107, "width": 36, "height": "auto",
         "font": {"family": "SF Pro", "style": "Bold", "weight": 800,
                  "stretch_pct": 100, "size": 26, "line_height_pct": 100,
                  "letter_spacing_pct": 0, "text_case": "sentence"},
         "color": "#FFFFFF", "align": "center"},
        {"type": "text", "slot_name": "header_handle",
         "text": "@tiago.alves.oliveira",
         "x": 250, "y": 170, "width": 600, "height": "auto",
         "font": {"family": "SF Pro", "style": "Regular", "weight": 400,
                  "stretch_pct": 100, "size": 30, "line_height_pct": 120,
                  "letter_spacing_pct": 0, "text_case": "sentence"},
         "color": "#536471", "align": "left"},
    ]


def build_tiago_twitter_card_text(briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Twitter Card variant CONTENT — só texto, sem foto. Emoji transition opcional.

    Layout (1080×1350 feed branco):
    - Header mock topo (y=80..240)
    - Tweet headline bold sentence (y=320)
    - Tweet body regular opcional (logo abaixo)
    - Emoji transition bottom-left ("👉 ARRASTA PRO LADO" ou similar)
    """
    W, H = 1080, 1350
    elements = _twitter_header_elements()

    headline = copy.get("headline", "").strip() or "Sua tese provocativa"
    body = copy.get("subhead", "").strip()  # subhead = body do tweet
    cta_text = copy.get("cta", "").strip() or "Arrasta pro lado"

    # Tweet headline — Bold sentence case, NÃO upper (mock-twitter), preto
    elements.append({
        "type": "text", "slot_name": "tweet_headline", "text": headline,
        "x": 64, "y": 320, "width": W - 128, "height": "auto",
        "font": {"family": "SF Pro", "style": "Bold", "weight": 700,
                 "stretch_pct": 100, "size": 56, "line_height_pct": 125,
                 "letter_spacing_pct": -1, "text_case": "sentence"},
        "color": "#0F1419", "align": "left",
    })

    # Tweet body — Regular, espaçado abaixo do headline
    if body:
        # Estima 4 linhas pra headline ~30 chars/linha
        head_lines = max(1, (len(headline) // 30) + 1)
        body_y = 320 + head_lines * 70 + 40
        elements.append({
            "type": "text", "slot_name": "tweet_body", "text": body,
            "x": 64, "y": body_y, "width": W - 128, "height": "auto",
            "font": {"family": "SF Pro", "style": "Regular", "weight": 400,
                     "stretch_pct": 100, "size": 44, "line_height_pct": 140,
                     "letter_spacing_pct": -0.5, "text_case": "sentence"},
            "color": "#0F1419", "align": "left",
        })

    # Emoji transition bottom-left (NÃO é pill — só texto inline com 👉)
    cta_display = f"{cta_text} 👉" if not cta_text.endswith("👉") else cta_text
    elements.append({
        "type": "text", "slot_name": "transition", "text": cta_display,
        "x": 64, "y": H - 100, "width": W - 128, "height": "auto",
        "font": {"family": "SF Pro", "style": "Regular", "weight": 400,
                 "stretch_pct": 100, "size": 32, "line_height_pct": 100,
                 "letter_spacing_pct": 0, "text_case": "sentence"},
        "color": "#536471", "align": "left",
    })

    return {
        "model_id": "TIAGO-TWITTER-CARD",
        "frame": {"width": W, "height": H, "background": {"type": "solid", "value": "#FFFFFF"}},
        "elements": elements,
    }


def build_tiago_twitter_card_image(briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Twitter Card variant COVER — texto curto + foto embed radius 28px na base.

    Header mock topo + tweet headline curto + foto card 952×460 com cantos
    arredondados ocupando metade inferior. Sem CTA pill — foto é o ancoragem visual.
    """
    W, H = 1080, 1350
    elements = _twitter_header_elements()

    headline = copy.get("headline", "").strip() or "Sua tese provocativa"

    # Tweet headline mais curto (porque foto vai ocupar metade)
    elements.append({
        "type": "text", "slot_name": "tweet_headline", "text": headline,
        "x": 64, "y": 320, "width": W - 128, "height": "auto",
        "font": {"family": "SF Pro", "style": "Bold", "weight": 700,
                 "stretch_pct": 100, "size": 52, "line_height_pct": 125,
                 "letter_spacing_pct": -1, "text_case": "sentence"},
        "color": "#0F1419", "align": "left",
    })

    # Foto embed card (radius 28px) — image_slot bottom
    elements.append({
        "type": "image_slot", "slot_name": "media_embed",
        "x": 64, "y": 720, "width": W - 128, "height": 560,
        "image_prompt_ref": "image-prompts/tiago/style-twitter-card.md",
        "url_placeholder": "pending",
        "corner_radius": 28,
    })

    return {
        "model_id": "TIAGO-TWITTER-CARD-IMAGE",
        "frame": {"width": W, "height": H, "background": {"type": "solid", "value": "#FFFFFF"}},
        "elements": elements,
    }


# ============================================================
# Registry — modelos com template determinístico
# ============================================================
TEMPLATES = {
    "TIAGO-STORY-COVER-HERO":     build_tiago_story_cover_hero,
    "TIAGO-EDITORIAL-HERO":       build_tiago_editorial_hero,
    "TIAGO-TWITTER-CARD":         build_tiago_twitter_card_text,
    "TIAGO-TWITTER-CARD-IMAGE":   build_tiago_twitter_card_image,
    # TODO: adicionar restantes (TIAGO-STORY-YELLOW-BLOCK, TIAGO-STORY-MINIMAL-QUESTION,
    # TIAGO-TYPO-PURE, TIAGO-NOTES-MOCKUP, TIAGO-TWITTER-CARD, TIAGO-EDITORIAL-*, etc.
    # + 6 Metta) — uma função por modelo, calibradas individualmente.
}


def has_template(model_id: str) -> bool:
    return model_id in TEMPLATES


def build_layout(model_id: str, briefing: dict, copy: dict, image_url: str | None) -> dict:
    """Constrói layout-spec determinístico pra modelo. Raise KeyError se model_id não tem template."""
    return TEMPLATES[model_id](briefing, copy, image_url)
