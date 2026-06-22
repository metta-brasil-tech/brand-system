#!/usr/bin/env python3
"""Re-render BARATO de YELLOW-BLOCO + DARK-OBJETO reusando a foto existente
(image_source='asset' → não gera imagem) com os fixes:
  - YELLOW-BLOCO: headline encurtada (≤50ch) → não estoura o bloco amarelo
  - DARK-OBJETO : foto full-bleed (CSS já editado) em vez de objeto contido
art_director=False → determinístico, sem custo de LLM de conceito.
Rodar com python3.11.
"""
import sys, base64, json, os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "api")); sys.path.insert(0, str(REPO / "engine"))
from dotenv import load_dotenv; load_dotenv(REPO / "engine" / ".env")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(REPO / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(REPO / "artifacts")

import generate as gen  # noqa: E402

SRC = REPO / "render_out" / "criativos-novos-21jun-icp"
OUT = REPO / "render_out" / "criativos-fix-2"
OUT.mkdir(parents=True, exist_ok=True)

bat = json.load(open(REPO / "engine/artifacts/battery_copy.json", encoding="utf-8"))
yb = dict(bat["YELLOW-BLOCO"])
yb["headline"] = "Cansou de bater meta no improviso?"  # 34ch (era 63) — cabe no bloco

JOBS = {
    "YELLOW-BLOCO": yb,
    "DARK-OBJETO": {
        "headline": "Meta nao se bate no grito.", "subhead": "Se bate com sistema.",
        "body": "Cadencia, diagnostico e treino no lugar do improviso.\nPrevisibilidade em vez de heroismo.",
        "cta": "Ver como funciona"},
}


def main():
    for model, copy in JOBS.items():
        crua = SRC / model / "crua.png"
        if not crua.exists():
            print(f"!! sem crua.png para {model}, pulando"); continue
        data_uri = "data:image/png;base64," + base64.b64encode(crua.read_bytes()).decode()
        res = gen._run_pipeline_inline(
            briefing_text="refix", forced_model_id=model, wizard_format="feed",
            image_source="asset", image_url=data_uri,
            user_headline=copy.get("headline", ""), user_subhead=copy.get("subhead", ""),
            user_body=copy.get("body", ""), user_cta_text=copy.get("cta", ""),
            render_png=True, art_director=False, vision_qa=False,
        )
        folder = OUT / model; folder.mkdir(parents=True, exist_ok=True)
        qa = (res.get("qa") or {})
        ok = res.get("ok")
        if res.get("png_data_uri"):
            (folder / "final.png").write_bytes(base64.b64decode(res["png_data_uri"].split(",", 1)[1]))
        (folder / "info.md").write_text(
            f"# {model} (re-fix)\n- H: {copy.get('headline','')}\n- ok: {ok}\n"
            f"- qa: {qa.get('status')} issues={qa.get('issues')}\n", encoding="utf-8")
        print(f"{model}: ok={ok} qa={qa.get('status')} issues={qa.get('issues')}")
    print(f"\nSaida: {OUT}")


if __name__ == "__main__":
    main()
