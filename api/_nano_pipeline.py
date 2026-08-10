"""Pipeline Nano Banana + referência do banco → motor de layout real.

Núcleo da Fase C (agente de imagem). Gera o FUNDO com o Nano Banana Pro SEMPRE
alimentando a peça real do banco como referência visual (o fundo herda a
linguagem Metta — colagem/editorial/grão/amarelo cirúrgico — em vez de sair
foto cinematográfica genérica), e monta o criativo final pelo motor de layout
real (`_blueprint_render` + `_render_png`).

REGRA DE OURO: nunca gerar só por texto. A referência é o que puxa pra
linguagem Metta (provado em 2026-07-10). A referência sai do
`engine/brand-knowledge/exemplars/metta/_curated-references.json`, filtrada
pela família do blueprint.

Uso:
    from _nano_pipeline import generate_creative
    png, meta = generate_creative("metta", "LIGHT-SURREAL", copy, scene, format="feed")

Latência ~20s (Nano Banana Pro) — cabe na Vercel Pro (maxDuration). Custo ~$0.03-0.05.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

import httpx

_ROOT = Path(__file__).resolve().parent.parent
_CURATED = _ROOT / "data/curated-references.json"
_MODEL = os.getenv("NANO_MODEL", "gemini-3-pro-image-preview")
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# Tratamento Metta explícito — instrui a casar o tratamento fotográfico da
# referência (não a copiar texto/layout). É o que transfere a linguagem da marca.
_METTA_TREAT = (
    "CRITICAL — match the EXACT photographic visual language of the reference image: its "
    "editorial magazine art-direction, its colour grade, its film-grain/print texture, its mood, "
    "and its DISCIPLINED single surgical yellow (#FFBE18) accent. This is Metta's language: "
    "editorial-documentary or surreal-collage, NOT glossy cinematic Hollywood stock, NOT dramatic "
    "movie-still lighting. IGNORE any text, logos or graphic overlays present in the reference — "
    "use ONLY its photographic treatment. Invent a COMPLETELY NEW scene as described. "
    "No text, no words, no letters, no layout copied."
)

# Tratamentos por LINGUAGEM visual do banco real (dna-visual-banco-real.md).
# A referência escolhida carrega `linguagem`; o treatment casa com ela — é o que
# fez a prova v4 bater com o banco (10/10). Sem etiqueta → _METTA_TREAT genérico.
_LANG_TREAT = {
    "L3": ("Comedic conceptual stock photograph: an absurd humorous concept played completely "
           "straight, professional studio photography, crisp commercial lighting, genuine playful "
           "expressions (NOT somber, NOT dramatic). Match the reference's background colour and "
           "palette exactly. "),
    "L4": ("Vintage black-and-white halftone print / paper-collage: cut-out photographic elements "
           "with visible print grain, surreal playful scale, premium 1970s magazine art direction, "
           "generous empty space for typography. Match the reference's background colour (cream, "
           "yellow or near-black) exactly. "),
    "L5": ("Photorealistic still photograph of a single object staged as a deadpan visual joke in "
           "a real business environment, shallow depth of field, warm natural light, the object "
           "treated with the seriousness of a luxury product shot. "),
    "L6": ("Grainy fine-art surreal photograph, painterly muted tones, heavy film grain, dreamlike "
           "atmosphere, tiny human figure in a vast surreal setting, dark vignette for typography. "),
    "L7": ("Documentary corporate detail photograph: hands, desks and screens only — NO faces. "
           "Natural office light, realistic candid business setting, screens showing plausible "
           "abstract dashboards (no readable words). "),
    # LR = foto-editorial realista COM pessoas. Não é linguagem do banco (as fotos
    # reais são L1, proibidas de virar referência) — é o BRIEF de tratamento usado
    # quando NÃO existe imagem de referência de foto pra casar (as 6 famílias-gap).
    # Fiel ao DNA do banco (dna-visual-banco-real.md): editorial-documental, NÃO
    # stock glossy, NÃO luz de filme dramática; amarelo #FFBE18 único e disciplinado.
    "LR": ("Editorial-documentary photograph of real, grounded business people in a real "
           "workplace — candid and believable, in the style of a premium brand magazine, "
           "NOT glossy advertising stock and NOT dramatic movie-still lighting. Soft "
           "directional daylight, restrained warm-neutral palette, gentle film texture, "
           "shallow depth of field, real (softly blurred) office or a clean flat studio "
           "background. At most ONE single disciplined yellow (#FFBE18) accent somewhere "
           "in the scene. Natural, unforced expressions. "),
}
# Tratamento por FAMÍLIA-GAP (B/D/NEWS/OUTROS): as famílias cujo banco só tem foto
# real (L1) ou tipografia (L8) não têm imagem de referência pra casar. Antes caíam
# TODAS no brief genérico LR. Aqui cada uma ganha um brief próprio, fiel ao DNA
# documental do banco (dna-visual-banco-real.md): editorial real, NÃO stock glossy,
# NÃO luz de filme; um único amarelo #FFBE18 disciplinado. Só entra quando o
# art-director NÃO marcou uma linguagem de tratamento (aí a linguagem sempre vence).
_FAMILY_TREAT = {
    # B — "foto no topo abre a cena emocional, headline entrega embaixo".
    "B": ("Editorial-documentary photograph of a real business owner or professional in a "
          "genuine, quietly emotional decision moment inside a real workplace — believable and "
          "unposed, premium brand-magazine style, NOT glossy stock and NOT dramatic movie "
          "lighting. The human subject sits in the UPPER portion of the frame with calm open "
          "space below for typography. Soft directional daylight, restrained warm-neutral "
          "palette, gentle film texture, shallow depth of field. At most ONE disciplined yellow "
          "(#FFBE18) accent. Natural, unforced expression. "),
    # D — fullbleed de tensão/urgência, mas ancorado no real (nada de filme).
    "D": ("Editorial-documentary photograph carrying real, grounded tension — a high-stakes "
          "business moment (a decision under pressure, a turning point) in a believable "
          "workplace, shot like a serious brand documentary and NOT like a movie still. "
          "Full-bleed composition with a naturally darker, restrained palette so bold "
          "typography can overlay one side. Soft realistic light, subtle film grain, shallow "
          "depth of field. At most ONE disciplined yellow (#FFBE18) accent. NO glossy stock, "
          "NO theatrical lighting, NO fake drama. "),
    # NEWS — estética de imprensa/documental crível.
    "NEWS": ("Editorial press-documentary photograph with a credible, journalistic feel — a real "
             "business or newsroom-adjacent scene (a briefing, a desk, a press moment), candid "
             "and believable like premium reportage, NOT glossy advertising stock. Natural "
             "available light, neutral realistic palette, gentle film texture, shallow depth of "
             "field, clean uncluttered background with room for a headline. At most ONE "
             "disciplined yellow (#FFBE18) accent. "),
}

# Anti micro-texto embolado (lição do Alisson): a IA renderiza letras tortas em
# telas/quadros/papéis. Onde a cena tiver esses elementos, eles mostram só formas
# abstratas — nunca texto legível (o dado real vai por cima, no motor de layout).
_NO_MICROTEXT = (
    "Any screen, monitor, laptop, whiteboard, document or paper in the scene shows ONLY "
    "abstract shapes, blurred charts, color blocks or is turned off/reflective — NEVER "
    "readable letters, words or numbers on them. Keep such surfaces out of sharp focus. ")

# Anti-falha de anatomia. O NEG_MODEL_FAILS do art-director (mãos deformadas, dedos
# extras, face distorcida, membros fundidos) NUNCA chegava ao Nano — generate_background/
# generate_via_route não têm parâmetro negative e a chamada nem o passa. A parte de
# texto/logo já está coberta inline (_NO_MICROTEXT + "ABSOLUTELY NO TEXT"); faltava a de
# corpo. Injetado inline no prompt (frase positiva funciona melhor no Gemini que "no ...").
_NO_ANATOMY = (
    "If any person appears, render anatomy correctly: natural hands with exactly five "
    "fingers each, undistorted realistic face, no extra or fused limbs. ")

# Anti cabeça-cortada (P1): o Gemini tende a cortar o topo da cabeça/testa quando
# enquadra pessoas. Cláusula de segurança — inofensiva pra cenas de objeto (só age
# se houver figura humana). O QA (vision) ainda reprova como rede de segurança.
_HEADROOM = (
    "If any person or human figure appears, keep their ENTIRE head fully inside the frame "
    "with comfortable empty space above the top of the head — NEVER crop the top of the "
    "head, the forehead or the chin against the frame edge. ")

# Foco-no-ROSTO (P1): o Gemini tende a enquadrar a pessoa de corpo inteiro / de longe,
# deixando o foco cair no tronco ou nas PERNAS (ex.: B-foto saía com a cabeça cortada e
# foco nas pernas). Esta cláusula fixa o RECORTE (cabeça+ombros até meio-tronco, rosto
# como ponto focal), NÃO a posição vertical — quem manda na faixa vazia é o `zone` do
# text_anchor, então as duas convivem. Guarda "se uma pessoa for o sujeito" → inerte em
# cena de objeto/tipografia, igual ao _HEADROOM. Rede de segurança: o QA (vision) reprova.
_FACE_FOCAL = (
    "If a person is the main subject, use a HEAD-AND-SHOULDERS to mid-torso crop so the "
    "FACE reads as the clear focal point at natural portrait scale, shot at eye level. "
    "NEVER frame the person full-body or from the waist down, never let the legs or lower "
    "torso become the focal point instead of the face, and never shoot from so far away "
    "that the face turns small. ")

# Linguagens que NUNCA servem de referência de geração: L1 = foto real do
# especialista (geraria um "especialista falso"); L2 = still de filme (direitos).
_NO_GEN_REF = {"L1", "L2"}

# Tratamento GRÁFICO por modelo — sobrepõe o tratamento por linguagem quando o
# estilo NÃO é foto. Ex: YELLOW-OBJETO é clay 3D sobre amarelo chapado; o Gemini
# vinha tratando como foto realista (saía objeto cinza num quarto real). Com isso
# o modelo gera do BRIEF gráfico, SEM referência de foto (que puxa pro realista).
_MODEL_TREAT = {
    "YELLOW-OBJETO": (
        "3D rendered illustration in a matte clay / soft-plastic material (like modern "
        "app-onboarding art or a Pixar-style concept render) — NOT photography, NOT a real "
        "photo, NOT a 2D cartoon. A SINGLE large hero object filling ~70-85% of the frame "
        "width, floating isolated on a SOLID FLAT YELLOW background (#F5C518) that reaches "
        "ALL FOUR edges with NO gradient, NO texture, NO real room or environment. Soft "
        "studio lighting, gentle contact shadow under the object, matte finish, at most 1-2 "
        "muted accent colours on the object itself. High-quality 3D render. "
        "Absolutely NO photorealism, NO real scene, NO people. "),
}

# blueprint model_id → família no banco de referências curado.
_FAMILY = {
    "A-headline-foto-dark": "A", "FOTO-PILL-CASUAL": "A", "I-retrato-editorial-pb": "A",
    "B-foto-top-headline-mixed": "B",
    "C-tipografia-pura-dark": "C",
    "D-foto-fullbleed-overlay": "D",
    "DARK-CARTA": "DARK", "DARK-COLAGEM": "DARK", "DARK-OBJETO": "DARK",
    "LIGHT-SURREAL": "LIGHT", "LIGHT-TIPO": "LIGHT",
    "NEWS-CARD": "NEWS",
    "YELLOW-BLOCO": "YELLOW", "YELLOW-DRAW": "YELLOW", "YELLOW-EDITORIAL": "YELLOW",
    "YELLOW-FRAME": "YELLOW", "YELLOW-OBJETO": "YELLOW", "YELLOW-SPLIT": "YELLOW",
    "H-fundo-branco-headline-gigante": "OUTROS", "K-bold-dourado-urgencia": "OUTROS",
}

# formato do canvas → proporção nativa que o Nano Banana entrega (sem letterbox).
_ASPECT = {"feed": "4:5", "story": "9:16", "sqr": "1:1"}

# Blueprints puramente tipográficos / sem foto — não geram fundo.
_NO_PHOTO = {"C-tipografia-pura-dark", "H-fundo-branco-headline-gigante",
             "METTA-TWEET-CARD", "LOGO-WALL", "LIGHT-TIPO"}


class NanoPipelineError(RuntimeError):
    pass


def _load_curated() -> dict:
    try:
        return json.loads(_CURATED.read_text(encoding="utf-8"))
    except Exception as e:  # pragma: no cover
        raise NanoPipelineError(f"não consegui ler _curated-references.json: {e}")


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"\w{3,}", (s or "").lower()))


_GENERATED = _ROOT / "data/generated-index.json"


def approved_generated_refs(marca: str, copy: dict | None = None, limit: int = 1) -> list[str]:
    """Peças APROVADAS da biblioteca 'Criativos gerados' (generated-index.json) que
    servem de INSPIRAÇÃO ao diretor de arte na criação (fecha o loop: peça boa que
    saiu vira referência da casa — F8 do Alisson). Filtra pela marca e desempata por
    overlap de tokens com a copy. São composições PRONTAS (com texto): valem pro
    diretor VER o estilo/composição — NÃO entram como referência de geração de
    imagem (Nano Banana), que segue só o banco real. Retorna caminhos de arquivo."""
    try:
        d = json.loads(_GENERATED.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = [it for it in d.get("items", [])
             if str(it.get("brand", "")).lower() == (marca or "").lower()
             and it.get("type") != "carousel"
             and (_ROOT / it.get("src", "")).is_file()]
    if not items:
        return []
    q = _tokens((copy or {}).get("headline", "")) | _tokens((copy or {}).get("subhead", ""))
    items.sort(key=lambda it: len(q & _tokens(f"{it.get('headline','')} {it.get('nota','')}")),
               reverse=True)
    return [str(_ROOT / it["src"]) for it in items[:max(1, limit)]]


# scene_type/brief do art-director → LINGUAGEM (tratamento fotográfico) do banco.
# A referência transfere TRATAMENTO (grão/paleta/luz), e o tratamento mora na
# linguagem — NÃO na família. Por isso a seleção casa a linguagem no banco INTEIRO.
# Ordem importa: o 1º grupo que casar vence (L3→L7).
_SCENE_TO_LANG = [
    (("comic", "cômic", "conceito-comic", "comedic", "absurd"), "L3"),
    (("colagem", "collage", "halftone", "vintage", "gravura", "cut-out", "cutout"), "L4"),
    (("humor-objeto", "humor por objeto", "single object", "object gag", "object",
      "objeto simból", "trophy", " lone ", "deadpan"), "L5"),
    (("surreal", "fine-art", "fine art", "dreamlike", "painterly", "granulad"), "L6"),
    (("documental", "documentary", "detalhe", "no faces", "sem rosto"), "L7"),
]
# Linguagens que carregam TRATAMENTO fotográfico (servem de referência de foto).
# L1/L2 = foto real/filme (proibidas); L8 = tipografia (não tem foto pra transferir).
_PHOTO_LANGS = {"L3", "L4", "L5", "L6", "L7"}


def _lang_from_scene(scene_type: str, scene_text: str) -> str | None:
    """Linguagem de tratamento que o art-director pediu, lida do scene_type + do
    texto da cena/brief. Retorna 'L3'..'L7' ou None (aí cai no fallback família)."""
    s = f"{scene_type or ''} {scene_text or ''}".lower()
    for keys, lg in _SCENE_TO_LANG:
        if any(k in s for k in keys):
            return lg
    return None


def _photo_refs_all() -> list[dict]:
    """Refs do banco INTEIRO que carregam tratamento fotográfico (L3-L7) e existem
    em disco. Cada uma marcada com _family (pra preferir a família na desempate)."""
    cur = _load_curated()
    out = []
    for fam, v in cur.get("by_family", {}).items():
        for r in ((v or {}).get("refs", []) if isinstance(v, dict) else []):
            if r.get("linguagem") in _PHOTO_LANGS and (_ROOT / r.get("path", "")).is_file():
                out.append({**r, "_family": fam})
    return out


def _ref_out(best: dict, fam: str, cur: dict) -> dict:
    return {
        "family": best.get("_family", fam),
        "id": best["id"],
        "path": str(_ROOT / best["path"]),
        "linguagem": best.get("linguagem"),
        "motor": ((cur.get("by_family", {}).get(fam) or {}).get("motor", "nano-banana-2")),
    }


def pick_reference(model_id: str, copy: dict, scene: str = "",
                   scene_type: str = "") -> dict | None:
    """Referência visual do banco. Retorna {family,id,path,linguagem,motor} ou None.

    ESTRATÉGIA: a referência transfere TRATAMENTO, e tratamento = linguagem, não
    família. Então:
    1) Se o art-director escolheu uma linguagem de tratamento (cômica/colagem/objeto/
       surreal/documental), casa essa linguagem no banco INTEIRO — resolve famílias
       B/D/NEWS que não têm ref de foto própria (hoje caem numa tipografia L8 inútil)
       e casa o CONCEITO, não só a família.
    2) Fallback: comportamento antigo por família (desempate por tokens da copy).
    """
    fam = _FAMILY.get(model_id, "OUTROS")
    cur = _load_curated()

    # 1) SELEÇÃO POR CONCEITO/LINGUAGEM (global) -------------------------------
    target = _lang_from_scene(scene_type, scene)
    if target:
        pool = [r for r in _photo_refs_all() if r.get("linguagem") == target]
        if pool:
            q = _tokens(f"{scene} {copy.get('headline','')} {copy.get('subhead','')}")

            def _score(r):
                overlap = len(q & _tokens(
                    f"{r.get('title','')} {r.get('mood','')} {r.get('archetype_foto','')}"))
                return overlap + (1 if r.get("_family") == fam else 0)  # leve prefer. da família

            return _ref_out(max(pool, key=_score), fam, cur)

    # 2) FALLBACK POR FAMÍLIA — só refs de FOTO (L3-L7) -------------------------
    # L1/L2 (foto real/filme) e L8 (tipografia pura) NUNCA guiam uma foto: L1/L2 por
    # direitos/identidade, L8 porque não tem tratamento fotográfico pra transferir
    # (o bug antigo: pescar um pôster de tipografia como "referência de foto").
    refs = (cur.get("by_family", {}).get(fam, {}) or {}).get("refs", [])
    refs = [r for r in refs
            if r.get("linguagem") in _PHOTO_LANGS and (_ROOT / r.get("path", "")).is_file()]
    if refs:
        q = _tokens(f"{scene} {copy.get('headline','')} {copy.get('subhead','')}")
        best = max(refs, key=lambda r: len(q & _tokens(
            f"{r.get('title','')} {r.get('mood','')} {r.get('archetype_foto','')}")))
        return _ref_out(best, fam, cur)

    # 3) GAP DE REFERÊNCIA — nenhuma imagem de foto no banco pra este conceito/família
    # (famílias B/D/NEWS/OUTROS/LOGO/TIAGO). Em vez de falhar (→ gpt-image genérico)
    # ou pescar tipografia, gera com um BRIEF de tratamento (texto) casado com a
    # linguagem pedida, ou realista-editorial (LR) por padrão — SEM imagem anexa.
    if target and _LANG_TREAT.get(target):
        # o art-director marcou uma linguagem — ela sempre vence
        brief_lang, brief, brief_id = target, _LANG_TREAT[target], f"brief:{target}"
    elif _FAMILY_TREAT.get(fam):
        # família-gap com brief próprio (B/D/NEWS) em vez do LR genérico
        brief_lang, brief, brief_id = "LR", _FAMILY_TREAT[fam], f"brief:fam:{fam}"
    else:
        brief_lang, brief, brief_id = "LR", _LANG_TREAT["LR"], "brief:LR"
    return {
        "family": fam,
        "id": brief_id,
        "path": None,
        "linguagem": brief_lang,
        "brief": brief,
        "motor": ((cur.get("by_family", {}).get(fam) or {}).get("motor", "nano-banana-2")),
    }


def _sniff_mime(data: bytes) -> str:
    """Detecta o mime real pelos magic bytes — a API do Gemini às vezes
    devolve JPEG mesmo quando pedimos imagem (rotular errado quebraria a
    data URI em parsers estritos)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"  # fallback razoável


