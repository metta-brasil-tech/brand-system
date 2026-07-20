# 🎯 TAREFA (handoff p/ outro agente) — Concept-first: matar o "picker de thumbnails iguais"

> **Para:** próximo agente de engenharia no repo `brand-system`.
> **Tamanho:** grande (multi-arquivo, front-end + back-end + UX). Faça em FASES, testando e commitando cada fase.
> **Fonte de verdade do plano:** `content/direcao-arte/PLANO-MESTRE-agente-imagem.md` (esta tarefa é a Fase 2). Atualize o status lá ao terminar cada fase.
> **Regra de ouro:** o wizard (`source/embed/criar.html`) é a UI ao vivo (oculta em prod, mas real). **Nunca pushe pela metade.** Teste local → `cp source/embed/criar.html embed/criar.html` → `git push` só quando funcionar de ponta a ponta.

---

## 1. O problema (por que essa tarefa existe)

Hoje o wizard mostra um **picker de ~20 estilos como thumbnails estáticos** (`.webp` fixos em `assets/style-previews/`). Problemas:
- Os thumbnails "parecem todos iguais" e **enganam** — o que sai não é o thumbnail, é a copy do usuário renderizada, que pode ficar bem diferente.
- O usuário escolhe às cegas: não vê a **própria copy** no estilo antes de gastar uma geração.
- Fere o princípio **UX-first** do projeto (pensar pela ótica de quem usa o site, não pela estrutura interna).

**Visão-alvo (do PLANO-MESTRE):**
> A pessoa **escreve a ideia/copy** → o motor propõe **2–3 composições calibradas da COPY DELA** (com preview real, não thumbnail) → ela escolhe, ajusta, publica.

O "estilo" deixa de ser miniatura cega e vira **preview vivo da mensagem dela**.

---

## 2. Estado atual do código (o que já existe — NÃO refazer)

**Arquitetura da peça:** `FOTO de fundo (gerada 1× por IA) + CAMADA DE TEXTO em HTML/CSS` (grátis, re-renderável). Isso é o que torna o preview barato: o texto/layout não custa nada.

**Motor de render (Python):** `api/_blueprint_render.py::render(marca, model_id, copy, image_url="", format="feed") -> {html, missing, ...}`.
- Com `image_url=""` renderiza **text-only** (sem foto) — perfeito pra preview.
- Blueprints em `source/ad-blueprints/<marca>/<ID>.md` (front-matter: `archetype`, `params`, `image.required`). CSS: `source/ad-blueprints/_engine.css`. Auto-fit JS: `_engine.js` (sinaliza `data-engine-ready=1` quando pronto).
- Hook `data-model="<ID>"` no `.ad` permite CSS por modelo (usado no FOTO-PILL).
- Ornamentos SVG (`_ornament()` + param `ornament`): recurso definidor de estilos sem foto (YELLOW-DRAW, DARK-CARTA).

**Endpoints HTTP (Vercel serverless, pasta `api/`):**
- ✅ **`api/preview.py`** — **JÁ CRIADO NESTA SESSÃO (commit 3c72b45, no ar).** `POST /api/preview` Body `{marca, model_id, copy:{headline,subhead,body,cta,tag}, format}` → `{html, usa_imagem, model_id, missing}`. Renderiza a copy real no estilo **sem gerar foto, sem LLM, custo zero**. `usa_imagem` vem do `image.required` do blueprint (true = estilo foto-real). **É a base desta tarefa — só falta consumir no front-end.**
- `api/render.js` — `POST {html, format}` → PNG (Chromium real @2x). Transforma o HTML do preview/geração em imagem final. Espera `data-engine-ready=1`.
- `api/generate.py` — pipeline COMPLETO (art-director LLM → prompt → imagem Gemini/gpt-image → focus-map → render → vision-qa/crítico). É o caminho caro (com foto). `maxDuration: 60`.
- `api/prompt-image.py` — ideia solta → direção visual (o botão "Gerar direção com IA").

**Front-end:** `source/embed/criar.html` (canônico) → `embed/criar.html` (deploy; o build só copia). O picker é montado a partir de `const STYLES_METTA = [...]` e `STYLES_TIAGO` (procure `previewSrc`). Cada estilo tem `{id, label, desc, usaImagem, formatos, previewSrc, comingSoon?}`. Cliente HTTP: procure `fetch(` e o wrapper que adiciona token nas `/api/*`.

**Roteamento de provider:** `api/_nano_pipeline.py::resolve_route(model_id)` — foto-real → Gemini (`gemini-3-pro-image-preview`); tipográfico/conceitual → gpt-image. `GEMINI_API_KEY` **já está na Vercel** (Nathan configurou). Localmente em `.env.local` (`set -a; source .env.local; set +a`).

---

