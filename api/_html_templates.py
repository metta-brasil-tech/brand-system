"""HTML template engine para ad-generator (substitui Pillow + api/_layouts.py).

Templates ficam em `source/ad-templates/{marca}/{model_id}.html` + `.css`.
Engine: carrega shell + tokens + CSS do modelo + HTML do modelo, hidrata
placeholders, retorna documento HTML completo pronto pra iframe srcdoc.

Hidratação minimalista (sem Jinja2/Mustache pra zero overhead):
  - {{var}}              → escapeHtml(value)
  - {{#has_field}}...{{/has_field}}  → bloco condicional (renderiza se truthy)

Conditional blocks evitam HTML vazio quando subhead/body são opcionais.
"""
from __future__ import annotations

import html
import re
from pathlib import Path


# Diretórios — relativos ao parent do api/ (brand-system root).
# No Vercel: __file__ = /var/task/api/_html_templates.py → parent.parent = /var/task
# Templates ficam em /var/task/source/ad-templates/ (incluídos via includeFiles
# do vercel.json — antes estavam excluídos pelo padrão de excludeFiles).
import os as _os
_BRAND_SYSTEM_ROOT = Path(__file__).resolve().parent.parent
_AD_TEMPLATES_DIR = _BRAND_SYSTEM_ROOT / "source" / "ad-templates"
# Override via env var pra dev/test
if _os.getenv("AD_TEMPLATES_DIR"):
    _AD_TEMPLATES_DIR = Path(_os.getenv("AD_TEMPLATES_DIR"))
_SHARED_CSS_PATH = _AD_TEMPLATES_DIR / "_shared.css"
_SHELL_PATH = _AD_TEMPLATES_DIR / "_preview-shell.html"


def templates_dir_path() -> str:
    """Debug helper — retorna o path absoluto onde estamos procurando templates."""
    return str(_AD_TEMPLATES_DIR)


def templates_dir_exists() -> bool:
    """Verifica se a pasta de templates está acessível no runtime."""
    return _AD_TEMPLATES_DIR.exists()


# Cache em memória — templates não mudam entre invocações na mesma instância
_FILE_CACHE: dict[str, str] = {}


def _read_cached(path: Path) -> str:
    key = str(path)
    if key not in _FILE_CACHE:
        if not path.exists():
            return ""
        _FILE_CACHE[key] = path.read_text(encoding="utf-8")
    return _FILE_CACHE[key]


def _escape(value: object) -> str:
    """HTML-escape com fallback pra string vazia."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _hydrate(template: str, ctx: dict) -> str:
    """Substitui {{var}} e {{#has_field}}...{{/has_field}} num template string.

    Conditionals processam-se ANTES de {{var}} pra não escapar tags do bloco.
    """
    # 1) Conditionals: {{#field}}...{{/field}}
    def replace_conditional(match):
        field = match.group(1)
        content = match.group(2)
        if ctx.get(field):
            return content
        return ""
    template = re.sub(
        r"\{\{#(\w+)\}\}([\s\S]*?)\{\{/\1\}\}",
        replace_conditional,
        template,
    )

    # 2) Simple vars: {{var}} OR {{var|default}} (default usado quando value falsy)
    def replace_var(match):
        token = match.group(1).strip()
        if "|" in token:
            key, default = token.split("|", 1)
            key = key.strip()
            default = default.strip()
        else:
            key, default = token, ""
        # `image_url` NÃO escapamos porque pode ser data:image/...;base64,...
        # que vira inutilizável se escapado. CSS url() já está em string com aspas.
        value = ctx.get(key, "")
        if not value:
            value = default
        if key in ("image_url", "image_data_uri"):
            return str(value)
        return _escape(value)
    # Token regex: \w (var name) + opcional |default sem }} (qualquer char exceto })
    return re.sub(r"\{\{(\w+(?:\|[^}]+)?)\}\}", replace_var, template)


def has_template(marca: str, model_id: str) -> bool:
    """Retorna True se o modelo tem template HTML disponível."""
    if not marca or not model_id:
        return False
    tpl_path = _AD_TEMPLATES_DIR / marca / f"{model_id}.html"
    return tpl_path.exists()


def render(
    marca: str,
    model_id: str,
    copy: dict,
    image_url: str = "",
    format: str = "story",
) -> dict:
    """Renderiza o ad como HTML completo pronto pra iframe.

    Args:
        marca: "metta" | "tiago"
        model_id: ID do modelo (bate com nome do arquivo HTML)
        copy: dict com headline, subhead, body, cta, tag (opcional)
        image_url: URL ou data: URI da foto (opcional pros modelos sem image)
        format: "story" | "feed" | "sqr"

    Returns:
        dict com keys:
          - html: documento HTML completo (pra iframe srcdoc ou window.write)
          - model_id, marca, format: metadados
          - missing: True se template não existir, False senão
    """
    tpl_html_path = _AD_TEMPLATES_DIR / marca / f"{model_id}.html"
    tpl_css_path = _AD_TEMPLATES_DIR / marca / f"{model_id}.css"

    if not tpl_html_path.exists():
        return {
            "html": "",
            "model_id": model_id,
            "marca": marca,
            "format": format,
            "missing": True,
        }

    # Carrega componentes
    shared_css = _read_cached(_SHARED_CSS_PATH)
    model_css = _read_cached(tpl_css_path)
    model_html = _read_cached(tpl_html_path)
    shell = _read_cached(_SHELL_PATH)

    # Hidrata contexto pra o template do modelo
    headline = (copy.get("headline") or "").strip()
    subhead = (copy.get("subhead") or "").strip()
    body = (copy.get("body") or "").strip()
    cta = (copy.get("cta") or "").strip()
    tag = (copy.get("tag") or "").strip()

    ctx = {
        "headline": headline,
        "subhead": subhead,
        "body": body,
        "cta": cta,
        "tag": tag,
        "image_url": image_url or "",
        "format": format,
        # Truthy flags pros conditionals
        "has_subhead": bool(subhead),
        "has_body": bool(body),
        "has_cta": bool(cta),
        "has_tag": bool(tag),
        "has_image": bool(image_url),
    }

    ad_html = _hydrate(model_html, ctx)

    # Monta shell — substitui placeholders no envelope
    document = shell.replace("/*__SHARED_CSS__*/", shared_css)
    document = document.replace("/*__MODEL_CSS__*/", model_css)
    document = document.replace("<!--__AD_HTML__-->", ad_html)

    return {
        "html": document,
        "model_id": model_id,
        "marca": marca,
        "format": format,
        "missing": False,
    }


def list_templates() -> dict[str, list[str]]:
    """Lista todos os templates HTML disponíveis, agrupados por marca."""
    out: dict[str, list[str]] = {"metta": [], "tiago": []}
    for marca_dir in _AD_TEMPLATES_DIR.iterdir():
        if not marca_dir.is_dir() or marca_dir.name.startswith("_"):
            continue
        for f in sorted(marca_dir.glob("*.html")):
            out.setdefault(marca_dir.name, []).append(f.stem)
    return out