def _api_key(explicit: str | None) -> str:
    key = explicit or os.getenv("GEMINI_API_KEY") or os.getenv("GK") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise NanoPipelineError("GEMINI_API_KEY ausente (defina no ambiente / .env.local / Vercel).")
    return key


def generate_background(model_id: str, copy: dict, scene: str,
                        format: str = "feed", api_key: str | None = None,
                        scene_type: str = "") -> tuple[bytes, dict]:
    """Gera o FUNDO via Nano Banana Pro com a referência do banco injetada.

    `scene` = descrição EM INGLÊS da cena/conceito (idealmente vinda do diretor de
    arte). `scene_type` = tag do art-director (ex: 'foto-conceito-comica') usada pra
    casar a LINGUAGEM da referência. Retorna (png_bytes, meta). Levanta em falha.
    """
    ref = pick_reference(model_id, copy, scene=scene, scene_type=scene_type)
    if not ref:
        raise NanoPipelineError(
            f"sem referência de banco pra '{model_id}' — NÃO gerar só por texto "
            f"(regra de ouro). Adicione refs da família no _curated-references.json.")
    key = _api_key(api_key)
    aspect = _ASPECT.get(format, "4:5")

    ref_path = ref.get("path")
    # Zona reservada pro texto: o diretor de arte decide a âncora (top|bottom)
    # e a IMAGEM nasce com aquela faixa vazia — o layout ancora o texto ali e
    # nunca tampa o sujeito. (Nunca mencionar "texto" pro modelo: só espaço vazio.)
    # Default: objeto/cena sem âncora explícita → topo vazio (sujeito embaixo). Sem
    # isso o gerador CENTRALIZA o sujeito e não sobra metade limpa (o focus map não
    # tem como salvar depois). Steering forte (~45%, não "um terço") + focus map = 1 shot.
    anchor = str(copy.get("text_anchor") or "top").strip().lower()
    zone = {"top": ("Composition: the subject sits ENTIRELY in the LOWER HALF of the frame; "
                    "its highest point does not rise above the vertical middle. The ENTIRE "
                    "UPPER 45% is clean, dark, softly blurred EMPTY space with nothing in it. "),
            "bottom": ("Composition: the subject sits ENTIRELY in the UPPER HALF of the frame; "
                       "its lowest point does not go below the vertical middle. The ENTIRE "
                       "LOWER 45% is clean, softly blurred EMPTY space with nothing in it. ")}.get(anchor, "")
    # brief (já resolvido no pick_reference — pode ser o da família-gap) vence o mapa
    # por linguagem; sem brief (refs de foto L3-L7) casa o tratamento pela linguagem.
    lang_treat = ref.get("brief") or _LANG_TREAT.get(ref.get("linguagem") or "") or ""
    # Estilo gráfico por modelo (ex: YELLOW-OBJETO clay-3D) vence o tratamento por
    # linguagem E dispensa a referência de foto (que puxaria pro realista).
    _mt = _MODEL_TREAT.get(model_id)
    if _mt:
        ref_path = None
        lang_treat = _mt
    if ref_path:
        refp = Path(ref_path)
        b64ref = base64.b64encode(refp.read_bytes()).decode("ascii")
        mime = "image/webp" if refp.suffix.lower() == ".webp" else "image/png"
        prompt = (
            "Use the attached real advertisement ONLY as a style reference: match its photographic "
            "treatment, grain, palette and lighting exactly; IGNORE its text, layout and typography. "
            f"Create: {lang_treat}Scene: {scene.strip()} {zone}{_FACE_FOCAL}{_HEADROOM}{_NO_MICROTEXT}{_NO_ANATOMY}"
            "ABSOLUTELY NO TEXT: no words, letters, numbers, logos or watermarks in the image.")
        parts = [{"text": prompt}, {"inlineData": {"mimeType": mime, "data": b64ref}}]
    else:
        # GAP DE REFERÊNCIA: sem imagem no banco pra este conceito. Gera do BRIEF de
        # tratamento (texto) — on-brand — em vez de anexar uma imagem enganosa.
        treat = lang_treat or _METTA_TREAT
        prompt = (
            "Invent a completely new image from scratch (no reference image is provided). "
            f"Create: {treat}Scene: {scene.strip()} {zone}{_FACE_FOCAL}{_HEADROOM}{_NO_MICROTEXT}{_NO_ANATOMY}"
            "ABSOLUTELY NO TEXT: no words, letters, numbers, logos or watermarks in the image.")
        parts = [{"text": prompt}]

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": aspect}},
    }
    url = _GEMINI_URL.format(model=_MODEL, key=key)
    t0 = time.time()
    for attempt in (1, 2):
        r = httpx.post(url, json=payload, timeout=240)
        if r.status_code == 200:
            break
        if attempt == 1:  # alguns modelos recusam imageConfig — tenta sem
            payload["generationConfig"].pop("imageConfig", None)
            continue
        raise NanoPipelineError(f"Nano Banana {r.status_code}: {r.text[:200]}")
    for c in r.json().get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            inl = p.get("inlineData") or p.get("inline_data")
            if inl and inl.get("data"):
                png = base64.b64decode(inl["data"])
                meta = {"model": _MODEL, "ref_id": ref["id"], "family": ref["family"],
                        "linguagem": ref.get("linguagem"), "aspect": aspect,
                        "ms": int((time.time() - t0) * 1000), "bytes": len(png)}
                return png, meta
    raise NanoPipelineError("Nano Banana não retornou imagem.")


