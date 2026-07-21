# 🧠 Gerador de Criativos Metta/Tiago — Raciocínio geral, arquitetura e estado

> **O que é este documento:** um dump completo e auto-contido do raciocínio, da
> arquitetura, de tudo que foi feito nesta jornada e das questões em aberto.
> **Para quem:** o Nathan e uma **outra IA revisora** (perspectiva fresca /
> revisão adversarial). Escrito pra ser lido do zero, sem contexto prévio.
> **Data:** 2026-07-21 · **Repo:** `brand-system` (github.com/metta-brasil-tech) ·
> **Produção:** https://brand-system-sigma.vercel.app · **HEAD:** `f95050f`.
> **Fontes de verdade relacionadas:** `PLANO-MESTRE-agente-imagem.md`,
> `TAREFA-concept-first.md`, `principios.md`, memórias `adgen-principios-criativo`,
> `brand-system-deploy-gotchas`, `dark-objeto-fora-do-wizard`.

---

## 0. TL;DR (leia isto primeiro)

A Metta tem um **gerador de criativos** (peças de Instagram/anúncio) pra duas
marcas: **Metta** (institucional, gestão comercial) e **Tiago Alves** (marca
pessoal, mentor). A pessoa escreve a copy, escolhe um estilo, e o sistema gera a
peça pronta (imagem + texto).

**O problema-mãe:** as peças que a gente montou **à mão** (com IA guiada) são
ótimas, mas as que o **site gera sozinho** saem piores/genéricas. Fechar essa
distância é o objetivo de tudo.

**Diagnóstico da distância, em 3 causas:**
1. **Fonte da imagem.** As boas usavam foto do **Gemini** (nano banana) ou foto
   curada; o site gera na hora com **gpt-image** (OpenAI), que sai genérico
   ("empresário de terno" padrão). E o **banco de referência** que faria o Gemini
   valer está **vazio**.
2. **Composição.** As regras de posicionamento (texto foge do sujeito) nem sempre
   venciam o layout fixo do modelo → texto cobria rosto, etc.
3. **UX do picker.** Mostrava thumbnails estáticos "todos iguais" que enganavam.

**O que foi feito nesta jornada:** consertei a causa 2 (regra vence sempre),
ataquei a causa 3 (concept-first: você vê sua copy real renderizada), limpei o
catálogo de modelos, consertei um monte de bug de produção/deploy, e deixei a
causa 1 (banco de referência) mapeada como o próximo grande passo.

**O maior bloqueio agora:** a **conta OpenAI estourou a cota** (o gerador usa
OpenAI pro "cérebro" E pra maioria das fotos — mais do que parecia). Enquanto não
recarregar o billing, a geração no site fica degradada.

---

## 1. A visão (onde queremos chegar)

> A pessoa **escreve a ideia/copy** → o motor propõe **2–3 composições calibradas
> da copy dela** (com foto limpa que ILUSTRA a mensagem) → ela escolhe, ajusta,
> publica. Sem retoque de designer.

O "estilo" deixa de ser miniatura cega e vira um **motor de composição** que
garante o nível dos exemplos feitos à mão — automatizado. Se a peça precisa de
retoque humano, o gerador falhou.

---

## 2. Os princípios inegociáveis (as "nossas regras")

Estabelecidos pelo Nathan; a regra de ouro é que **eles vencem o que o modelo do
criativo manda**:

1. **UX-first** — pensar pela ótica de quem usa o site. Ex.: tweet = 1 mensagem,
   sem título/subtítulo.
2. **A imagem tem que ILUSTRAR a copy** — foto que não conversa com a mensagem é
   defeito (ex.: troféu enrolado em fita métrica = "a meta é régua").
3. **Foco/composição adaptativa** — o texto vai no **espaço vazio REAL da imagem**,
   longe do sujeito; esse espaço muda a cada imagem. Molde fixo é o inimigo.
4. **Nada de amarelo gratuito** — amarelo #FFBE18 só quando a peça pede.
5. **Pessoa composta AO LADO, não centralizada com texto por cima.**
6. **Gemini pra pessoa real/conceito**; gpt-image pra objeto/tipográfico.
7. **Nunca inventar dado** (faturamento/%/nº de empresas fabricado).
8. **Só expor o que entrega qualidade** — estilo sem creative provado vira "Em breve".
9. **Foto real do Tiago = as que o Nathan enviou** (recortes), nunca stock nem
   rosto gerado por IA.
