"""Auditoria do achado #3: a vision-QA está severa demais?

Re-roda a vision-QA ATUAL sobre os final.png que já existem em disco, COM e SEM
model_dna, e imprime verdict/relevance/integrity/reason lado a lado. Isola o
comportamento do gate (não regera nada). Rodar:

    set -a; source .env.local; set +a
    python3.11 render_out/_audit_visionqa.py
"""
import os, re, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from _vision_qa import check as vqa
from _blueprint_dna import extract_dna

ROOT = os.path.join(os.path.dirname(__file__), "criativos-atuais")

# (model_id, marca, nota, veredito-final) — as 13 visao=FAIL + 1 controle PASS
CASES = [
    ("TIAGO-EDITORIAL-HERO", "tiago", 9.4, "SHIP"),
    ("TIAGO-EDITORIAL-DARK", "tiago", 9.1, "SHIP"),
    ("A-headline-foto-dark", "metta", 8.8, "SHIP"),
    ("DARK-COLAGEM", "metta", 8.7, "SHIP"),
    ("TIAGO-STORY-COVER-HERO", "tiago", 8.5, "SHIP"),
    ("D-foto-fullbleed-overlay", "metta", 8.6, "REVISAR"),
    ("NEWS-CARD", "metta", 9.0, "REVISAR"),
    ("TIAGO-EDITORIAL-CTA", "tiago", 5.5, "REVISAR"),  # FAIL legítimo esperado
    ("I-retrato-editorial-pb", "metta", 8.7, "REVISAR"),  # controle: era PASS
]


def read_copy(model_id):
    p = os.path.join(ROOT, model_id, "info.md")
    t = open(p, encoding="utf-8").read()
    def grab(label):
        m = re.search(rf"\*\*{label}:\*\*\s*(.+)", t)
        return (m.group(1).strip() if m else "")
    return {"headline": grab("Headline"), "subhead": grab("Subhead"),
            "body": grab("Body"), "cta": grab("CTA")}


def short(d):
    return (f"{d.get('verdict'):7} rel={d.get('relevance'):5} "
            f"integ={str(d.get('integrity')):6} "
            f"{'ANTI ' if d.get('anti_pattern_violated') else ''}"
            f"— {str(d.get('reason',''))[:70]}")


print(f"{'MODELO':26} NOTA VER     | gate ATUAL (com e sem DNA)")
print("=" * 100)
for model_id, marca, nota, ver in CASES:
    png_path = os.path.join(ROOT, model_id, "final.png")
    if not os.path.exists(png_path):
        print(f"{model_id:26} -- sem final.png"); continue
    png = open(png_path, "rb").read()
    copy = read_copy(model_id)
    dna = extract_dna(marca, model_id)
    dna = dna if (dna and not dna.get("missing")) else None
    r_nodna = vqa(png, copy, model_dna=None)
    r_dna = vqa(png, copy, model_dna=dna)
    print(f"{model_id:26} {nota:<4} {ver:7} | dna={'sim' if dna else 'NAO'}")
    print(f"{'':26}   sem DNA: {short(r_nodna)}")
    print(f"{'':26}   com DNA: {short(r_dna)}")
    print("-" * 100)
