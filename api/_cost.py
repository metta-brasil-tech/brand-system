"""Cost-log (P4): custo estimado por geração.

Cada geração usa 2+ chamadas de LLM (cérebro: diretor de arte, engenheiro de
prompt, às vezes briefing/style/QA) + 1 geração de imagem (Gemini/gpt-image).
Este módulo soma o custo em USD por chamada, a partir dos tokens REAIS que o
LLMAdapter já expõe (tokens_in/tokens_out) + um custo fixo por imagem.

Os preços são estimativas (USD por 1M tokens) e podem ser sobrescritos por env
(ex.: COST_OPUS_IN=15). Não é faturamento — é para o Nathan enxergar a ordem de
grandeza de cada peça e decidir tier (Haiku no prompt já derrubou o custo).
"""
from __future__ import annotations
import os


def _env_price(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, "") or default)
    except (TypeError, ValueError):
        return default


# Preços USD por 1M tokens: (input, output). Substring match no nome do modelo.
PRICES: list[tuple[str, tuple[float, float]]] = [
    ("claude-opus-4-8", (_env_price("COST_OPUS_IN", 15.0), _env_price("COST_OPUS_OUT", 75.0))),
    ("claude-sonnet-5", (_env_price("COST_SONNET_IN", 3.0), _env_price("COST_SONNET_OUT", 15.0))),
    ("claude-haiku-4-5", (_env_price("COST_HAIKU_IN", 1.0), _env_price("COST_HAIKU_OUT", 5.0))),
    ("haiku", (1.0, 5.0)),
    ("sonnet", (3.0, 15.0)),
    ("opus", (15.0, 75.0)),
]
_DEFAULT_LLM = (5.0, 25.0)  # fallback conservador p/ modelo desconhecido

# Custo por imagem gerada (USD). Substring match no provider/modelo.
IMAGE_PRICES: list[tuple[str, float]] = [
    ("nano-banana", _env_price("COST_IMG_NANO", 0.039)),
    ("gemini", _env_price("COST_IMG_NANO", 0.039)),
    ("gpt-image", _env_price("COST_IMG_GPT", 0.020)),
    ("openai", _env_price("COST_IMG_GPT", 0.020)),
    ("mock", 0.0),
]


def _llm_price(model: str) -> tuple[float, float]:
    m = (model or "").lower()
    for key, price in PRICES:
        if key in m:
            return price
    return _DEFAULT_LLM


def llm_usd(model: str, tin: int, tout: int) -> float:
    pin, pout = _llm_price(model)
    return (tin / 1_000_000) * pin + (tout / 1_000_000) * pout


def image_usd(provider: str, model: str = "") -> float:
    hay = f"{provider or ''} {model or ''}".lower()
    for key, price in IMAGE_PRICES:
        if key in hay:
            return price
    return 0.0


class Meter:
    """Acumula uso de LLM por chamada. Use `meter.stage = 'art-director'` antes de
    cada etapa; cada chamada do LLM é registrada sob esse rótulo."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.stage: str = "llm"
        self.image: dict | None = None

    def add_llm(self, model: str, tin: int, tout: int) -> None:
        self.calls.append({
            "stage": self.stage, "model": model,
            "tokens_in": int(tin or 0), "tokens_out": int(tout or 0),
            "usd": round(llm_usd(model, tin, tout), 6),
        })

    def set_image(self, provider: str, model: str = "") -> None:
        self.image = {
            "provider": provider, "model": model,
            "usd": round(image_usd(provider, model), 6),
        }

    def summary(self) -> dict:
        llm_total = round(sum(c["usd"] for c in self.calls), 6)
        img_total = round((self.image or {}).get("usd", 0.0), 6)
        return {
            "usd_total": round(llm_total + img_total, 6),
            "usd_llm": llm_total,
            "usd_image": img_total,
            "tokens_in": sum(c["tokens_in"] for c in self.calls),
            "tokens_out": sum(c["tokens_out"] for c in self.calls),
            "calls": self.calls,
            "image": self.image,
            "estimated": True,
        }

    def one_line(self) -> str:
        s = self.summary()
        stages = " · ".join(f"{c['stage']}={c['model'].split('-')[1] if '-' in c['model'] else c['model']}"
                            f"({c['tokens_in']}/{c['tokens_out']}tok ${c['usd']:.4f})"
                            for c in self.calls)
        img = self.image or {}
        return (f"cost: ${s['usd_total']:.4f} (LLM ${s['usd_llm']:.4f} + img "
                f"${s['usd_image']:.4f} [{img.get('provider','-')}]) — {stages}")


class MeteredLLM:
    """Embrulha um LLMAdapter e registra tokens no Meter a cada chamada. Delega
    todo o resto (o SkillRunner só usa complete_json; o art-director usa o mesmo)."""

    def __init__(self, inner, meter: Meter) -> None:
        self._inner = inner
        self._meter = meter

    def __getattr__(self, name):  # provider, model, temperature, embed, etc.
        return getattr(self._inner, name)

    def complete(self, *a, **k):
        r = self._inner.complete(*a, **k)
        self._meter.add_llm(getattr(self._inner, "model", "?"), r.tokens_in, r.tokens_out)
        return r

    def complete_json(self, *a, **k):
        data, r = self._inner.complete_json(*a, **k)
        self._meter.add_llm(getattr(self._inner, "model", "?"), r.tokens_in, r.tokens_out)
        return data, r
