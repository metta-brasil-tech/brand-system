# Série de carrossel — direção e regras mecânicas

Fonte canônica das regras de série usadas pelo modo `--serie` do CLI
(`api/_serie.py`). Porta das serie-rules do `plugin-metta-ads` (v0.6),
adaptada ao pipeline blueprint-driven do brand-system.

**Filosofia:** carrossel Metta não é um template replicado em N slides com copy
diferente. É decisão slide-a-slide ancorada em **família visual travada** +
tipografia consistente — a identidade vem do vocabulário, não da repetição de
molde. (Anti-padrão histórico: 10 carrosséis tipográficos chapados da v0.4 do
plugin.)

## Anatomia

| Posição | Função | Default |
|---|---|---|
| Slide 1 (capa) | Gancho visual + headline curta | nunca tipográfica pura |
| Slides 2..N-1 | Argumento, dado, lista, narrativa | tratamento por estrutura da copy |
| Slide N | CTA forte | sempre `T-CTA-FINAL` |

Default Metta: 6-8 slides. Mínimo 2 (mecânico) / 4 (editorial). Máximo 10.
**UM formato por série** (feed 1080×1350 default; story se o brief pedir).

## Tratamentos → blueprints (ponte)

Vocabulário fechado — não se inventa tratamento. IDs preservados do plugin.

| Tratamento | Quando | Blueprints (ordem de preferência) | Capa? | Tipográfico? | Foto IA? |
|---|---|---|---|---|---|
| `T-FOTO-CENA` | headline + sub sobre cena | A-headline-foto-dark, B-foto-top-headline-mixed, D-foto-fullbleed-overlay, I-retrato-editorial-pb, FOTO-PILL-CASUAL | ✓ | — | ✓ |
| `T-SPLIT-DUAL` | comparativo 2 zonas | YELLOW-SPLIT | ✓ | — | ✓ |
| `T-OBJ-ESCURO` | objeto-conceito sobre dark | DARK-OBJETO, DARK-COLAGEM | ✓ | — | ✓ |
| `T-TWEET-CARD` | statement/citação em card | METTA-TWEET-CARD | — | — | — |
| `T-MOCKUP-NEWS` | dado/manchete, credibilidade | NEWS-CARD | — | — | ✓ |
| `T-BULLETS-DARK` | lista/checklist | YELLOW-BLOCO | — | ✓ | — |
| `T-AMARELO-STATEMENT` | frase categórica curta | YELLOW-DRAW, YELLOW-EDITORIAL, YELLOW-FRAME, YELLOW-OBJETO | ✓ | — | ✓ |
| `T-DEFINICAO` | conceito/manifesto tipográfico | LIGHT-TIPO, H-fundo-branco-headline-gigante, DARK-CARTA | — | ✓ | — |
| `T-HIGHLIGHT-XL` | headline grande, palavra em destaque | C-tipografia-pura-dark, K-bold-dourado-urgencia | ✓ | ✓ | — |
| `T-CTA-FINAL` | fechamento com CTA | K-bold-dourado-urgencia, D-foto-fullbleed-overlay, YELLOW-EDITORIAL | — | — | — |

## Famílias visuais

`DARK` · `LIGHT` · `YELLOW`, derivadas do `params.theme` do blueprint (overrides:
DARK-CARTA→DARK, YELLOW-SPLIT→YELLOW, YELLOW-BLOCO→YELLOW). No plugin a trava é
por paleta nomeada (P1–P10); aqui a paleta vive dentro do blueprint, então o
análogo mecânico trava a **família dominante** no slide 1.

## Regras (quem valida)

| Regra | Enunciado | Onde |
|---|---|---|
| C1 | Capa nunca é tipográfica pura (perde o stop-scroll) | `_serie.validate_serie` |
| C2 | Último slide é sempre `T-CTA-FINAL` | `_serie.validate_serie` |
| C3 | Tratamento não repete o do slide anterior (exceção: `continued` pra lista que continua) | `_serie.validate_serie` |
| C4 | Família travada no slide 1; inversão pontual ok, troca de família não (máx 2 famílias, dominante ≥ metade) | `_serie.validate_serie` |
| C5 | Motivos recorrentes na série | julgamento visual (critic) |
| C6 | Máximo 2 slides tipográficos na série | `_serie.validate_serie` |
| C7 | Reconhecibilidade de marca no conjunto | julgamento visual (critic) |
| C8 | UM formato por série | modo `--serie` do CLI |

C5 e C7 são julgamento por design — mecanizar reprovaria peças legítimas do
banco (lição do plugin v0.6: regra mecânica que contradiz o banco é regra errada).

## Classificação copy → tratamento

Mecânica (sem interpretação): `word_count`, lista (`- •` ou `1.`), pergunta,
número/R$, aspas, muito-curto (≤8 palavras), longo (≥50). Mapa em
`_serie._candidates`. Com a família travada, tratamentos com blueprint na
família têm prioridade (sort estável preserva a ordem estrutural).

## Modo panorama (cena contínua no swipe)

`--panorama "<cena>"` (2-4 slides): UMA imagem panorâmica (Nano Banana Pro, com
referência do banco) é fatiada localmente entre os slides — o fundo se completa
no swipe. Todos os slides saem em `D-foto-fullbleed-overlay` (fatia como fundo,
texto por cima com caixa `plain`), o último leva o CTA (C2), e a repetição de
tratamento é marcada `continued` (exceção legítima da C3 — é uma cena só).
1 chamada de imagem pra série inteira. Requer `GEMINI_API_KEY`. O fatiamento
(`_nano_pipeline.slice_panorama`) é puro/local e testado sem API.

## Anti-monotonia entre séries

Antes de planejar, o CLI olha os últimos `serie-config.json` sob `render_out/`
(`_serie.familia_hint_from`): se as 2 séries mais recentes foram da mesma
família, a capa da próxima prefere **outra família** — porta da regra da seção
3.5 do plugin (opera sobre família, não sobre paleta individual).

## Uso

```bash
# slides.json: [{"headline":"...","subhead":"...","body":"...","cta":"..."}, ...]
python cli.py --serie slides.json --plan-only    # plano + validação, sem custo
python cli.py --serie slides.json --format feed  # gera ad-slide-N.png + serie-config.json
```

Campos opcionais por slide no JSON:

- `"treatment": "T-*"` — força um tratamento do vocabulário (o planner não
  reclassifica; validação C1–C6 continua valendo).
- `"continued": true` — exceção da C3 pra lista/thread que continua no slide
  seguinte com o mesmo tratamento.

Marcadores de lista no `body` (`- `, `• `) servem só pra classificação — o CLI
os remove antes do render (o blueprint de bullets põe o próprio marcador).

`serie-config.json` registra família, tratamento e blueprint por slide —
mesmo artefato de paridade do plugin.
