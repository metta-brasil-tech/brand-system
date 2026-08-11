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


def _no_dash(text: str) -> str:
    """Regra dura (Nathan): NUNCA travessão/traço-separador na copy — o em-dash '—'
    tem cara de texto de IA. Vira vírgula. NÃO toca hífen intra-palavra (bem-vindo,
    DEMONSTRA-SE): só em/en dash e hífen cercado por espaços (usado como separador)."""
    if not isinstance(text, str) or not text:
        return text
    t = re.sub(r"\s*[—–]\s*", ", ", text)          # travessão (em/en dash) → vírgula
    t = re.sub(r"(?<=\w)\s+-\s+(?=\w)", ", ", t)    # hífen SEPARADOR (com espaços) → vírgula
    t = re.sub(r"^[\s,]+", "", t)                    # sem vírgula órfã no início
    t = re.sub(r"\s*,\s*,", ",", t)                  # colapsa vírgula dupla
    return t


def _accent(text: str) -> str:
    """Converte *palavra* em <span class="hi">palavra</span> e quebras de linha
    explícitas (\\n) em <br> — quebras são decisão de composição do Diretor de Arte.

    Sem marcador nenhum (diretor de arte off ou omisso), headline de 3+ palavras
    ganha a ÚLTIMA palavra em destaque — no banco real a peça tipográfica sempre
    tem 1-2 palavras em amarelo; toda branca é peça sem assinatura Metta."""
    if "*" not in text and len(text.split()) >= 3:
        parts = text.rstrip().rsplit(" ", 1)
        if len(parts) == 2 and parts[1]:
            text = f"{parts[0]} *{parts[1]}*"
    esc = _esc(text)
    # Hífen NÃO-QUEBRÁVEL (U+2011) dentro de palavras (ex: DEMONSTRA-SE): impede a
    # quebra feia no hífen que partia a palavra E o realce amarelo em duas caixas.
    # Com a palavra inteira, o auto-fit (fitHead) detecta o estouro de largura e
    # encolhe a fonte até caber — assim o accent nunca quebra no meio.
    esc = re.sub(r"(?<=\w)-(?=\w)", "‑", esc)
    esc = re.sub(r"\*([^*]+)\*", r'<span class="hi">\1</span>', esc)
    return esc.replace("\n", "<br>")


def _embed_aspect(image_url: str, ar_min: float = 0.52, ar_max: float = 1.30):
    """Mede W×H da imagem embed do tweet e devolve (w, h) inteiros pro
    aspect-ratio do CSS, CLAMPADO estilo Twitter (muito wide → ~1.91:1; muito
    tall → ~4:5). Assim a foto aparece na proporção dela em vez de esticar.
    None se não der pra medir (o CSS cai no fallback)."""
    if not image_url:
        return None
    try:
        import base64 as _b64, io as _io
        from PIL import Image as _Image
        if image_url.startswith("data:"):
            im = _Image.open(_io.BytesIO(_b64.b64decode(image_url.split(",", 1)[1])))
        else:
            p = Path(image_url)
            if not p.exists():
                return None
            im = _Image.open(p)
        w, h = im.size
        if not w or not h:
            return None
        ar = max(ar_min, min(ar_max, h / w))
        return (1000, int(round(1000 * ar)))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Markup por archetype — recebe (copy, params) e devolve o innerHTML do .ad
# ---------------------------------------------------------------------------
def _txt_blocks(copy: dict, head_accent=True, divider=False,
                only_head=False, skip_head=False) -> str:
    """Blocos de texto. only_head=só a headline (+tag); skip_head=tudo menos a
    headline (pro layout de 2 zonas: headline na foto + apoio no card)."""
    head = _accent(copy.get("headline", "")) if head_accent else _esc(copy.get("headline", ""))
    parts = []
    if not skip_head:
        if copy.get("tag"):
            parts.append(f'<p class="t-tag">{_esc(copy["tag"])}</p>')
        parts.append(f'<h1 class="t-head">{head}</h1>')
        if divider:  # divisor amarelo (assinatura do K) — depois da headline
            parts.append('<div class="t-divider"></div>')
        if only_head:
            return "\n".join(parts)
    elif copy.get("tag"):  # sem headline mas com tag → tag encabeça o card
        parts.append(f'<p class="t-tag">{_esc(copy["tag"])}</p>')
    if copy.get("subhead"):
        parts.append(f'<p class="t-sub">{_esc(copy["subhead"])}</p>')
    if copy.get("body"):
        body = _esc(copy["body"]).replace("\n", "<br>")
        parts.append(f'<p class="t-body">{body}</p>')
    # Chip de prova emoldurado (assinatura convite/60-min real): SÓ quando tem
    # legenda ("valor | legenda") vira caixinha com borda no fluxo. Prova simples
    # (sem "|") segue como linha no rodapé (_proof_line, estilo extraia).
    if copy.get("proof") and "|" in str(copy["proof"]):
        _pv, _, _pc = str(copy["proof"]).partition("|")
        _cap = f'<span class="proof-cap">{_esc(_pc.strip())}</span>' if _pc.strip() else ""
        parts.append(f'<div class="proof-chip"><span class="proof-val">{_esc(_pv.strip())}</span>{_cap}</div>')
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
_TIAGO_SIG_DIR = _ROOT / "assets" / "tiago" / "assinatura"

# Fundo aproximado por tema, pra o sistema de assinatura decidir a variante.
# Fundo real de cada tema — usado pra escolher a cor da assinatura por CONTRASTE.
# Faltavam offwhite/white/photo: caíam no fallback dark → assinatura BRANCA em fundo
# claro (bug do editorial-hero/cta: assinatura sumindo). offwhite/white = claro →
# assinatura night; paper (DARK-CARTA) é escuro esverdeado; photo = tratado dark.
_THEME_BG = {"dark": "#0C161B", "light": "#FAFCFD", "yellow": "#FFBE18", "paper": "#12201A",
             "offwhite": "#EDEEEE", "white": "#FFFFFF", "photo": "#0C161B"}

try:  # sistema contrast-aware de seleção de assinatura (opcional; fallback binário)
    from _brand_signature import pick_signature as _pick_signature
except Exception:  # pragma: no cover
    _pick_signature = None


def _pick_sig(bg_hex: str, marca: str, intent: str = "default"):
    """Escolhe a variante de assinatura/logo pro fundo. None → cai no binário."""
    if _pick_signature is None:
        return None
    try:
        return _pick_signature(bg_hex, brand=str(marca), intent=intent)
    except Exception:
        return None
_METTA_NO_BRAND = {"card-mock", "logo-wall"}                       # mock/UI falsa: sem logo
_METTA_COVER_ARCH = {"photo-full", "photo-side", "photo-band", "photo-versus"}  # covers ganham eyebrow categoria
_TIAGO_SIG_ARCH = {"tiago-editorial-hero", "tiago-editorial-dark",
                   "tiago-editorial-card", "tiago-editorial-cta"}  # editoriais levam assinatura


