"""Presets de estilo de foto pro gerador de ad.

Desacopla o estilo do AD (layout/tipografia/cor) do estilo da FOTO
(tratamento visual). Antes essa amarração causava: escolher ad LIGHT-SURREAL
→ foto SEMPRE surrealista. Escolher TIAGO-EDITORIAL-HERO → foto SEMPRE B&W
selective yellow. User não conseguia pedir "ad YELLOW-BLOCO com foto realista".

Cada preset é injetado no extra_context da skill 04 como TRATAMENTO PRIORITÁRIO,
acima do template do estilo do ad. Briefing visual textual do user continua
controlando o SUJEITO/CENA. Os dois acumulam.

Hierarquia final no prompt da skill 04:
  1. briefing_image_text (user) — SUJEITO/CENA
  2. image_style_preset (user) — TRATAMENTO (cores, mood, lighting)
  3. template do estilo do ad — FALLBACK quando preset não cobre
"""

PRESETS: dict[str, dict] = {
    "fotorrealista": {
        "id": "fotorrealista",
        "label": "Fotorrealista editorial",
        "desc": "Foto realista limpa estilo HBR/Bloomberg — natural, sem efeito heavy. Default seguro.",
        "preview_src": "/assets/photo-presets/fotorrealista.webp",
        "prompt_overlay": (
            "Style of treatment: PHOTOREALISTIC editorial photography. "
            "Natural full color, realistic skin tones, soft natural lighting, "
            "documentary business magazine quality. NO color grading effects, "
            "NO black and white, NO selective color highlights, NO surreal elements. "
            "Just clean professional editorial photography in natural colors."
        ),
        "negative_overlay": (
            "without black and white, without selective color, without monochrome, "
            "without surreal elements, without heavy color grading, without HDR look, "
            "without cinematic teal-orange grade"
        ),
    },
    "bw-yellow": {
        "id": "bw-yellow",
        "label": "P&B + amarelo selecionado",
        "desc": "Preto e branco editorial cinema com um detalhe amarelo destacado. Estilo TIAGO-EDITORIAL.",
        "preview_src": "/assets/photo-presets/bw-yellow.webp",
        "prompt_overlay": (
            "Style of treatment: high-contrast BLACK AND WHITE editorial cinema "
            "photography with ONE selective yellow element preserved in full color "
            "(a single object, a detail of clothing, or an accent in the scene). "
            "All other elements are monochrome black and white. Cinema editorial "
            "grade, deep blacks, sharp contrast, magazine cover quality."
        ),
        "negative_overlay": (
            "without full color photograph, without multiple color highlights, "
            "without colorized look, without sepia tone"
        ),
    },
    "surreal-hbr": {
        "id": "surreal-hbr",
        "label": "Surreal conceitual (HBR)",
        "desc": "Foto realista com objeto incongruente. Metáfora visual estilo Harvard Business Review.",
        "preview_src": "/assets/photo-presets/surreal-hbr.webp",
        "prompt_overlay": (
            "Style of treatment: SURREAL editorial conceptual photography in the "
            "style of Harvard Business Review or The New Yorker covers. Clean "
            "minimalist composition on a plain off-white background. Subject is a "
            "real photographed person but with one INCONGRUENT symbolic object "
            "added to the scene as visual metaphor (e.g., a stone where the head "
            "should be, a vintage CRT monitor as a head, heavy chains attached). "
            "Muted desaturated palette dominated by whites and neutral grays."
        ),
        "negative_overlay": (
            "without dark moody lighting, without cinematic teal grade, "
            "without children's book illustration, without cartoon, without 3D render look"
        ),
    },
    "cinematic-dark": {
        "id": "cinematic-dark",
        "label": "Cinematic dark moody",
        "desc": "Foto cinematográfica dark, chiaroscuro, drama. Tom Bloomberg Businessweek capa séria.",
        "preview_src": "/assets/photo-presets/cinematic-dark.webp",
        "prompt_overlay": (
            "Style of treatment: CINEMATIC DARK MOODY photography. Dramatic "
            "chiaroscuro lighting with half the scene in shadow, deep blacks, "
            "single warm light source, golden amber rim light. Editorial cinema "
            "quality, Bloomberg Businessweek cover gravitas, low-key palette "
            "dominated by dark teals, charcoal, and one warm amber highlight."
        ),
        "negative_overlay": (
            "without bright cheerful lighting, without flat even lighting, "
            "without pastel colors, without white background, without high-key look"
        ),
    },
}


def get_preset(preset_id: str | None) -> dict | None:
    """Retorna o preset pelo id, ou None se não existe."""
    if not preset_id:
        return None
    return PRESETS.get(preset_id.lower())


def list_presets() -> list[dict]:
    """Lista todos os presets pra o frontend renderizar cards."""
    return [
        {"id": p["id"], "label": p["label"], "desc": p["desc"], "preview_src": p["preview_src"]}
        for p in PRESETS.values()
    ]


def preset_to_extra_context(preset: dict) -> str:
    """Formata o preset como bloco pro extra_context da skill 04."""
    return (
        f"=== PRESET DE ESTILO DE FOTO ESCOLHIDO PELO USER (TRATAMENTO PRIORITÁRIO) ===\n"
        f"ID: {preset['id']} — {preset['label']}\n\n"
        f"TRATAMENTO VISUAL OBRIGATÓRIO PRA ESTA FOTO:\n{preset['prompt_overlay']}\n\n"
        f"ANTI-PADRÕES PRA ACUMULAR NO negative_prompt:\n{preset['negative_overlay']}\n\n"
        f"IMPORTANTE: esse preset SOBRESCREVE qualquer tratamento que o template do estilo do AD "
        f"sugira (ex: se o template do TIAGO-EDITORIAL-HERO pede 'B&W com selective yellow' mas o "
        f"preset do user é 'fotorrealista', a foto VAI ser fotorrealista — sem B&W, sem selective "
        f"yellow). O template do AD só ajuda no SUJEITO/CENA/composição, NUNCA no tratamento "
        f"visual quando há preset explícito."
    )
