# Ad Generator — rodar e testar localmente

A UI (`/criar`) está **oculta em produção** (validação interna). A forma suportada
de gerar/testar ads é o **CLI** (`cli.py`), que roda o mesmo pipeline da API.

## Pré-requisitos
- Python 3.10+
- `OPENAI_API_KEY` (a geração de texto e de imagem usa a OpenAI)
- (opcional, recomendado) Google Chrome OU Playwright — pra exportar o PNG

## 1. Clonar / atualizar o repo (com o submódulo `engine`)

O engine (ad-generator) é um **submódulo git**. Precisa inicializar.

```bash
# clone novo:
git clone --recurse-submodules https://github.com/metta-brasil-tech/brand-system.git
cd brand-system

# OU, se já tem o repo:
git pull origin main
git submodule update --init --recursive   # traz o engine no commit PINADO (não dê pull cego no submódulo)
```

## 2. Ambiente Python

```bash
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (git-bash):    source .venv/Scripts/activate
# macOS/Linux:           source .venv/bin/activate

pip install -r requirements.txt          # runtime do pipeline
pip install -r requirements-local.txt    # opcional: render PNG via Playwright
python -m playwright install chromium     # opcional: baixa o Chromium do Playwright
```
> Sem Playwright: se você tiver o **Google Chrome** instalado, o render do PNG cai
> num fallback automático. Sem nenhum dos dois, o CLI ainda gera o **HTML** (abra no navegador).

## 3. Chave da OpenAI

```bash
# git-bash/macOS/Linux:
export OPENAI_API_KEY="sk-..."
# Windows PowerShell:
$env:OPENAI_API_KEY="sk-..."
```

## 4. Gerar um ad

```bash
# ver os modelos disponíveis:
python cli.py --list

# ad COM foto (gera imagem via IA):
python cli.py --model A-headline-foto-dark \
  --headline "Crescer deixou de ser sorte." \
  --subhead "Quando a operação tem método, a próxima venda é previsível." \
  --cta "Conheça a Metta" \
  --image generate --preset fotorrealista

# ad tipográfico (SEM foto):
python cli.py --model C-tipografia-pura-dark \
  --headline "Vendedor herói não é estratégia." \
  --body "Método transforma esforço em previsibilidade." \
  --cta "Conheça a mentoria" --image none

# bullets (YELLOW-BLOCO) — use \n no body:
python cli.py --model YELLOW-BLOCO \
  --headline "Sua operação tem método ou tem sorte?" \
  --body $'Processo estruturado\nIndicadores que orientam\nRitmo de gestão semanal' \
  --cta "Aplique para a mentoria" --image generate --preset bw-yellow
```

Saída em `./render_out/out/<modelo>.png` (+ `.html`). Abra o PNG.
(Outra pasta: `--out <caminho>`.)

## 5. Gerar um carrossel (série)

```bash
# slides.json: [{"headline":"...","subhead":"...","body":"...","cta":"..."}, ...]
python cli.py --serie slides.json --plan-only    # só o plano (tratamento/modelo/família por slide) — sem custo
python cli.py --serie slides.json --format feed  # gera ad-slide-N.png + serie-config.json
```

O plano segue as regras de série (capa nunca tipográfica, último slide sempre
CTA, anti-repetição, família visual travada no slide 1, máx 2 tipográficos) —
detalhes em `content/direcao-arte/serie-carrossel.md`. Carrossel é **um formato
por série** (`--format`, default feed).

## Opções úteis
- `--format feed|story|sqr` (default feed = 1080×1350)
- `--preset fotorrealista | cinematic-dark | bw-yellow | surreal-hbr`
- `--tag "..."` eyebrow/label (NEWS-CARD, K)
- `--auto-improve` loop gera→avalia→regera até SHIP (teto: `--max-attempts`, default 3; só com `--image generate`)
- `--no-vision-qa` desliga a checagem final por visão (mais rápido/barato)
- `--no-art-director` desliga composição/direção visual

## O que o pipeline faz por baixo (resumo)
copy → **Diretor de Arte + Visual** (composição + conceito de cena variado, com memória
pra não repetir) → **engenheiro de prompt** (identidade da marca + composição-por-slot)
→ **gpt-image-2** → **render** (blueprint adaptativo, Zalando real) → **export @2× Chromium**
→ **checagem final por visão** (imagem ilustra a copy? layout não mutila? → regenera se falhar).

## Notas
- Modelo de imagem default: `gpt-image-2` no `low` (~20-30s/imagem). Troque com
  `IMAGE_GEN_PROVIDER` / `IMAGE_QUALITY`.
- A memória de conceitos fica em `render_out/artifacts/concept_memory.json` no CLI
  (`ARTIFACTS_DIR` configurável) — garante variação entre execuções na mesma máquina.
- Em produção o PNG é renderizado pela função Node `api/render.js` (Chromium no Vercel),
  não pelo Python.
