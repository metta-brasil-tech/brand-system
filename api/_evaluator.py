"""Avaliador FINAL — a nota holística da peça pronta (SHIP / REVISAR / DESCARTAR).

É a 3ª camada de avaliação, diferente das outras duas:
  - `_vision_qa.py`  → a imagem ILUSTRA a copy? o layout mutila? (peça isolada)
  - `_critic.py`     → same-designer test vs banco + anti-slop + texto inventado
  - `_evaluator.py`  → **juiz final**: olha a peça acabada, dá nota 0-10 por dimensão,
                       um veredito de publicação e os ajustes que mais elevam a nota.

Consolida os sinais que o pipeline já computou (vision_qa + critic) como GUARDRAIL
determinístico: defeito objetivo (texto inventado / corte / layout quebrado) limita o
veredito por baixo, independente do que o juiz holístico ache. Assim a nota é honesta.

Degrada gracioso (SKIPPED) sem OpenAI, igual às outras camadas.
"""
from __future__ import annotations

import base64
import json
import os
import re

_DIMS = ("relevancia", "marca", "hierarquia", "acabamento")


def _intent_block(dl: dict | None) -> str:
    """Resumo da INTENÇÃO do diretor de arte (do 03-decision-log.json) pra o juiz
    confrontar intenção × peça final. Vazio se não houver decision-log."""
    if not dl:
        return ""
    av = dl.get("avatar") or {}
    ad = dl.get("art_director") or {}
    prov = dl.get("knowledge_provenance") or []
    fontes = "; ".join(f"{p.get('tipo')}: {str(p.get('fonte','')).strip()[:50]}" for p in prov[:6])
    ic = ad.get("image_concept") or {}
    cena = (ic.get("scene_type") or ic.get("scene") or "") if isinstance(ic, dict) else str(ic)
    parts: list[str] = []
    if av.get("segment"):
        parts.append(f"AVATAR/ICP alvo: segmento={av.get('segment')} variante={av.get('variant','')}")
    if ad.get("rationale"):
        parts.append(f"RACIOCÍNIO do diretor: {str(ad['rationale'])[:400]}")
    if cena:
        parts.append(f"CENA pretendida: {cena}")
    if ad.get("crop_focus") or ad.get("gaze_direction"):
        parts.append(f"enquadramento pretendido: foco={ad.get('crop_focus','')} olhar={ad.get('gaze_direction','')}")
    if fontes:
        parts.append(f"ANCORADO no conhecimento da marca: {fontes}")
    return "\n".join(parts)


def _user_direction_block(user_direction: str = "") -> str:
    """Achado #5: quando o usuário dá direção visual EXPLÍCITA, ela domina o juízo —
    senão o avaliador penaliza 'falta de persona/ICP' numa peça que o user pediu sem
    pessoas (dava 9.4 pra versão com pessoa vs 7.8 pra só-objeto que o user QUERIA)."""
    ud = (user_direction or "").strip()
    if not ud:
        return ""
    return (
        f"\n\n⚠️ DIREÇÃO VISUAL EXPLÍCITA DO USUÁRIO (PRIORIDADE MÁXIMA): \"{ud}\"\n"
        "Julgue a fidelidade a ESSA direção acima de tudo. Se o usuário pediu SEM pessoas, "
        "só objeto, ou uma cena específica, ESSA é a intenção correta — NÃO penalize a "
        "ausência de persona/retrato/ICP na foto e NÃO sugira 'adicionar pessoa'. Aqui a "
        "ancoragem se mede pela direção do usuário, não pelo avatar-persona padrão: uma peça "
        "que HONRA a direção do usuário merece nota ALTA mesmo sem pessoa nenhuma."
    )