## 3. A tarefa (fazer em 3 fases)

### FASE A — Preview vivo da copy no picker (2.2) · começar por aqui
Substituir o thumbnail estático pelo **preview real da copy do usuário**, para os estilos **sem foto primeiro** (grátis).

1. **Pré-requisito de UX:** a copy do usuário precisa existir ANTES do picker. Hoje verificar a ordem dos passos no wizard (copy → estilo, ou estilo → copy?). Se o picker vem antes da copy, reordenar OU disparar o preview assim que a copy existir. Preview só faz sentido com copy digitada.
2. Para cada card de estilo `usaImagem:false` visível no picker: chamar `POST /api/preview` com a copy atual + `model_id` + `format`. Receber `html`, injetar num `<iframe srcdoc>` ou renderizar via `/api/render` → `<img>` (iframe é mais barato/rápido pra preview; render.js só quando for confirmar/exportar). Trocar o `previewSrc` estático por esse preview vivo.
3. Estilos `usaImagem:true` (foto-real: A, B, D, DARK-OBJETO, FOTO-PILL, NEWS, YELLOW-SPLIT, etc.): mostrar o preview text-only (o layout/tipografia já é fiel, só falta a foto) + **badge "gera a foto quando você escolher"**. Só chamar `/api/generate` (caro, Gemini) no estilo REALMENTE escolhido.
4. **Performance:** não renderizar os 20 de uma vez de forma síncrona. Renderizar sob demanda (lazy, ao entrar na viewport / ao focar o card) e cachear por `(model_id, hash da copy, format)`. Debounce quando a copy muda.
5. **Fallback:** se `/api/preview` falhar, cair no thumbnail estático (`previewSrc`) — nunca deixar card vazio.

### FASE B — Concept-first: 2–3 composições calibradas (2.1)
O salto de paradigma. Em vez de listar 20 estilos, o motor **recomenda 2–3** estilos que melhor servem a copy/ideia do usuário e mostra a copy dela renderizada neles.
1. Recomendador de estilo por copy: dado `{ideia, copy, funil (TOFU/BOFU), tem_número?, é_caso_nominal?, tom}`, escolher 2–3 `model_id` candidatos. Pode ser (a) heurística por regras (mapear os `## Quando brilha` / `## Anti-padrões` dos blueprints — eles já descrevem quando cada estilo serve), ou (b) um classificador LLM leve (1 chamada barata). Começar por heurística (grátis, determinística).
2. Renderizar a copy real nos 2–3 (via `/api/preview` p/ sem-foto; 1 geração Gemini p/ foto-real só se o usuário pedir "ver com foto").
3. UI: apresentar as 2–3 composições lado a lado com a MENSAGEM DELA já dentro. Usuário escolhe → ajusta → publica.
4. Manter um "ver todos os estilos" como escape hatch (o picker atual vira secundário).

### FASE C — Editor manual de texto pós-preview (liga com protótipo existente)
Já existe `prototipos/editor-texto.html` (WYSIWYG que reposiciona texto sobre a foto ao vivo, custo zero). Plugar no fluxo: depois de escolher a composição, o usuário ajusta âncora/caixa/alinhamento do texto ao vivo e "Confirmar" re-renderiza o PNG via `/api/render` sobre a MESMA foto (sem regerar imagem). Ver memória `brand-system-plano-retomada` (passo do editor Fase 2).

---

### FASE D — Editar a COPY no resultado + escolher a voz de escrita (pedido do Nathan, 20/07)
Hoje a tela "Sua peça foi gerada" só tem **Baixar / Salvar / Gerar variação / Criar nova** — **não dá pra editar o texto** que a IA escreveu, nem escolher o modelo/voz de copy. Isso é um gap real (o usuário quer ajustar as palavras sem regerar tudo).
1. **Editar a copy no resultado (barato, sem regerar foto):** adicionar campos editáveis (headline / body / CTA / tag) na tela de resultado. Ao editar, re-renderizar via **`/api/preview`** passando a **MESMA foto** (`image_data_uri` passthrough — o endpoint já aceita isso, é o mesmo mecanismo do editor de âncora 2.4) + a copy nova. Custo zero, instantâneo. Só o texto muda; a foto fica.
2. **Escolher a voz/modelo de escrita:** antes/durante a copy, deixar o usuário escolher o registro (ex.: direto/provocativo, institucional, reflexivo) ou pedir "reescrever" — chama o copywriter (`api/_copywriter.py`) com o registro escolhido e devolve variações de copy pra escolher. Mínimo viável: um botão "reescrever a copy" com 2–3 variações; ideal: seletor de tom.
3. **Permissão de edição:** o ponto do Nathan foi "sem permissão de edição" — a copy final tem que ser editável à mão pelo usuário, não só gerada. Garantir que os campos são editáveis e persistem no re-render/download.
Liga com a FASE C (editor de âncora já existe): unificar num painel "Ajustar" no resultado = **texto (palavras) + posição (âncora) + tom (voz)**, tudo re-renderizando sobre a mesma foto via `/api/preview`.

