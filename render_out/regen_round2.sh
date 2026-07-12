#!/bin/zsh
# Round 2 — melhora os 2 previews reprovados: NEWS-CARD (dark) e YELLOW-BLOCO (corte da pessoa)
set -a; source "$(dirname "$0")/../.env.local"; set +a
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=render_out/previews-novos/round2
mkdir -p "$OUT"

echo "=== 1/2 NEWS-CARD (dark) ==="
$PY cli.py --model NEWS-CARD \
  --tag "ANÚNCIO METTA" \
  --headline "Método que transformou +1.000 operações no Brasil." \
  --subhead "Da meta impossível à meta batida todo mês — com estrutura, não com sorte." \
  --cta "SAIBA MAIS" --image generate --preset cinematic-dark \
  --format feed --auto-improve --max-attempts 3 --out "$OUT" 2>&1 | tail -6

echo "=== 2/2 YELLOW-BLOCO ==="
$PY cli.py --model YELLOW-BLOCO \
  --headline "Convite: mentoria pra quem lidera a operação comercial." \
  --subhead "Método validado em +1.000 operações no Brasil." \
  --body $'Diagnóstico da sua operação\nRotina comercial estruturada\nMeta batida sem depender de herói' \
  --cta "Aplicar para mentoria" --image generate --preset fotorrealista \
  --format feed --auto-improve --max-attempts 3 --out "$OUT" 2>&1 | tail -6

echo "=== FIM ==="
ls -la "$OUT"
