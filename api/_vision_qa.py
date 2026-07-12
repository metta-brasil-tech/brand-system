"""Checagem final por VISÃO — diretor de arte revisando a peça renderizada.

Avalia 3 regras (feedback do dono + safe zones do IG):
  1) RELEVÂNCIA: a imagem ILUSTRA a mensagem da copy? (copy de dados → tem
     dashboard/gráfico/reunião à vista? ou é genérica/desconexa?)
  2) INTEGRIDADE: algum elemento principal (pessoa/objeto) está cortado pela
     metade, espremido no canto, ou coberto de forma que parece ACIDENTE (não
     direção de arte intencional)? bloco de cor sobrando em área morta?
  3) SAFE ZONES (quando o formato é conhecido): headline/CTA/marca dentro da
     zona útil do formato — a UI do Instagram cobre topo/rodapé do story e as
     margens do feed truncam. Fonte canônica: content/direcao-arte/safe-zones.md.

Retorna {verdict: PASS|FAIL, relevance, integrity, safe_zones, reason}. Usa OpenAI vision.
"""
from __future__ import annotations

import base64
import json
import os
import re


_SYS_BASE = """Você é DIRETOR DE ARTE sênior fazendo a revisão final de um anúncio da
Metta (inteligência comercial, estética editorial séria). Avalie a peça e seja
RIGOROSO — reprova fácil:

1. RELEVÂNCIA (a imagem ilustra a copy?): a foto/cena PRECISA mostrar o assunto da
   copy. Se a copy fala de dados/indicador/métrica/gestão/decisão, a imagem tem que
   ter algo concreto disso visível (tela com dashboard, gráfico, planilha, relatório,
   pessoas decidindo sobre números). Retrato genérico de "pessoa olhando pro lado"
   sem nada do assunto = relevance:"weak".

2. INTEGRIDADE do layout (o layout respeita a imagem?): NENHUM elemento principal
   pode parecer cortado SEM QUERER — pessoa cortada pela metade, rosto/corpo
   espremido no canto, sujeito coberto por bloco de texto, bloco de cor sobrando
   sobre fundo morto, foto com corte duro estranho. Recorte SÓ vale se for
   claramente intencional (direção de arte). Caso contrário integrity:"broken"."""

# Safe zones por formato — espelho condensado de content/direcao-arte/safe-zones.md.
# Frações da ALTURA da imagem (o modelo de visão não vê coordenadas em px).
_SAFE_ZONES = {
    "story": (
        "3. SAFE ZONES do story IG (1080×1920): a UI do Instagram cobre o topo "
        "~11% (handle/hora) e a base ~15% (botão de ação/navegação) da imagem. "
        "Headline, subhead, CTA e marca precisam estar INTEIROS dentro da faixa "
        "útil (entre ~11% e ~85% da altura). Imagem de fundo pode sangrar; "
        "elemento decorativo intencional pode sair. Essencial coberto/na zona "
        "morta = safe_zones:\"violated\"."
    ),
    "feed": (
        "3. SAFE ZONES do feed IG (1080×1350): elementos essenciais (headline, "
        "subhead, CTA, marca) precisam de respiro de ~4-5% da altura no topo e "
        "na base — nada essencial colado ou cortado nas bordas. Imagem de fundo "
        "pode sangrar. Essencial encostado/cortado = safe_zones:\"violated\"."
    ),
    "sqr": (
        "3. SAFE ZONES do quadrado (1080×1080): elementos essenciais (headline, "
        "subhead, CTA, marca) precisam de respiro de ~4-5% em cada borda — nada "
        "essencial colado ou cortado. Imagem de fundo pode sangrar. Essencial "
        "encostado/cortado = safe_zones:\"violated\"."
    ),
}

_TAIL_2AXIS = """

Responda APENAS JSON, sem cercas:
{"relevance":"ok|weak","integrity":"ok|broken","verdict":"PASS|FAIL","reason":"frase curta em pt"}
verdict = PASS só se relevance=ok E integrity=ok."""

_TAIL_3AXIS = """

Responda APENAS JSON, sem cercas:
{"relevance":"ok|weak","integrity":"ok|broken","safe_zones":"ok|violated","verdict":"PASS|FAIL","reason":"frase curta em pt"}
verdict = PASS só se relevance=ok E integrity=ok E safe_zones=ok."""


def _sys_prompt(format_key: str) -> str:
    zone = _SAFE_ZONES.get((format_key or "").lower())
    if zone:
        return _SYS_BASE + "\n\n" + zone + _TAIL_3AXIS
    return _SYS_BASE + _TAIL_2AXIS


def check(png_bytes: bytes, copy: dict, model: str | None = None,
          format_key: str = "") -> dict:
    """Roda a checagem de visão sobre o PNG renderizado.

    format_key ("feed"|"story"|"sqr") liga o eixo de safe zones; vazio mantém
    o comportamento de 2 eixos.
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
                {"role": "system", "content": _sys_prompt(format_key)},
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
        return out
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"vision falhou: {e.__class__.__name__}", "relevance": "?", "integrity": "?"}