## 4. Protocolo de teste e deploy (OBRIGATÓRIO)

1. **Local primeiro.** Testar o motor: `.venv/bin/python cli.py --model <ID> --headline "..." --image none --out /tmp/x` e abrir o PNG. Testar o endpoint importando `api/preview.py::_make_preview({...})` num script (ver exemplo abaixo).
2. **Renderizar e OLHAR** a saída (não confiar só em "rodou"). Este projeto exige prova visual — gere a peça e inspecione.
3. **Propagação de deploy:** `cp source/embed/criar.html embed/criar.html` (o build só copia; `npm` pode não estar no PATH — o `cp` replica o que o `build.mjs` faz).
4. **`git push origin main`** = deploy automático na Vercel. **Só pushe quando funcionar de ponta a ponta.** Um wizard quebrado vai pro ar.
5. Se criar/alterar endpoint em `api/`, **registrar no `vercel.json`** com `includeFiles` dos arquivos que ele lê em runtime (ex: `preview.py` precisa de `source/ad-blueprints/**` + `assets/symbols/**` + `assets/tiago/**`). Sem isso, funciona local e quebra em prod.

Exemplo de teste local do endpoint:
```python
import importlib.util, sys; sys.path.insert(0,'api')
spec=importlib.util.spec_from_file_location("preview","api/preview.py")
pv=importlib.util.module_from_spec(spec); spec.loader.exec_module(pv)
print(pv._make_preview({"marca":"metta","model_id":"LIGHT-TIPO",
  "copy":{"headline":"Método não é sorte. É régua.","cta":"Conhecer"}})["usa_imagem"])
```

---

## 5. Gotchas (aprendidos na marra)

- **Submódulo `engine/`** (repo ad-generator): mudança DENTRO dele = `cd engine` → commit → push → bumpar ponteiro no pai. NUNCA commitar arquivos do engine como do pai. Os blueprints/CSS de render ficam no PAI (`source/ad-blueprints/`), não no engine — então mexer em render NÃO toca o submódulo.
- **`render_out/`** fica fora do deploy (`.vercelignore`) — é 168MB de teste; se entrar na função, o bundle estoura 225MB e o deploy falha.
- **Geração de foto é estocástica:** o layout é 100% reproduzível, a FOTO varia a cada chamada. Setar essa expectativa na UI ("a foto é gerada, muda a cada vez").
- **Custo:** `/api/preview` é grátis (sem imagem/LLM). `/api/generate` com foto-real gasta ~1 geração Gemini (~20s, ~$0.04). Não disparar geração de foto em massa no picker — só no estilo escolhido.
- **Vision-qa às vezes deriva** foto-real pra metáfora de objeto (a "chupeta"): é comportamento do art-director/relevância, não do estilo. Item aberto no PLANO-MESTRE §6.
- **`_engine.js`** faz auto-fit (headline cresce/encolhe). O `/api/render` espera `data-engine-ready=1`. Um `<iframe srcdoc>` de preview roda esse JS igual — bom.
- **"Sofia" nas anotações antigas = o próprio Nathan** (nome na conta).

---

## 6. Critérios de aceite

- [ ] **Fase A:** ao digitar a copy e abrir o picker, cada estilo sem-foto mostra a **copy real do usuário renderizada** (não o thumbnail). Foto-real mostra layout text-only + badge. Fallback pro thumbnail se o preview falhar. Testado local, `cp` feito, pushado, e **verificado ao vivo** na URL da Vercel.
- [ ] **Fase B:** ao escrever uma ideia/copy, o wizard recomenda 2–3 estilos com a copy dela renderizada, lado a lado; escolher leva pra geração/ajuste. "Ver todos" continua disponível.
- [ ] **Fase C (opcional/stretch):** editor de texto ao vivo plugado após a escolha, re-render sobre a mesma foto sem regerar.
- [ ] PLANO-MESTRE atualizado (Fase 2 → status) e memória `brand-system-plano-retomada` atualizada.

---

## 7. Primeiros comandos ao pegar a tarefa
```bash
cd ~/Documents/Claude/brand-system
set -a; source .env.local; set +a          # carrega OPENAI + GEMINI
git log --oneline -12                        # ver o que já foi feito (até 3c72b45)
# ler: content/direcao-arte/PLANO-MESTRE-agente-imagem.md (Fase 2)
# ler: api/preview.py (a base já pronta) e source/embed/criar.html (STYLES_METTA, fetch /api/*)
# testar o endpoint local (ver §4), depois começar pela FASE A.
```
```
```
