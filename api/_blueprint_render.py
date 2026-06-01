"""Renderizador BLUEPRINT-DRIVEN (cria, não clona).

Lê um blueprint `source/ad-blueprints/{marca}/{id}.md`, parseia o front-matter
(archetype + params + slots), e monta HTML adaptativo via o motor
(`_engine.css` + `_engine.js`). Substitui o clone-and-fill de `_html_templates.py`.

API espelha _html_templates.render() pra ser drop-in no generate.py:
    render(marca, model_id, copy, image_url="", format="story") -> dict
"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BLUEPRINTS_DIR = _ROOT / "source" / "ad-blueprints"
if os.getenv("AD_BLUEPRINTS_DIR"):
    _BLUEPRINTS_DIR = Path(os.getenv("AD_BLUEPRINTS_DIR"))

_CACHE: dict[str, str] = {}


def _read(path: Path) -> str:
    k = str(path)
    if k not in _CACHE:
        _CACHE[k] = path.read_text(encoding="utf-8") if path.exists() else ""
    return _CACHE[k]


def _esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


# ---------------------------------------------------------------------------
# Front-matter parser (mínimo — suporta o subset usado nos blueprints).
# Aceita pyyaml se disponível; senão faz um parse leve de chaves + dict inline.
# ---------------------------------------------------------------------------
def _parse_front_matter(md: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", md, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(block) or {}
    except Exception:
        pass
    # Fallback leve: chave: valor + dict inline {a: b, c: d} + lista [a, b]
    out: dict = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        if line[0] in " \t":  # ignora aninhado no fallback
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("{") and val.endswith("}"):
            d = {}
            for pair in val[1:-1].split(","):
                if ":" in pair:
                    k2, v2 = pair.split(":", 1)
                    d[k2.strip()] = v2.strip().strip('"\'')
            out[key] = d
        elif val.startswith("[") and val.endswith("]"):
            out[key] = [x.strip().strip('"\'') for x in val[1:-1].split(",") if x.strip()]
        else:
            out[key] = val.strip('"\'')
    return out


def _accent(text: str) -> str:
    """Converte *palavra* em <span class="hi">palavra</span> e quebras de linha
    explícitas (\\n) em <br> — quebras são decisão de composição do Diretor de Arte."""
    esc = _esc(text)
    esc = re.sub(r"\*([^*]+)\*", r'<span class="hi">\1</span>', esc)
    return esc.replace("\n", "<br>")


# ---------------------------------------------------------------------------
# Markup por archetype — recebe (copy, params) e devolve o innerHTML do .ad
# ---------------------------------------------------------------------------
def _txt_blocks(copy: dict, head_accent=True, divider=False) -> str:
    head = _accent(copy.get("headline", "")) if head_accent else _esc(copy.get("headline", ""))
    parts = []
    if copy.get("tag"):
        parts.append(f'<p class="t-tag">{_esc(copy["tag"])}</p>')
    parts.append(f'<h1 class="t-head">{head}</h1>')
    if divider:  # divisor amarelo (assinatura do K) — depois da headline
        parts.append('<div class="t-divider"></div>')
    if copy.get("subhead"):
        parts.append(f'<p class="t-sub">{_esc(copy["subhead"])}</p>')
    if copy.get("body"):
        body = _esc(copy["body"]).replace("\n", "<br>")
        parts.append(f'<p class="t-body">{body}</p>')
    return "\n".join(parts)


def _cta(copy: dict, cls: str = "") -> str:
    if not copy.get("cta"):
        return ""
    return f'<div class="cta-wrap"><button class="cta {cls}">{_esc(copy["cta"])}</button></div>'


def _photo(image_url: str, cls: str = "photo") -> str:
    if not image_url:
        return ""
    return f'<div class="{cls}" style="background-image:url(\'{image_url}\')"></div>'


def _markup(arch: str, copy: dict, params: dict, image_url: str) -> str:
    cta_cls = "cta--dark" if params.get("cta") == "dark" else ("cta--outline" if params.get("cta") == "outline" else "")

    if arch == "typo":
        _div = bool(params.get("divider"))
        return f'<div class="layer"><div class="stack">{_txt_blocks(copy, divider=_div)}</div></div>{_cta(copy, cta_cls)}'

    if arch == "photo-side":
        block = params.get("block", "none")
        inner = f'{_photo(image_url)}<div class="grad"></div>' if block != "yellow" else _photo(image_url)
        return (f'{inner}'
                f'<div class="layer"><div class="stack">{_txt_blocks(copy)}</div></div>'
                f'{_cta(copy, cta_cls)}')

    if arch == "photo-full":
        return (f'{_photo(image_url)}<div class="grad"></div>'
                f'<div class="layer">{_txt_blocks(copy)}{_cta(copy, cta_cls)}</div>')

    if arch == "photo-band":
        return f'{_photo(image_url)}<div class="layer">{_txt_blocks(copy)}{_cta(copy, cta_cls)}</div>'

    if arch == "object-center":
        obj = _photo(image_url, "object")
        return f'<div class="layer">{obj}{_txt_blocks(copy)}{_cta(copy, cta_cls)}</div>'

    if arch == "card-mock":
        name = params.get("name", "Metta")
        handle = params.get("handle", "@metta.brasil")
        avatar = (name or "M")[0].upper()
        # Tweet mock NÃO tem palavra colorida nem quebra forçada — remove os
        # marcadores de accent (*) e quebras do Diretor de Arte (texto corre natural).
        head_plain = _esc(copy.get("headline", "").replace("*", "").replace("\n", " "))
        body = _esc(copy.get("body", "").replace("*", "")).replace("\n", "<br>")
        cta_line = f'<p class="t-body" style="color:#1D9BF0">{_esc(copy["cta"])} →</p>' if copy.get("cta") else ""
        return (f'<div class="card"><div class="mock-head"><div class="avatar">{avatar}</div>'
                f'<div class="who"><span class="name">{_esc(name)} <span class="verified">✔</span></span>'
                f'<span class="handle">{_esc(handle)}</span></div></div>'
                f'<h1 class="t-head">{head_plain}</h1>'
                f'{f"<p class=t-body>{body}</p>" if body else ""}{cta_line}</div>')

    if arch == "logo-wall":
        slots = "".join('<div class="slot">logo</div>' for _ in range(6))
        return (f'<div class="layer"><div class="stack">{_txt_blocks(copy)}</div>'
                f'<div class="wall">{slots}</div>{_cta(copy, cta_cls)}</div>')

    if arch == "framed":
        return f'<div class="frame"></div><div class="layer">{_txt_blocks(copy)}{_cta(copy, cta_cls)}</div>'

    if arch == "split":
        media = f'<div class="half-media" style="background-image:url(\'{image_url}\')"></div>' if image_url else '<div class="half-media"></div>'
        return (f'{media}<div class="half-text"><div class="stack">{_txt_blocks(copy)}</div>'
                f'{_cta(copy, cta_cls)}</div>')

    # fallback
    return f'<div class="layer"><div class="stack">{_txt_blocks(copy)}</div></div>{_cta(copy, cta_cls)}'


def _blueprint_path(marca: str, model_id: str) -> Path:
    return _BLUEPRINTS_DIR / marca / f"{model_id}.md"


def has_blueprint(marca: str, model_id: str) -> bool:
    return bool(marca and model_id and _blueprint_path(marca, model_id).exists())


def list_blueprints() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for d in _BLUEPRINTS_DIR.iterdir() if _BLUEPRINTS_DIR.exists() else []:
        if d.is_dir() and not d.name.startswith("_"):
            out[d.name] = sorted(p.stem for p in d.glob("*.md"))
    return out


def render(marca: str, model_id: str, copy: dict, image_url: str = "", format: str = "story") -> dict:
    bp_path = _blueprint_path(marca, model_id)
    if not bp_path.exists():
        return {"html": "", "model_id": model_id, "marca": marca, "format": format, "missing": True}

    fm = _parse_front_matter(_read(bp_path))
    arch = fm.get("archetype", "typo")
    params = fm.get("params", {}) or {}
    theme = params.get("theme", "dark")
    align = params.get("align", "left")
    scale = params.get("scale", "normal")
    photo = params.get("photo", "right-bleed")
    block = params.get("block", "none")
    anchor = params.get("anchor", "bottom")

    copy_clean = {k: (str(v).strip() if v else "") for k, v in (copy or {}).items()}
    inner = _markup(arch, copy_clean, params, image_url or "")

    head_style = params.get("head", "")
    case = params.get("case", "upper")
    data_attrs = (
        f'data-case="{_esc(case)}" '
        f'data-arch="{_esc(arch)}" data-theme="{_esc(theme)}" data-format="{_esc(format)}" '
        f'data-align="{_esc(align)}" data-scale="{_esc(scale)}" data-photo="{_esc(photo)}" '
        f'data-block="{_esc(block)}" data-anchor="{_esc(anchor)}" data-head="{_esc(head_style)}"'
    )

    fonts_css = _read(_BLUEPRINTS_DIR / "_fonts.css")
    css = _read(_BLUEPRINTS_DIR / "_engine.css")
    js = _read(_BLUEPRINTS_DIR / "_engine.js")

    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{_esc(model_id)}</title>
<style>{fonts_css}</style>
<style>{css}</style>
<style>body{{display:flex;justify-content:center;align-items:flex-start;}}</style>
</head><body>
<div class="ad ad-canvas" {data_attrs}>
{inner}
</div>
<script>{js}</script>
</body></html>"""

    return {"html": doc, "model_id": model_id, "marca": marca, "format": format,
            "archetype": arch, "missing": False}