def resolve_route(model_id: str) -> str:
    """Motor pra este blueprint: 'nano-banana' ou 'gpt-image'. Decide POR
    FAMÍLIA (curated-references.json) — DARK/LIGHT (conceitual/surreal) ficam
    no gpt-image; A/B/C/D/NEWS/OUTROS/TIAGO (foto-real) vão pro Nano Banana.

    Fallback SEMPRE seguro: sem GEMINI_API_KEY disponível, cai pra gpt-image
    mesmo que a família mande Nano Banana — nunca quebra a geração por falta
    de chave (útil enquanto a chave ainda não está configurada na Vercel).
    """
    if model_id in _NO_PHOTO:
        return "gpt-image"  # sem foto — não passa pelo Nano Banana de qualquer forma
    # Override: com IMAGE_ROUTE_FORCE=nano-banana|gemini (+ chave), TUDO com foto
    # vai pro Gemini — inclusive DARK/LIGHT que normalmente iriam pro gpt-image.
    # Útil quando a OpenAI está fora (teto de billing): o gpt-image morto viraria
    # mock; assim o Gemini (que funciona) assume os slides de objeto/conceito.
    # (Env DEDICADA — não a IMAGE_GEN_PROVIDER, que o ImageGenAdapter valida e
    # quebraria com um valor 'nano-banana'.)
    _force = (os.getenv("IMAGE_ROUTE_FORCE") or "").lower()
    if _force in ("nano-banana", "nano-banana-2", "gemini") and (
            os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        return "nano-banana"
    fam = _FAMILY.get(model_id, "OUTROS")
    try:
        cur = _load_curated()
        motor = (cur.get("by_family", {}).get(fam, {}) or {}).get("motor", "gpt-image-2")
    except Exception:
        motor = "gpt-image-2"
    if motor == "hibrido":
        motor = "nano-banana-2"  # peças YELLOW com foto tratadas como foto-real
    if motor == "grafico":
        motor = "gpt-image-2"  # sem geração de foto (LOGO-WALL etc.)
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if motor != "gpt-image-2" and not has_key:
        return "gpt-image"
    return "nano-banana" if motor != "gpt-image-2" else "gpt-image"


# Motivo do último fallback pro gpt-image — o caller (generate.py) lê e joga no
# diagnóstico. Antes o fallback era MUDO: no deploy a foto virava mock/gpt-image
# sem dizer se foi falta de chave, teto de gasto (429) ou timeout do Pro.
_LAST_ROUTE_ERR: str | None = None


def last_route_error() -> str | None:
    return _LAST_ROUTE_ERR


def generate_via_route(model_id: str, copy: dict, prompt_or_scene: str,
                       format: str = "feed", scene_type: str = "") -> tuple[str, dict] | None:
    """Tenta gerar pelo Nano Banana (com referência do banco) SE a família
    deste blueprint mandar isso e a chave estiver disponível. `scene_type` = tag
    do art-director pra casar a linguagem da referência. Retorna (data_uri, meta)
    em caso de sucesso, ou None (caller segue o caminho gpt-image). O MOTIVO do
    None fica em last_route_error() — nunca mais um fallback mudo.
    """
    global _LAST_ROUTE_ERR
    route = resolve_route(model_id)
    if route != "nano-banana":
        # Diz EXATAMENTE por que não foi pro Gemini (antes juntava tudo num "OU").
        has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        try:
            bank_ok = bool(_load_curated().get("by_family"))
        except Exception:
            bank_ok = False
        why = ("banco ausente no bundle (data/curated-references.json fora do deploy)"
               if not bank_ok else
               "sem GEMINI_API_KEY no ambiente" if not has_key else
               "motor da família não é nano-banana")
        _LAST_ROUTE_ERR = f"rota={route} — {why}"
        return None
    try:
        raw, meta = generate_background(model_id, copy, prompt_or_scene,
                                        format=format, scene_type=scene_type)
        mime = _sniff_mime(raw)
        _LAST_ROUTE_ERR = None
        return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii"), meta
    except Exception as e:
        _LAST_ROUTE_ERR = f"{e.__class__.__name__}: {str(e)[:180]}"
        return None


def generate_creative(marca: str, model_id: str, copy: dict, scene: str,
                      format: str = "feed", api_key: str | None = None) -> tuple[bytes, dict]:
    """Criativo PRONTO: fundo (Nano Banana + referência) → motor de layout real.

    Retorna (png_final, meta). Requer Chromium (Playwright) pro render — o mesmo
    que o resto do pipeline já usa.
    """
    if model_id in _NO_PHOTO:
        raise NanoPipelineError(f"'{model_id}' é tipográfico/sem foto — não usa Nano Banana.")
    from _blueprint_render import render
    from _render_png import render_format

    bg, meta = generate_background(model_id, copy, scene, format=format, api_key=api_key)
    # FOCUS MAP (Fase 1.1): mede a imagem REAL e ancora o texto na zona vazia —
    # não confia no prompt ter deixado o topo/base livre. É o que garante, em 1
    # geração, que o texto não tampe o sujeito (matou os "3 retries" do troféu).
    try:
        from _focus_map import focus_anchor
        anc, fmeta = focus_anchor(bg)
        meta["focus_map"] = fmeta
        if not fmeta.get("ambiguous"):
            copy = {**copy, "text_anchor": anc}
    except Exception as _e:
        meta["focus_map"] = {"error": str(_e)[:80]}
    data_uri = f"data:{_sniff_mime(bg)};base64," + base64.b64encode(bg).decode("ascii")
    res = render(marca, model_id, copy, image_url=data_uri, format=format)
    if res.get("missing"):
        raise NanoPipelineError(f"blueprint '{model_id}' não encontrado pro motor de layout.")
    png = render_format(res["html"], fmt=format)
    meta["final_bytes"] = len(png)
    return png, meta


# ---------------------------------------------------------------------------
# Carrossel panorâmico: 1 imagem larga → fatiada em N slides que se completam.
# É 1 geração só (cabe na Vercel ~20s) + fatiamento local (PIL). Resolve o
# limite de timeout: metade da imagem no slide 1, metade no 2 (o que a Sofia pediu).
# ---------------------------------------------------------------------------
_PANO_ASPECT = {2: "3:2", 3: "21:9", 4: "21:9"}


def generate_panorama(scene: str, n_slides: int = 2, family: str = "A",
                      api_key: str | None = None) -> tuple[list[bytes], dict]:
    """Gera UMA imagem panorâmica (Nano Banana Pro, com referência da família pra
    herdar a linguagem Metta) e FATIA em n_slides verticais que se completam.

    Retorna (lista_de_png_por_slide, meta). O texto por cima fica a cargo do
    render/front — aqui são só os fundos contínuos. n_slides ∈ [2,4].
    """
    # (io/PIL não são usados aqui — o fatiamento é delegado a slice_panorama,
    # que faz o próprio import; imports mortos removidos na auditoria.)
    n_slides = max(2, min(4, int(n_slides)))
    aspect = _PANO_ASPECT.get(n_slides, "3:2")
    key = _api_key(api_key)

    # referência de coerência: 1ª peça da família (charcoal/editorial) do banco.
    cur = _load_curated()
    refs = [r for r in (cur.get("by_family", {}).get(family, {}) or {}).get("refs", [])
            if (_ROOT / r.get("path", "")).is_file()]
    gen_ok = [r for r in refs if r.get("linguagem") not in _NO_GEN_REF]
    if gen_ok:
        refs = gen_ok
    parts: list[dict] = [{"text": (
        f"Invent ONE single continuous ultra-wide image. Scene: {scene.strip()} {_METTA_TREAT}")}]
    ref_id = None
    if refs:
        refp = _ROOT / refs[0]["path"]
        ref_id = refs[0]["id"]
        parts.append({"inlineData": {
            "mimeType": "image/webp" if refp.suffix.lower() == ".webp" else "image/png",
            "data": base64.b64encode(refp.read_bytes()).decode("ascii")}})

    payload = {"contents": [{"parts": parts}],
               "generationConfig": {"responseModalities": ["IMAGE"],
                                    "imageConfig": {"aspectRatio": aspect}}}
    url = _GEMINI_URL.format(model=_MODEL, key=key)
    t0 = time.time()
    for attempt in (1, 2):
        r = httpx.post(url, json=payload, timeout=300)
        if r.status_code == 200:
            break
        if attempt == 1:
            payload["generationConfig"].pop("imageConfig", None)
            continue
        raise NanoPipelineError(f"Nano Banana panorama {r.status_code}: {r.text[:200]}")

    raw = None
    for c in r.json().get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            inl = p.get("inlineData") or p.get("inline_data")
            if inl and inl.get("data"):
                raw = base64.b64decode(inl["data"])
                break
        if raw:
            break
    if not raw:
        raise NanoPipelineError("Nano Banana não retornou panorama.")

    slices, (W, H) = slice_panorama(raw, n_slides)
    meta = {"model": _MODEL, "aspect": aspect, "n_slides": n_slides,
            "ref_id": ref_id, "size": [W, H], "ms": int((time.time() - t0) * 1000)}
    return slices, meta


def slice_panorama(raw: bytes, n_slides: int) -> tuple[list[bytes], tuple[int, int]]:
    """Fatia uma imagem larga em n_slides tiras verticais que se completam
    (puro/local — sem API). Retorna (pngs_por_slide, (W, H) da original)."""
    import io

    from PIL import Image

    n_slides = max(2, min(4, int(n_slides)))
    img = Image.open(io.BytesIO(raw))
    W, H = img.size
    step = W // n_slides
    slices: list[bytes] = []
    for i in range(n_slides):
        x0 = i * step
        x1 = W if i == n_slides - 1 else (i + 1) * step
        buf = io.BytesIO()
        img.crop((x0, 0, x1, H)).save(buf, format="PNG")
        slices.append(buf.getvalue())
    return slices, (W, H)
