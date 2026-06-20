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


def _system(marca: str) -> str:
    dna = (
        "Metta = inteligência comercial B2B: editorial sério (HBR/Bloomberg), dark moody, "
        "autoridade, display Zalando Sans Expanded, amarelo Metta CIRÚRGICO (nunca difuso)."
        if (marca or "").lower() != "tiago" else
        "Tiago Alves = marca pessoal cinematográfica: B&W de alto contraste com UM amarelo "
        "seletivo (#FFCC00), grão analógico 35mm, autoral, nunca corporativo."
    )
    return f"""Você é o DIRETOR DE CRIAÇÃO fazendo a aprovação FINAL de um anúncio antes
de publicar. {dna}

Olhe a peça acabada e dê uma nota 0-10 (decimais ok) em CADA dimensão:

- **relevancia**: a imagem/cena ilustra a MENSAGEM da copy? (copy de dado/método/gestão
  pede algo concreto à vista; retrato genérico que não comunica o tema = nota baixa)
- **marca**: fidelidade ao DNA da marca acima (paleta, tipografia, mood, uso do amarelo)?
- **hierarquia**: leitura clara (headline domina, sub apoia, CTA evidente), legível num
  feed comprimido no mobile?
- **acabamento**: polish e integridade — nada cortado sem querer, sem AI-slop (gradiente
  arco-íris, glassmorphism, amarelo decorativo difuso, centrado genérico, texto torto na
  foto, badge de e-commerce), respiro correto?

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
{{"scores":{{"relevancia":0,"marca":0,"hierarquia":0,"acabamento":0}},
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
             model: str | None = None) -> dict:
    """Avalia a peça final. Retorna scores + geral + verdict + fixes (ou SKIPPED)."""
    try:
        from openai import OpenAI
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"openai indisponível: {e}"}

    model = model or os.getenv("EVAL_MODEL") or os.getenv("VISION_QA_MODEL", "gpt-4.1")
    copy_txt = (
        f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}"
    ).replace("*", "")
    try:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model, max_tokens=500,
            messages=[
                {"role": "system", "content": _system(marca)},
                {"role": "user", "content": [
                    {"type": "text", "text": f"COPY do anúncio:\n{copy_txt}\n\nAvalie a peça final:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]},
            ],
        )
        out = _coerce(resp.choices[0].message.content or "")
        out.setdefault("verdict", "REVISAR")
        out.setdefault("scores", {})
        out.setdefault("image_fixable", True)
        out.setdefault("image_feedback", "")
        return _guardrail(out, vision_result, critic_result)
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"eval falhou: {e.__class__.__name__}"}
