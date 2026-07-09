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

1. RELEVÂNCIA (a imagem dialoga com a copy?): a foto/cena deve CONVERSAR com o
   assunto da copy — seja mostrando algo concreto (dashboard, gráfico, reunião sobre
   números) OU traduzindo o tema/mood num retrato editorial, cena ou metáfora coerente.
   NÃO exija dashboard/gráfico quando a peça é retrato ou conceito: um retrato editorial
   sério que carrega o tom da copy já é relevance:"ok". Marque relevance:"weak" só se a
   imagem for genérica E desconexa do tema (não ilustra nem evoca o assunto da copy).

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

3. FIDELIDADE AO MODELO: marque anti_pattern_violated:true SOMENTE quando um item
   da seção rotulada "ANTI-PADRÕES" do SPEC estiver VISIVELMENTE PRESENTE na imagem
   (ex.: o SPEC lista "foto humana realista" como anti-padrão E a peça mostra uma foto
   humana realista). Considere APENAS os bullets dessa lista — NÃO transforme as
   descrições de INTENÇÃO/ESTRUTURA em anti-padrões. Em particular NUNCA dispare por:
   (a) AUSÊNCIA de um elemento esperado (assinatura/logo/selo/headline que não apareceu
   = completude, não anti-padrão); (b) impressão SUBJETIVA não listada ("parece banco
   de imagens", "pouco editorial" = gosto). Na dúvida, anti_pattern_violated:false.
   Quando marcar true, copie em "anti_pattern_evidence" o TEXTO EXATO do bullet da
   lista ANTI-PADRÕES que está presente. Se não conseguir citar um bullet da lista,
   anti_pattern_violated DEVE ser false e evidence "". Quando true de fato,
   verdict:FAIL — é violação grave.

Responda APENAS JSON, sem cercas:
{"relevance":"ok|weak","integrity":"ok|broken","anti_pattern_violated":false,"anti_pattern_evidence":"","verdict":"PASS|FAIL","reason":"frase curta em pt"}
verdict = PASS só se relevance=ok E integrity=ok E anti_pattern_violated=false."""


_STOP = {"de", "da", "do", "a", "o", "e", "em", "um", "uma", "que", "com", "para",
         "no", "na", "the", "use", "pra", "por", "se", "ou"}


def _overlap(ev: str, bullet: str) -> bool:
    """True se a evidência citada e o bullet compartilham ≥2 palavras significativas
    (≥4 letras). Casa 'foto humana realista' ⇄ 'foto humana realista (use B/D...)'
    sem exigir igualdade literal."""
    def words(s):
        return {w for w in re.findall(r"[a-zà-ú]{4,}", s.lower()) if w not in _STOP}
    return len(words(ev) & words(bullet)) >= 2


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
        # GUARD (achado #3): o modelo às vezes marca anti_pattern_violated por AUSÊNCIA
        # de um elemento esperado (assinatura/logo/selo) — que é chrome do template,
        # composto no render e não na imagem gerada. Isso não é anti-padrão e não deve
        # reprovar+regerar a IMAGEM. Anti-padrão por PRESENÇA (foto stock, humano
        # realista em modelo abstrato etc.) não bate nesta guarda e segue reprovando.
        if out.get("anti_pattern_violated") and out.get("integrity") == "ok":
            _ev = str(out.get("anti_pattern_evidence", "")).strip().lower()
            _r = str(out.get("reason", "")).lower()
            _antis = [str(a).lower() for a in (model_dna or {}).get("anti_patterns", [])]
            # evidência só conta se casar de fato com um bullet da lista do DNA
            _ev_real = bool(_ev) and any(
                _ev in a or a in _ev or _overlap(_ev, a) for a in _antis)
            _absence = ("ausente", "ausência", "ausencia", "falta ", "falta a",
                        "faltam", "faltando", "sem a assinatura", "sem assinatura",
                        "não aparece", "nao aparece", "não há ", "nao ha ",
                        "não tem ", "nao tem ", "não está presente", "nao esta presente")
            _by_absence = any(k in _r for k in _absence) or any(k in _ev for k in _absence)
            if (not _ev_real or _by_absence) and out.get("relevance") == "ok":
                out["anti_pattern_violated"] = False
                out["verdict"] = "PASS"
                out["guard"] = "anti-padrão sem bullet real/por ausência rebaixado (achado #3)"
        return out
    except Exception as e:
        return {"verdict": "SKIPPED", "reason": f"vision falhou: {e.__class__.__name__}", "relevance": "?", "integrity": "?"}
