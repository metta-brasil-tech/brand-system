"""Ledger de AUTO-MELHORIA — a auditoria do flywheel.

O loop de melhoria roda automático (gera posts, reavalia, aprende, entra no banco).
Sem auditoria, ele pode PIORAR a qualidade e ninguém percebe. Este ledger registra,
a cada alteração, o **antes→depois** medido sobre um conjunto comparável (golden set
ou batch): "depois dessa alteração, isto melhorou (ou piorou)".

É o freio de segurança do flywheel: se uma mudança regrediu a nota/SHIP rate, fica
marcado VERMELHO no ledger — candidato a reverter.

Fluxo:
    from _ledger import compute_metrics, record
    m = compute_metrics(manifest)                 # mede um run (manifest do batch)
    record("ligou passo 5 (flywheel)", m,         # compara com o último snapshot,
           change_desc="peça SHIP entra no banco") # grava e renderiza o MD

Arquivos:
    data/improvement-ledger.json   # append-only, fonte de verdade
    docs/IMPROVEMENT-LEDGER.md     # tabela legível (antes→depois por alteração)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
LEDGER_JSON = _ROOT / "data" / "improvement-ledger.json"
LEDGER_MD = _ROOT / "docs" / "IMPROVEMENT-LEDGER.md"

# Métrica-chave que decide MELHOROU/PIOROU (a "nota do flywheel").
KEY_METRIC = "avg_score"


def _g(r: dict, *ks):
    for k in ks:
        if k in r and r[k] is not None:
            return r[k]
    return None


def compute_metrics(manifest: list[dict]) -> dict:
    """Métricas de um run a partir do manifest do batch (_run_all.py).

    Aceita variações de nome (score/nota, verdict/veredito, regenerated/regen).
    """
    rows = [r for r in (manifest or []) if isinstance(r, dict)]
    n = len(rows)
    if not n:
        return {"n": 0}
    scores = [float(_g(r, "score", "nota") or 0) for r in rows]
    verds = [str(_g(r, "verdict", "veredito") or "").upper() for r in rows]
    foto = [bool(_g(r, "foto", "image")) for r in rows]
    regen = [bool(_g(r, "regenerated", "regen")) for r in rows]
    pct = lambda c: round(100 * c / n, 1)
    return {
        "n": n,
        "ship_rate": pct(verds.count("SHIP")),
        "revisar_rate": pct(verds.count("REVISAR")),
        "descartar_rate": pct(verds.count("DESCARTAR")),
        "avg_score": round(sum(scores) / n, 2),
        "regen_rate": pct(sum(regen)),
        "foto_rate": pct(sum(foto)),
    }


def _load() -> list[dict]:
    try:
        return json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(entries: list[dict]) -> None:
    LEDGER_JSON.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_JSON.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def record(label: str, metrics: dict, change_desc: str = "", note: str = "") -> dict:
    """Grava um snapshot comparado ao anterior. Renderiza o MD. Retorna a entrada."""
    led = _load()
    prev = led[-1]["metrics"] if led else None
    deltas: dict = {}
    verdict = "BASELINE"
    if prev:
        for k, v in metrics.items():
            pv = prev.get(k)
            if isinstance(v, (int, float)) and isinstance(pv, (int, float)):
                deltas[k] = round(v - pv, 2)
        d = deltas.get(KEY_METRIC, 0)
        verdict = "MELHOROU" if d > 0.01 else ("PIOROU" if d < -0.01 else "NEUTRO")
    entry = {
        "ts": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M"),
        "label": label, "change": change_desc, "note": note,
        "metrics": metrics, "deltas": deltas, "verdict": verdict,
    }
    led.append(entry)
    _save(led)
    render_md(led)
    return entry


def _sign(x) -> str:
    if not isinstance(x, (int, float)):
        return "—"
    return f"+{x}" if x > 0 else (str(x) if x < 0 else "0")


def render_md(led: list[dict] | None = None) -> None:
    led = led if led is not None else _load()
    icon = {"MELHOROU": "🟢", "PIOROU": "🔴", "NEUTRO": "⚪", "BASELINE": "⚫"}
    lines = [
        "# Ledger de auto-melhoria — antes→depois por alteração",
        "",
        "Auditoria do flywheel. Cada linha = uma alteração e o que ela fez com a",
        "qualidade, medido no mesmo conjunto. 🔴 PIOROU = candidato a reverter.",
        "",
        "| Data | Alteração | n | SHIP% | Nota | ΔNota | ΔSHIP | Veredito |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in led:
        m, d = e["metrics"], e.get("deltas", {})
        lines.append(
            f"| {e['ts']} | {e['label']} | {m.get('n','?')} | "
            f"{m.get('ship_rate','?')}% | {m.get('avg_score','?')} | "
            f"{_sign(d.get('avg_score'))} | {_sign(d.get('ship_rate'))} | "
            f"{icon.get(e['verdict'],'')} {e['verdict']} |"
        )
    # detalhe da última (o "depois dessa alteração melhorou isto")
    if led:
        e = led[-1]
        lines += ["", f"## Última: {e['label']} — {e['verdict']}"]
        if e.get("change"):
            lines.append(f"**O que mudou:** {e['change']}")
        if e.get("deltas"):
            difs = " · ".join(f"{k} {_sign(v)}" for k, v in e["deltas"].items() if v)
            lines.append(f"**Efeito:** {difs or 'sem variação'}")
        if e["verdict"] == "PIOROU":
            lines.append("\n> 🔴 **REGRESSÃO** — esta alteração piorou a métrica-chave. Revisar/reverter.")
    LEDGER_MD.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