_TIAGO_AVATAR_CACHE: str | None = None


def _tiago_avatar() -> str:
    """Data URI do avatar (rosto) do Tiago pro header do mock-tweet. '' se ausente."""
    global _TIAGO_AVATAR_CACHE
    if _TIAGO_AVATAR_CACHE is None:
        import base64
        p = _BRAND_DIR / "tiago-avatar.png"
        try:
            _TIAGO_AVATAR_CACHE = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        except Exception:
            _TIAGO_AVATAR_CACHE = ""
    return _TIAGO_AVATAR_CACHE


_METTA_SYMBOL_CACHE = None
def _metta_symbol() -> str:
    """SVG do símbolo real da Metta — avatar do tweet (não a letra 'M')."""
    global _METTA_SYMBOL_CACHE
    if _METTA_SYMBOL_CACHE is None:
        # _brand PRIMEIRO: é o único caminho presente no bundle da Vercel
        # (assets/** fica fora — excludeFiles tem teto de 256 chars, não dá
        # pra enumerar exceções). assets/ segue como fallback pro dev local.
        for p in (_BRAND_DIR / "simbolo_metta_amarelo.svg",
                  _ROOT / "assets" / "symbols" / "simbolo_metta_amarelo.svg"):
            try:
                _METTA_SYMBOL_CACHE = p.read_text(encoding="utf-8")
                break
            except Exception:
                _METTA_SYMBOL_CACHE = ""
    return _METTA_SYMBOL_CACHE


# ---------------------------------------------------------------------------
# Tweet-card REAL — o que separa um "card com avatar" de um PRINT de tweet:
# selo verificado de verdade (dourado = organização no X → Metta; azul = pessoa
# → Tiago), logo do X no canto, linha de timestamp + Visualizações e a barra de
# engajamento com números plausíveis. Ícones = a UI real do X sendo replicada
# (mock de interface, não decoração — não conta como ícone-de-biblioteca do
# anti-slop). Números FAKE mas determinísticos pela copy: a mesma peça
# re-renderizada mantém os números; peças diferentes variam.
# ---------------------------------------------------------------------------
_VERIFIED_SEAL = (
    '<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="6" fill="#fff"/>'
    '<path fill="{fill}" fill-rule="evenodd" d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z"/></svg>')
_X_LOGO = (
    '<svg class="x-logo" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" '
    'd="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>')
# ícones reais de status bar iOS (sinal/wifi/bateria) — mock de UI real,
# feedback Sofia: texto de bolinhas ("●●●●") não parece uma status bar real.
_IOS_SIGNAL = (
    '<svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor" aria-hidden="true">'
    '<rect x="0" y="7" width="3" height="5" rx="0.8"/><rect x="4.5" y="5" width="3" height="7" rx="0.8"/>'
    '<rect x="9" y="3" width="3" height="9" rx="0.8"/><rect x="13.5" y="0.5" width="3" height="11.5" rx="0.8"/></svg>')
_IOS_WIFI = (
    '<svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor" aria-hidden="true">'
    '<path d="M8 11.3a1.3 1.3 0 1 1 0-2.6 1.3 1.3 0 0 1 0 2.6zM8 6.2c1.7 0 3.2.6 4.4 1.7l-1.4 1.5A4.3 4.3 0 0 0 8 8.2c-1.2 0-2.2.4-3 1.2L3.6 7.9A6.3 6.3 0 0 1 8 6.2zm0-4.2c3 0 5.7 1.1 7.8 3l-1.4 1.5A9 9 0 0 0 8 4.3a9 9 0 0 0-6.4 2.2L.2 5C2.3 3.1 5 2 8 2z"/></svg>')
_IOS_BATTERY = (
    '<svg width="25" height="12" viewBox="0 0 25 12" fill="none" aria-hidden="true">'
    '<rect x="0.75" y="0.75" width="20.5" height="10.5" rx="2.5" stroke="currentColor" stroke-opacity="0.4"/>'
    '<rect x="2.25" y="2.25" width="17.5" height="7.5" rx="1.3" fill="currentColor"/>'
    '<rect x="22.5" y="4" width="1.5" height="4" rx="0.7" fill="currentColor" fill-opacity="0.4"/></svg>')
# ── ORNAMENTOS decorativos (SVG inline, camada ATRÁS do texto) ──────────────
# Recurso definidor de estilos cujo YAML pede um elemento visual que NÃO é foto
# gerada (grátis, re-renderável, legível). Ativados por params.ornament no
# blueprint. Ficam em .ad-ornament (z-index 0); o texto (.layer) fica acima.
# carta-selo (DARK-CARTA): motivo de carta/contrato em ângulo + selo M de cera.
_CARTA_DOC = (
    '<svg class="carta-doc" viewBox="0 0 400 300" fill="none" stroke="#ffffff" '
    'stroke-width="2" stroke-linecap="round">'
    '<g transform="rotate(-5 200 150)">'
    '<rect x="62" y="18" width="276" height="264" rx="6"/>'
    '<line x1="92" y1="66" x2="308" y2="66"/><line x1="92" y1="96" x2="308" y2="96"/>'
    '<line x1="92" y1="126" x2="286" y2="126"/><line x1="92" y1="156" x2="308" y2="156"/>'
    '<line x1="92" y1="186" x2="254" y2="186"/>'
    '<path d="M96 244 q22 -20 44 0 t44 0 t44 0" stroke-width="3"/>'
    '</g></svg>')
_CARTA_SEAL = (
    '<svg class="carta-seal" viewBox="0 0 100 100" aria-hidden="true">'
    '<circle cx="50" cy="50" r="45" fill="#FFBE18"/>'
    '<circle cx="50" cy="50" r="45" fill="none" stroke="#0C161B" stroke-opacity="0.28" stroke-width="1.5"/>'
    '<circle cx="50" cy="50" r="36" fill="none" stroke="#0C161B" stroke-opacity="0.55" '
    'stroke-width="2" stroke-dasharray="2 4.2"/>'
    '<text x="50" y="51" font-family="Inter, Arial, sans-serif" font-weight="900" '
    'font-size="48" fill="#0C161B" text-anchor="middle" dominant-baseline="central">M</text>'
    '</svg>')
# draw (YELLOW-DRAW): ilustração hand-drawn (curva de crescimento + seta) com
# wobble de traço via filtro de deslocamento — leveza editorial, não cartoon.
_DRAW_ILLO = (
    '<svg class="draw-illo" viewBox="0 0 600 240" fill="none" stroke="#0C161B" '
    'stroke-width="7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<filter id="orn-rough" x="-5%" y="-5%" width="110%" height="110%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.013" numOctaves="2" seed="7" result="n"/>'
    '<feDisplacementMap in="SourceGraphic" in2="n" scale="6"/></filter>'
    '<g filter="url(#orn-rough)">'
    '<path d="M60 205 L560 205" stroke-opacity="0.5"/>'
    '<path d="M78 216 L78 40" stroke-opacity="0.5"/>'
    '<path d="M92 188 C180 178 226 150 286 150 S372 118 420 92 S506 66 548 42"/>'
    '<path d="M548 42 l-36 6 M548 42 l-7 35"/>'
    '<path d="M150 205 l0 11 M260 205 l0 11 M370 205 l0 11 M470 205 l0 11" '
    'stroke-opacity="0.38" stroke-width="4"/>'
    '</g></svg>')

