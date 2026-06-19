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


# ---------------------------------------------------------------------------
# Marca: logo Metta (símbolo + wordmark) / assinatura Tiago. SVGs em
# source/ad-blueprints/_brand/ (bundlados no deploy). Theme-aware:
#   dark/yellow → wordmark branco + símbolo amarelo · light/paper → wordmark escuro.
# Ligado por padrão; blueprint pode sobrescrever com param `brand`:
#   none | tl | tr | bl | br | center.
# ---------------------------------------------------------------------------
_BRAND_DIR = _BLUEPRINTS_DIR / "_brand"
_METTA_NO_BRAND = {"card-mock", "logo-wall"}                       # mock/UI falsa: sem logo
_METTA_COVER_ARCH = {"photo-full", "photo-side", "photo-band"}     # covers ganham eyebrow categoria
_TIAGO_SIG_ARCH = {"tiago-editorial-hero", "tiago-editorial-dark",
                   "tiago-editorial-card", "tiago-editorial-cta"}  # editoriais levam assinatura


def _brand_mark(marca: str, arch: str, theme: str, params: dict) -> str:
    pref = (params.get("brand") or "").strip().lower()
    if pref == "none":
        return ""
    is_tiago = str(marca).lower() == "tiago"
    if not pref:  # defaults por marca/archetype
        if is_tiago and arch not in _TIAGO_SIG_ARCH:
            return ""
        if not is_tiago and arch in _METTA_NO_BRAND:
            return ""
    dark = theme in ("dark", "yellow")
    if is_tiago:
        svg = _read(_BRAND_DIR / ("assinatura-branco.svg" if dark else "assinatura-escuro.svg"))
        # Editoriais levam a assinatura no TOPO (igual às refs de carrossel do Tiago);
        # hero entre as eyebrows (centro), os demais à direita. Outros archetypes: rodapé.
        cls = "brand-sig"
        default_pos = "center" if arch == "tiago-editorial-hero" else ("tr" if arch in _TIAGO_SIG_ARCH else "br")
    else:
        svg = _read(_BRAND_DIR / ("logo_metta_colorido_h.svg" if dark else "logo_metta_colorido_escuro_h.svg"))
        cls, default_pos = "brand-logo", "tl"
    if not svg:
        return ""
    pos = pref if pref in ("tl", "tr", "bl", "br", "center") else default_pos
    out = f'<div class="brand-mark {cls}" data-pos="{pos}">{svg}</div>'
    # Cover Metta: eyebrow de categoria no topo-direito (igual às refs)
    if not is_tiago and arch in _METTA_COVER_ARCH and pos == "tl":
        out += '<div class="brand-eyebrow" data-pos="tr">INTELIGÊNCIA COMERCIAL</div>'
    return out


def _photo(image_url: str, cls: str = "photo") -> str:
    if not image_url:
        return ""
    return f'<div class="{cls}" style="background-image:url(\'{image_url}\')"></div>'


def _br(text) -> str:
    """Escapa e converte quebras de linha em <br> (subhead/body Tiago)."""
    return _esc(text).replace("\n", "<br>")


