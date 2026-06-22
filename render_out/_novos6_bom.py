#!/usr/bin/env python3
"""Regera os 6 modelos com a RECEITA BOA do _run_all.py:
_autogen.generate_until_approved (re-roll ligado) + copy CURADA da
battery_copy.json (+ FALLBACK p/ DARK-OBJETO). Saída em pasta nova.
"""
import sys, base64, json, os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "api")); sys.path.insert(0, str(REPO / "engine"))
from dotenv import load_dotenv; load_dotenv(REPO / "engine" / ".env")
os.environ["BRAND_KNOWLEDGE_PATH"] = str(REPO / "engine" / "brand-knowledge")
os.environ["ARTIFACTS_DIR"] = str(REPO / "artifacts")
os.environ.setdefault("IMAGE_QUALITY", "medium")

from _autogen import generate_until_approved   # noqa: E402

OUT = REPO / "render_out" / "criativos-novos-21jun-icp"
OUT.mkdir(parents=True, exist_ok=True)
MAX_ATTEMPTS = 2

MODELS = ["A-headline-foto-dark", "D-foto-fullbleed-overlay", "YELLOW-BLOCO",
          "DARK-OBJETO", "TIAGO-DARK-SURREAL", "TIAGO-EDITORIAL-HERO"]

# ICP por vertical: cada peça Metta-com-pessoa ancora num vertical REAL (em vez de
# cair em 'generico' por a copy ser horizontal). DARK-OBJETO é objeto (sem persona)
# e os Tiago têm o Tiago como sujeito (avatar = None por design) → ficam de fora.
AVATAR = {
    "A-headline-foto-dark":   "servico-profissional",   # clínica/consultório
    "D-foto-fullbleed-overlay": "varejo-farmacia",       # farmácia/drogaria
    "YELLOW-BLOCO":           "varejo-otica-joias",      # ótica/joalheria
}

# copy curada: battery_copy.json + FALLBACK (só DARK-OBJETO não está na battery)
bat = json.load(open(REPO / "engine/artifacts/battery_copy.json", encoding="utf-8"))
FALLBACK = {"DARK-OBJETO": {
    "headline": "Meta nao se bate no grito.",
    "subhead": "Se bate com sistema.",
    "body": "Cadencia, diagnostico e treino no lugar do improviso.\nPrevisibilidade em vez de heroismo.",
    "cta": "Ver como funciona"}}
COPY = dict(bat); COPY.update(FALLBACK)


def save_uri(uri, path):
    if uri and uri.startswith("data:"):
        path.write_bytes(base64.b64decode(uri.split(",", 1)[1]))


def main():
    results = []
    for model in MODELS:
        copy = COPY.get(model, {"headline": model, "subhead": "", "body": "", "cta": "Saiba mais"})
        seg = AVATAR.get(model)  # None → inferência (Tiago=None por design; objeto=generico)
        brief = dict(
            briefing_text=f"{copy.get('headline','')} {copy.get('subhead','')}",
            forced_model_id=model, wizard_format="feed", image_source="generate",
            user_headline=copy.get("headline", ""), user_subhead=copy.get("subhead", ""),
            user_body=copy.get("body", ""), user_cta_text=copy.get("cta", ""),
            avatar_segment=seg,
            render_png=True, art_director=True, vision_qa=True,
        )
        print(f"\n=== {model} === (copy: {copy.get('headline','')[:50]}) [ICP={seg or 'auto'}]", flush=True)
        best, history = generate_until_approved(brief, max_attempts=MAX_ATTEMPTS, verbose=True)
        r = best.get("result", {}) if isinstance(best, dict) else {}
        folder = OUT / model
        folder.mkdir(parents=True, exist_ok=True)
        save_uri(r.get("image_data_uri"), folder / "crua.png")
        save_uri(r.get("png_data_uri"), folder / "final.png")
        ev = best.get("eval") or {}
        vqa = r.get("vision_qa") or {}
        (folder / "info.md").write_text(
            f"# {model}\n- H: {copy.get('headline','')}\n- S: {copy.get('subhead','')}\n"
            f"- B: {(copy.get('body','') or '').replace(chr(10),' / ')}\n- CTA: {copy.get('cta','')}\n"
            f"- ICP: {seg or 'auto/generico'}\n"
            f"- nota: {best.get('score')} veredito: {ev.get('verdict')} tentativa: {best.get('attempt')}\n"
            f"- vision-qa: {vqa.get('verdict')} (rel={vqa.get('relevance')})\n", encoding="utf-8")
        print(f"   -> nota={best.get('score')} veredito={ev.get('verdict')} "
              f"tentativa={best.get('attempt')} visao={vqa.get('verdict')}", flush=True)
        results.append((model, best.get("score"), ev.get("verdict"), vqa.get("verdict")))

    print("\n===== RESUMO =====", flush=True)
    for m, sc, vd, vq in results:
        print(f"  {m:28s} nota={sc} veredito={vd} visao={vq}", flush=True)
    print(f"\nTudo em: {OUT}", flush=True)


if __name__ == "__main__":
    main()
