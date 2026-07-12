"""Modo B — ideia → copy proposta (ancorada no ICP/voz/método/depoimento).

O plugin tem 2 modos de brief: A (copy literal pronta) e B (o usuário dá só um
TEMA/ângulo → o sistema propõe a copy → aprovação → produz). Hoje só temos o A.

Este módulo traz o B, e melhor que o plugin: a proposta nasce **fundamentada** no
acervo via `_knowledge` (ICP + voz da marca + metodologia + depoimento real). Ou seja,
a headline não sai do nada — sai do eixo identitário do ICP, na voz da marca, com
linguagem de cliente real.

Fluxo de produto:
    proposta = propose_copy("burnout do dono que não consegue delegar", "metta")
    # usuário escolhe 1 headline + ajusta → vira copy LITERAL → segue no pipeline (Modo A)

Self-contained (OpenAI direto, como _critic/_evaluator). Não escreve nada — só propõe.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _knowledge  # noqa: E402


def _system(marca: str) -> str:
    voz = ("Metta — inteligência comercial B2B. Tom: direto e confiante, humano, "
           "especialista e acessível; arquétipos Sábio + Governante; o eixo é "
           "IDENTITÁRIO (o empresário quer virar 'dono do sistema', parar de ser o "
           "gargalo), não técnico."
           if (marca or "").lower() != "tiago" else
           "Tiago Alves — marca pessoal, autoridade técnica calma, cinema editorial. "
           "Direto, sem motivacional barato, sem clichê.")
    return f"""Você é COPYWRITER sênior da marca. {voz}

Você recebe um TEMA e o CONHECIMENTO DA MARCA (ICP real, voz, método, depoimento).
Proponha copy de anúncio FUNDAMENTADA nisso — nunca genérica. Regras:
- Fale com o ICP descrito (dor, linguagem, eixo de decisão). Se o ICP é identitário,
  a headline ataca a IDENTIDADE ("você virou refém da própria empresa"), não a técnica.
- Use a VOZ da marca (tom/arquétipos acima). Sem clichê de stock, sem motivacional raso.
- Headline que para o scroll: curta, afirmação ou pergunta de confronto.
- Aproveite o método e o depoimento como substrato (não copie literal o depoimento).
- Copy PRONTA pra usar (sem placeholder).

- Além da headline, o criativo real da marca carrega TEXTOS DE APOIO menores
  (ver banco real): uma TAG qualificadora curta em caixa alta que filtra o ICP
  (ex: "EXCLUSIVO PARA DONOS DE NEGÓCIOS QUE FATURAM +R$200K/MÊS") e um SUBHEAD
  de 1-2 frases com o próximo passo/prova (ex: "Aplique agora para uma reunião
  estratégica 1 a 1 e construa uma equipe que bate meta sem depender de você.").
  Quando houver prova social no conhecimento (nº de empresas, faturamento gerado),
  use-a na tag ou no subhead ("+1.000 empresas", "+R$8,5 bi em vendas").

Responda APENAS JSON, sem cercas:
{{"angulo":"<1 frase: o ângulo escolhido e por quê bate no ICP>",
"headlines":["<alt 1>","<alt 2>","<alt 3>"],
"tag":"<tag qualificadora curta em CAIXA ALTA>",
"subhead":"<1 subhead>","cta":"<1 cta>",
"fundamento":"<1 frase citando do que ancorou: ICP/voz/método/depoimento>"}}"""


def propose_copy(theme: str, marca: str = "metta", n_headlines: int = 3,
                 model: str | None = None) -> dict:
    """Dado um tema, propõe copy ancorada no ICP/voz/método. Retorna dict + proveniência."""
    try:
        from openai import OpenAI
    except Exception as e:
        return {"ok": False, "reason": f"openai indisponível: {e}"}

    # Recupera o conhecimento relevante ao tema (mesmo motor da geração).
    picks = _knowledge.retrieve(
        {"headline": theme, "subhead": "", "body": theme, "cta": ""}, marca)
    block = _knowledge.build_block(picks)

    model = model or os.getenv("COPYWRITER_MODEL") or os.getenv("LLM_MODEL_OPENAI", "gpt-4.1")
    try:
        r = OpenAI().chat.completions.create(
            model=model, max_tokens=600,
            messages=[
                {"role": "system", "content": _system(marca)},
                {"role": "user", "content":
                    f"TEMA: {theme}\n\n{block}\n\n"
                    f"Proponha {n_headlines} headlines alternativas + 1 subhead + 1 CTA, "
                    f"fundamentadas no conhecimento acima."},
            ])
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (r.choices[0].message.content or "").strip())
        m = re.search(r"\{.*\}", t, re.DOTALL)
        out = json.loads(m.group(0) if m else t)
        out["ok"] = True
        out["marca"] = marca
        out["grounded_in"] = picks.get("provenance", [])
        return out
    except Exception as e:
        return {"ok": False, "reason": f"copywriter falhou: {e.__class__.__name__}: {e}"}