def _markup_tiago(arch: str, copy: dict, params: dict, image_url: str) -> str:
    """Markup dos 12 estilos da marca Tiago — espelha os templates de referência
    em source/ad-templates/tiago/*. Headlines levam classe `t-head` (auto-fit do
    _engine.js encolhe copy longa) + a classe específica do estilo (visual)."""
    head = lambda cls: f'<h1 class="t-head {cls}">{_accent(copy.get("headline", ""))}</h1>'
    sub = lambda cls: f'<p class="{cls}">{_br(copy["subhead"])}</p>' if copy.get("subhead") else ""
    body = lambda cls: f'<p class="{cls}">{_br(copy["body"])}</p>' if copy.get("body") else ""
    photo = lambda cls: (f'<div class="{cls}" style="background-image:url(\'{image_url}\')"></div>'
                         if image_url else f'<div class="{cls}"></div>')

    if arch == "tiago-editorial-hero":
        cta = _esc(copy.get("cta") or "Arrasta pro lado")
        return (f'{photo("teh-photo")}'
                f'<div class="teh-eyebrows"><p class="teh-eyebrow-left">ESTRATÉGIAS DE GESTÃO DE VENDAS</p>'
                f'<p class="teh-eyebrow-right">VENDAS É CIÊNCIA</p></div>'
                f'<div class="teh-text layer">{head("teh-headline")}{sub("teh-subhead")}{body("teh-body")}</div>'
                f'<div class="teh-cta-wrap"><button class="ad-cta ad-cta--tiago-yellow">{cta}</button></div>')

    if arch == "tiago-editorial-dark":
        return (f'{photo("ted-photo")}<div class="ted-overlay"></div>'
                f'<div class="ted-text layer">{head("ted-headline")}{sub("ted-subhead")}{body("ted-body")}</div>')

    if arch == "tiago-editorial-card":
        return (f'{photo("tec-photo")}<div class="tec-overlay"></div>'
                f'<div class="tec-text layer">{head("tec-headline")}{sub("tec-subhead")}{body("tec-body")}</div>')

    if arch == "tiago-editorial-cta":
        cta = _esc(copy.get("cta") or "Saiba mais")
        return (f'<div class="tecta-text layer">{head("tecta-headline")}{sub("tecta-subhead")}{body("tecta-body")}</div>'
                f'<div class="tecta-cta-wrap"><button class="ad-cta ad-cta--tiago-yellow">{cta}</button></div>')

    if arch == "tiago-typo":
        cta = f'<p class="tt-cta">{_esc(copy["cta"])} 👉</p>' if copy.get("cta") else ""
        handle = '<p class="tt-handle">@tiago.alves.oliveira</p>'
        return (f'<div class="tt-text layer">{head("tt-headline")}{sub("tt-subhead")}{body("tt-body")}</div>'
                f'{cta}{handle}')

    if arch == "tiago-dark-surreal":
        return photo("tds-photo")

    if arch == "tiago-photo-raw":
        return photo("tpr-photo")

    if arch == "tiago-notes":
        # body multi-linha vira lista numerada (DNA do estilo); 1 linha vira parágrafo
        _lines = [l.strip() for l in (copy.get("body", "") or "").split("\n") if l.strip()]
        if len(_lines) > 1:
            body_html = '<ol class="tn-list">' + "".join(f"<li>{_esc(l)}</li>" for l in _lines) + "</ol>"
        elif _lines:
            body_html = f'<div class="tn-body">{_esc(_lines[0])}</div>'
        else:
            body_html = ""
        cta = f'<p class="tn-cta">{_esc(copy["cta"])} 👉</p>' if copy.get("cta") else ""
        return ('<div class="tn-phone">'
                '<div class="tn-statusbar"><span class="tn-time">9:41</span><span class="tn-icons">●●●●● 100%</span></div>'
                '<div class="tn-navbar"><span class="tn-back">‹ Notas</span>'
                '<span class="tn-actions"><span>…</span><span>OK</span></span></div>'
                f'<div class="tn-notes-body">{head("tn-headline")}{sub("tn-subhead")}{body_html}</div>'
                f'{cta}</div>')

    if arch == "tiago-story-hero":
        cta = _esc(copy.get("cta") or "Arrasta pro lado")
        return (f'{photo("tch-photo")}<div class="tch-scrim"></div>'
                f'<div class="tch-text layer">{head("tch-headline")}{sub("tch-subhead")}{body("tch-body")}</div>'
                f'<div class="tch-cta-wrap"><button class="ad-cta ad-cta--tiago-yellow">{cta}</button></div>')

    if arch == "tiago-story-yellow":
        cta = (f'<div class="tyb-cta-wrap"><button class="ad-cta ad-cta--tiago-yellow">{_esc(copy["cta"])}</button></div>'
               if copy.get("cta") else "")
        return (f'{photo("tyb-photo")}<div class="tyb-overlay"></div>'
                f'<div class="tyb-block layer">{head("tyb-headline")}{sub("tyb-subhead")}{body("tyb-body")}</div>'
                f'{cta}')

    if arch == "tiago-story-minimal":
        return (f'{photo("tmq-photo")}<div class="tmq-overlay"></div>'
                f'<div class="tmq-text layer">{head("tmq-headline")}{sub("tmq-subhead")}</div>')

    if arch == "tiago-twitter":
        cta = f'<p class="tw-cta">{_esc(copy["cta"])} 👉</p>' if copy.get("cta") else ""
        # Variant IMAGE: foto embed (radius 28px) na base quando há imagem.
        has_img = bool(image_url)
        embed = (f'<div class="tw-embed"><div class="tw-embed-photo" '
                 f'style="background-image:url(\'{image_url}\')"></div></div>') if has_img else ""
        txtcls = "tw-text tw-text--withimg" if has_img else "tw-text"
        return ('<header class="tw-header"><div class="tw-avatar"><span class="tw-avatar-initial">T</span></div>'
                '<div class="tw-user"><div class="tw-name-row"><span class="tw-name">Tiago Alves</span>'
                '<span class="tw-verified">✓</span></div>'
                '<span class="tw-handle">@tiago.alves.oliveira</span></div></header>'
                f'<div class="{txtcls}">{head("tw-headline")}{sub("tw-subhead")}{body("tw-body")}</div>'
                f'{cta}{embed}')

    # fallback Tiago desconhecido → tipográfico simples
    return f'<div class="tt-text layer">{head("tt-headline")}{sub("tt-subhead")}{body("tt-body")}</div>'


