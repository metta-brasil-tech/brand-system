"""Sistema de seleção de cor da assinatura Metta / Tiago Alves.

Dado o FUNDO onde a assinatura vai entrar, decide QUAL versão usar — como um
designer sênior faria: contraste primeiro, regra de marca por cima.

Base de verdade:
  - Cores reais das assinaturas (medidas nos SVGs).
  - DS `design/metta-logos.md §1 — Seleção de logo por fundo`.
  - Paleta dual da Metta: Yellow (#FFBE18) + Night (#0C161B).

Filosofia "2 principais + especiais":
  ┌───────────────────────────────────────────────────────────────────┐
  │ AS 2 QUE MAIS APARECEM (cobrem ~90% dos casos):                    │
  │   • ESCURO/night  #0C161B  → fundos CLAROS e AMARELOS              │
  │   • BRANCO         #FAFCFD  → fundos ESCUROS                       │
  │                                                                     │
  │ ESPECIAIS (situações pontuais):                                    │
  │   • AMARELO  #FFBE18  → só em fundo ESCURO, quando se quer o       │
  │                          acento de marca (pop), não o branco neutro│
  │   • CINZA             → assinatura que precisa RECUAR (marca       │
  │                          d'água / foto ocupada / co-branding sutil)│
  └───────────────────────────────────────────────────────────────────┘

Sem dependências externas — só stdlib. Importável e roda como demo (`__main__`).
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Cores reais de cada variante (fill medido no SVG) ───────────────────────
_METTA = {
    "escuro":  {"file": "assinatura_metta_azul.svg",    "color": "#0C161B"},  # night
    "branco":  {"file": "assinatura_metta_branco.svg",  "color": "#FAFCFD"},
    "amarelo": {"file": "assinatura_metta_amarelo.svg", "color": "#FFBE18"},
    "cinza":   {"file": "assinatura_metta_cinza.svg",   "color": "#435965"},  # steel
}
_TIAGO = {
    "escuro":  {"file": "assinatura-escuro.svg",  "color": "#0C161B"},
    "branco":  {"file": "assinatura-branco.svg",  "color": "#FAFCFD"},
    "amarelo": {"file": "assinatura-amarelo.svg", "color": "#FFBE18"},
    "cinza":   {"file": "assinatura-cinza.svg",   "color": "#A3BECC"},  # light steel
}

BRAND_YELLOW = "#FFBE18"
BRAND_NIGHT = "#0C161B"

# Um wordmark não é corpo de texto, mas precisa ler com folga. WCAG usa 3.0 pra
# objeto gráfico / texto grande; adotamos 3.0 como mínimo e 4.5 como confortável.
CONTRAST_MIN = 3.0
CONTRAST_OK = 4.5


# ── Matemática de cor (WCAG) ────────────────────────────────────────────────
def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    """Luminância relativa WCAG (0 = preto, 1 = branco)."""
    def _lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(hex_color)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(c1: str, c2: str) -> float:
    """Razão de contraste WCAG entre duas cores (1.0 a 21.0)."""
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _hsv(hex_color: str) -> tuple[float, float, float]:
    r, g, b = (x / 255.0 for x in _rgb(hex_color))
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / d) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / d) + 120) % 360
    else:
        h = (60 * ((r - g) / d) + 240) % 360
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx


def is_brand_yellow(hex_color: str) -> bool:
    """Fundo é da família do amarelo da marca? (hue âmbar + saturado + claro)."""
    h, s, v = _hsv(hex_color)
    return 35 <= h <= 55 and s >= 0.45 and v >= 0.7


# ── O sistema de decisão ────────────────────────────────────────────────────
@dataclass
class SignaturePick:
    variant: str        # 'escuro' | 'branco' | 'amarelo' | 'cinza'
    file: str           # nome do SVG
    color: str          # hex da tinta
    contrast: float     # contraste contra o fundo
    tier: str           # 'principal' | 'especial'
    reason: str         # porquê legível (auditável)
    warn: str | None = None  # aviso se contraste marginal


def pick_signature(bg_hex: str, *, brand: str = "metta", intent: str = "default") -> SignaturePick:
    """Escolhe a melhor assinatura pro fundo `bg_hex`.

    intent:
      'default' — o designer neutro: máxima legibilidade com a versão certa.
      'accent'  — quer o POP da marca (usa amarelo em fundo escuro).
      'subtle'  — assinatura discreta / marca d'água (usa cinza se aguentar).
    """
    palette = _TIAGO if brand.lower() in ("tiago", "tiago-alves", "thiago") else _METTA

    def make(variant: str, tier: str, reason: str) -> SignaturePick:
        info = palette[variant]
        cr = contrast_ratio(info["color"], bg_hex)
        warn = None
        if cr < CONTRAST_MIN:
            warn = (f"contraste {cr:.1f}:1 abaixo do mínimo {CONTRAST_MIN}:1 — "
                    f"aplique scrim/borda ou troque o fundo")
        elif cr < CONTRAST_OK:
            warn = f"contraste {cr:.1f}:1 ok, mas justo (confortável ≥ {CONTRAST_OK}:1)"
        return SignaturePick(variant, info["file"], info["color"], round(cr, 2), tier, reason, warn)

    yellow_bg = is_brand_yellow(bg_hex)
    lum = relative_luminance(bg_hex)

    # 1) FUNDO AMARELO — nunca amarelo-no-amarelo nem branco (contraste ruim).
    #    Regra DS: fundo amarelo → assinatura night. Sempre a principal escura.
    if yellow_bg:
        if intent == "subtle":
            return make("cinza", "especial", "fundo amarelo + pedido discreto → cinza (recua sem sumir)")
        return make("escuro", "principal", "fundo amarelo → night #0C161B (regra DS; branco/amarelo falham aqui)")

    # 2) FUNDO ESCURO — principal é BRANCO; especiais amarelo (pop) / cinza (recuo).
    if lum < 0.22:
        if intent == "accent":
            return make("amarelo", "especial", "fundo escuro + acento de marca → amarelo pop (#FFBE18)")
        if intent == "subtle":
            return make("cinza", "especial", "fundo escuro + discreto → cinza")
        return make("branco", "principal", "fundo escuro → branco #FAFCFD (workhorse, máx. legibilidade)")

    # 3) FUNDO CLARO — principal é ESCURO/night; especial cinza (recuo).
    if lum > 0.55:
        if intent == "subtle":
            return make("cinza", "especial", "fundo claro + discreto → cinza")
        return make("escuro", "principal", "fundo claro → night #0C161B (workhorse)")

    # 4) MEIO-TOM / FOTO / CINZA AMBÍGUO — decide pelo polo de MAIOR contraste
    #    e sinaliza se ficar justo (aí o certo é scrim).
    dark_cr = contrast_ratio(palette["escuro"]["color"], bg_hex)
    light_cr = contrast_ratio(palette["branco"]["color"], bg_hex)
    if light_cr >= dark_cr:
        p = make("branco", "principal", f"meio-tom → branco vence no contraste ({light_cr:.1f} vs {dark_cr:.1f})")
    else:
        p = make("escuro", "principal", f"meio-tom → night vence no contraste ({dark_cr:.1f} vs {light_cr:.1f})")
    return p


# ── Demo ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    casos = [
        ("#FFBE18", "Amarelo da marca (fundo mais comum)"),
        ("#FAFCFD", "Branco gelo (feed claro)"),
        ("#0C161B", "Night (fundo escuro editorial)"),
        ("#000000", "Preto puro"),
        ("#EBF3F7", "Gelo azulado (card claro)"),
        ("#435965", "Steel médio"),
        ("#808080", "Cinza 50% (foto ambígua)"),
    ]
    print(f"{'FUNDO':<9} {'variante':<9} {'tier':<10} {'contraste':<10} motivo")
    print("─" * 96)
    for bg, label in casos:
        for intent in ("default", "accent", "subtle"):
            p = pick_signature(bg, brand="metta", intent=intent)
            tag = "" if intent == "default" else f"[{intent}] "
            flag = f"  ⚠ {p.warn}" if p.warn else ""
            print(f"{bg:<9} {p.variant:<9} {p.tier:<10} {str(p.contrast)+':1':<10} {tag}{p.reason}{flag}")
        print()
