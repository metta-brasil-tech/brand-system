#!/usr/bin/env python3
"""Auditoria de consistência dos blueprints — FASE 1 (logo/marca visível).

Para cada blueprint que renderiza marca (logo Metta / assinatura Tiago), compara a
LUMINÂNCIA da wordmark com a do CANVAS atrás dela. Se as duas forem da mesma
luminância (escura sobre escuro ou clara sobre claro) a marca fica invisível →
FLAG. Era o bug do DARK-CARTA (theme paper ficou de fora do set de temas escuros).

Fonte única de verdade: importa `_theme_is_dark`/`_brand_is_light` e os sets de
presença de marca de `_blueprint_render` — a auditoria nunca diverge do render.

Limite honesto: em archetypes com FOTO atrás da marca a luminância depende da
imagem (não do theme). Esses não viram FLAG determinístico; são listados em
"revisar PNG". Use `params.brand_logo: light|dark` p/ fixar a cor quando preciso.

Uso:
    python3 api/_audit_blueprints.py            # tabela + total; exit!=0 se houver FLAG
    python3 api/_audit_blueprints.py --strict   # FLAG inclui também os de foto p/ revisão

Saída: tabela por blueprint + contagem. Exit code != 0 quando há FLAG
determinístico (vira teste de CI da FASE 1).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _blueprint_render as br  # noqa: E402

# --- luminância -------------------------------------------------------------
# Canvas sólido por theme (espelha _engine.css). Temas sem regra de CSS caem no
# bg default do .ad (= night-10, escuro), mas os archetypes Tiago sobrescrevem
# (ver _TIAGO_ARCH_BG abaixo), então o theme só decide o canvas pros archetypes
# de cor chapada da Metta.
_THEME_BG = {
    "dark":  "#0C161B",   # --m-night-10
    "paper": "#12201a",
    "light": "#EBF3F7",   # --m-night-95
    "yellow": "#FFBE18",  # --m-yellow
}
_DEFAULT_BG = "#0C161B"   # .ad bg default quando o theme não tem regra de CSS

# Archetypes Tiago definem o próprio fundo (vence o data-theme).
_TIAGO_ARCH_BG = {
    "tiago-editorial-hero": "#EDEEEE",  # --t-paper (claro)
    "tiago-editorial-card": "#EDEEEE",
    "tiago-editorial-cta":  "#EDEEEE",
    "tiago-editorial-dark": "#0F1419",  # --t-ink (escuro)
}

# Cor real das wordmarks (p/ comparar luminância com o canvas).
_MARK_LIGHT_HEX = "#FAFCFD"  # wordmark clara (logo_metta_colorido_h / assinatura-branco)
_MARK_DARK_HEX = "#0C161B"   # wordmark escura (logo_..._escuro_h / assinatura-escuro)

# Archetypes com FOTO atrás da marca → luminância depende da imagem (revisar PNG),
# não vira FLAG determinístico.
_PHOTO_ARCH = {
    "photo-full", "photo-side", "photo-band", "split",
    "tiago-editorial-hero", "tiago-editorial-card", "tiago-editorial-dark",
    "tiago-dark-surreal", "tiago-photo-raw", "tiago-story-hero",
    "tiago-story-yellow", "tiago-story-minimal", "tiago-twitter",
}


def _rel_luminance(hex_color: str) -> float:
    """Luminância relativa WCAG (0=preto, 1=branco)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _is_dark(hex_color: str) -> bool:
    return _rel_luminance(hex_color) < 0.5


def _renders_mark(marca: str, arch: str, params: dict) -> bool:
    """Replica a regra de presença de marca do `_brand_mark`."""
    pref = (params.get("brand") or "").strip().lower()
    if pref == "none":
        return False
    is_tiago = str(marca).lower() == "tiago"
    if not pref:
        if is_tiago and arch not in br._TIAGO_SIG_ARCH:
            return False
        if not is_tiago and arch in br._METTA_NO_BRAND:
            return False
    return True


def _canvas_hex(marca: str, arch: str, theme: str) -> str:
    if str(marca).lower() == "tiago" and arch in _TIAGO_ARCH_BG:
        return _TIAGO_ARCH_BG[arch]
    return _THEME_BG.get(str(theme).strip().lower(), _DEFAULT_BG)


def audit(strict: bool = False) -> int:
    rows = []
    flags = 0
    reviews = 0
    for marca_dir in sorted(d for d in br._BLUEPRINTS_DIR.iterdir()
                            if d.is_dir() and not d.name.startswith("_")):
        for bp in sorted(marca_dir.glob("*.md")):
            fm = br._parse_front_matter(br._read(bp))
            arch = fm.get("archetype", "typo")
            params = fm.get("params", {}) or {}
            theme = params.get("theme", "dark")
            marca = (fm.get("marca") or marca_dir.name or "").strip().lower()

            model = f"{marca_dir.name}/{bp.stem}"
            if not _renders_mark(marca, arch, params):
                rows.append((model, theme, arch, "—", "—", "sem marca", ""))
                continue

            mark_light = br._brand_is_light(theme, params)
            mark_hex = _MARK_LIGHT_HEX if mark_light else _MARK_DARK_HEX
            mark_lum = "clara" if mark_light else "escura"

            canvas = _canvas_hex(marca, arch, theme)
            canvas_dark = _is_dark(canvas)
            canvas_lum = "escuro" if canvas_dark else "claro"

            is_photo = arch in _PHOTO_ARCH
            collide = (mark_light and not canvas_dark) or (not mark_light and canvas_dark)

            if is_photo:
                status = "revisar(foto)"
                note = f"marca {mark_lum} sobre foto — conferir PNG"
                if strict and collide:
                    status, flags = "FLAG(foto)", flags + 1
                else:
                    reviews += 1
            elif collide:
                status = "FLAG"
                note = f"marca {mark_lum} sobre canvas {canvas_lum} ({canvas}) = invisível"
                flags += 1
            else:
                status = "ok"
                note = ""
            rows.append((model, theme, arch, mark_lum, canvas_lum, status, note))

    # tabela
    w = max(len(r[0]) for r in rows)
    print(f"{'BLUEPRINT':<{w}}  {'THEME':<8} {'ARCHETYPE':<22} {'MARCA':<7} {'CANVAS':<7} STATUS")
    print("-" * (w + 60))
    for model, theme, arch, mark_lum, canvas_lum, status, note in rows:
        line = f"{model:<{w}}  {theme:<8} {arch:<22} {mark_lum:<7} {canvas_lum:<7} {status}"
        if note:
            line += f"  · {note}"
        print(line)

    print("-" * (w + 60))
    print(f"{len(rows)} blueprints · {flags} FLAG · {reviews} revisar(foto)")
    if flags:
        print("\n✗ Auditoria reprovou: corrija o theme correto ou defina params.brand_logo.")
    else:
        print("\n✓ Sem FLAG determinístico. Revise os PNGs dos 'revisar(foto)'.")
    return 1 if flags else 0


if __name__ == "__main__":
    raise SystemExit(audit(strict="--strict" in sys.argv))
