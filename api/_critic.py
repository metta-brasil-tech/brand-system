"""Crítico VISUAL comparativo — o "same-designer test" do banco.

Porta o insight central do plugin-metta-ads (v0.6 vision-first) pro ad-generator:
o `_vision_qa.py` já checa a peça ISOLADA (a imagem ilustra a copy? o layout
mutila?). Aqui a peça é julgada CONTRA UMA REFERÊNCIA do banco — a pergunta-mãe é
"isso passaria como peça do mesmo designer que fez o banco?".

Dois passos, espelhando o plugin:
  1) pick_reference()  → F1: filtra o catálogo (applications-index.json) pela marca
     e escolhe a referência mais próxima que tem RASTER (thumb .webp) em disco.
     SVG do banco é ilegível por visão (texto vetorizado em <path>) — por isso só
     entram candidatos com thumb raster.
  2) critique()        → critic-visual: manda a peça produzida + a referência pro
     modelo de visão e pede o veredito comparativo + anti-slop + texto-inventado,
     com feedback acionável pro designer (vira brief da regeneração).

Degrada gracioso igual ao _vision_qa: sem OpenAI, sem referência ou em erro,
retorna SKIPPED/None e o pipeline segue só com a checagem isolada.
"""
from __future__ import annotations

import base64
import difflib
import json
import os
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_INDEX = _ROOT / "data" / "applications-index.json"