def _markup(arch: str, copy: dict, params: dict, image_url: str) -> str:
    if arch.startswith("tiago"):
        return _markup_tiago(arch, copy, params, image_url)

    cta_cls = "cta--dark" if params.get("cta") == "dark" else ("cta--outline" if params.get("cta") == "outline" else "")

    if arch == "typo":
        _div = bool(params.get("divider"))
        return f'<div class="layer"><div class="stack">{_txt_blocks(copy, divider=_div)}</div></div>{_cta(copy, cta_cls)}'

    if arch == "photo-side":
        block = params.get("block", "none")
        if block == "yellow":
            # DNA §4.5: bloco amarelo = headline + BULLETS (3-5). Body com várias
            # linhas (\n) vira lista de bullets; uma linha só vira parágrafo.
            parts = [f'<h1 class="t-head">{_accent(copy.get("headline",""))}</h1>']
            if copy.get("subhead"):
                parts.append(f'<p class="t-sub">{_esc(copy["subhead"])}</p>')
            _lines = [l.strip() for l in (copy.get("body","") or "").split("\n") if l.strip()]
            if len(_lines) > 1:
                parts.append('<ul class="bullets">' + "".join(f'<li>{_esc(l)}</li>' for l in _lines) + '</ul>')
            elif _lines:
                parts.append(f'<p class="t-body">{_esc(_lines[0])}</p>')
            return (f'{_photo(image_url)}'
                    f'<div class="layer"><div class="stack">{chr(10).join(parts)}</div></div>'
                    f'{_cta(copy, cta_cls)}')
        return (f'{_photo(image_url)}<div class="grad"></div>'
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
        # Card DARK (DNA Metta) tem palavra-accent amarela; card light (Twitter)
        # corre texto sem cor. Quebras (\n) sempre viram espaço (texto fluido).
        if params.get("theme") == "dark":
            head_plain = _accent(copy.get("headline", "").replace("\n", " "))
        else:
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

    if arch == "number-hero":
        # colagem PB no topo (opcional) + número gigante + sub/body + CTA
        return (f'{_photo(image_url)}'
                f'<div class="layer"><div class="stack">{_txt_blocks(copy)}</div>{_cta(copy, cta_cls)}</div>')

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
    orient = params.get("orient", "vertical")
    marca_attr = (fm.get("marca") or marca or "").strip().lower()
    brand = _brand_mark(marca_attr, arch, theme, params)
    data_attrs = (
        f'data-marca="{_esc(marca_attr)}" '
        f'data-case="{_esc(case)}" data-orient="{_esc(orient)}" '
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
{brand}
{inner}
</div>
<script>{js}</script>
</body></html>"""

    return {"html": doc, "model_id": model_id, "marca": marca, "format": format,
            "archetype": arch, "missing": False}
