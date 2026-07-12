#!/bin/zsh
# Regenera os 5 previews quebrados do wizard (assets/style-previews/metta/)
set -a; source "$(dirname "$0")/../.env.local"; set +a
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=render_out/previews-novos
mkdir -p "$OUT"

echo "=== 1/5 YELLOW-BLOCO ==="
$PY cli.py --model YELLOW-BLOCO \
  --headline "Convite: mentoria pra quem lidera a operação comercial." \
  --subhead "Método validado em +1.000 operações no Brasil." \
  --body $'Diagnóstico da sua operação\nRotina comercial estruturada\nMeta batida sem depender de herói' \
  --cta "Aplicar para mentoria" --image generate --preset fotorrealista \
  --format feed --auto-improve --max-attempts 2 --out "$OUT" 2>&1 | tail -4

echo "=== 2/5 NEWS-CARD ==="
$PY cli.py --model NEWS-CARD \
  --tag "ANÚNCIO METTA" \
  --headline "Método que transformou +1.000 operações no Brasil." \
  --subhead "Da meta impossível à meta batida todo mês — com estrutura, não com sorte." \
  --cta "SAIBA MAIS" --image generate --preset fotorrealista \
  --format feed --auto-improve --max-attempts 2 --out "$OUT" 2>&1 | tail -4

echo "=== 3/5 YELLOW-SPLIT ==="
$PY cli.py --model YELLOW-SPLIT \
  --headline "Time que bate meta todo mês." \
  --subhead "Método M.E.T.T.A. — estrutura que escala." \
  --cta "CONHECER" --image generate --preset cinematic-dark \
  --format feed --auto-improve --max-attempts 2 --out "$OUT" 2>&1 | tail -4

echo "=== 4/5 LIGHT-SURREAL ==="
$PY cli.py --model LIGHT-SURREAL \
  --headline "A gestão que separa os que escalam dos que estacionam." \
  --subhead "Insights que a maioria dos gestores aprende tarde demais." \
  --cta "CONHECER" --image generate --preset surreal-hbr \
  --format feed --auto-improve --max-attempts 2 --out "$OUT" 2>&1 | tail -4

echo "=== 5/5 I-retrato-editorial-pb ==="
$PY cli.py --model I-retrato-editorial-pb \
  --headline "Autoridade se constrói com método, não com volume." \
  --subhead "Gestão de vendas que fala por si mesma." \
  --cta "CONHECER" --image generate --preset bw-yellow \
  --format feed --auto-improve --max-attempts 2 --out "$OUT" 2>&1 | tail -4

echo "=== FIM ==="
ls -la "$OUT"
