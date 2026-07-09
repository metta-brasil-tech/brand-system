"""Vercel serverless function — ideia solta → direção visual completa.

POST /api/prompt-image
Body: {
  "brand": "metta" | "tiago",
  "model_id": "<estilo do wizard>",
  "preset": "fotorrealista" | "bw-yellow" | "surreal-hbr" | "cinematic-dark",
  "avatar_segment": "<id do avatar (opcional)>",
  "avatar_variant": "<id da variante (opcional)>",
  "idea": "<o que o user imagina, escrito solto (pode ser vazio)>"
}
Resposta: { "direction": "<direção visual pronta pro campo briefing_image>" }
                 ou { "error": "<mensagem amigável>" }

O botão "Gerar direção com IA" do wizard chama isto. A direção sai no MESMO
formato que o campo espera (sujeito/cena/ambiente/enquadramento) — o TRATAMENTO
(cores, mood, lighting) fica com o preset, então a direção não fala de paleta.
Custo: 1 chamada de texto curta (sem imagem) — centavos.
"""
from __future__ import annotations

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

_MAX_IDEA = 600  # ideia solta não precisa de mais que isso


def _blueprint_treatment(brand: str, model_id: str) -> str:
    """`image.treatment` do blueprint do estilo — ancora a direção no que o slot
    de imagem realmente é (objeto flutuante ≠ retrato ≠ foto embed)."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "", model_id or "")
    p = _ROOT / "source" / "ad-blueprints" / (brand or "metta") / f"{safe}.md"
    if not p.exists():
        return ""
    m = re.search(r"treatment:\s*\"([^\"]+)\"", p.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def _avatar_context(segment: str, variant: str) -> str:
    """Persona/ambiente do avatar escolhido, direto do JSON canônico do engine."""
    if not segment or segment == "generico":
        return ""
    try:
        p = Path(os.getenv("BRAND_KNOWLEDGE_PATH", str(_ROOT / "engine" / "brand-knowledge")))
        data = json.loads((p / "audience" / "avatars.json").read_text(encoding="utf-8"))
        segs = data if isinstance(data, list) else data.get("segments") or data.get("avatars") or []
        for s in segs:
            if isinstance(s, dict) and s.get("id") == segment:
                bits = [s.get("persona_male", ""), s.get("environment", ""),
                        s.get("clothing", ""), s.get("age_range", "")]
                if variant and variant != "padrao":
                    for v in (data.get("variants") or []):
                        if isinstance(v, dict) and v.get("id") == variant:
                            bits.append(v.get("mood") or v.get("ui_desc") or variant)
                            break
                return " · ".join(x for x in bits if x)
    except Exception:
        pass
    return f"segmento: {segment}" + (f" · registro: {variant}" if variant else "")


def _generate_direction(payload: dict) -> dict:
    brand = (payload.get("brand") or "metta").strip().lower()
    model_id = (payload.get("model_id") or "").strip()
    preset = (payload.get("preset") or "fotorrealista").strip()
    idea = (payload.get("idea") or "").strip()[:_MAX_IDEA]

    try:
        from openai import OpenAI
    except Exception:
        return {"error": "OpenAI indisponível no servidor — checar dependências do deploy."}
    if not os.getenv("OPENAI_API_KEY"):
        return {"error": "OPENAI_API_KEY não configurada no Vercel."}

    treatment = _blueprint_treatment(brand, model_id)
    avatar = _avatar_context(payload.get("avatar_segment", ""), payload.get("avatar_variant", ""))

    mundo = ("Metta: inteligência comercial B2B brasileira. Sujeitos típicos: empresário/gestor "
             "brasileiro em contexto real de negócio (loja, escritório, indústria)."
             if brand != "tiago" else
             "Tiago Alves: marca pessoal de vendas, estética autoral cinematográfica. "
             "NUNCA descreva o rosto do Tiago — a IA não reproduz pessoas reais; cenas sem ele ou com figura anônima.")

    system = (
        "Você é diretor de arte de um estúdio. Transforme a ideia solta do usuário numa "
        "DIREÇÃO VISUAL de cena pra geração de imagem, em pt-BR, 2 a 4 frases corridas.\n"
        "Descreva APENAS: sujeito (quem/o quê), ação, ambiente concreto, enquadramento e 1-2 "
        "detalhes que dão verdade à cena (objetos, luz do ambiente, hora do dia).\n"
        "NÃO descreva: paleta/cores/tratamento (o preset cuida disso), texto/letreiros na imagem "
        "(o layout põe o texto), logos, emojis. Nada de clichê de banco de imagem "
        "(aperto de mão, sorriso vazio pra câmera, lâmpada de ideia).\n"
        f"MARCA: {mundo}\n"
        + (f"SLOT DE IMAGEM DESTE ESTILO: {treatment}\n" if treatment else "")
        + (f"AVATAR-ALVO (quem deve aparecer): {avatar}\n" if avatar else "")
        + f"PRESET DE TRATAMENTO JÁ ESCOLHIDO (não repetir na direção): {preset}\n"
        "Responda SÓ com a direção, sem preâmbulo nem aspas."
    )
    user = idea if idea else (
        "Sem ideia do usuário — proponha a cena mais forte pro estilo e avatar acima, "
        "ancorada em situação real de negócio.")

    model = os.getenv("PROMPT_GEN_MODEL") or os.getenv("LLM_MODEL_OPENAI", "gpt-4.1-mini")
    try:
        r = OpenAI().chat.completions.create(
            model=model, max_tokens=260, temperature=0.8,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}])
        direction = (r.choices[0].message.content or "").strip().strip('"')
        if not direction:
            return {"error": "A IA não retornou direção — tenta de novo."}
        return {"direction": direction, "model": model}
    except Exception as e:
        return {"error": f"Falha ao gerar direção: {e.__class__.__name__}"}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            result = _generate_direction(payload)
            self._json(200 if "direction" in result else 502, result)
        except Exception as e:
            self._json(500, {"error": f"Erro interno: {e.__class__.__name__}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
