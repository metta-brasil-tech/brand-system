#!/usr/bin/env python3
"""validate_styles.py — guard de regressão do pipeline blueprint-driven.

Para CADA blueprint em source/ad-blueprints/{metta,tiago}/*.md valida o CHAIN
completo e falha (exit != 0) se algo estrutural quebrar:

  1. front-matter parseia (id, marca, archetype, image.required, prompt_ref)
  2. archetype é tratado no renderer (_blueprint_render._markup)
  3. archetype está nos sets do _qa (ARCHETYPES | TIAGO_ARCHETYPES)
  4. existe regra CSS  data-arch="<archetype>"  no _engine.css
  5. prompt_ref (quando image.required) resolve para um arquivo existente
  6. render() não lança e não retorna missing/html-vazio
  7. _qa.qa() não retorna FAIL (ignora 'headline vazia' em estilos text:none)

Rode no CI / pre-commit pra impedir que alguém habilite/edite um estilo e quebre
o pipeline sem perceber. Foi escrito depois de uma sessão em que vários desses
checks foram feitos à mão — agora são automáticos.

Uso:  python3 scripts/validate_styles.py
"""
from __future__ import annotations
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from api import _blueprint_render as R   # noqa: E402
from api import _qa                      # noqa: E402

# Copy representativa (todos os slots preenchidos pra exercitar o render).
COPY = {
    "tag": "ANÚNCIO",
    "headline": "Headline de exemplo para validar o estilo no pipeline",
    "subhead": "Subhead de apoio para o estilo.",
    "body": "Corpo de texto de exemplo para preencher os slots que pedem corpo.",
    "cta": "Saiba mais",
}
PLACEHOLDER = "https://example.com/placeholder.png"

# Inputs do chain (lidos uma vez).
_renderer = open(os.path.join(ROOT, "api/_blueprint_render.py"), encoding="utf-8").read()
RENDERED = set(re.findall(r'arch == "([^"]+)"', _renderer))
ENGINE_CSS = open(os.path.join(ROOT, "source/ad-blueprints/_engine.css"), encoding="utf-8").read()
QA_ARCH = _qa.ARCHETYPES | _qa.TIAGO_ARCHETYPES


def _fm(content: str) -> str:
    m = re.search(r"^---\n(.*?)\n---", content, re.S)
    return m.group(1) if m else ""


def _val(fm: str, key: str, default: str = "") -> str:
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip('"') if m else default


def _fmt(fm: str) -> str:
    m = re.search(r"formato_nativo:\s*\[([a-z, ]+)\]", fm)
    first = m.group(1).split(",")[0].strip() if m else "feed"
    return "story" if first in ("story", "reel") else "feed"


def validate_one(bp_path: str) -> tuple[str, list[str]]:
    content = open(bp_path, encoding="utf-8").read()
    fm = _fm(content)
    mid = _val(fm, "id") or os.path.basename(bp_path)
    marca = _val(fm, "marca")
    arch = _val(fm, "archetype")
    img_req = bool(re.search(r"required:\s*(true|True|yes)", fm))
    pref = re.search(r'prompt_ref:\s*"([^"]+)"', fm)
    theme_m = re.search(r"theme:\s*([a-z]+)", fm)
    text_none = bool(re.search(r"text:\s*none", fm))
    problems: list[str] = []

    # 1-4 chain estrutural
    if arch not in RENDERED:
        problems.append(f"archetype '{arch}' não é tratado no renderer (_blueprint_render)")
    if arch not in QA_ARCH:
        problems.append(f"archetype '{arch}' não está nos sets do _qa")
    if f'data-arch="{arch}"' not in ENGINE_CSS:
        problems.append(f"sem regra CSS data-arch=\"{arch}\" no _engine.css")
    # 5 prompt_ref resolve
    if img_req and pref:
        ref_path = os.path.join(ROOT, "engine/brand-knowledge", pref.group(1))
        if not os.path.exists(ref_path):
            problems.append(f"prompt_ref '{pref.group(1)}' não existe no disco")

    # 6 render() roda
    html = ""
    try:
        res = R.render(marca, mid, COPY, PLACEHOLDER if img_req else "", _fmt(fm))
        if res.get("missing"):
            problems.append("render() retornou missing=True (blueprint não encontrado)")
        html = res.get("html", "")
        if not html:
            problems.append("render() retornou HTML vazio")
    except Exception as e:  # noqa: BLE001
        problems.append(f"render() lançou {e.__class__.__name__}: {e}")

    # 7 qa() não FAIL
    if html:
        fmdict = {
            "archetype": arch,
            "marca": marca,
            "image": {"required": img_req},
            "params": {"theme": theme_m.group(1) if theme_m else "dark",
                       "text": "none" if text_none else ""},
        }
        q = _qa.qa(fmdict, COPY, PLACEHOLDER if img_req else "", html)
        for iss in q["issues"]:
            problems.append(f"QA FAIL: {iss}")

    return mid, problems


def main() -> int:
    bps = sorted(glob.glob(os.path.join(ROOT, "source/ad-blueprints/*/*.md")))
    fails: list[tuple[str, list[str]]] = []
    for bp in bps:
        mid, problems = validate_one(bp)
        if problems:
            fails.append((mid, problems))

    print(f"Estilos validados: {len(bps)}")
    print(f"  PASS: {len(bps) - len(fails)}")
    print(f"  FAIL: {len(fails)}")
    for mid, problems in fails:
        print(f"\n  ✗ {mid}")
        for p in problems:
            print(f"      - {p}")
    if not fails:
        print("\n✓ chain consistente em todos os estilos.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
