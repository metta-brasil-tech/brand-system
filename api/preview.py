"""Endpoint /api/preview — wrapper fino. A lógica vive em `_preview_impl.py`.

⚠️ BUNDLE (causa dos builds falhando desde 3c72b45): a config desta função no
`vercel.json` PRECISA excluir `assets/` (~300MB) e `render_out/` — igual ao
`generate.py`. Sem isso a função Python empacota o repo inteiro e estoura o
limite de 225MB da Vercel. NÃO remover o bloco "api/preview.py" do vercel.json.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _preview_impl import handler  # noqa: E402,F401 — Vercel usa a classe `handler`
