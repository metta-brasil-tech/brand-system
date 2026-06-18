#!/usr/bin/env python3
"""run_generation_battery.py — roda TODOS os estilos ativos do wizard pelo
pipeline real (api/generate.py::_run_pipeline_inline), gera PNG final via
Chromium e roda o QA estático (_qa.py) + QA por visão (_vision_qa.py, quando
a peça usa imagem gerada).

Lê os estilos diretamente de embed/criar.html (STYLES_METTA / STYLES_TIAGO),
ignorando os marcados `comingSoon: true` — ou seja, testa exatamente o que o
usuário vê no wizard.

Uso:
    OPENAI_API_KEY=sk-... python3 scripts/run_generation_battery.py
    python3 scripts/run_generation_battery.py --mock   # dry-run sem custo, sem chamar OpenAI
    python3 scripts/run_generation_battery.py --only YELLOW-BLOCO,TIAGO-TWITTER-CARD-IMAGE

Custo real: cada estilo com usaImagem=true chama 1x o image-gen (gpt-image-2,
~US$0.17 em quality=high). Roda IMAGE_QUALITY=low pra bateria de validação
sair mais barato (~US$0.04/imagem) — ajuste via env se quiser qualidade final.

Saída: artifacts/battery/<run_id>/<MODEL_ID>.png + summary.json + summary.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "engine"))

CRIAR_HTML = ROOT / "embed" / "criar.html"

# Briefing genérico por marca — dá contexto pro skill 04 (image-prompt) e pro
# preenchimento de copy quando o estilo não recebe headline/body explícitos.
BRIEFING_METTA = (
    "Metta, consultoria de inteligência comercial B2B. Tese: time que bate meta "
    "não é motivado, é bem gerenciado — processo, dado e cadência batem talento. "
    "Prova social: +1.000 operações comerciais no Brasil. Tom institucional, "
    "editorial, sério."
)
BRIEFING_TIAGO = (
    "Tiago Alves, voz pessoal sobre gestão de vendas. Tese: a maioria contrata "
    "tráfego antes de ter copy/processo — resultado é dinheiro no ralo. Tom "
    "confessional, direto, primeira pessoa, sem jargão de vendas raso."
)

SAMPLE_COPY = {
    "metta": {
        "headline": "O time que bate meta não é motivado.",
        "subhead": "É bem gerenciado.",
        "body": "Processo, dado e cadência batem talento isolado.\nMétodo aplicado em +1.000 operações comerciais no Brasil.",
        "cta": "Conhecer o método",
    },
    "tiago": {
        "headline": "Demorei 3 anos pra entender isso sobre vendas",
        "subhead": "",
        "body": "A maioria contrata tráfego antes de ter copy. Resultado: dinheiro no ralo.",
        "cta": "",
    },
}


def _parse_styles_array(js: str, var_name: str) -> list[dict]:
    m = re.search(rf"const {var_name}\s*=\s*\[(.*?)\n\];", js, re.S)
    if not m:
        return []
    body = m.group(1)
    out = []
    for entry_m in re.finditer(r"\{(.*?)\}", body, re.S):
        entry = entry_m.group(1)
        def _field(key, pattern):
            fm = re.search(pattern, entry)
            return fm.group(1) if fm else None
        style_id = _field("id", r"id:\s*'([^']+)'")
        if not style_id:
            continue
        usa_imagem = _field("usaImagem", r"usaImagem:\s*(true|false)") == "true"
        formatos = re.findall(r"'([\w-]+)'", _field("formatos", r"formatos:\s*(\[[^\]]*\])") or "[]")
        coming_soon = bool(re.search(r"comingSoon:\s*true", entry))
        out.append({
            "id": style_id,
            "usaImagem": usa_imagem,
            "formatos": formatos or ["feed"],
            "comingSoon": coming_soon,
        })
    return out


def load_active_styles(only: list[str] | None = None) -> list[dict]:
    js = CRIAR_HTML.read_text(encoding="utf-8")
    metta = [dict(s, marca="metta") for s in _parse_styles_array(js, "STYLES_METTA")]
    tiago = [dict(s, marca="tiago") for s in _parse_styles_array(js, "STYLES_TIAGO")]
    styles = [s for s in (metta + tiago) if not s["comingSoon"]]
    if only:
        wanted = set(only)
        styles = [s for s in styles if s["id"] in wanted]
    return styles


def run_battery(mock: bool, only: list[str] | None, render_png: bool) -> int:
    os.environ.setdefault("ARTIFACTS_DIR", str(ROOT / "artifacts"))
    os.environ.setdefault("BRAND_KNOWLEDGE_PATH", str(ROOT / "engine" / "brand-knowledge"))
    os.environ.setdefault("IMAGE_GEN_PROVIDER", "mock" if mock else os.getenv("IMAGE_GEN_PROVIDER", "openai"))
    os.environ.setdefault("IMAGE_QUALITY", "low")  # bateria de validação — não é entrega final

    if not mock and not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_IMAGE_API_KEY")):
        print("✗ Nenhuma OPENAI_API_KEY no ambiente. Rode com --mock pra dry-run sem custo,\n"
              "  ou exporte a chave antes de rodar a bateria real.", file=sys.stderr)
        return 1

    from generate import _run_pipeline_inline  # api/generate.py

    styles = load_active_styles(only)
    if not styles:
        print("✗ Nenhum estilo encontrado (cheque --only ou embed/criar.html).", file=sys.stderr)
        return 1

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    out_dir = Path(os.environ["ARTIFACTS_DIR"]) / "battery" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"▶ Bateria de geração — {len(styles)} estilos ativos · run_id={run_id} · mock={mock}\n")

    results = []
    for i, s in enumerate(styles, 1):
        model_id, marca, formato = s["id"], s["marca"], s["formatos"][0]
        copy = SAMPLE_COPY[marca]
        briefing = BRIEFING_METTA if marca == "metta" else BRIEFING_TIAGO
        print(f"[{i}/{len(styles)}] {marca}/{model_id} ({formato}) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            res = _run_pipeline_inline(
                briefing,
                mock=mock,
                forced_model_id=model_id,
                image_source="generate" if s["usaImagem"] else "none",
                wizard_format=formato,
                user_headline=copy["headline"],
                user_subhead=copy["subhead"] or None,
                user_body=copy["body"] or None,
                user_cta_text=copy["cta"] or None,
                render_png=render_png,
                vision_qa=render_png,
            )
        except Exception as exc:
            print(f"💥 EXCEPTION: {exc.__class__.__name__}: {exc}")
            results.append({"model_id": model_id, "marca": marca, "status": "EXCEPTION", "error": str(exc)})
            continue

        elapsed = round(time.time() - t0, 1)
        if not res.get("ok"):
            print(f"✗ FAIL ({elapsed}s) — {res.get('error')}")
            results.append({"model_id": model_id, "marca": marca, "status": "FAIL", "error": res.get("error"),
                             "diagnostics": res.get("diagnostics", [])})
            continue

        qa = res.get("qa") or {}
        vqa = res.get("vision_qa") or {}
        png_uri = res.get("png_data_uri")
        if png_uri and png_uri.startswith("data:image"):
            png_path = out_dir / f"{model_id}.png"
            import base64
            png_path.write_bytes(base64.b64decode(png_uri.split(",", 1)[1]))

        status = qa.get("status", "?")
        vqa_verdict = vqa.get("verdict", "—") if vqa else "—"
        print(f"{status} (qa) · vision={vqa_verdict} · {elapsed}s")
        results.append({
            "model_id": model_id, "marca": marca, "status": status,
            "qa_issues": qa.get("issues", []), "qa_warnings": qa.get("warnings", []),
            "vision_qa": vqa, "elapsed_s": elapsed,
        })

    summary_json = out_dir / "summary.json"
    summary_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    n_pass = sum(1 for r in results if r["status"] in ("PASS",))
    n_warn = sum(1 for r in results if r["status"] == "PASS_WITH_WARNINGS")
    n_fail = sum(1 for r in results if r["status"] in ("FAIL", "EXCEPTION"))

    md_lines = [f"# Bateria de geração — {run_id}", "",
                f"Total: {len(results)} · PASS: {n_pass} · PASS_WITH_WARNINGS: {n_warn} · FAIL: {n_fail}", ""]
    for r in results:
        md_lines.append(f"## {r['marca']}/{r['model_id']} — {r['status']}")
        for w in r.get("qa_warnings", []):
            md_lines.append(f"- ⚠ {w}")
        for issue in r.get("qa_issues", []):
            md_lines.append(f"- ✗ {issue}")
        vqa = r.get("vision_qa")
        if vqa:
            md_lines.append(f"- 👁 vision: {vqa.get('verdict')} — {vqa.get('reason', '')}")
        if r.get("error"):
            md_lines.append(f"- 💥 {r['error']}")
        md_lines.append("")
    (out_dir / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n— Resultado: {n_pass} PASS · {n_warn} PASS_WITH_WARNINGS · {n_fail} FAIL —")
    print(f"PNGs + summary em {out_dir}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="dry-run com MockImageGen (sem custo, sem chamar OpenAI)")
    ap.add_argument("--only", default=None, help="lista de model_id separados por vírgula")
    ap.add_argument("--no-png", action="store_true", help="pula render PNG + QA por visão (mais rápido, só testa o HTML)")
    args = ap.parse_args()
    only = args.only.split(",") if args.only else None
    sys.exit(run_battery(mock=args.mock, only=only, render_png=not args.no_png))
