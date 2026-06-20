# Insights do plugin-metta-ads aplicados ao ad-generator

Síntese do estudo do **plugin-metta-ads v0.6 "vision-first"**
(github.com/AllissonOliveira/plugin-metta-ads, mantido por Alisson Oliveira) e o
que foi portado pra cá. O plugin e o ad-generator resolvem o mesmo problema por
caminhos diferentes: o plugin é um orquestrador de subagents do Claude Code; o
ad-generator é um pipeline Python determinístico. Vários insights já existiam aqui
em outra forma — este doc separa o que **já tínhamos**, o que **entrou agora**, e o
que ficou **fora de escopo** (com motivo).

## Mudança principal: o "same-designer test"

O insight central do plugin é **vision-first com comparação contra o banco**: a
peça produzida é julgada *ao lado* de uma referência campeã, com a pergunta-mãe
*"isso passaria como obra do mesmo designer?"*. O ad-generator já tinha o banco
(`data/applications-index.json`, 73 ads + 36 outros) e já olhava a peça produzida
(`api/_vision_qa.py`), mas **nunca comparava com a referência** — julgava no vácuo.

Entrou:

- **`api/_critic.py`** — dois passos espelhando o plugin:
  - `pick_reference()` (≈ F1 do plugin): filtra o catálogo por marca e escolhe a
    referência mais próxima da peça (por copy + conceito visual + tratamento). Só
    entram candidatos com **raster** em disco — as 106 peças com thumb `.webp`. Os
    ads "mid" são **SVG do Figma** (texto vetorizado em `<path>`), ilegíveis por
    visão: exatamente a cegueira que matou as v0.1–0.5 do plugin. Por isso usamos os
    thumbs raster.
  - `critique()` (≈ critic-visual): manda **referência + peça produzida** pro modelo
    de visão e pede veredito comparativo em 4 eixos — same-designer, integridade
    física, texto inventado, anti-slop — com `feedback_for_designer` acionável.
- **`content/direcao-arte/anti-slop.md`** — checklist anti-slop (16 itens + regra-mãe
  "se o banco faz, não é slop") portado do `metta-anti-slop.md`.
