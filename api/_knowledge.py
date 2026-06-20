"""Camada de RECUPERAÇÃO de conhecimento do brand-system.

Problema que resolve: o gerador roda com input pobre tendo um acervo enorme sem
uso — `content/audiencia/icp.md` (847 linhas), `verbal/identidade-verbal.md` (voz),
`metodologia/*` (~5k linhas), `depoimentos.md` (fala real de cliente), transcrições.
Hoje a geração carrega ~3 arquivos pequenos. Esta camada, dado um brief (a copy),
seleciona as FATIAS relevantes e devolve um bloco compacto pronto pra injetar no
diretor de arte (o pensador) e na skill 04 (o escritor).

Determinística — token-overlap + difflib, sem embeddings (mesmo padrão de
_resolve_catalog / _critic.pick_reference). Docs são estáticos → cache no módulo.

    from _knowledge import retrieve, build_block
    k = retrieve({"headline": "...", "subhead": "...", "body": "...", "cta": "..."}, "metta")
    bloco = build_block(k)   # texto pra colar no prompt
    k["provenance"]          # [(tipo, fonte)] — pro decision log
"""
from __future__ import annotations

import difflib
import glob
import re
import unicodedata
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

# Registro de fontes. mode: "always" = sempre entra (quem é / como fala);
# "topic" = entra a fatia que casa com a copy. marca: both | metta | tiago.
_SOURCES = [
    {"id": "icp",    "glob": "content/audiencia/icp.md",         "marca": "both",  "mode": "always", "label": "ICP"},
    {"id": "voz",    "glob": "content/verbal/identidade-verbal.md", "marca": "both", "mode": "always", "label": "Voz da marca"},
    {"id": "metodo", "glob": "content/metodologia/*.md",          "marca": "metta", "mode": "topic",  "label": "Metodologia"},
    {"id": "prova",  "glob": "content/audiencia/depoimentos.md",  "marca": "both",  "mode": "topic",  "label": "Depoimento real"},
    {"id": "fala",   "glob": "content/transcricoes/*.md",         "marca": "tiago", "mode": "topic",  "label": "Fala do Tiago"},
]

_CACHE: list[dict] | None = None


def _words(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]{3,}", s)


# stopwords PT que poluem o overlap
_STOP = {"que", "com", "para", "uma", "voce", "seu", "sua", "tem", "nao", "como",
         "dos", "das", "por", "mais", "the", "and", "isso", "ele", "ela", "mas"}


