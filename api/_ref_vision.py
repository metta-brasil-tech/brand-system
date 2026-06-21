"""Fase 7 — geração REFERENCE-AWARE: o pensador OLHA a referência (não só texto).

O maior salto de qualidade que falta. Hoje o diretor de arte compõe a cena a partir de
TEXTO (ficha + copy). O designer do plugin-metta-ads OLHA o PNG da referência campeã
antes de compor. Aqui a geração passa a herdar o CRAFT da referência (composição, luz,
enquadramento, tratamento, disciplina de cor) — não só a "família" — adaptado à nova copy.

Como entra sem mexer no pipeline: o prompt enriquecido é injetado via
`briefing_image_text` (a direção visual de PRIORIDADE MÁXIMA da skill 04). Então dá pra
A/B testar (baseline vs reference-aware) sem editar `generate.py`/`_art_director.py`.

    ref = _critic.pick_reference(query, marca)         # escolhe a referência campeã
    enr = enrich_scene(ref, copy, base_concept, marca) # olha o PNG e enriquece a direção
    _run_pipeline_inline(..., briefing_image_text=enr["enriched_prompt"])
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _system(marca: str) -> str:
    dna = ("Metta — editorial sério B2B (HBR/Bloomberg), dark moody, amarelo cirúrgico, "
           "fotografia documental decision-grade, sem stock."
           if (marca or "").lower() != "tiago" else
           "Tiago Alves — cinema editorial B&W com amarelo seletivo, grão 35mm, autoral.")
    return f"""Você é DIRETOR DE ARTE. {dna}

Você vê a REFERÊNCIA: um anúncio CAMPEÃO da marca (padrão-ouro). Sua tarefa é fazer a
PRÓXIMA peça herdar o NÍVEL DE CRAFT dela — não a cena, o craft.

1. Leia o craft da referência OLHANDO a imagem: enquadramento do sujeito, distância/
   ângulo de câmera, luz e mood, tratamento da foto (cor/contraste/grão), disciplina de
   paleta, profundidade, respiro, como o sujeito "carrega" significado.
2. Para a NOVA copy (abaixo), escreva UM prompt de imagem em inglês que alcance ESSE
   mesmo craft, adaptado à mensagem nova. ESPECÍFICO, nunca genérico ("a man looking at
   camera" é proibido). Sem texto/logo/número na imagem.
3. NÃO copie a cena da referência — herde a linguagem e a especificidade.

Responda APENAS JSON:
{{"enriched_prompt":"<prompt em inglês, específico, com luz/ângulo/tratamento/composição + tail 'no text, no logos, photorealistic, cinematic'>",
"borrowed":"<1 frase: o que herdou do craft da referência>",
"avoid":"<1 frase: o genérico que está evitando>"}}"""


def enrich_scene(reference: dict, copy: dict, base_concept: str = "",
                 marca: str = "metta", model: str | None = None) -> dict:
    """Olha o PNG da referência e devolve um prompt de imagem reference-aware."""
    if not reference or not reference.get("path"):
        return {"ok": False, "reason": "sem referência"}
    try:
        from openai import OpenAI
    except Exception as e:
        return {"ok": False, "reason": f"openai indisponível: {e}"}
    p = Path(reference["path"])
    mime = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg"}.get(p.suffix.lower(), "image/png")
    model = model or os.getenv("REFVISION_MODEL") or os.getenv("VISION_QA_MODEL", "gpt-4.1")
    copy_txt = (f"headline: {copy.get('headline','')}\nsubhead: {copy.get('subhead','')}\n"
                f"body: {copy.get('body','')}\ncta: {copy.get('cta','')}").replace("*", "")
    try:
        uri = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        r = OpenAI().chat.completions.create(
            model=model, max_tokens=500,
            messages=[
                {"role": "system", "content": _system(marca)},
                {"role": "user", "content": [
                    {"type": "text", "text": f"REFERÊNCIA campeã '{reference.get('id')}':"},
                    {"type": "image_url", "image_url": {"url": uri}},
                    {"type": "text", "text": f"NOVA copy:\n{copy_txt}\n\n"
                     + (f"conceito de cena base: {base_concept}\n\n" if base_concept else "")
                     + "Escreva o prompt reference-aware."},
                ]}])
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (r.choices[0].message.content or "").strip())
        m = re.search(r"\{.*\}", t, re.DOTALL)
        out = json.loads(m.group(0) if m else t)
        out["ok"] = True
        out["reference_id"] = reference.get("id")
        return out
    except Exception as e:
        return {"ok": False, "reason": f"ref-vision falhou: {e.__class__.__name__}: {e}"}
