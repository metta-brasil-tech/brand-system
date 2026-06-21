#!/usr/bin/env python3
"""Fase 5 — runner do flywheel: ingere peças APROVADAS (SHIP) do golden no banco.

Lê render_out/golden/manifest.json, filtra SHIP, e para cada uma chama
_bank.ingest_to_bank(approved=True). DRY-RUN por padrão (não escreve o índice nem
roda vision-tagging) — porque o banco é lido AO VIVO pelo crítico durante geração:
NUNCA rodar a escrita real enquanto um batch estiver gerando (regra do PLANO-MESTRE).

Uso:
  python3.11 render_out/_flywheel_ingest.py            # dry-run (mostra o que entraria)
  COMMIT=1 python3.11 render_out/_flywheel_ingest.py   # escreve de verdade (máquina ociosa!)

Depois da escrita real, o efeito é auditado no PRÓXIMO golden run (o _ledger compara
SHIP%/nota antes→depois de o banco ter crescido).
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
import _bank  # noqa: E402

GOLD = ROOT / "render_out" / "golden"
COMMIT = os.getenv("COMMIT") == "1"


def _selftest_gate() -> None:
    """Prova o gate de segurança SEM tocar o índice (não passa approved=True)."""
    png = b"\x89PNG\r\n"  # bytes fake — o gate barra antes de usar
    cases = [
        ("sem aprovação",      dict(verdict="SHIP", approved=False)),
        ("aprovado mas REVISAR", dict(verdict="REVISAR", approved=True)),
        ("aprovado mas DESCARTAR", dict(verdict="DESCARTAR", approved=True)),
    ]
    print("== self-test do gate (deve RECUSAR todos) ==")
    allok = True
    for name, kw in cases:
        r = _bank.ingest_to_bank(png, {"headline": "x"}, "M", "metta", tag_with_vision=False, **kw)
        ok = (r.get("ok") is False)
        allok &= ok
        print(f"  [{'OK' if ok else 'FALHOU'}] {name}: recusou={r.get('ok') is False} — {r.get('reason')}")
    print(f"  => gate {'íntegro' if allok else 'QUEBRADO'}\n")


def main() -> None:
    _selftest_gate()
    manifest = json.loads((GOLD / "manifest.json").read_text())
    ships = [m for m in manifest if str(m.get("verdict")).upper() == "SHIP"]
    print(f"== flywheel: {len(ships)}/{len(manifest)} peças SHIP candidatas ==")
    print(f"   modo: {'ESCRITA REAL (COMMIT=1)' if COMMIT else 'DRY-RUN (nada é escrito)'}\n")
    for m in ships:
        png_path = GOLD / m["id"] / "final.png"
        marca = m.get("marca", "metta")
        copy = {"headline": m.get("headline", ""), "subhead": "", "cta": ""}
        if not png_path.exists():
            print(f"  [skip] {m['id']}: sem final.png"); continue
        if not COMMIT:
            print(f"  [dry]  {m['id']} ({marca}, nota {m.get('score')}) → entraria como ad-<slug(headline)>")
            continue
        r = _bank.ingest_to_bank(
            png_path.read_bytes(), copy, m["model"], marca,
            verdict="SHIP", approved=True, tag_with_vision=True)
        print(f"  [{'ok' if r.get('ok') else 'ERRO'}] {m['id']} → {r.get('id') or r.get('reason')}"
              + (f" (vision-tag={r.get('tagged_by_vision')})" if r.get('ok') else ""))
    if not COMMIT:
        print("\n   (dry-run) rode com COMMIT=1 e a máquina OCIOSA pra escrever o banco.")


if __name__ == "__main__":
    main()