def _fm_summary(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else ""
    m = re.search(r'^summary:\s*"?(.+?)"?\s*$', fm, re.M)
    return m.group(1).strip() if m else ""


def _strip_fm(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _split_md(text: str) -> list[tuple[str, str]]:
    """Quebra markdown em (heading, corpo) por '#'..'####'."""
    chunks, head, buf = [], "(intro)", []
    for line in _strip_fm(text).splitlines():
        m = re.match(r"^#{1,4}\s+(.*)", line)
        if m:
            if buf:
                chunks.append((head, "\n".join(buf).strip()))
            head, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if buf:
        chunks.append((head, "\n".join(buf).strip()))
    return [(h, t) for h, t in chunks if len(t) > 40]


def _window(text: str, size: int = 700) -> list[str]:
    """Sub-janela um texto longo em pedaços ~size chars (limite de palavra).

    Necessário porque docs achatados de HTML (ex: identidade-verbal.md) põem todo
    o conteúdo sob 1 heading — sem isto, a fatia vira o índice, não o tom de voz.
    """
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out or [text]


# Seções que não são conteúdo (índice, navegação, links) — não indexar.
_JUNK_HEAD = ("documentos relacionados", "tl;dr", "tldr", "quando consultar",
              "indice", "sumario", "referencias", "links", "ver tambem",
              "navegacao", "metadados", "changelog", "historico")


def _is_junk(head: str) -> bool:
    h = "".join(c for c in unicodedata.normalize("NFKD", head.lower())
                if not unicodedata.combining(c))
    return any(k in h for k in _JUNK_HEAD)


def _load() -> list[dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    out: list[dict] = []
    for s in _SOURCES:
        for fp in sorted(glob.glob(str(_ROOT / s["glob"]))):
            try:
                text = Path(fp).read_text(encoding="utf-8")
            except Exception:
                continue
            summ = _fm_summary(text)
            stem = Path(fp).stem
            for head, body in _split_md(text):
                if _is_junk(head):
                    continue
                for pc in (_window(body) if len(body) > 1200 else [body]):
                    out.append({**s, "file": stem, "head": head, "text": pc,
                                "summary": summ, "toks": set(_words(head + " " + pc)) - _STOP})
    _CACHE = out
    return out


# Densidade de linguagem que DESCREVE a voz da marca (pra achar a fatia de tom).
_VOZ_DESC = ("tom", "voz", "vocabul", "mensagen", "arquetip", "dizer", "falar",
             "evitar", "linguagem", "estilo", "palavra", "frase")


def _voz_density(text: str) -> int:
    tl = "".join(c for c in unicodedata.normalize("NFKD", text.lower())
                 if not unicodedata.combining(c))
    return sum(tl.count(k) for k in _VOZ_DESC)


def _score(qset: set, chunk: dict) -> float:
    overlap = len(qset & chunk["toks"])
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(qset)),
                                    " ".join(sorted(chunk["toks"]))).ratio()
    return overlap + ratio


def _trunc(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    dot = cut.rfind(". ")
    return (cut[:dot + 1] if dot > n * 0.5 else cut.rstrip() + "…")


def retrieve(copy: dict, marca: str = "metta") -> dict:
    """Seleciona as fatias relevantes do brand-system pra esta copy."""
    marca = (marca or "metta").lower()
    qset = set(_words(" ".join(str(copy.get(k, "")) for k in
                              ("headline", "subhead", "body", "cta")))) - _STOP
    pool = [c for c in _load() if c["marca"] == "both" or c["marca"] == marca]

    picks: dict = {"sections": [], "provenance": []}
    seen_ids: set = set()

    # ALWAYS: ICP (essência = summary do frontmatter) + voz (a fatia que mais
    # DESCREVE o tom/voz da marca — independente do tema da copy).
    for sid in ("icp", "voz"):
        cand = [c for c in pool if c["id"] == sid]
        if not cand:
            continue
        if sid == "icp" and cand[0]["summary"]:
            text, head = cand[0]["summary"], "essência"
        elif sid == "voz":
            best = max(cand, key=lambda c: _voz_density(c["text"]))
            text, head = best["text"], "tom & voz"
        else:
            best = max(cand, key=lambda c: _score(qset, c))
            text, head = best["text"], best["head"]
        picks["sections"].append((cand[0]["label"], head, _trunc(text, 480)))
        picks["provenance"].append((cand[0]["label"], head))
        seen_ids.add(sid)

    # TOPIC: melhor fatia de cada fonte de tópico (metodologia/prova/fala).
    for sid in ("metodo", "prova", "fala"):
        cand = [c for c in pool if c["id"] == sid]
        if not cand:
            continue
        best = max(cand, key=lambda c: _score(qset, c))
        if _score(qset, best) < 1.0:  # nada relevante o suficiente
            continue
        loc = f"{best['file']} · {best['head']}" if best["file"] not in best["label"] else best["head"]
        picks["sections"].append((best["label"], loc, _trunc(best["text"], 460)))
        picks["provenance"].append((best["label"], loc))

    return picks


def build_block(picks: dict) -> str:
    """Formata as fatias num bloco pra injetar no prompt do diretor de arte."""
    if not picks.get("sections"):
        return ""
    lines = ["=== CONHECIMENTO DA MARCA (fundamente a persona e a cena nisto) ==="]
    for label, loc, text in picks["sections"]:
        lines.append(f"\n[{label} — {loc}]\n{text}")
    return "\n".join(lines)
