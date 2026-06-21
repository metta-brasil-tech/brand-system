# Auditoria de integração — o que está REALMENTE encaixado no pipeline

Verificação: cada coisa que construímos está no `_run_pipeline_inline` (o caminho real
de geração, usado pelo site e pelo CLI)? Ou só existe no disco / no batch?

## ✅ Encaixado e correto
| Componente | Onde | Confirmação |
|---|---|---|
| Camada de conhecimento | `generate.py:519` → `_ad_direct(knowledge=…)` | o diretor de arte injeta o bloco no prompt (`_art_director.py:388-409`) e usa |
| Crítico (same-designer) | loop de visão, default `CRITIC_COMPARE=1` | roda na geração com foto |
| Guardrails copy-literal + no_invented_text | `_qa.py` | roda em toda peça |
| Modos de falha gpt-image | `_art_director.NEG_MODEL_FAILS` + skill 04 | em todo negative_prompt |
| Decision log | `generate.py:592` → `03-decision-log.json` | salva rationale + proveniência + avatar |
| CLI passa avatar | `cli.py:53-54,81-82` | `--avatar-segment/--avatar-variant` |

## 🔴 Erros encontrados (claimed ≠ wired) — a família do bug do ICP

### Erro 1 — Avatar/ICP nunca era inferido → CORRIGIDO
- **Sintoma:** `generate.py` só usava `avatar_segment` se passado. Sem `--avatar-segment`,
  o `avatar_blk` ficava vazio e a instrução de persona ("dono no chão da farmácia,
  respeite o gênero") era **pulada** (`_art_director.py:399`). O handoff dizia "segmento
  inferido pela copy" — mas a inferência **não existia**.
- **Efeito:** o texto do ICP chegava ao pensador, mas a **persona estruturada** voltava
  pra heurística "use mulheres". Passo 2 estava meio-ligado.
- **Fix (aplicado):** `api/_avatar_infer.py` infere o segmento pela copy (pistas
  setoriais: farmácia→varejo-farmacia, dentista→servico-profissional, pet→varejo-pet,
  ótica→varejo-otica-joias; genérico→`generico/padrao` = ICP estratégico). Brand-aware:
  Tiago→(None,None). Ligado em `generate.py` (infere quando não foi passado). Validado.

### Erro 2 — Avaliador final NÃO roda no pipeline → A LIGAR (Fase 6)
- **Sintoma:** só `vision-qa` + `critic` rodam na geração real. O `_evaluator` (nota
  0-10, SHIP/REVISAR/DESCARTAR, e o "critica o raciocínio" lendo o decision-log) **só
  roda no batch/autogen**. Uma geração no **site não tem nota final** nem crítica de
  raciocínio; o decision-log é salvo mas ninguém o lê fora do batch.
- **Por que não corrigi agora:** é uma **decisão de produto**, não bug — adiciona +1
  chamada de visão por geração em produção (custo). Deve ser ligado de propósito (Fase 6),
  com flag (ex: `FINAL_EVAL`) e teto de custo.
- **Patch sugerido (Fase 6):** após o crítico, se `FINAL_EVAL=1` e há PNG:
  `from _evaluator import evaluate; ev = evaluate(_png, copy_dict, marca, vision_result,
  critic_result, decision_log=<03-decision-log>)` → anexar `evaluation` ao retorno.

## ⚠️ Standalone POR DESIGN (ainda não no pipeline — esperado)
| Componente | Status |
|---|---|
| `_evaluator.py` | só batch/autogen (vira pipeline na Fase 6 — ver Erro 2) |
| `_autogen.py` (loop) | só batch/CLI (Fase 6: opcional no pipeline com `AUTO_IMPROVE`) |
| `_bank.py` (flywheel) | construído, não executado (Fase 5; rodar com máquina ociosa) |
| `_copywriter.py` (Modo B) | construído; falta expor no wizard/CLI (`--theme`) |
| `_ledger.py` (auditoria) | runner manual; vira automático no flywheel |

## Conclusão
O **núcleo da geração** (conhecimento + ICP no pensador + decision log + crítico +
guardrails) está encaixado. Os dois furos eram: **(1)** avatar não-inferido — **corrigido**;
**(2)** avaliador fora do pipeline — **deliberado pra Fase 6** (custo). O resto é
standalone por design, com caminho claro de integração.