10. **As nossas regras se sobressaem SEMPRE do que é pra ser o modelo do criativo.**

---

## 3. A arquitetura (como o sistema funciona de verdade)

### 3.1 As duas "inteligências" e os dois geradores de imagem — o ponto contra-intuitivo

Tem **dois níveis** e a maioria das pessoas (inclusive o Nathan, com razão) acha
que "usa Gemini". Na prática:

- **O CÉREBRO roda na OpenAI.** `LLM_PROVIDER=openai` (`.env.local` e Vercel) →
  todo o raciocínio usa OpenAI (modelo padrão gpt-5 via LiteLLM):
  **art-director** (decide composição/cena), **image-prompt-engineer** (escreve o
  prompt da imagem), **copywriter**, **vision-QA** (confere copy↔imagem),
  **crítico** (teste "same-designer"). São ~4 chamadas OpenAI **por peça**.
- **A FOTO deveria ser Gemini, mas quase sempre cai no gpt-image.** A rota Gemini
  (`api/_nano_pipeline.py::resolve_route` + `generate_via_route`) só dispara pra
  famílias foto-real da Metta **E** quando existe uma **referência do banco
  curado**. Como o banco está vazio, quase tudo cai no **gpt-image** (OpenAI).
  Prova real: num lote de 11 fotos, **só o YELLOW-BLOCO usou Gemini**.

**Consequência:** a OpenAI é o cavalo de tração (cérebro + maioria das fotos), o
Gemini é a exceção. Por isso a cota da OpenAI derruba o site inteiro.

Adapter de imagem: `engine/adapters/image_gen.py::ImageGenAdapter`. Providers:
`nano-banana-2`/`gemini-nano-banana` → `gemini-3-pro-image-preview`;
`openai`/`gpt-image-2` → gpt-image; `gemini`/`imagen` → imagen (não usar, o modelo
imagen-3 não existe na conta). Todos os modelos Gemini de imagem testados OK com a
chave: `gemini-2.5-flash-image`, `gemini-3-pro-image`, `imagen-4.0-generate-001`.

### 3.2 O pipeline de geração, passo a passo (`api/generate.py`)

Endpoint `POST /api/generate`. Fluxo (modo wizard, com `model_id` forçado):

1. **01-briefing-parser** — PULADO no wizard (marca vem do blueprint).
2. **02-style-selector** — PULADO (estilo forçado pelo wizard).
3. **03-blueprint** — carrega o blueprint do modelo (`source/ad-blueprints/<marca>/<ID>.md`):
   front-matter com `archetype`, `params` (theme/anchor/align/…), `image.required`.
4. **avatar-infer** + **art-director** (LLM/OpenAI) — decide ênfase, crop, gaze, e
   a **cena** da imagem a partir da copy. **`66b4dd9`:** quando o usuário escreve a
   "Direção visual da cena", o enquadramento do blueprint vira **DICA, não regra** —
   a direção do user vence em sujeito/cena/tratamento (inclusive "sem pessoa").
5. **04-image-prompt-engineer** (LLM/OpenAI) — transforma a cena num prompt de imagem.
6. **04-image-gen** — gera a foto. Roteamento: Metta foto-real + referência → Gemini;
   objeto/dark/sem-pessoa/Tiago → gpt-image. **Guard "sem pessoa" (`66b4dd9`):**
   se o briefing tem "sem pessoa/gente/humano/ninguém", pula a rota nano (que usa
   uma referência humana e forçava pessoa) e vai pro gpt-image puro.
7. **focus-map** (`api/_focus_map.py`) — **MEDE a imagem gerada** (energia de borda
   por faixa horizontal: topo/meio/base) e decide a **âncora do texto** (top/bottom)
   na faixa mais vazia. **`f95050f` (hoje):** a regra agora VENCE o anchor fixo do
   blueprint sempre que há zona segura (antes cedia em falso "ambíguo").
8. **render** (`api/_blueprint_render.py`) — monta o HTML (foto de fundo via CSS +
   camada de texto). O texto é **camada re-editável** (não é queimado na foto).
9. **vision-QA + crítico** (LLM/OpenAI) — checam relevância copy↔imagem, slop
   (card branco flutuante, texto de IA na foto, número inventado) e "same-designer".
   Podem **regenerar** a imagem (retry).
10. Retorna `{html, image_data_uri, diagnostics, qa, ...}`. O front renderiza o HTML
    num iframe e exporta PNG (html2canvas) ou via `/api/render` (Chromium @2×).