def _system(marca: str, has_intent: bool = False, image_based: bool = True,
            user_direction: str = "") -> str:
    dna = (
        "Metta = inteligência comercial B2B: editorial sério (HBR/Bloomberg), dark moody, "
        "autoridade, display Zalando Sans Expanded, amarelo Metta CIRÚRGICO (nunca difuso)."
        if (marca or "").lower() != "tiago" else
        "Tiago Alves = marca pessoal cinematográfica: B&W de alto contraste com UM amarelo "
        "seletivo (#FFCC00), grão analógico 35mm, autoral, nunca corporativo."
    )
    if has_intent and image_based:
        intent_dim = (
            "\n- **ancoragem**: a peça é FIEL à INTENÇÃO do diretor de arte (bloco INTENÇÃO "
            "abaixo)? a persona/cena retratada condiz com o AVATAR/ICP alvo, e a copy ilustra "
            "o método/depoimento que ancorou a decisão? (ex.: ICP é dono de PME 40-55 mas a foto "
            "mostra jovem genérico de stock; a copy fala de método mas a cena é um retrato vazio "
            "que não comunica o tema = nota baixa). Julgue a fidelidade INTENÇÃO→PEÇA, não só o pixel."
        )
    elif has_intent:  # peça tipográfica: ancoragem julga COPY/voz, não persona-foto
        intent_dim = (
            "\n- **ancoragem**: a COPY e o tratamento tipográfico honram a INTENÇÃO do diretor "
            "(bloco INTENÇÃO abaixo)? o discurso fala com o AVATAR/ICP alvo e ativa o método/"
            "depoimento que ancorou a decisão? NÃO exija foto/persona aqui — esta peça é "
            "tipográfica por design."
        )
    else:
        intent_dim = ""
    intent_schema = ',"ancoragem":0' if has_intent else ""

    # relevância muda conforme a peça tem foto ou é tipográfica
    if image_based:
        relevancia = (
            "- **relevancia**: a imagem/cena ilustra a MENSAGEM da copy? (copy de dado/método/"
            "gestão pede algo concreto à vista; retrato genérico que não comunica o tema = nota baixa)"
        )
    else:
        relevancia = (
            "- **relevancia**: a TIPOGRAFIA e a composição comunicam a MENSAGEM da copy com força "
            "(frase memorável, ênfase certa, conceito claro)? NÃO penalize a ausência de foto — "
            "esta peça é tipográfica por design; julgue o impacto do texto, não a falta de imagem."
        )
    typo_note = "" if image_based else (
        "\n\nIMPORTANTE: esta peça é TIPOGRÁFICA por design — NÃO usa foto. NÃO baixe a nota por "
        "'falta de imagem/retrato/pessoa' e NÃO sugira 'adicionar foto'. `image_fixable` deve ser "
        "`false` e `image_feedback` vazio (não há foto a regerar)."
    )
    return f"""Você é o DIRETOR DE CRIAÇÃO fazendo a aprovação FINAL de um anúncio antes
de publicar. {dna}{_user_direction_block(user_direction)}

Olhe a peça acabada e dê uma nota 0-10 (decimais ok) em CADA dimensão:{intent_dim}

{relevancia}
- **marca**: fidelidade ao DNA da marca acima (paleta, tipografia, mood, uso do amarelo)?
- **hierarquia**: leitura clara (headline domina, sub apoia, CTA evidente), legível num
  feed comprimido no mobile?
- **acabamento**: polish e integridade — nada cortado sem querer, sem AI-slop (gradiente
  arco-íris, glassmorphism, amarelo decorativo difuso, centrado genérico, texto torto na
  foto, badge de e-commerce), respiro correto?{typo_note}

Depois dê uma **nota geral 0-10** (julgamento, não precisa ser média) e um VEREDITO:
- **SHIP**: publicaria como está (geral >= 7.5 e sem defeito grave).
- **REVISAR**: bom conceito mas precisa de ajuste antes de subir.
- **DESCARTAR**: não serve, refazer.

E liste 1-3 **ajustes** acionáveis (o que mudar e pra onde) que mais elevariam a nota.

Por fim, **image_fixable**: os principais problemas se resolvem REGERANDO A FOTO (cena,
mood, relevância, enquadramento, tratamento)? → `true`. Ou são de LAYOUT/TEMPLATE
(hierarquia tipográfica, cor/posição dos blocos, uso da marca) que regerar a imagem
NÃO muda? → `false` (aí o caminho é trocar de modelo ou editar o blueprint, não re-rodar).

Responda APENAS JSON, sem cercas:
{{"scores":{{"relevancia":0,"marca":0,"hierarquia":0,"acabamento":0{intent_schema}}},
"geral":0,"verdict":"SHIP|REVISAR|DESCARTAR","image_fixable":true,
"image_feedback":"o que a PRÓXIMA foto precisa mostrar/evitar pra subir a nota (1 frase, EN ou PT)",
"fixes":["..."],"reason":"frase curta em pt"}}"""


def _coerce(text: str) -> dict:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.IGNORECASE)
    m = re.search(r"\{.*\}", t, re.DOTALL)
    return json.loads(m.group(0) if m else t)


