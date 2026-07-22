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

Retorna {verdict: PASS|FAIL, relevance, integrity, safe_zones, reason}.

Visão via LiteLLM (mesmo caminho do cérebro) — provider-agnóstico. Por padrão
usa o MESMO provider do cérebro (`LLM_PROVIDER`, default claude): assim o loop
de QA enxerga com Claude e FUNCIONA no deploy. Antes usava a OpenAI direto —
com a OpenAI fora do ar (cota) a QA voltava SKIPPED e o loop ficava CEGO, nunca
regenerava. Override: VISION_QA_PROVIDER / VISION_QA_MODEL.
"""
from __future__ import annotations

import base64
import json
import os
import re


_SYS_BASE = """Você é DIRETOR DE ARTE sênior fazendo a revisão final de um anúncio da
Metta (inteligência comercial, estética editorial séria). Avalie a peça e seja
RIGOROSO — reprova fácil:

1. RELEVÂNCIA (a imagem ilustra a copy?): a cena PRECISA ilustrar o CONCEITO da
   copy — e vale de DUAS formas (o banco real da Metta usa muito a segunda):
   (a) LITERAL: dados/indicador/gestão → dashboard, gráfico, relatório, pessoas
       decidindo sobre números.
   (b) METÁFORA / HUMOR / SÍMBOLO: uma cena conceitual que qualquer um entende como
       a mensagem. Ex: "funcionário do próprio negócio" → pessoa soterrada de papel;
       "apagar incêndio" → mesa/pessoa pegando fogo; "operação implora por babá" →
       chupeta na mesa executiva; "clonar o talento" → pessoa clonada. ISSO É
       relevance:"ok" — NÃO exija dashboard quando a copy pede metáfora.
   Só é relevance:"weak" o retrato GENÉRICO que não ilustra nada (pessoa de blazer
   olhando pro lado, sorriso de stock, sem metáfora nem assunto visível).

2. INTEGRIDADE (a imagem e o layout não mutilam o sujeito?): reprove o defeito
   CLARO (texto SEMPRE fica sobre parte da foto — isso é normal, não reprove por
   isso). É integrity:"broken" quando:
   - a caixa de texto cobre CLARAMENTE o ROSTO/cabeça da pessoa (mais da metade do
     rosto escondida) ou esconde o OBJETO que é a piada/assunto da copy. Se a
     pessoa/objeto aparece OK numa área livre e o card está sobre fundo vazio,
     está CERTO (não é broken) mesmo que o card encoste na silhueta.
   - HÁ UM ROSTO na cena e o TOPO DA CABEÇA / a TESTA está CORTADO pela BORDA
     SUPERIOR da imagem (rosto aparece mas sem NENHUM respiro acima da cabeça —
     o crânio raspa/some na borda de cima). Esse é o erro MAIS COMUM do gerador —
     seja RIGOROSO: rosto presente + topo da cabeça/testa raspando a borda = broken.
     EXCEÇÃO: enquadramento de DETALHE documental SEM rosto nenhum (só mãos, mesa,
     telas, torso) é intencional = ok.
   - a pessoa está cortada pela metade de forma esquisita, espremida no canto, ou
     há corte duro estranho não-intencional.
   - o BLOCO DE TEXTO / card ENCOSTA, RASPA ou fica COLADO no sujeito/ponto focal
     (em especial no rosto) SEM respiro — mesmo que não cubra. A regra da marca: o
     texto vai pra uma ZONA VAZIA da imagem (céu, parede, fundo liso), com FOLGA do
     foco. Se metade da imagem está vazia e o card foi parar encostado no rosto em
     vez de na zona vazia, isso é integrity:"broken". (NÃO confunda com o card sobre
     fundo vazio encostando de leve na silhueta do corpo/ombro = OK.)
   Sujeito parcialmente atrás do card mas com o ROSTO INTEIRO visível E com respiro
   = OK. Recorte de detalhe documental SEM rosto = OK. Fora os casos acima, na
   dúvida com o rosto inteiro e folgado = ok."""

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
        from litellm import completion
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"litellm indisponível: {e}", "relevance": "?", "integrity": "?"}

    # Provider/modelo da VISÃO — por padrão o MESMO do cérebro (claude). É o que
    # faz a QA enxergar no deploy (a OpenAI está fora). Override por env.
    provider = (os.getenv("VISION_QA_PROVIDER") or os.getenv("LLM_PROVIDER", "claude")).lower()
    model = model or os.getenv("VISION_QA_MODEL") or {
        "claude": os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"),
        "openai": "gpt-4.1",
        "gemini": os.getenv("LLM_MODEL_GEMINI", "gemini-2.5-flash"),
    }.get(provider, os.getenv("LLM_MODEL_CLAUDE", "claude-opus-4-8"))

    b64 = base64.b64encode(png_bytes).decode("ascii")
    copy_txt = (
        f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
        f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}"
    ).replace("*", "")
    kwargs = {
        "model": model,
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": _sys_prompt(format_key)},
            {"role": "user", "content": [
                {"type": "text", "text": f"COPY do anúncio:\n{copy_txt}\n\nAvalie a peça:"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]},
        ],
        "timeout": float(os.getenv("VISION_QA_TIMEOUT_S", "60")),
        "num_retries": int(os.getenv("LLM_NUM_RETRIES", "2")),
    }
    # Claude descontinuou temperature; só manda pros demais.
    if not str(model).startswith(("claude-", "anthropic/")):
        kwargs["temperature"] = 0
    try:
        resp = completion(**kwargs)
        content = resp.choices[0].message.content or ""
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        m = re.search(r"\{.*\}", content, re.DOTALL)
        out = json.loads(m.group(0) if m else content)
        out.setdefault("verdict", "PASS")
        return out
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"vision falhou: {e.__class__.__name__}", "relevance": "?", "integrity": "?"}
