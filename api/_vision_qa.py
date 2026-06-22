"""Checagem final por VISÃO — diretor de arte revisando a peça renderizada.

Avalia 2 regras (feedback do dono):
  1) RELEVÂNCIA: a imagem ILUSTRA a mensagem da copy? (copy de dados → tem
     dashboard/gráfico/reunião à vista? ou é genérica/desconexa?)
  2) INTEGRIDADE: algum elemento principal (pessoa/objeto) está cortado pela
     metade, espremido no canto, ou coberto de forma que parece ACIDENTE (não
     direção de arte intencional)? bloco de cor sobrando em área morta?

Retorna {verdict: PASS|FAIL, relevance, integrity, reason}. Usa OpenAI vision.
"""
from __future__ import annotations

import base64
import json
import os
import re


_SYS = """Você é DIRETOR DE ARTE sênior fazendo a revisão final de um anúncio da
Metta (inteligência comercial, estética editorial séria). Avalie a peça em 2 eixos
e seja RIGOROSO — reprova fácil:

1. RELEVÂNCIA (a imagem ilustra a copy?): a foto/cena PRECISA mostrar o assunto da
   copy. Se a copy fala de dados/indicador/métrica/gestão/decisão, a imagem tem que
   ter algo concreto disso visível (tela com dashboard, gráfico, planilha, relatório,
   pessoas decidindo sobre números). Retrato genérico de "pessoa olhando pro lado"
   sem nada do assunto = relevance:"weak".

2. INTEGRIDADE do layout (o layout respeita a imagem?): NENHUM elemento principal
   pode parecer cortado SEM QUERER — pessoa cortada pela metade, rosto/corpo
   espremido no canto, sujeito coberto por bloco de texto, bloco de cor sobrando
   sobre fundo morto, foto com corte duro estranho. Recorte SÓ vale se for
   claramente intencional (direção de arte). Caso contrário integrity:"broken".

Responda APENAS JSON, sem cercas:
{"relevance":"ok|weak","integrity":"ok|broken","verdict":"PASS|FAIL","reason":"frase curta em pt"}
verdict = PASS só se relevance=ok E integrity=ok."""


# FASE 3 — variante MODEL-AWARE: quando há DNA do blueprint, a relevância passa a
# ser julgada contra a INTENÇÃO do modelo (não contra a régua fixa "tem que ter
# dashboard"), e um anti-padrão presente reprova direto. Isso conserta os dois
# lados do mesmo defeito: retrato/abstrato deixa de levar `weak` injusto, e
# colagem com humano realista (anti-padrão) deixa de passar.
_SYS_DNA = """Você é DIRETOR DE ARTE sênior fazendo a revisão final de um anúncio da
Metta (inteligência comercial, estética editorial séria). Há um SPEC DO MODELO no
fim da mensagem — use-o como referência. Avalie em 3 eixos e seja RIGOROSO:

1. RELEVÂNCIA (a imagem cumpre a INTENÇÃO do modelo e dialoga com a copy?): julgue
   contra a INTENÇÃO esperada do SPEC, NÃO contra uma régua fixa. Se a intenção do
   modelo é metáfora abstrata, objeto-conceito ou retrato editorial, NÃO exija
   dashboard/gráfico — basta a imagem realizar a intenção do modelo e conversar com
   o tema da copy. Marque relevance:"weak" só se a imagem fugir da intenção do
   modelo OU for genérica a ponto de não dialogar com a copy.

2. INTEGRIDADE do layout: NENHUM elemento principal pode parecer cortado SEM QUERER
   — pessoa/objeto cortado pela metade, espremido no canto, coberto por texto, bloco
   de cor sobrando em área morta, corte duro estranho. Recorte só vale se claramente
   intencional. Caso contrário integrity:"broken".

3. FIDELIDADE AO MODELO: se a peça contém QUALQUER anti-padrão listado no SPEC
   (ex.: "foto humana realista" num modelo de colagem abstrata), marque
   anti_pattern_violated:true e verdict:FAIL — isso é violação grave, não estética.

Responda APENAS JSON, sem cercas:
{"relevance":"ok|weak","integrity":"ok|broken","anti_pattern_violated":false,"verdict":"PASS|FAIL","reason":"frase curta em pt"}
verdict = PASS só se relevance=ok E integrity=ok E anti_pattern_violated=false."""


def _system(model_dna: dict | None) -> str:
    """System prompt da vision-qa. Sem DNA → régua genérica (backward-compat).
    Com DNA útil → variante model-aware + o SPEC do modelo anexado."""
    if not model_dna:
        return _SYS
    try:
        from _blueprint_dna import dna_judge_block
        spec = dna_judge_block(model_dna)
    except Exception:
        spec = ""
    if not spec:
        return _SYS
    return _SYS_DNA + "\n\n" + spec


def check(png_bytes: bytes, copy: dict, model: str | None = None,
          model_dna: dict | None = None) -> dict:
    """Roda a checagem de visão sobre o PNG renderizado.

    `model_dna` (FASE 3): DNA do blueprint. Quando passado, a relevância é julgada
    contra a intenção do modelo e anti-padrão presente reprova (`anti_pattern_violated`).
    """
    try:
        from openai import OpenAI
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"openai indisponível: {e}", "relevance": "?", "integrity": "?"}

    model = model or os.getenv("VISION_QA_MODEL", "gpt-4.1")
    b64 = base64.b64encode(png_bytes).decode("ascii")
    copy_txt = (
        f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}"
    ).replace("*", "")
    try:
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[
                {"role": "system", "content": _system(model_dna)},
                {"role": "user", "content": [
                    {"type": "text", "text": f"COPY do anúncio:\n{copy_txt}\n\nAvalie a peça:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]},
            ],
        )
        content = resp.choices[0].message.content or ""
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        m = re.search(r"\{.*\}", content, re.DOTALL)
        out = json.loads(m.group(0) if m else content)
        out.setdefault("verdict", "PASS")
        out.setdefault("anti_pattern_violated", False)
        return out
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"vision falhou: {e.__class__.__name__}", "relevance": "?", "integrity": "?"}
