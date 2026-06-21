"""Loop de auto-melhoria — gera, avalia, e REGERA com o feedback até aprovar.

Fecha o ciclo que faltava: o criativo é feito → o avaliador final julga → se não
for SHIP e o problema for de IMAGEM (não de template), regera injetando os ajustes
da avaliação como DIREÇÃO VISUAL (prioridade máxima da skill 04) → reavalia. Repete
até SHIP ou bater `max_attempts`. Guarda a MELHOR tentativa (maior nota geral).

Por que não regera sempre: hierarquia/cor/posição vêm do blueprint (fixos por modelo)
— regerar a foto não muda isso. Quando o avaliador diz `image_fixable=false`, o loop
PARA e sinaliza "trocar de modelo / editar blueprint" em vez de queimar imagens à toa.

    from _autogen import generate_until_approved
    best, history = generate_until_approved(brief, max_attempts=3)
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path


def _png_bytes(res: dict) -> bytes | None:
    uri = res.get("png_data_uri") or ""
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    return None


def _decision_log(res: dict) -> dict | None:
    """Carrega artifacts/<run_id>/03-decision-log.json — a INTENÇÃO do diretor de arte,
    pra o avaliador julgar fidelidade ao ICP (passo 4). Best-effort: None se faltar."""
    rid = res.get("run_id")
    if not rid:
        return None
    art = os.getenv("ARTIFACTS_DIR") or "artifacts"
    p = Path(art) / rid / "03-decision-log.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def generate_until_approved(brief: dict, max_attempts: int = 3,
                            target: str = "SHIP", verbose: bool = True) -> tuple[dict, list]:
    """Gera e auto-melhora um criativo.

    `brief` = kwargs de `_run_pipeline_inline` (model, copy, formato, preset...).
    Retorna (melhor_tentativa, historico). Cada item do histórico:
    {attempt, result, eval, score, visual_feedback_usado}.
    """
    from generate import _run_pipeline_inline
    from _evaluator import evaluate

    history: list[dict] = []
    best: dict | None = None
    best_score = -1.0
    visual_feedback = (brief.get("briefing_image_text") or "").strip()
    base_visual = visual_feedback  # direção original do usuário (preservada)

    for attempt in range(1, max_attempts + 1):
        kwargs = dict(brief)
        kwargs["briefing_image_text"] = visual_feedback or None
        if verbose:
            print(f"  tentativa {attempt}/{max_attempts}"
                  + (f" · mirando: {visual_feedback[:70]}" if attempt > 1 else ""))

        res = _run_pipeline_inline(**kwargs)
        if not res.get("ok"):
            history.append({"attempt": attempt, "result": res, "eval": {},
                            "score": -1, "visual_feedback": visual_feedback})
            if verbose:
                print(f"    pipeline falhou: {res.get('error')}")
            break

        png = _png_bytes(res)
        marca = "tiago" if str(brief.get("forced_model_id", "")).upper().startswith("TIAGO") else "metta"
        copy = {"headline": brief.get("user_headline", ""), "subhead": brief.get("user_subhead", ""),
                "body": brief.get("user_body", ""), "cta": brief.get("user_cta_text", "")}
        # peça tipográfica (sem foto) não deve ser penalizada por "falta de imagem"
        image_based = bool(res.get("image_data_uri"))
        ev = evaluate(png, copy, marca, res.get("vision_qa"), res.get("critic"),
                      decision_log=_decision_log(res), image_based=image_based) if png else {"verdict": "SKIPPED"}

        score = float(ev.get("geral") or 0)
        item = {"attempt": attempt, "result": res, "eval": ev, "score": score,
                "visual_feedback": visual_feedback}
        history.append(item)
        if score > best_score:
            best_score, best = score, item

        if verbose:
            print(f"    → {ev.get('verdict')} nota={score} "
                  f"(image_fixable={ev.get('image_fixable')})")

        if ev.get("verdict") == target:
            break
        if attempt == max_attempts:
            break
        # Decide se vale regerar: só se o problema for de IMAGEM.
        if ev.get("image_fixable") is False:
            if verbose:
                print("    parando: problema é de template/layout (não adianta regerar a foto).")
            break
        # Monta o feedback pra próxima imagem: direção original + ajustes da avaliação.
        fixes = "; ".join(ev.get("fixes", []) or [])
        img_fb = ev.get("image_feedback", "") or ev.get("reason", "")
        visual_feedback = " ".join(x for x in [
            base_visual,
            f"A versão anterior tirou nota {score}/10 ({ev.get('verdict')}).",
            f"Corrija na imagem: {img_fb}." if img_fb else "",
            f"Ajustes: {fixes}." if fixes else "",
        ] if x).strip()

    return (best or (history[-1] if history else {}), history)
