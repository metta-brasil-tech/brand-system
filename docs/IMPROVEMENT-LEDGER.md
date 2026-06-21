# Ledger de auto-melhoria — antes→depois por alteração

Auditoria do flywheel. Cada linha = uma alteração e o que ela fez com a
qualidade, medido no mesmo conjunto. 🔴 PIOROU = candidato a reverter.

| Data | Alteração | n | SHIP% | Nota | ΔNota | ΔSHIP | Veredito |
|---|---|---|---|---|---|---|---|
| 2026-06-21 01:18 | baseline golden set (pós-fix ICP) | 12 | 33.3% | 8.19 | — | — | ⚫ BASELINE |
| 2026-06-21 01:37 | best-of (autogen, qualidade média) | 6 | 50.0% | 8.33 | +0.14 | +16.7 | 🟢 MELHOROU |

## Última: best-of (autogen, qualidade média) — MELHOROU
**O que mudou:** auto-melhoria nos melhores briefs, qualidade média (não comparável 1:1 ao golden baseline low)
**Efeito:** n -6 · ship_rate +16.7 · revisar_rate -16.7 · avg_score +0.14 · foto_rate +8.3