def _ornament(name: str, theme: str = "") -> str:
    """HTML da camada de ornamento decorativo p/ o model_id, ou '' se não houver.
    Fica ATRÁS do texto (CSS z-index). Best-effort: nome desconhecido → sem nada."""
    name = (name or "").strip().lower()
    if name == "carta-selo":
        return ('<div class="ad-ornament ad-ornament--carta" aria-hidden="true">'
                f'{_CARTA_DOC}{_CARTA_SEAL}</div>')
    if name == "draw":
        return ('<div class="ad-ornament ad-ornament--draw" aria-hidden="true">'
                f'{_DRAW_ILLO}</div>')
    return ""

_ICO = {  # ícones de ação do X (stroke, minimal — legíveis em print pequeno)
    "reply": '<svg viewBox="0 0 24 24"><path d="M21 11.3c0 3.7-3.8 6.7-8.5 6.7-.9 0-1.8-.1-2.6-.3L5.2 20l1.2-3.1C4.6 15.7 3.5 13.6 3.5 11.3 3.5 7.6 7.4 4.6 12 4.6s9 3 9 6.7z"/></svg>',
    "repost": '<svg viewBox="0 0 24 24"><path d="M7 8h8.5a3 3 0 0 1 3 3v1.5M17 16.5H8.5a3 3 0 0 1-3-3V12"/><path d="M15.5 5.5 18.5 8l-3 2.5M9 19l-3-2.5 3-2.5"/></svg>',
    "like": '<svg viewBox="0 0 24 24"><path d="M12 19.5s-7-4.3-8.7-8.4C2.2 8.4 4 5.5 6.9 5.5c2 0 3.3 1 4.1 2.4h2c.8-1.4 2.1-2.4 4.1-2.4 2.9 0 4.7 2.9 3.6 5.6-1.7 4.1-8.7 8.4-8.7 8.4z"/></svg>',
    "bookmark": '<svg viewBox="0 0 24 24"><path d="M7 4.5h10a.8.8 0 0 1 .8.8V20l-5.8-4-5.8 4V5.3a.8.8 0 0 1 .8-.8z"/></svg>',
    "share": '<svg viewBox="0 0 24 24"><path d="M12 14.5V4M8.5 7.5 12 4l3.5 3.5M5 12.5V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19v-6.5"/></svg>',
}


def _fmt_compact_ptbr(n: int) -> str:
    """1234 → '1,2 mil' · 2_400_000 → '2,4 mi' (formato compacto do X em pt-BR)."""
    def _one(v: float, suf: str) -> str:
        s = f"{v:.1f}".replace(".", ",")
        s = s[:-2] if s.endswith(",0") else s
        return f"{s} {suf}"
    if n >= 1_000_000:
        return _one(n / 1_000_000, "mi")
    if n >= 1_000:
        return _one(n / 1_000, "mil")
    return str(n)


def _tweet_metrics(seed: str) -> dict:
    """Timestamp + engajamento plausível (replies << reposts < likes << views),
    derivados por hash da copy — estáveis por peça, variados entre peças."""
    import hashlib
    from datetime import datetime, timedelta
    h = int(hashlib.sha1((seed or "metta").encode("utf-8")).hexdigest(), 16)
    likes = 400 + h % 4200
    reposts = max(8, int(likes * (0.16 + ((h >> 8) % 100) / 800)))
    replies = max(3, int(likes * (0.04 + ((h >> 16) % 50) / 1000)))
    views = likes * (60 + (h >> 24) % 90)
    dt = datetime.now() - timedelta(days=1 + (h >> 32) % 6, hours=(h >> 40) % 13)
    meses = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
    return {
        "stamp": f"{dt.hour:02d}:{dt.minute:02d} · {dt.day} de {meses[dt.month - 1]} de {dt.strftime('%y')}",
        "replies": _fmt_compact_ptbr(replies), "reposts": _fmt_compact_ptbr(reposts),
        "likes": _fmt_compact_ptbr(likes), "views": _fmt_compact_ptbr(views),
    }


def _tweet_proof(mx: dict, prefix: str) -> str:
    """Linha de meta (timestamp · views) + barra de engajamento (layout do print
    de detalhe do X: views só na meta; bookmark/share sem contagem). `prefix` = mock|tw."""
    eng = (f'<span class="eng">{_ICO["reply"]}<i>{mx["replies"]}</i></span>'
           f'<span class="eng">{_ICO["repost"]}<i>{mx["reposts"]}</i></span>'
           f'<span class="eng">{_ICO["like"]}<i>{mx["likes"]}</i></span>'
           f'<span class="eng">{_ICO["bookmark"]}</span>'
           f'<span class="eng">{_ICO["share"]}</span>')
    return (f'<div class="{prefix}-meta">{mx["stamp"]} · <b>{mx["views"]}</b> Visualizações</div>'
            f'<div class="{prefix}-engage">{eng}</div>')


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
    # Cor da assinatura/logo pelo FUNDO — sistema contrast-aware (_brand_signature),
    # não mais binário. Nos casos comuns escolhe a mesma versão que antes (sem
    # regressão), mas pela razão certa: corrige "paper" (fundo escuro) e habilita os
    # especiais amarelo/cinza quando params.sig_intent = "accent"/"subtle".
    bg_hex = _THEME_BG.get(str(theme).lower(), _THEME_BG["dark"])
    intent = str(params.get("sig_intent") or "default").strip().lower()
    pick = _pick_sig(bg_hex, marca, intent)
    dark = theme == "dark"
    if is_tiago:
        # _brand primeiro (único caminho no bundle Vercel), assets como fallback local
        svg = ""
        if pick:
            svg = _read(_BRAND_DIR / f"assinatura-{pick.variant}.svg") or _read(_TIAGO_SIG_DIR / f"assinatura-{pick.variant}.svg")
        if not svg:  # fallback binário se o sistema/arquivo faltar
            svg = _read(_BRAND_DIR / ("assinatura-branco.svg" if dark else "assinatura-escuro.svg"))
        # Editoriais levam a assinatura no TOPO (igual às refs de carrossel do Tiago);
        # hero entre as eyebrows (centro), os demais à direita. Outros archetypes: rodapé.
        cls = "brand-sig"
        default_pos = "center" if arch == "tiago-editorial-hero" else ("tr" if arch in _TIAGO_SIG_ARCH else "br")
    else:
        # Corner Metta = logo colorido (símbolo + wordmark). A variante do sistema dá
        # a polaridade da tinta: branco/amarelo = tinta clara (fundo escuro) → logo_h;
        # escuro/cinza = tinta escura (fundo claro/amarelo) → logo_escuro_h.
        light_ink = pick.variant in ("branco", "amarelo") if pick else dark
        # Header sobre FOTO no topo (photo-band photo:top, ex: FOTO-PILL, B-foto): quem
        # fica atrás do logo é a FOTO, não o fundo do tema. O _pick_sig usava o bg do
        # tema — em tema light escolhia o logo ESCURO, que sumia sobre foto escura
        # (dark-on-dark, achado do QA). Força tinta CLARA (o logo claro + drop-shadow
        # lê tanto sobre foto escura quanto clara).
        if arch == "photo-band" and str(params.get("photo") or "top").lower() == "top":
            light_ink = True
        svg = _read(_BRAND_DIR / ("logo_metta_colorido_h.svg" if light_ink else "logo_metta_colorido_escuro_h.svg"))
        cls, default_pos = "brand-logo", "tl"
    if not svg:
        return ""
    pos = pref if pref in ("tl", "tr", "bl", "br", "center") else default_pos
    out = f'<div class="brand-mark {cls}" data-pos="{pos}">{svg}</div>'
    # Cover Metta: eyebrow de categoria no topo-direito (igual às refs)
    if not is_tiago and arch in _METTA_COVER_ARCH and pos == "tl":
        out += '<div class="brand-eyebrow" data-pos="tr">INTELIGÊNCIA COMERCIAL</div>'
    return out