**Arquitetura-chave:** `FOTO (gerada 1×) + CAMADA DE TEXTO em HTML/CSS (grátis,
re-renderável)`. É o que torna o preview e a edição de texto **custo zero**.

### 3.3 O motor de render e o `data-anchor`

`_blueprint_render.render(marca, model_id, copy, image_url, format)`. A âncora do
texto (`copy.text_anchor`) é lida do focus-map; se vazia, cai no `params.anchor`
do blueprint. O CSS (`source/ad-blueprints/_engine.css`) posiciona o bloco por
`data-arch` + `data-anchor` (ex.: `photo-full[data-anchor=top] .layer{padding-top}`).
**Nem todo archetype move o bloco por anchor** — verificar caso a caso. Assets de
marca (logo Metta, assinatura Tiago) são lidos em runtime de
`source/ad-blueprints/_brand/` (ver §7 gotcha do bundle).

### 3.4 O fluxo do WIZARD (a ordem dos passos) — e a pergunta do Nathan

Ordem atual (`STEPS_WIZARD` em `source/embed/criar.html`):

```
marca → modo → formato → COPY → CTA → ESTILO → imagem(gerar/enviar) →
avatar → DIREÇÃO VISUAL DA CENA (o prompt) → revisão → gerar → RESULTADO
```

No **resultado**, dá pra editar **posição do texto** (Fase C: Auto/Topo/Base,
re-render custo zero) e **a copy** (Fase D). **NÃO** dá pra ajustar/regenerar a
**imagem** no resultado — pra isso, regera tudo.

> **A pergunta do Nathan: "a imagem não devia vir antes da copy? não tem como
> editar depois? tá meio esquisito."** — Análise honesta na §6.

---

## 4. O concept-first (a mudança de paradigma da Fase 2)

**Antes:** o picker mostrava ~20 estilos como **thumbnails estáticos** — "todos
parecem iguais" e enganavam (o thumbnail não é o que sai; o que sai é a SUA copy
renderizada).

**Depois (`79d9c78` + `7b33c4c`):**
- **Ordem virou copy-primeiro:** você escreve a mensagem, e o passo de estilo
  mostra **a SUA copy renderizada de verdade** em cada card (via `/api/preview`,
  um endpoint que roda só o motor de layout — **sem gerar foto, sem LLM, custo
  zero**). Estilo com foto mostra o layout fiel text-only + selo "+ foto ao
  escolher"; a foto (cara) só é gerada no estilo REALMENTE escolhido.
- **Recomendador heurístico:** por sinais da copy (tem número? é pergunta? tem
  bullets? urgência? convite? tamanho?), sugere **2–3 composições** com o PORQUÊ.
  "Ver todos os estilos" é o escape hatch.
- **Editor no resultado (Fase C/D):** ajustar posição do texto e editar a copy sem
  regerar a foto (mesma imagem, re-render via `/api/preview` com passthrough de
  `image_data_uri` + `layout`).

`/api/preview` (`api/preview.py`) é a base disso: `POST {marca, model_id, copy,
format, [image_data_uri], [layout]}` → `{html, usa_imagem}`.

---

## 5. Tudo que foi feito nesta jornada (com commits)

### Motor / composição (a raiz)
- **`f95050f` (hoje) — a regra de posicionamento VENCE o blueprint sempre.**
  Causa raiz do "card na cara": o focus-map só comparava topo vs base e ignorava o
  meio; sujeito centralizado virava "ambíguo" e o anchor fixo do blueprint vencia.
  Agora considera o meio (centralizado = confiável) e o anchor medido vence sempre
  que há zona vazia. Validado nos 12 fundos.
- **`66b4dd9` — a direção do usuário vence o blueprint** (incl. "sem pessoa";
  guard que pula a referência humana). Provado ao vivo: briefing "sem pessoa, só
  caderno e caneta" → saiu caderno e caneta, sem pessoa.
- **`620a2dd` (jornada anterior) — focus-map ligado no `generate.py`** (mede a
  imagem gerada NO SITE, não só no teste local).

### Paradigma / wizard (Fase 2)
- **`79d9c78` — concept-first:** ordem copy→estilo, preview vivo da copy,
  recomendador, editor de âncora no resultado.
