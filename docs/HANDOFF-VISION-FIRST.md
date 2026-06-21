# Handoff — Vision-first + Camada de Conhecimento (estado atual)

Contexto pra quem pega este trabalho frio. Tudo isto nasceu de portar os insights
do plugin `AllissonOliveira/plugin-metta-ads` (vision-first) pro ad-generator, e
evoluiu pra resolver o problema de raiz: **a geração nasce cega ao que a marca sabe.**

## Onde está o quê (IMPORTANTE)
- **Repo `brand-system`** (este) = 95% do trabalho. Clone com `--recurse-submodules`.
- **Repo `ad-generator`** = submódulo `engine/`. Só a skill 04 mudou lá.
- Roda em **Python 3.11** (o 3.9 do sistema quebra). Env: `OPENAI_API_KEY`,
  `BRAND_KNOWLEDGE_PATH=$PWD/engine/brand-knowledge`, `ARTIFACTS_DIR=$PWD/artifacts`.

## O que está PRONTO
| Arquivo | O que é | Wired na geração? |
|---|---|---|
| `api/_critic.py` | crítico comparativo (same-designer test vs banco) + anti-slop + texto-inventado | ✅ sim (`generate.py`, default `CRITIC_COMPARE=1`) |
| `api/_qa.py` | + guardrails copy-literal e no_invented_text (brand-aware) | ✅ sim |
| `api/_art_director.py` | + `NEG_MODEL_FAILS` (modos de falha gpt-image) | ✅ sim |
| `engine/.../04-image-prompt-engineer.md` | seção de modos de falha do gpt-image | ✅ sim |
| `api/_render_png.py` | acha Chrome no macOS/Linux (era bug) | ✅ sim |
| `api/_evaluator.py` | juiz final: nota 0-10 + SHIP/REVISAR/DESCARTAR + `image_fixable` | ⚠️ standalone (driver: `render_out/_avaliar_criativos.py`) |
| `api/_autogen.py` | loop de auto-melhoria (gera→avalia→regera com feedback→melhor) | ⚠️ standalone (driver: `render_out/_autogen_demo.py`) |
| `api/_knowledge.py` | **camada de recuperação** — puxa ICP/voz/metodologia/depoimento por copy | ✅ sim (passo 2: injetada no diretor de arte) |
| `api/generate.py` (decision log) | salva `artifacts/<run_id>/03-decision-log.json`: rationale + image_concept + proveniência + avatar | ✅ sim (passo 3) |

Docs: `INSIGHTS-PLUGIN-METTA-ADS.md`, `CAMADA-RECUPERACAO.md`, `ARQUITETURA-GERACAO.md`.

## O insight central (o "por quê" disto tudo)
A geração (diretor de arte + skill 04) decide cena/persona com **input pobre** — daí
"use mulher / cena genérica". O brand-system tem ICP, voz, metodologia, depoimentos,
95 transcrições — quase tudo **sem uso** na geração. Pior: o **ICP existe e está bom**
(`content/audiencia/icp.md` v3 + `engine/brand-knowledge/audience/avatars.json` com 7
segmentos), mas o CLI nunca passa avatar, e mesmo o site só leva o avatar à skill 04,
**nunca ao diretor de arte (o pensador)**.

## Roadmap (ordem por dependência) — estamos no passo 4
1. ✅ **Camada de recuperação** (`_knowledge.py`) — dá contexto rico.
2. ✅ **ICP no pensador** — segmento inferido pela copy + `_knowledge.retrieve()`
   e avatar injetados **dentro de `_art_director.direct()`**; persona/cena nascem
   ancoradas no ICP+voz+método, não na heurística "use mulheres".
3. ✅ **Decision log** — `generate.py` persiste `artifacts/<run_id>/03-decision-log.json`
   por criativo: `rationale` do diretor + `image_concept` + proveniência do
   `_knowledge` (`[(tipo, fonte)]`) + bloco injetado + avatar escolhido. Best-effort
   (nunca derruba a geração); diagnóstico `decision-log: salvo …`. É a base do passo 4/5.
4. ◀ **Avaliador critica o raciocínio** (PRÓXIMO) — `_evaluator` lê o `03-decision-log.json`
   e julga "persona bate com o ICP? cena ilustra a copy?", não só o pixel.
5. **Flywheel** — peça aprovada (SHIP) entra no banco → crítico mais afiado + geração
   reference-aware → melhora composta.

## Como testar local
```bash
set -a; . engine/.env; set +a
BRAND_KNOWLEDGE_PATH="$PWD/engine/brand-knowledge" ARTIFACTS_DIR="$PWD/artifacts" \
python3.11 cli.py --model A-headline-foto-dark --headline "..." --subhead "..." \
  --cta "..." --image generate --preset fotorrealista --format feed
```
> ⚠️ O CLI ainda **não tem** `--avatar-segment/--avatar-variant` — adicionar isso faz
> parte do passo 2. Atenção: local usa OpenAI; produção usa Claude + render via
> `api/render.js` — resultados podem divergir.