def _guardrail(out: dict, vision_result: dict | None, critic_result: dict | None) -> dict:
    """Defeito objetivo limita o veredito por baixo — a nota não pode mentir."""
    vr = vision_result or {}
    cr = critic_result or {}
    reasons = []
    # Texto inventado na imagem = defeito grave → no máximo REVISAR (capa em DESCARTAR
    # se também houver quebra de integridade).
    if cr.get("invented_text") == "yes":
        reasons.append("texto inventado na imagem")
        out["verdict"] = "REVISAR" if out.get("verdict") == "SHIP" else out.get("verdict")
    # Integridade quebrada (corte acidental) = não pode SHIP.
    if vr.get("integrity") == "broken" or cr.get("integrity") == "broken":
        reasons.append("integridade do layout quebrada")
        if out.get("verdict") == "SHIP":
            out["verdict"] = "REVISAR"
    # Crítico reprovou no same-designer test = não pode SHIP sem revisão.
    if cr.get("verdict") == "FAIL":
        reasons.append("reprovado no same-designer test")
        if out.get("verdict") == "SHIP":
            out["verdict"] = "REVISAR"
    if reasons:
        out["guardrail"] = reasons
    return out


def evaluate(png_bytes: bytes, copy: dict, marca: str,
             vision_result: dict | None = None, critic_result: dict | None = None,
             model: str | None = None, decision_log: dict | None = None,
             image_based: bool | None = None, user_direction: str | None = None) -> dict:
    """Avalia a peça final. Retorna scores + geral + verdict + fixes (ou SKIPPED).

    Se `decision_log` (03-decision-log.json) for passado, o juiz também confronta a
    INTENÇÃO do diretor de arte (avatar/ICP, raciocínio, cena, conhecimento ancorado)
    com a peça final — dimensão `ancoragem` (passo 4: julga o raciocínio, não só o pixel).
    """
    try:
        from litellm import completion
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"litellm indisponível: {e}"}

    # Juiz FINAL por visão via LiteLLM — mesmo caminho do cérebro (provider-agnóstico).
    # Antes usava o SDK da OpenAI direto; com a OpenAI fora do ar (sem crédito) o
    # avaliador voltava SKIPPED e o PORTÃO FINAL (+ a nota de ranking do auto_improve)
    # ficava MORTO no deploy — a única das 3 camadas de visão ainda presa à OpenAI
    # (o _vision_qa e o _critic já migraram). Agora defaulta pro provider do cérebro
    # (LLM_PROVIDER, default claude). Override: EVAL_PROVIDER / EVAL_MODEL.
    provider = (os.getenv("EVAL_PROVIDER") or os.getenv("LLM_PROVIDER", "claude")).lower()
    model = model or os.getenv("EVAL_MODEL") or os.getenv("VISION_QA_MODEL") or {
        "claude": os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"),
        "openai": "gpt-4.1",
        "gemini": os.getenv("LLM_MODEL_GEMINI", "gemini-2.5-flash"),
    }.get(provider, os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"))
    copy_txt = (
        f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}"
    ).replace("*", "")
    intent = _intent_block(decision_log)
    has_intent = bool(intent)
    if image_based is None:  # default: peça é fotográfica salvo sinal em contrário
        image_based = True
    user_txt = f"COPY do anúncio:\n{copy_txt}\n\n"
    if has_intent:
        user_txt += f"INTENÇÃO do diretor de arte (o que a peça DEVERIA entregar):\n{intent}\n\n"
    user_txt += "Avalie a peça final:"
    try:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        kwargs = {
            "model": model, "max_tokens": 500,
            "messages": [
                {"role": "system", "content": _system(marca, has_intent, image_based, user_direction or "")},
                {"role": "user", "content": [
                    {"type": "text", "text": user_txt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]},
            ],
            "timeout": float(os.getenv("EVAL_TIMEOUT_S", "60")),
            "num_retries": int(os.getenv("LLM_NUM_RETRIES", "2")),
        }
        # Claude descontinuou temperature; só manda pros demais.
        if not str(model).startswith(("claude-", "anthropic/")):
            kwargs["temperature"] = 0
        resp = completion(**kwargs)
        out = _coerce(resp.choices[0].message.content or "")
        out.setdefault("verdict", "REVISAR")
        out.setdefault("scores", {})
        out.setdefault("image_fixable", True)
        out.setdefault("image_feedback", "")
        return _guardrail(out, vision_result, critic_result)
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"eval falhou: {e.__class__.__name__}"}