- **`7b33c4c` — Fase D:** editar a copy no resultado sem regerar foto.
- **`7ba882d` + `cf99060` — catálogo:** destrava **YELLOW-OBJETO** (aprovado);
  **LOGO-WALL** segue "Em breve" (reprovado); **colapsa modelos Tiago 13→5** no
  picker de peça única via flag novo `carouselOnly` (aparece no carrossel, some do
  picker). Ficam: Tweet, Tweet-imagem, Notas, Frase-grande, Capa-revista. Viram
  só-carrossel: Editorial-CARD/DARK/CTA + Dark-surreal + Photo-raw. Viram "Em
  breve": as 3 stories (zero creative provado).
- **`505f59e` (jornada anterior) — expõe DARK-OBJETO no wizard.**

### Correções de produção / deploy (a saga)
- **`fe440d8` — geração real destravada:** `/api/generate` dava 500 (OOM do import
  do litellm no limite de 1024MB) → `memory: 1769`.
- **`5da1a60`→`95826a3` — logo/assinatura no bundle.** Descobertas na marra:
  (a) `excludeFiles` VENCE `includeFiles` na Vercel; (b) esses campos têm **teto de
  256 chars** (enumerar demais quebra o build sem mensagem). Solução: os SVGs que o
  render lê (`simbolo_metta`, `assinatura-*`) moram TAMBÉM em `source/ad-blueprints/_brand/`
  (já entra no bundle) e o render tenta `_brand` primeiro.
- **`8799ca6`/`8431558`/`ba809d0` — `/api/preview` self-contained + bundle <225MB.**

### Entregáveis (artifacts, fora do repo)
- Devolutiva ao feedback do editor (antes/depois dos 8 pontos).
- Protocolo de teste pro designer.
- Galeria dos criativos produzidos + catálogo completo (20 Metta + 10 Tiago).

---

## 6. A pergunta do Nathan: imagem antes da copy? editar depois? (análise honesta)

**O desconforto é legítimo.** No concept-first você escolhe o estilo vendo só o
TEXTO (selo "+ foto ao escolher"); a **imagem — a maior variável de qualidade —
aparece por último** e pode decepcionar. Você se compromete antes de ver a foto.

**Por que copy-primeiro foi a escolha:** princípio #2 (a imagem ILUSTRA a copy) —
a mensagem é o produto, a imagem serve a mensagem. Então a copy lidera.

**As opções (pra revisora pesar):**
- **(A) Manter copy-primeiro, mas gerar a foto MAIS CEDO** — logo após escolher o
  estilo, mostrar a foto real antes de "confirmar". Custo: gera imagem antes de ter
  certeza (mais chamadas).
- **(B) Resultado como EDITOR COMPLETO** — hoje o resultado já edita posição (Fase
  C) e copy (Fase D) sem regerar. **Falta editar/regenerar a IMAGEM no resultado.**
  Se adicionar isso, a ordem importa pouco: você flui copy→estilo→gera e depois
  ajusta TUDO (copy, imagem, posição) ao vivo. **É a resposta direta ao "não tem
  como editar depois?".**
- **(C) Modo "começar pela imagem"** — pra quem já tem um visual na cabeça: gera/
  sobe a imagem primeiro, depois a copy por cima. Segundo modo de entrada, não
  substituto. Adiciona complexidade.