- **Wiring em `api/generate.py`** — o crítico roda dentro do loop de regeneração que
  já existia. No FAIL (de qualquer um dos dois checks), o `feedback_for_designer`
  vira o brief da próxima tentativa (o plugin chama isso de "feedback colado no
  re-spawn"). Gated por `CRITIC_COMPARE=1`, degrada gracioso sem OpenAI/sem
  referência. O retorno ganhou o campo `critic`, e os diagnostics logam a referência
  usada (transparência ≈ F7 do plugin).

## Dependência `metta-brand`: NÃO precisamos — usamos o nosso

O plugin depende de uma skill global `metta-brand` (voz da marca + identidade visual
+ banco de referências). **Não recriamos isso.** O ad-generator já tem cada função,
na própria estrutura — o crítico lê o NOSSO banco, sem nenhuma dependência externa:

| Função do `metta-brand` | Nosso equivalente já existente |
|---|---|
| Voz / identidade da marca | `content/marca/`, `content/verbal/identidade-verbal.md`, `content/visual/ds-*`, `content/audiencia/icp.md` |
| Logos, símbolos, assinaturas, ícones | `assets/logos` · `assets/symbols` · `assets/signatures` · `assets/icons` + `source/ad-blueprints/_brand/` |
| Índice do banco com metadados (`INDEX-VISUAL.md`) | `data/applications-index.json` (73 ads · mood/intent/archetype_foto/tokens/notes) |
| PNGs de referência que o pipeline olha | `assets/applications/ads/thumbs/*.webp` (106 utilizáveis) |
| Skills consultadas pelo pipeline | `engine/brand-knowledge/skills/01–06` |

`api/_critic.py` resolve tudo a partir de `data/applications-index.json` + os thumbs
locais (`_ROOT/...`). Importar ou clonar `metta-brand` seria duplicar o que já temos.

## Guardrails — o que o plugin tem vs o que temos

O `gate.py` do plugin tem 6 travas mecânicas + regras de série. Mapa contra o nosso
`api/_qa.py` (depois do trabalho desta rodada):

| Guardrail (plugin) | Ad-generator |
|---|---|
| `copy_*_literal` (copy byte-a-byte) | **✅ portado** — por sequência de palavras (robusto a `<br>`/`<span>` do auto-quebra e à pontuação), em `_qa.py` |
| `no_invented_text` | **✅ portado** — texto visível ∈ copy ∪ chrome da marca ∪ whitelist. Whitelist **brand-aware** (eyebrow Metta vs assinatura Tiago) |
| `tokens_compliance` | ⚠️ parcial — `_qa.py` checa Zalando presente; cor é controlada pelo template/`_engine.css` |
| `data_roles_present` | ➖ mecanismo diferente (checa canvas `.ad` + fonte injetada) |
| copy literal (não editar, admitir impossível) | ✅ art director rejeita `headline_marked` se as palavras divergem |
| whitelist montada com o user | ✅ `copy.whitelist` + chrome de marca embutido |
| iteration caps | ✅ `VISION_QA_MAX` + `_autogen.max_attempts` |
| anti-slop | ✅ no crítico (`_critic.py` + `anti-slop.md`) |
| guardrail de defeito objetivo | ✅ **a mais que o plugin** — `_evaluator.py` capa o veredito por defeito (texto inventado/integridade) |
| moderação/segurança de imagem | ✅ **a mais que o plugin** — skill 04 (regra de dignidade/moderação) |
| série C1–C8 / family diversity | ➖ N/A neste pipeline (peça única por chamada) |

Resumo: temos hoje **a maioria das travas do plugin** + duas que ele não tem
(guardrail de defeito no juiz final, e moderação na skill 04).

## Mapa completo dos insights

| # | Insight do plugin | Status no ad-generator |
|---|---|---|
| 1 | **Vision-first** (olhar PNG, não parsear código) | **Reforçado.** Já olhava a peça produzida; agora olha também a **referência** do banco. (O render aqui é HTML legível — a cegueira do plugin era no banco Figma; resolvida usando os thumbs raster.) |
| 2 | **3 papéis** (director/designer/critic), quem aprova não escreveu | **Já tínhamos em espírito** (art director compõe, vision-qa julga). Agora o crítico é juiz **comparativo** de verdade, chamada de visão separada. |
| 3 | **Gate mínimo e mecânico** (copy literal, no_invented_text, tokens) | **Já alinhado.** `api/_qa.py` checa só o binário (archetype, headline, overflow, fonte). Copy é literal **por construção** (injetada no template). `no_invented_text` agora coberto **visualmente** pelo crítico. |
| 4 | **2 modos de brief** (A literal / B ideia→proposta) | **Parcial / fora de escopo.** Modo A é o padrão (wizard/CLI). Modo B (ideia→copy proposta) existe como skill 01 mas é pulado no wizard. Feature de produto — não mexido aqui. |
| 5 | **Banco como referência + same-designer test** | **NOVO.** `pick_reference` + `critique`. É a mudança principal. |
| 6 | **Subagents não spawnam subagents** → orquestra no main loop | **N/A.** Pipeline é processo Python único, não há subagents. |
| 7 | **Whitelist montada COM o usuário** | **Parcial.** Eyebrow/label via `--tag`; texto inventado na imagem agora pego pelo crítico. |
| 8 | **Copy literal byte-a-byte sagrada** | **Já garantido.** Template injeta a copy; o art director rejeita `headline_marked` se as palavras divergirem. |
| 9 | **Designer inspeciona o próprio render** | **Já tínhamos.** `_vision_qa` abre o PNG produzido. |
| 10 | **Diversidade de família entre variantes** | **Fora de escopo.** Gera 1 peça por `model_id`; `concept_memory` varia a cena entre execuções. Multi-variante divergente é feature maior. |
| 11 | **Anti-slop como julgamento** | **NOVO.** `anti-slop.md` + eixo no crítico. |
| 12 | **Marca/texto/números nunca na imagem gerada** (HTML por cima) | **Já tínhamos.** Render põe texto via HTML; prompts têm "no text in image". Crítico agora **dupla-checa** texto rasterizado na foto. |
| 13 | **Modos de falha do gpt-image documentados** | **NOVO.** Seção "MODOS DE FALHA DO gpt-image-2" na skill 04 (texto/mãos/faces/UI/numerais + como reformular) + `NEG_MODEL_FAILS` em `_art_director.py` anexado a todo negative_prompt (caminho primário, determinístico e regeneração). Vale pras 2 marcas. |
| 14 | **feedback_for_designer → regeneração** | **NOVO.** Antes a regen só recebia o `reason` da vision-qa; agora recebe o feedback acionável do crítico comparativo. |
| 15 | **Transparência: reportar referência usada (F7)** | **NOVO.** Diagnostics logam `referência do banco = <id> (score)`; retorno expõe `critic.reference_id`. |

## Como ligar/desligar

- `CRITIC_COMPARE=1` (default) liga o crítico comparativo. `=0` desliga (volta ao
  comportamento anterior: só vision-qa isolada).
- `CRITIC_MODEL` (default = `VISION_QA_MODEL`, que é `gpt-4.1`) escolhe o modelo de visão.
- `VISION_QA_MAX` (default 2) limita as regenerações — agora compartilhado pelos dois checks.
- Só roda em peças com **foto gerada** (`image_source=generate`), onde existe PNG —
  igual à vision-qa. Peças tipográficas puras não disparam o crítico (limitação
  conhecida; o same-designer test também valeria pra elas — próximo passo).

## Próximos passos recomendados (não feitos aqui)

1. **Crítico em peças tipográficas** — estender o gate de `image_source=generate`
   pra também comparar peças sem foto contra referências tipográficas do banco.
2. **Modo B no wizard** — ideia bruta → proposta de copy aprovada antes de produzir.
3. **Multi-variante divergente** — gerar 2 variantes de famílias diferentes por chamada.

> Feito nesta rodada além do crítico: **modos de falha do gpt-image** (item 13)
> portados pra skill 04 + `NEG_MODEL_FAILS`. Bugfixes de ambiente: `_find_chrome()`
> acha o Chrome no macOS/Linux (`_render_png.py`); `cli.py` mostra o crítico.
