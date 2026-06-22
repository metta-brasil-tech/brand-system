# AUDITORIA HONESTA — estado real das Fases 1–6 (2026-06-21)

> Cruzamento do que o `PLANO-MESTRE.md §0` **afirma** contra o que o **código vivo +
> artifacts reais** mostram. Verificado ao vivo nesta sessão (não por leitura do plano).
> Régua: VERIFICADO (rodou e provei) · PARCIAL (existe, falta integrar/ligar) · NÃO.

## Veredito por fase

| Fase | Afirmação do plano | Verificação ao vivo | Estado |
|---|---|---|---|
| **1 — Camada de recuperação** (`_knowledge.retrieve`) | puxa ICP/voz/método/depoimento por copy | 10/10 decision-logs do batch 19h mostram `knowledge_provenance` = ICP · Voz · Metodologia · Depoimento | ✅ **VERIFICADO** |
| **2 — ICP no pensador** (`_avatar_infer` + `_art_director`) | persona nasce do ICP, não de "use mulheres" | 5/5 prompts com pessoa carregam a persona do ICP (`brazilian/blazer/button-up/office`). Forçar `avatar_segment` muda cena+figurino (validado offline: farmácia≠serviços≠ótica) | ✅ **VERIFICADO** |
| **3 — Decision log** | `03-decision-log.json` com rationale+proveniência+avatar | arquivos existem, chaves: `marca, archetype, theme, avatar, knowledge_provenance, knowledge_block, art_director` | ✅ **VERIFICADO** |
| **4 — Avaliador critica o raciocínio** (`_evaluator` lê decision_log) | julga intenção→peça, não só pixel | `_evaluator.py` referencia `decision_log` 5×; gate `FINAL_EVAL=1` em `generate.py:1088` | ✅ **VERIFICADO** (opt-in) |
| **5 — Flywheel / entrada no banco** | peça SHIP entra no banco, gated por aprovação | `_bank.ingest_to_bank()` existe (`:98`); runner `render_out/_flywheel_ingest.py` existe | ⚙️ **PARCIAL — por design** (manual-com-aprovação, não automático) |
| **5.5 — Ledger de auditoria** | mede antes→depois no golden set | `_ledger.compute_metrics()/record()` + runner `_audit_ledger.py` + `data/improvement-ledger.json` | ✅ **VERIFICADO** |
| **6 — Auto-melhoria no pipeline** | `generate.py` roda o loop sob flag | `generate.py:1178` lê `auto_improve` (body) ou `AUTO_IMPROVE=1`, devolve melhor+nota | ✅ **VERIFICADO** (gated) |
| **Modo B — ideia→copy** (`_copywriter.propose_copy`) | tema → ângulo+headlines ancorados no ICP | módulo existe e validado standalone; **CLI não tem `--theme`** | ⚠️ **PARCIAL — falta expor** no wizard/CLI |

## Achados que o plano §0 NÃO captura (e te confundiram)

1. **ICP horizontal → `generico` silencioso.** O pipeline puxa o ICP certo, mas com copy
   que não cita vertical, o `_avatar_infer` cai em `generico` ("empresário em ponto de
   inflexão") **sem avisar**. Não é bug — é a copy sem pista. Quem olha o criativo acha
   que "não puxou ICP". **Mitigado:** receita agora aceita `avatar_segment` por peça e
   carimba o ICP no `info.md`. Para ancorar num vertical, **passe o segmento** (ou use
   copy que cite o setor).

2. **Armadilha de versão do Python.** `python3` do sistema é **3.9.6** e quebra o
   pipeline (`str | None` em `_image_presets.py:93`). As runs boas usam **`python3.11`**.
   Sempre rodar a geração com `python3.11`.

## Fila (não feito / próximo)
- Fase 7 (reference-aware como CONTEXTO, não override — 1ª tentativa regrediu -0.53)
- Fase 8 (paridade local↔prod: local=OpenAI, prod=Claude+render.js)
- Fases 9–11 (carrossel: série/guardrails/panorâmica) — PRIORIDADE declarada
- Fases 12–15 (briefer A↔B, safe-zones, 2 variantes divergentes, acabamentos)
- Integração do Modo B no CLI/wizard (`--theme` + aprovar→gerar)