**Minha recomendação:** **(B) é o maior valor.** Manter copy-primeiro (é
principiado) e transformar o resultado num editor completo (somar "regenerar/
ajustar imagem" aos editores de copy e posição que já existem). Isso dissolve a
ansiedade da ordem — porque tudo vira editável no fim. **(A)** é um bom
complemento. **(C)** é opcional. *(Ponto explícito pra revisora criticar.)*

---

## 7. Os problemas em aberto (ranqueados, honestos)

### 🔴 1. "Todas parecem iguais" = fonte da imagem (o problema-mãe)
As fotos vêm do **gpt-image genérico** porque a rota Gemini precisa de uma
**referência do banco curado**, e o banco está **vazio** (item **1.2** do plano).
As boas referências do Gemini que o Nathan diz que "é pra ficar lá" **existem mas
não estão ligadas no banco**. **Fix:** montar o banco (separar as boas peças
Gemini por família) → o pipeline REUSA em vez de gerar genérico. É o maior salto.

### 🔴 2. Dependência + cota da OpenAI
O cérebro inteiro roda em OpenAI, e um lote pesado **estourou a cota** — o que
derruba a geração no site (art-director + gpt-image caem). **Fixes:** (a) recarregar
billing; (b) `LLM_PROVIDER=gemini` (cérebro no Gemini — precisa testar qualidade);
(c) chave OpenAI separada pro dev. Confirmado ao vivo: prod mostra `art-director:
PULADO (RateLimitError ... quota)`.

### 🟡 3. `GEMINI_API_KEY` não está no runtime da Vercel
Mesmo com banco de referência, sem a chave no ambiente a rota Gemini cai no
gpt-image em prod. Adicionar em Settings→Environment Variables (Production) + redeploy.

### 🟡 4. Composição: o focus-map é heurístico cru
3 faixas de energia de borda — **não "enxerga" o sujeito** (sem detecção de rosto/
saliência). O `f95050f` melhorou (considera o meio), mas o "ver de verdade" =
saliência/face-detection é o próximo nível. O Nathan lembrou disso ("a IA ver e
entender o local").

### 🟡 5. Qualidade de imagem (distinta de posição)
- **Cabeça cortada** (ex.: B-foto-top): a foto não deixou headroom → é image-gen,
  não posição. Fix: prompt garantir "ample headroom" + QA rejeitar.
- **Preto no amarelo / contraste** (ex.: YELLOW-SPLIT): tratamento/legibilidade.

### 🟢 6. Editor de imagem no resultado (ver §6-B)
Somar "regenerar/ajustar imagem" aos editores de copy+posição já existentes.

---

## 8. Perguntas explícitas pra IA revisora

1. **Ordem copy vs imagem:** a recomendação (B — editor completo no resultado,
   mantendo copy-primeiro) faz sentido? Ou o modo "imagem-primeiro" (C) é melhor?
2. **Focus-map:** vale trocar o heurístico de energia de borda por **saliência/
   detecção de rosto** de verdade (ex.: um modelo leve)? Ou o heurístico melhorado
   basta pro nível de qualidade alvo?
3. **Banco de referência (1.2):** qual a melhor arquitetura pra indexar as boas
   peças Gemini por conceito/família e escolher a referência certa por copy (não só
   por família)?
4. **LLM_PROVIDER=gemini:** trocar o cérebro pro Gemini vale o risco de mudança de
   comportamento do art-director? Como testar isso com rigor?
5. **A regra vence o blueprint (`f95050f`):** forçar o anchor medido sempre pode
   regredir algum caso onde o blueprint tinha razão? (Validado nos 12, mas a
   revisora pode achar contra-exemplos.)
6. **Slop (card branco flutuante, número inventado):** o vision-QA/crítico barra o
   suficiente? O "300 mil vendedores impactados" inventado num teste sugere que não.

---

## 9. Próximos passos recomendados (ordem)

1. **Recarregar o billing da OpenAI** (destrava o site) — ação do Nathan.
2. **Montar o banco de referência (1.2)** com as boas peças Gemini por família —
   mata o "todas iguais". Maior salto de qualidade. **Não depende da OpenAI.**
3. **Adicionar `GEMINI_API_KEY` na Vercel** — a foto passa a usar Gemini em prod.
4. **Resultado = editor completo** (somar regen/ajuste de imagem) — resolve o
   "editar depois".
5. **Testar `LLM_PROVIDER=gemini`** ponta a ponta — reduz dependência da OpenAI.
6. **Saliência real** no lugar do heurístico de faixas — "a IA ver o local".

---

## 10. Como continuar (pra próxima IA)

- Repo `~/Documents/Claude/brand-system`. `set -a; source .env.local; set +a`
  carrega OPENAI + GEMINI. `.venv/bin/python`.
- **Regra de ouro de deploy:** teste local → `cp source/embed/criar.html
  embed/criar.html` → `git push origin main` (deploy automático Vercel) só quando
  funcionar de ponta a ponta. Status do deploy via `gh api repos/metta-brasil-tech/
  brand-system/deployments`.
- **Gotchas de deploy** (memória `brand-system-deploy-gotchas`): teto de 256 chars
  em include/excludeFiles; excludeFiles vence includeFiles; OOM do generate
  (memory 1769); assets de runtime via `_brand`; OpenAI compartilhada dev↔prod.
- **Fonte única do plano:** `PLANO-MESTRE-agente-imagem.md` (atualizar status lá).
- Rodar peça local: `.venv/bin/python cli.py --model <ID> --headline "..."
  [--image generate|none] --preset <p> --out /tmp/x` e **OLHAR** o PNG (este
  projeto exige prova visual, não confiar em "rodou").

---

*Fim. Este documento é um retrato de 2026-07-21 no commit `f95050f`. Se algo aqui
divergir do código, o código vence — confira antes de agir.*