def _proof_line(copy: dict, anchor: str = "", brand_html: str = "") -> str:
    """Linha de PROVA SOCIAL solta no canto inferior (fora do card), assinatura do
    banco real (ex: '+1.000 EMPRESAS · +R$8,5 BI EM VENDAS'). Vazio se não houver.

    Guardas de colisão: com anchor=bottom o texto/CTA já ocupa o rodapé — a linha
    é suprimida (a regra do diretor de arte é usá-la com card no topo). Com a
    marca em bottom-left, a linha muda pro canto direito (data-side)."""
    p = (copy or {}).get("proof")
    if not p:
        return ""
    if "|" in str(p):  # prova com legenda vira CHIP no fluxo (não a linha)
        return ""
    if (anchor or "").lower() == "bottom":
        return ""
    side = ' data-side="right"' if 'data-pos="bl"' in (brand_html or "") else ""
    return f'<div class="proof-line"{side}>{_esc(str(p))}</div>'


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
        # Assinatura do Tiago no fundo — ligável (wizard). Default LIGADO; desliga
        # com copy.sig_bg = 0/off/false. Variante por contraste com o tema.
        sig = ""
        if str(copy.get("sig_bg", "on")).strip().lower() not in ("0", "off", "false", "no", "none"):
            _sig_theme = params.get("theme", "offwhite")
            _var = "escuro" if _sig_theme in ("offwhite", "light", "white", "paper", "yellow") else "branco"
            _svg = _read(_TIAGO_SIG_DIR / f"assinatura-{_var}.svg") or _read(_BRAND_DIR / f"assinatura-{_var}.svg")
            if _svg:
                sig = f'<div class="tt-signature" aria-hidden="true">{_svg}</div>'
        return (f'{sig}<div class="tt-text layer">{head("tt-headline")}{sub("tt-subhead")}{body("tt-body")}</div>'
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
        # headline inteiro marca-texto (como o app real quando vc seleciona e
        # destaca) — sem *accent* parcial, que ficaria invisível dentro do highlight.
        title_txt = _esc((copy.get("headline", "") or "").replace("*", ""))
        title_html = f'<h1 class="t-head tn-headline"><span class="tn-hl">{title_txt}</span></h1>'
        return ('<div class="tn-phone">'
                f'<div class="tn-statusbar"><span class="tn-time">9:41</span>'
                f'<span class="tn-status-icons">{_IOS_SIGNAL}{_IOS_WIFI}{_IOS_BATTERY}</span></div>'
                '<div class="tn-navbar"><span class="tn-back">‹ Notas</span>'
                '<span class="tn-actions"><span>…</span><span>OK</span></span></div>'
                f'<div class="tn-notes-body">{title_html}{sub("tn-subhead")}{body_html}</div>'
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
        # Variant IMAGE: foto embed na base quando há imagem. A proporção do
        # embed segue a da imagem (medida + clampada estilo X) — não estica.
        has_img = bool(image_url)
        _ar = _embed_aspect(image_url) if has_img else None
        _ar_style = f' style="aspect-ratio:{_ar[0]}/{_ar[1]}"' if _ar else ""
        embed = (f'<div class="tw-embed"{_ar_style}><div class="tw-embed-photo" '
                 f'style="background-image:url(\'{image_url}\')"></div></div>') if has_img else ""
        # Post reflexivo real (feedback: texto "esticado" quando é 1 bloco só
        # centralizado) — headline com linha em branco vira vários parágrafos
        # curtos, lidos do topo pra baixo, cada um podendo ter *negrito* no
        # início (ex: "*A boa:* dá tempo de chegar..."). 1 parágrafo só cai no
        # comportamento antigo (headline gigante centralizada).
        def _bold_only(t: str) -> str:
            # como _accent(), mas SEM o fallback de auto-negritar a última
            # palavra — aqui cada parágrafo só fica em negrito onde o
            # diretor de arte marcou *explicitamente* com asterisco.
            e = _esc(t)
            e = re.sub(r"\*([^*]+)\*", r'<span class="hi">\1</span>', e)
            return e.replace("\n", "<br>")
        _paras = [p.strip() for p in re.split(r"\n\s*\n", copy.get("headline", "") or "") if p.strip()]
        _multi = len(_paras) > 1
        if _multi:
            text_html = "".join(f'<p class="tw-para">{_bold_only(p)}</p>' for p in _paras)
            txtcls = "tw-text tw-text--multi tw-text--withimg" if has_img else "tw-text tw-text--multi"
        else:
            text_html = head("tw-headline")
            txtcls = "tw-text tw-text--withimg" if has_img else "tw-text"
        # post reflexivo real fecha só com a setinha (👉), sem texto de CTA antes
        if copy.get("cta"):
            cta = f'<p class="tw-cta">{_esc(copy["cta"])} 👉</p>'
        elif _multi:
            cta = '<p class="tw-cta tw-cta--arrow-only">👉</p>'
        else:
            cta = ""
        _av = _tiago_avatar()
        avatar_html = (f'<div class="tw-avatar tw-avatar--photo" style="background-image:url(\'{_av}\')"></div>'
                       if _av else '<div class="tw-avatar"><span class="tw-avatar-initial">T</span></div>')
        # Selo azul REAL (pessoa verificada) + prova social de print de tweet.
        seal = _VERIFIED_SEAL.format(cls="tw-verified", fill="#1D9BF0")
        proof = ("" if params.get("engagement") == "none"
                 else _tweet_proof(_tweet_metrics(copy.get("headline", "") + "tiago"), "tw"))
        return (f'<header class="tw-header">{avatar_html}'
                '<div class="tw-user"><div class="tw-name-row"><span class="tw-name">Tiago Alves</span>'
                f'{seal}</div>'
                f'<span class="tw-handle">@tiago.alves.oliveira</span></div>{_X_LOGO}</header>'
                f'<div class="{txtcls}">{text_html}{sub("tw-subhead")}{body("tw-body")}</div>'
                f'{cta}{embed}{proof}')

    # fallback Tiago desconhecido → tipográfico simples
    return f'<div class="tt-text layer">{head("tt-headline")}{sub("tt-subhead")}{body("tt-body")}</div>'


def _markup(arch: str, copy: dict, params: dict, image_url: str) -> str:
    if arch.startswith("tiago"):
        return _markup_tiago(arch, copy, params, image_url)

    cta_cls = "cta--dark" if params.get("cta") == "dark" else ("cta--outline" if params.get("cta") == "outline" else "")

    # Caixa de texto (text-panel): agrupa o texto+CTA num card arredondado sobre a
    # foto (assinatura do banco real). CTA fica DENTRO da caixa (branca/amarela pede
    # CTA escuro pra contraste). Retorna o HTML já embrulhado, ou o conteúdo cru.
    # panel: white/yellow/dark = caixa COM fundo · plain = caixa SEM fundo (texto
    # agrupado e limitado, com sombra pra legibilidade) · none = livre (legado).
    # Com ou sem fundo, a caixa limita o auto-fit (headline encolhe pra caber e
    # não cobre a imagem embaixo — ver _engine.js/fitHead e .text-panel max-height).
    panel = str(params.get("panel", "none")).strip().lower()
    # REGRA DURA (Nathan, categórico): NENHUM card com fundo AMARELO atrás de
    # texto/CTA — em modelo nenhum. Se qualquer coisa pedir panel amarelo, vira
    # card BRANCO (o card claro aprovado). Garantia estrutural: não depende do
    # art-director nem do blueprint se comportarem.
    if panel == "yellow":
        panel = "white"
    # Divisor amarelo entre headline e subtítulo: assinatura das peças SEM card
    # (texto sobre foto/dark). No banco real — cliente-na-loja, sem-processo,
    # serviços-300, FCA — o divisor separa a headline do apoio. Só quando NÃO há
    # card (o card já agrupa) E existe subtítulo.
    # SEM traço separador (feedback Nathan): a barrinha amarela entre headline e
    # apoio lê como "design feito por IA". Removida de todos os padrões.
    _div_photo = False
    def _panel_wrap(body_html: str, cta_variant: str = "") -> str:
        cta_c = cta_variant if cta_variant else cta_cls
        if panel in ("white", "yellow"):
            cta_c = "cta--dark"  # sobre card claro, CTA escuro
        inner_cta = _cta(copy, cta_c)
        if panel in ("white", "dark", "yellow", "plain"):
            return f'<div class="text-panel" data-panel="{panel}">{body_html}{inner_cta}</div>'
        return f'{body_html}{inner_cta}'

    if arch == "modulo-num":
        # Sistema "Lista Numerada" (= c1-metta-julho): módulo IDÊNTICO repetido em
        # cada slide — nº grande + thumb pequena + colchete amarelo + headline +
        # body com 1 palavra em amarelo. A unidade do carrossel vem da REPETIÇÃO
        # deste molde (não de tratamentos diferentes por slide). Número vem de
        # copy['num'] (o assembler de série passa 1..k).
        num = _esc(copy.get("num") or params.get("num") or "")
        thumb = _photo(image_url, cls="mod-thumb") if (image_url or "").strip() else ""
        # colchete/aspas amarelo — motivo recorrente do sistema
        bracket = ('<svg class="mod-bracket" viewBox="0 0 120 96" aria-hidden="true">'
                   '<path fill="currentColor" d="M8 96V52C8 26 26 8 52 6l4 15C40 24 30 34 '
                   '29 48h19v48zM68 96V52C68 26 86 8 112 6l4 15C100 24 90 34 89 48h19v48z"/>'
                   '</svg>')
        head = _accent(copy.get("headline", ""))
        _bd = copy.get("body") or copy.get("subhead") or ""
        body = f'<p class="t-body mod-body">{_accent(_bd)}</p>' if _bd else ""
        return (f'<div class="layer mod-layer">'
                f'<div class="mod-top">'
                f'<span class="mod-num">{num}</span>'
                f'{thumb}{bracket}</div>'
                f'<div class="mod-txt"><h1 class="t-head mod-title">{head}</h1>{body}</div>'
                f'</div>')

    if arch == "typo":
        _div = False  # sem linha divisória em nenhum padrão (inclui K-bold) — Nathan
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
        # photo-side (sem bloco amarelo): texto pode ganhar caixa (panel)
        return (f'{_photo(image_url)}<div class="grad"></div>'
                f'<div class="layer">{_panel_wrap(f"<div class=stack>{_txt_blocks(copy, divider=_div_photo)}</div>")}</div>')

    if arch == "photo-full":
        # ZONAS FIXAS (determinístico, como os blueprints fixos tweet/notes): headline
        # numa banda no TOPO + subhead/body/CTA numa banda na BASE, com scrim duplo. O
        # LUGAR de cada coisa é FIXO — não a âncora calculada (focus-map) que erra e
        # tampa o sujeito / gruda o CTA. O auto-fit só dimensiona DENTRO da banda (a
        # parte confiável). A imagem deve deixar topo/base livres (headroom). Liga com
        # `zones: split`. É o padrão que o VERSUS-COVER provou, generalizado.
        if str(params.get("zones", "")).strip().lower() == "split":
            # SELETOR (item 3): dentro do frame fixo, o focus-map escolhe entre 3
            # layouts SEGUROS conforme onde o sujeito está (copy.zone, medido em
            # generate.py). split = sujeito no meio (headline topo + CTA base) ·
            # top = sujeito embaixo → todo o texto EM CIMA · bottom = sujeito em cima
            # → todo o texto EMBAIXO. Assim, quando a imagem NÃO coopera, o texto foge
            # do sujeito em vez de sentar em cima (o scrim segue como rede). Isto é o
            # "automático preso a opções seguras", não posicionamento livre.
            zplace = str((copy or {}).get("zone") or "split").strip().lower()
            if zplace not in ("split", "top", "bottom"):
                zplace = "split"
            cta_html = _cta(copy, cta_cls)
            if zplace == "split":
                inner_zones = (f'<div class="zone-head">{_txt_blocks(copy, only_head=True)}</div>'
                               f'<div class="zone-foot">{_txt_blocks(copy, skip_head=True)}{cta_html}</div>')
            else:  # zona única no lado LIVRE (sujeito ocupa o oposto)
                inner_zones = f'<div class="zone-solo">{_txt_blocks(copy)}{cta_html}</div>'
            return (f'{_photo(image_url)}<div class="grad grad--zone" data-zone="{zplace}"></div>'
                    f'<div class="layer layer--zones" data-zone="{zplace}">{inner_zones}</div>')
        # 2 zonas (padrão CRM/chupeta real): headline SOBRE a foto (sem card, com
        # sombra) no topo + card só com apoio/CTA embaixo. Liga com head_out=1
        # quando há caixa. Senão, caixa única com tudo dentro.
        head_out = str(params.get("head_out", "")).lower() in ("1", "true", "yes")
        if head_out and panel in ("white", "yellow", "dark", "plain"):
            head_band = (f'<div class="text-panel head-band" data-panel="plain">'
                         f'{_txt_blocks(copy, only_head=True)}</div>')
            card = _panel_wrap(_txt_blocks(copy, skip_head=True))
            return (f'{_photo(image_url)}<div class="grad"></div>'
                    f'<div class="layer layer--split">{head_band}{card}</div>')
        return (f'{_photo(image_url)}<div class="grad"></div>'
                f'<div class="layer">{_panel_wrap(_txt_blocks(copy, divider=_div_photo))}</div>')

    if arch == "photo-versus":
        # Cover "VERSUS" com ZONAS INDEPENDENTES — cada elemento tem posição própria,
        # NÃO um bloco flex único (a limitação do photo-full que colava o CTA no
        # headline). Layout: headline(s) no TOPO (top-pinned, sobre scrim) · foto/
        # pessoas livres no MEIO · ✕ central · subline+CTA na BASE (bottom-pinned,
        # sobre scrim). Resolve de vez: texto tampando o sujeito, CTA grudado no
        # headline e logo-branca-no-branco (scrim garantido em cima e embaixo).
        # Copy: headline (esq) + headline_right (dir, opcional) → comparação A × B.
        hr = copy.get("headline_right")
        if hr:
            heads = (f'<div class="versus-heads">'
                     f'<div class="versus-col vs-left"><h1 class="t-head">{_accent(copy.get("headline",""))}</h1></div>'
                     f'<div class="versus-col vs-right"><h1 class="t-head">{_accent(hr)}</h1></div></div>')
        else:
            heads = (f'<div class="versus-heads versus-heads--single">'
                     f'<div class="versus-col"><h1 class="t-head">{_accent(copy.get("headline",""))}</h1></div></div>')
        x_mark = ("" if str(params.get("vs_mark", "1")).lower() in ("0", "false", "no")
                  else '<span class="versus-x" aria-hidden="true">&#10005;</span>')
        foot_parts = []
        if copy.get("subhead"):
            foot_parts.append(f'<p class="t-sub">{_esc(copy["subhead"])}</p>')
        foot_parts.append(_cta(copy, cta_cls))
        foot = f'<div class="versus-foot">{"".join(foot_parts)}</div>'
        return (f'{_photo(image_url)}<div class="grad grad--versus"></div>'
                f'<div class="layer layer--versus">{heads}{x_mark}{foot}</div>')

    if arch == "photo-band":
        return f'{_photo(image_url)}<div class="layer">{_panel_wrap(_txt_blocks(copy, divider=_div_photo))}</div>'

    if arch == "object-center":
        obj = _photo(image_url, "object")
        # CTA vai pro RODAPÉ, SEPARADO da zona de texto do topo (Nathan: o botão
        # colado na headline no topo espremia a composição "headline em cima, objeto
        # embaixo"). O texto (headline/sub/body) fica no topo; o CTA desce.
        _obj_cta = _cta(copy, cta_cls)
        _obj_txt = _txt_blocks(copy)
        if panel in ("white", "dark", "plain"):
            _obj_txt = f'<div class="text-panel" data-panel="{panel}">{_obj_txt}</div>'
        if params.get("object_scale") == "full":
            # Imagem cobre o canvas inteiro (o gerador AI já bake-a o fundo sólido do
            # tema) — objeto vira background, texto ancora no topo, CTA no rodapé.
            # `.obj-text-zone` tem altura PRÓPRIA (não o canvas inteiro) — é o que
            # permite o auto-fit do _engine.js medir overflow e encolher a headline.
            return (f'{obj}<div class="layer"><div class="obj-text-zone">{_obj_txt}</div>'
                    f'{_obj_cta}</div>')
        return f'<div class="layer">{obj}<div class="obj-text-zone">{_obj_txt}</div>{_obj_cta}</div>'

    if arch == "card-mock":
        name = params.get("name", "Metta")
        handle = params.get("handle", "@metta.brasil")
        _sym = _metta_symbol()
        avatar = _sym if _sym else f'<span class="avatar-initial">{(name or "M")[0].upper()}</span>'
        # Card DARK (DNA Metta) tem palavra-accent amarela; card light (Twitter)
        # corre texto sem cor. Quebras (\n) sempre viram espaço (texto fluido).
        if params.get("theme") == "dark":
            head_plain = _accent(copy.get("headline", "").replace("\n", " "))
        else:
            head_plain = _esc(copy.get("headline", "").replace("*", "").replace("\n", " "))
        body = _esc(copy.get("body", "").replace("*", "")).replace("\n", "<br>")
        cta_line = f'<p class="t-body" style="color:#1D9BF0">{_esc(copy["cta"])} →</p>' if copy.get("cta") else ""
        # Selo DOURADO = conta de organização no X (a Metta é empresa). Prova
        # social (timestamp + engajamento) desligável via params.engagement=none.
        seal = _VERIFIED_SEAL.format(cls="verified", fill="#1D9BF0")  # azul (pedido do Nathan)
        proof = ("" if params.get("engagement") == "none"
                 else _tweet_proof(_tweet_metrics(copy.get("headline", "") + handle), "mock"))
        return (f'<div class="card"><div class="mock-head"><div class="avatar">{avatar}</div>'
                f'<div class="who"><span class="name">{_esc(name)} {seal}</span>'
                f'<span class="handle">{_esc(handle)}</span></div>{_X_LOGO}</div>'
                f'<h1 class="t-head">{head_plain}</h1>'
                f'{f"<p class=t-body>{body}</p>" if body else ""}{cta_line}{proof}</div>')

    if arch == "logo-wall":
        slots = "".join('<div class="slot">logo</div>' for _ in range(6))
        return (f'<div class="layer"><div class="stack">{_txt_blocks(copy)}</div>'
                f'<div class="wall">{slots}</div>{_cta(copy, cta_cls)}</div>')

    if arch == "framed":
        return f'<div class="frame"></div><div class="layer">{_panel_wrap(_txt_blocks(copy))}</div>'

    if arch == "split":
        media = f'<div class="half-media" style="background-image:url(\'{image_url}\')"></div>' if image_url else '<div class="half-media"></div>'
        return (f'{media}<div class="half-text">{_panel_wrap(f"<div class=stack>{_txt_blocks(copy)}</div>")}</div>')

    if arch == "number-hero":
        # colagem PB no topo (opcional) + número gigante + sub/body + CTA
        return (f'{_photo(image_url)}'
                f'<div class="layer">{_panel_wrap(f"<div class=stack>{_txt_blocks(copy)}</div>")}</div>')

    if arch == "stat-stack":
        # 2+ estatísticas empilhadas em cards (número gigante + descrição), fonte
        # embaixo. headline = 1º dado; body = dados seguintes (1 por linha);
        # tag = fonte/ano. (banco real: slide 'pesquisa 2026 / gallup')
        def _stat(txt: str) -> str:
            # aceita sinal à frente (+141%, -30%) e sufixo x/% — sem o [+\-]? o
            # "+" quebrava a detecção e o número caía no stat-desc (miudinho).
            m = re.match(r"\s*([+\-]?[\d.,]+\s*[%x]?)\s*(.*)", txt or "", re.S)
            if m and m.group(1).strip():
                return (f'<div class="stat"><div class="stat-num">{_esc(m.group(1).strip())}</div>'
                        f'<div class="stat-desc">{_esc(m.group(2).strip())}</div></div>')
            return f'<div class="stat"><div class="stat-desc">{_esc(txt.strip())}</div></div>'
        rows = [copy.get("headline", "")] + [l.strip() for l in
                (copy.get("body", "") or "").split("\n") if l.strip()]
        stats = "".join(_stat(r) for r in rows if r.strip())
        src = f'<div class="stat-source">{_esc(copy["tag"])}</div>' if copy.get("tag") else ""
        return f'<div class="layer"><div class="stat-wrap">{stats}</div>{src}{_cta(copy, cta_cls)}</div>'

    if arch == "equation":
        # headline com "=" vira termos empilhados + sinal amarelo entre eles.
        # subhead = linha de apoio embaixo (aceita *destaque*).
        terms = [t.strip() for t in re.split(r"\s*=\s*", copy.get("headline", "")) if t.strip()]
        blocks = []
        for i, t in enumerate(terms):
            if i:
                blocks.append('<div class="eq-sign" aria-hidden="true"></div>')
            blocks.append(f'<div class="eq-term">{_accent(t)}</div>')
        sub = f'<p class="t-sub">{_accent(copy["subhead"])}</p>' if copy.get("subhead") else ""
        return (f'<div class="layer"><div class="stack eq-stack">{"".join(blocks)}'
                f'{sub}</div></div>{_cta(copy, cta_cls)}')

    if arch == "chat-def":
        # palavra-definição gigante + definição + citação em balão de chat +
        # "escrevendo…". headline=palavra; subhead=definição; body=fala do balão.
        word = f'<h1 class="t-head cd-word">{_esc(copy.get("headline", ""))}</h1>'
        sub = f'<p class="t-sub">{_esc(copy["subhead"])}</p>' if copy.get("subhead") else ""
        quote = (copy.get("body", "") or "").strip().strip('"').strip("“”")
        bubble = typing = ""
        if quote:
            bubble = f'<div class="cd-bubble">{_esc(quote)}</div>'
            typing = ('<div class="cd-typing"><span class="cd-brand">metta</span>'
                      '<span class="cd-dot"></span><span class="cd-dot"></span>'
                      '<span class="cd-dot"></span><em>escrevendo…</em></div>')
        return (f'{_photo(image_url)}<div class="grad"></div>'
                f'<div class="layer"><div class="stack">{word}{sub}{bubble}{typing}</div></div>')

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
    # IMAGE-FIRST (sensor focal 2D): quando o sujeito ocupa a coluna lateral do
    # photo-side, o texto vira FAIXA (photo-full + anchor + gradiente, sem card,
    # como o exemplo aprovado). A IMAGEM manda, não o blueprint. generate.py mede
    # a foto e seta copy._force_band = 'top'|'bottom'.
    _force_band = str((copy or {}).get("_force_band") or "").strip().lower()
    if _force_band not in ("top", "bottom"):
        _force_band = ""
    if _force_band and arch == "photo-side":
        arch = "photo-full"
    # Alinhamento: o diretor de arte pode variar por peça (copy.align) — o banco real
    # NÃO fica sempre no mesmo lugar (centraliza em fundo chapado, lateral em foto).
    # Sem override, vale o default do blueprint (já calibrado pela convenção da família).
    align = str((copy or {}).get("align") or params.get("align", "left")).strip().lower()
    if align not in ("left", "center", "right"):
        align = params.get("align", "left")
    scale = params.get("scale", "normal")
    photo = params.get("photo", "right-bleed")
    block = params.get("block", "none")
    # Âncora do bloco de texto: o diretor de arte pode sobrescrever por peça
    # (copy.text_anchor) pra levar o texto pra zona VAZIA da cena — ex: objeto
    # ocupa a metade de baixo → texto em cima (como no banco real). Sem
    # override, vale o default do blueprint.
    anchor = str((copy or {}).get("text_anchor") or "").strip().lower()
    if _force_band:
        anchor = _force_band   # a faixa vai pra zona vazia medida na imagem
    if anchor not in ("top", "bottom"):
        anchor = params.get("anchor", "bottom")
    obj_scale = params.get("object_scale", "boxed")

    # Caixa de texto: o diretor de arte pode escolher por peça (copy.panel);
    # senão vale o default do blueprint. white/dark/plain/none.
    # "yellow" fica de fora de propósito (feedback da Sofia: caixa amarela atrás
    # de texto nunca ficou boa) — não confundir com params.block="yellow", o
    # layout estrutural fixo do YELLOW-BLOCO/TIAGO-STORY-YELLOW-BLOCK, que é outra coisa.
    panel = str((copy or {}).get("panel") or "").strip().lower()
    if panel not in ("white", "dark", "plain", "none"):
        panel = str(params.get("panel", "none")).strip().lower()
    if panel == "yellow":  # REGRA DURA: nunca card amarelo atrás de texto → vira branco
        panel = "white"
    if _force_band:  # faixa = texto sobre o gradiente (como o exemplo aprovado), sem card
        panel = "none"

    # head_out: headline na foto + card só com apoio (2 zonas, padrão CRM).
    head_out = str((copy or {}).get("head_out") or params.get("head_out", "")).strip().lower()

    # Decor de carrossel (copy.serie = {"i","n","last"}): seta de navegação nos
    # slides intermediários; wordmark gigante cortado na base no slide final
    # (assinatura dos carrosséis reais do banco — burnout slide 9). É dict,
    # sai ANTES do copy_clean (que stringifica tudo).
    serie = (copy or {}).get("serie") or None

    # Ornamento decorativo (recurso definidor de estilos sem foto gerada —
    # ex: selo M da DARK-CARTA, ilustração hand-drawn do YELLOW-DRAW). Camada
    # atrás do texto; nome desconhecido → sem nada (best-effort).
    ornament = str(params.get("ornament", "")).strip().lower()
    ornament_html = _ornament(ornament, theme)

    # Dedupe de eyebrow (achado do QA): capas Metta (photo-full/side/band) já ganham
    # a eyebrow de categoria "INTELIGÊNCIA COMERCIAL" no topo-direita (_brand_mark).
    # Se o slide passa um `tag` IDÊNTICO, a mesma frase aparece 2x (topo-direita +
    # kicker acima da headline, ex: caos-ordem). Quando forem iguais, dropa o kicker.
    if (str(marca).lower() != "tiago" and arch in _METTA_COVER_ARCH
            and str((copy or {}).get("tag") or "").strip().upper() == "INTELIGÊNCIA COMERCIAL"):
        copy = {**(copy or {}), "tag": ""}
    copy_clean = {k: (_no_dash(str(v).strip()) if v else "")
                  for k, v in (copy or {}).items() if k != "serie"}
    params_eff = {**params, "anchor": anchor, "panel": panel, "head_out": head_out}
    inner = _markup(arch, copy_clean, params_eff, image_url or "")

    serie_under = ""   # atrás do conteúdo (wordmark base / spine)
    serie_over = ""    # sobre o conteúdo (seta → / progress)
    _arc_i = _arc_n = 0
    if isinstance(serie, dict) and serie:
        _arc_i = int(serie.get("i") or 0)
        _arc_n = int(serie.get("n") or 0)
        # ARCO VISUAL — camada 1: SPINE viajante (eco do logo-alvo). Um anel
        # concêntrico gigante e sutil cujo centro CAMINHA da esquerda (slide 1) à
        # direita (slide n), sangrando nas bordas — a mesma "coluna" corre por
        # todos os slides, ligando os quadros numa jornada (não no slide final,
        # que já tem o wordmark). Atrás do conteúdo, nunca tampa o foco.
        if _arc_n >= 2 and _arc_i >= 1 and arch != "modulo-num":
            # CAMPO CONTÍNUO: os anéis são UM sistema concêntrico fixo, centrado no
            # MEIO do carrossel. O centro anda EXATAMENTE 100% (uma largura de slide)
            # por slide — então a fatia da borda direita de um slide continua na borda
            # esquerda do próximo. Ao deslizar (o IG passa da direita p/ esquerda), lê
            # como um campo inteiro, não "a bola num lugar diferente em cada slide".
            # (Antes andava ~32%/slide → desalinhado.) Todos os slides mostram a sua
            # fatia (inclusive o último — o wordmark de rodapé já foi removido).
            _spine_left = round(50 + ((_arc_n + 1) / 2 - _arc_i) * 100)
            serie_under += (f'<div class="serie-spine" aria-hidden="true" '
                            f'style="left:{_spine_left}%"></div>')
        # ARCO VISUAL — camada 2: PROGRESS (posição na jornada). Fileira de traços,
        # o atual em amarelo. Topo-centro (zona livre entre logo e olho-de-marca).
        if _arc_n >= 2 and _arc_i >= 1:
            _ticks = "".join(
                f'<span class="{"on" if k == _arc_i else ""}"></span>'
                for k in range(1, _arc_n + 1))
            serie_over += (f'<div class="serie-progress" aria-hidden="true">'
                           f'{_ticks}</div>')
        # só a seta -> nos intermediários. O wordmark gigante "metta" no rodapé do
        # slide final foi REMOVIDO (regra do Nathan: logo embaixo é desnecessário,
        # já tem o logo no topo de todo slide) — não confundir com o logo do header.
        if not serie.get("last"):
            serie_over += '<div class="serie-next" aria-hidden="true">&#8594;</div>'

    head_style = params.get("head", "")
    case = params.get("case", "upper")
    orient = params.get("orient", "vertical")
    marca_attr = (fm.get("marca") or marca or "").strip().lower()
    brand = _brand_mark(marca_attr, arch, theme, params)
    data_attrs = (
        f'data-marca="{_esc(marca_attr)}" data-model="{_esc(model_id)}" '
        f'data-case="{_esc(case)}" data-orient="{_esc(orient)}" '
        f'data-arch="{_esc(arch)}" data-theme="{_esc(theme)}" data-format="{_esc(format)}" '
        f'data-align="{_esc(align)}" data-scale="{_esc(scale)}" data-photo="{_esc(photo)}" '
        f'data-block="{_esc(block)}" data-anchor="{_esc(anchor)}" data-head="{_esc(head_style)}" '
        f'data-obj-scale="{_esc(obj_scale)}" data-panel="{_esc(panel)}"'
        + (f' data-ornament="{_esc(ornament)}"' if ornament else "")
        + (f' data-arc-i="{_arc_i}" data-arc-n="{_arc_n}"' if _arc_n >= 2 else "")
        # tweet COM imagem → canvas auto-height (print cru, altura = conteúdo)
        + (' data-embed="1"' if (arch == "tiago-twitter" and (image_url or "").strip()) else "")
    )

    # glow do arco: 0 no gancho → cresce até ~22 no CTA (tensão→alívio amarelo)
    _arc_style = ""
    if _arc_n >= 2 and _arc_i >= 1:
        _arc_glow = round(((_arc_i - 1) / max(1, _arc_n - 1)) * 22)
        _arc_style = f' style="--arc-glow:{_arc_glow}"'

    fonts_css = _read(_BLUEPRINTS_DIR / "_fonts.css")
    css = _read(_BLUEPRINTS_DIR / "_engine.css")
    js = _read(_BLUEPRINTS_DIR / "_engine.js")

    # A decoração de série (anel-spine de 4200px) sangra de propósito pras bordas.
    # Solta no .ad ela INFLA o scrollHeight → o portão de overflow do _engine.js
    # (data-overflow) dava FALSO POSITIVO em TODO slide de carrossel. Envolver num
    # container inset:0 overflow:hidden clipa o anel na borda (visual igual) E isola
    # o overflow (não propaga pro .ad). Corrige o falso-FAIL que o QA #6 propagava.
    serie_field = (f'<div class="serie-field" aria-hidden="true">{serie_under}</div>'
                   if serie_under.strip() else "")

    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{_esc(model_id)}</title>
<style>{fonts_css}</style>
<style>{css}</style>
<style>body{{display:flex;justify-content:center;align-items:flex-start;}}</style>
</head><body>
<div class="ad ad-canvas" {data_attrs}{_arc_style}>
{serie_field}
{ornament_html}
{brand}
{inner}
{_proof_line(copy_clean, anchor=anchor, brand_html=brand)}
{serie_over}
</div>
<script>{js}</script>
</body></html>"""

    return {"html": doc, "model_id": model_id, "marca": marca, "format": format,
            "archetype": arch, "missing": False}