_MIME = {".webp": "image/webp", ".png": "image/png",
         ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


# ===========================================================================
# Anti-slop — espelho condensado de content/direcao-arte/anti-slop.md.
# Mantenha em sincronia com aquele arquivo (o .md é a fonte humana canônica).
# Regra-mãe: se uma peça REAL do banco faz aquilo, é repertório legítimo, não
# slop — na dúvida, comparar com a referência antes de reprovar.
# ===========================================================================
_ANTI_SLOP = (
    "1. Gradiente arco-íris / multicolor decorativo. "
    "2. Glassmorphism (cartão de vidro fosco, blur translúcido). "
    "3. Ícones de biblioteca genérica (Lucide/Heroicons/FontAwesome) colados. "
    "4. Layout em 3 faixas horizontais simétricas sem hierarquia. "
    "5. Box-shadow difusa estilo Tailwind / cards flutuando sem motivo. "
    "6. Emoji na peça. "
    "7. Tudo centralizado sem propósito (simetria vazia de 'AI poster'). "
    "8. Badge de e-commerce não pedido ('OFERTA', '50% OFF', selo de garantia). "
    "9. Sorriso de stock / aperto de mão clichê / lâmpada de ideia. "
    "10. Saturação inflada / HDR / grade teal-orange turística. "
    "11. Texto rasterizado dentro da foto gerada (palavras tortas inventadas pela IA). "
    "12. Tipografia default de sistema (Arial/Helvetica) onde devia ser a display da marca. "
    "13. Mockup de device genérico sem contexto. "
    "14. Faixas pretas de preenchimento (letterbox) forçando proporção. "
    "15. Amarelo decorativo espalhado — na Metta/Tiago o amarelo é cirúrgico, nunca difuso. "
    "16. Sujeito-fantasma centralizado, composição genérica que não herdou nada da marca."
)


# ---------------------------------------------------------------------------
# F1 — seleção de referência no banco
# ---------------------------------------------------------------------------
def _load_index() -> list[dict]:
    try:
        d = json.loads(_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = d if isinstance(d, list) else (
        d.get("items") or d.get("applications")
        or next((v for v in d.values() if isinstance(v, list)), [])
    )
    return [x for x in items if isinstance(x, dict)]


def _raster_path(ad: dict) -> Path | None:
    """Caminho do RASTER da referência (thumb .webp), se existir em disco.

    O `src.mid` dos ads aponta pro SVG (ilegível por visão). Preferimos
    `src.thumb`; senão derivamos /mid/→/thumbs/ e .svg→.webp. Só retorna se o
    arquivo existir de fato.
    """
    src = ad.get("src") or {}
    cands: list[str] = []
    if src.get("thumb"):
        cands.append(src["thumb"])
    mid = src.get("mid") or ""
    if mid:
        cands.append(re.sub(r"/mid/", "/thumbs/", mid).rsplit(".", 1)[0] + ".webp")
        cands.append(mid)  # último recurso: o próprio mid se já for raster
    for rel in cands:
        ext = Path(rel).suffix.lower()
        if ext not in _MIME:
            continue
        p = _ROOT / rel
        if p.is_file():
            return p
    return None


def _searchable(ad: dict) -> str:
    parts = [
        ad.get("mood", ""), ad.get("intent", ""), ad.get("archetype_foto", ""),
        ad.get("title", ""), ad.get("tese", ""), ad.get("notes", ""),
        ad.get("formato_canonico", ""), " ".join(ad.get("tokens_used", []) or []),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _norm(s: str) -> list[str]:
    return re.findall(r"\w{3,}", (s or "").lower())


def pick_reference(query: str, marca: str, exclude_ids=()) -> dict | None:
    """Escolhe a referência do banco mais próxima da peça em produção.

    Filtro DURO por marca; só candidatos com raster em disco. Pontua por
    sobreposição de tokens + similaridade difflib entre `query` (copy + conceito
    visual + tratamento) e o texto buscável da referência (mood/intent/
    archetype_foto/notes/tese/tokens). Retorna {id, path, meta, score} ou None.
    """
    marca = (marca or "").strip().lower()
    q_tokens = set(_norm(query))
    best: dict | None = None
    best_score = -1.0
    for ad in _load_index():
        if (ad.get("brand") or "").strip().lower() != marca:
            continue
        if ad.get("id") in exclude_ids:
            continue
        path = _raster_path(ad)
        if not path:
            continue
        text = _searchable(ad)
        overlap = len(q_tokens & set(_norm(text)))
        ratio = difflib.SequenceMatcher(None, query.lower(), text).ratio()
        score = overlap + ratio  # overlap domina; ratio desempata
        if score > best_score:
            best_score = score
            best = {
                "id": ad.get("id"),
                "path": str(path),
                "score": round(score, 3),
                "meta": {
                    "mood": ad.get("mood"), "intent": ad.get("intent"),
                    "archetype_foto": ad.get("archetype_foto"),
                    "tokens_used": ad.get("tokens_used"),
                    "title": ad.get("title"),
                },
            }
    return best


def _img_data_uri(path: str) -> str:
    p = Path(path)
    mime = _MIME.get(p.suffix.lower(), "image/png")
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# critic-visual — julgamento comparativo
# ---------------------------------------------------------------------------
def _system(marca: str) -> str:
    dna = (
        "A Metta é inteligência comercial B2B: editorial sério (HBR/Bloomberg), dark "
        "moody, autoridade, display Zalando Sans Expanded, amarelo Metta cirúrgico."
        if (marca or "").lower() != "tiago" else
        "Tiago Alves é marca pessoal cinematográfica: B&W de alto contraste com UM "
        "amarelo seletivo (#FFCC00), grão analógico 35mm, profundidade rasa, autoral."
    )
    return f"""Você é o CRÍTICO VISUAL sênior do estúdio. Você recebe DUAS imagens:
[REFERÊNCIA] = uma peça campeã do banco da marca, e [PRODUZIDA] = a peça nova que
o pipeline acabou de gerar. {dna}

Você JULGA IMAGENS, não código. A pergunta-mãe que organiza tudo é:
  "A peça PRODUZIDA passaria como obra do MESMO designer que fez a REFERÊNCIA?"

Avalie 4 eixos, todos OLHANDO as duas imagens lado a lado:

1. SAME-DESIGNER (o coração): paleta na mesma família? hierarquia tipográfica em
   proporção comparável (a headline domina/cede como na referência)? tratamento de
   foto análogo (full-bleed, duotone, recorte)? peso/posição da marca comparável
   (AUSÊNCIA NÃO REPROVA se a referência também dispensa marca)? respiro/densidade
   na mesma chave? Se a PRODUZIDA parece um clone genérico com texto trocado por
   cima, ou uma peça que não herdou NADA da linguagem do banco, reprova.

2. INTEGRIDADE física: nada essencial cortado sem querer (pessoa pela metade, rosto
   espremido no canto, sujeito coberto por bloco, CTA com curvatura cortada na
   borda). Bleed proposital de foto é permitido; corte acidental não.

3. TEXTO INVENTADO: todo texto legível na PRODUZIDA precisa estar no CORPUS
   permitido (a copy do anúncio ∪ a palavra "metta"). Atenção especial a texto
   RASTERIZADO DENTRO da foto gerada pela IA (palavras tortas/inventadas) — isso é
   falha grave. Qualquer string legível fora do corpus = invented_text:"yes".

4. ANTI-SLOP: marque padrões de IA genérica presentes na PRODUZIDA. Lista:
   {_ANTI_SLOP}
   REGRA-MÃE: se a REFERÊNCIA (peça real do banco) também faz aquilo, é repertório
   legítimo, NÃO slop — compare antes de reprovar.

Seja RIGOROSO mas JUSTO: não reprove por divergência criativa saudável, reprove por
quebra física, texto inventado, slop genuíno, ou fuga total da linguagem do banco.

Responda APENAS JSON, sem cercas:
{{"same_designer":"yes|no","integrity":"ok|broken","invented_text":"yes|no",
"anti_slop_failed":["..."],"verdict":"PASS|FAIL",
"reason":"frase curta em pt",
"feedback_for_designer":"instrução ACIONÁVEL do que mudar e pra onde, comparando com a referência (vazio se PASS)"}}
verdict = PASS só se same_designer=yes E integrity=ok E invented_text=no E anti_slop_failed=[]."""


def critique(png_bytes: bytes, copy: dict, reference: dict, marca: str,
             model: str | None = None) -> dict:
    """Crítica comparativa da peça produzida contra a referência do banco.

    `reference` = dict de pick_reference() (precisa de 'path' e 'meta'). Retorna
    {same_designer, integrity, invented_text, anti_slop_failed, verdict, reason,
    feedback_for_designer}. SKIPPED se OpenAI indisponível ou erro.
    """
    if not reference or not reference.get("path"):
        return {"verdict": "SKIPPED", "reason": "sem referência"}
    try:
        from litellm import completion
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"litellm indisponível: {e}"}

    # Mesmo provider do cérebro por padrão (claude) — funciona no deploy sem OpenAI.
    provider = (os.getenv("VISION_QA_PROVIDER") or os.getenv("LLM_PROVIDER", "claude")).lower()
    model = model or os.getenv("CRITIC_MODEL") or os.getenv("VISION_QA_MODEL") or {
        "claude": os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"),
        "openai": "gpt-4.1",
        "gemini": os.getenv("LLM_MODEL_GEMINI", "gemini-2.5-flash"),
    }.get(provider, os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"))
    copy_txt = (
        f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}"
    ).replace("*", "")
    meta = reference.get("meta") or {}
    ref_txt = (f"referência '{reference.get('id')}' — mood={meta.get('mood')} "
               f"intent={meta.get('intent')} foto={meta.get('archetype_foto')}")
    try:
        ref_uri = _img_data_uri(reference["path"])
        prod_uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
        kwargs = {
            "model": model,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": _system(marca)},
                {"role": "user", "content": [
                    {"type": "text", "text": f"CORPUS de texto permitido (a copy):\n{copy_txt}\n\n"
                                             f"[REFERÊNCIA] do banco ({ref_txt}):"},
                    {"type": "image_url", "image_url": {"url": ref_uri}},
                    {"type": "text", "text": "[PRODUZIDA] — a peça nova a julgar:"},
                    {"type": "image_url", "image_url": {"url": prod_uri}},
                    {"type": "text", "text": "Julgue a PRODUZIDA contra a REFERÊNCIA."},
                ]},
            ],
            "timeout": float(os.getenv("VISION_QA_TIMEOUT_S", "60")),
            "num_retries": int(os.getenv("LLM_NUM_RETRIES", "2")),
        }
        if not str(model).startswith(("claude-", "anthropic/")):
            kwargs["temperature"] = 0
        resp = completion(**kwargs)
        content = resp.choices[0].message.content or ""
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        m = re.search(r"\{.*\}", content, re.DOTALL)
        out = json.loads(m.group(0) if m else content)
        out.setdefault("verdict", "PASS")
        out["reference_id"] = reference.get("id")
        return out
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"critic falhou: {e.__class__.__name__}"}
