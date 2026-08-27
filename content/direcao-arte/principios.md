---
title: "Direção Fotográfica — Metta"
aliases:
  - "Direção de Arte Fotografia"
  - "Photography Direction Metta"
tags:
  - marca/metta
  - status/vigente
  - tema/design
  - tema/marca
  - tema/fotografia
  - tipo/direção-arte
  - tipo/referencia
  - usado-por/skill-marca-metta
  - usado-por/skill-design-metta
  - usado-por/skill-nano-banana
formato_consumo: contexto-skill
prioridade_carregamento: alta
versão: "1.0"
sucedido_por: null
complementar_com: "[[Metta - PRD Identidade Visual]] · [[manual-de-marca]] · [[brand-system-spec]]"
summary: "Direção fotográfica oficial da Metta. Define o DNA visual (luz, paleta, composição, mood, câmera, pós), 21 arquétipos editoriais com prompt templates pra geração via gpt-image-1, e regras claras de do/don't. Cada arquétipo tem prompt em inglês profissional pronto pra alimentar Codex CLI."
created: 2026-05-08
updated: 2026-05-08
---

# Direção Fotográfica — Metta

> A fotografia da Metta não é "stock corporativo bonito". É **editorial documental** — cabeça analítica, luz natural deliberada, paleta neutra com amarelo cirúrgico. Esta direção governa toda imagem Metta: ads, LPs, carrosséis, slides, e — principalmente — toda imagem GERADA via IA pela skill `/marca-metta`.

## TL;DR ^tldr

- **DNA em 7 elementos:** subject · composition · light · mood · palette · camera · post
- **21 arquétipos editoriais** com prompt template em inglês pra cada (alimenta gpt-image-1 via Codex CLI)
- **Não é stock photo:** documental, deliberado, sem sorrisos forçados, sem clichê de high-five
- **Amarelo é cirúrgico:** 1 ponto focal por cena, nunca decorativo, nunca disperso
- **Galeria ativa:** 156 fotos curadas com archetype + prompt em `output/brand-system/data/photo-index.json`

## Quando consultar ^quando-consultar

- Antes de gerar QUALQUER imagem nova com IA pra Metta
- Quando alguém pedir "uma foto pra esse carrossel" — primeiro identifica arquétipo, depois usa o prompt
- Em briefing pra fotógrafo externo: este doc é o "manual da marca em fotografia"
- Pra calibrar peças que parecem "fora da marca" — quase sempre é um dos 7 elementos do DNA quebrado
- Antes de aprovar nova foto pro banco — comparar contra o DNA e os arquétipos

---

## §1. DNA Visual — os 7 elementos ^dna

Toda imagem Metta passa por 7 dimensões. Não é checklist sequencial — é como mecânico abrindo o carro: você verifica todas, em qualquer ordem.

### §1.1 Subject — o que está na cena ^subject

Tipos válidos:
- **Empresário sozinho** em momento analítico (decidindo, lendo dado, em pausa de pensamento)
- **Dupla** em mentoria 1-on-1 (mentor + mentorado)
- **Time pequeno** (3-6 pessoas) em reunião de mesa, colaboração ou apresentação
- **Mãos / detalhes** (handshake fechando acordo, caneta sobre dado, dedo em gráfico)
- **Ambiente vazio** (sala de reunião pronta, escritório curado)
- **Objeto simbólico** (relógio, chave, copo) com função metafórica
- **Textura** (gradiente, luz volumétrica, dourado em preto) como pano de fundo

Tipos PROIBIDOS:
- Pessoa olhando direto pra câmera com sorriso largo
- Mulher executiva com braços cruzados defensivamente em pose
- Time fazendo high-five exagerado com papéis voando
- Mão segurando lâmpada acesa "tendo ideia"
- Empresário pulando de alegria
- Aperto de mão visto de frente com dois rostos sorrindo

### §1.2 Composition — como enquadra ^composition

- **Regra dos terços** — sujeito raramente no centro
- **Negative space deliberado** — vazio que respira, contexto que sustenta
- **Eye-line lock** — quando há pessoa, olhar conduz o frame (mas não pra câmera)
- **Off-axis** — boardroom shots ligeiramente diagonais, nunca perfeitamente frontais
- **Profundidade construída** — primeiro plano + médio + fundo, com pelo menos 2 planos em foco diferenciado

### §1.3 Light — qualidade da luz ^light

- **Natural lateral** é o padrão (janela alta, manhã ou tarde dourada)
- **Soft falloff** — sombras que decaem suave, nunca duras de meio-dia
- **Volumétrica controlada** — raios visíveis quando justifica narrativa, nunca "god rays" turísticos
- **Quente em ambiente, neutra em estúdio** — nunca azul-frio dramático
- **Screen glow** quando alguém olha tela — luz clara no rosto, mantém naturalidade

Proibido: flash direto, fluorescente puro, HDR, "cinematic teal-and-orange" exagerado.

### §1.4 Mood — sentimento dominante ^mood

A escala Metta: composto · analítico · decisão. Nunca:
- Eufórico (estilo "vendemos motivacional")
- Ansioso (estilo "olha o caos do gestor")
- Teatral (estilo "pose pra revista de aeroporto")
- Inocente (estilo "estou aprendendo, sou júnior")

A foto deve transmitir **peso da escolha sustentada com calma**. Se o sujeito está sorrindo, é meio-sorriso de quem sabe — não sorriso de stock.

### §1.5 Palette — cores ^palette

Anchored em neutros:
- Carvão (charcoal) — `#2E3E47` a `#0C161B`
- Carvalho (oak wood) — tons quentes médios
- Creme/off-white — paredes, papel, camisas
- Slate grey — tecidos, fundos arquitetônicos

**Amarelo Metta `#FFBE18`** entra como **um único acento focal por cena**:
- Capa de caderno
- Detalhe de gravata ou pin
- Highlight em gráfico
- Reflexo em copo/lâmpada

NUNCA: paleta arco-íris, múltiplos acentos competindo, amarelo decorativo (parede inteira, fundo).

### §1.6 Camera — feel da lente ^camera

- **35mm equivalente** pra cenas amplas (boardroom, time, ambiente)
- **50mm equivalente** pra cenas médias (apresentação, mentoria)
- **85mm equivalente** pra retratos individuais
- **f/2.8 a f/4** — profundidade média a rasa, isola sujeito mas mantém contexto legível
- **NUNCA** wide-angle distorcido (24mm ou menos), nunca fisheye
- **NUNCA** macro extremo

### §1.7 Post — pós-produção ^post

- **Mid contrast** — preserva tons médios, não esmaga shadow nem queima highlight
- **Subtle film grain** — leve granulação que sugere captura real, nunca digital limpo demais
- **White balance neutro com warm shadow** — base neutra, sombra ligeiramente quente
- **NÃO**: HDR, color grading agressivo, saturação inflada, vinheta heavy, oversharp

---

## §2. Arquétipos editoriais ^arquétipos

Os arquétipos são **lentes de leitura**: dado um briefing, você identifica qual arquétipo serve, pega o prompt template, ajusta o briefing específico, alimenta o gpt-image-1. Isso garante que toda imagem nova respeite o DNA Metta.

> **Onde está o catálogo vivo:** `output/brand-system/data/photo-index.json` — 156 fotos curadas, cada uma classificada num dos 21 arquétipos abaixo, com prompt completo. A galeria do mini-app permite copiar o prompt direto pra Codex CLI.

### §2.1 Liderança ^arquétipos-liderança

| ID | Nome | Quando usar |
|---|---|---|
| `executivo-em-decisao` | Executivo em decisão | Sujeito sozinho em momento analítico |
| `mentoria-1-on-1` | Mentoria 1-on-1 | Conselho, transferência de método entre dois |
| `reuniao-mesa-decisao` | Reunião de mesa — decisão | Time em mesa com líder no comando |
| `líder-apresentando-time` | Líder apresentando ao time | Em pé, explicando, time sentado |
| `palco-evento` | Palco / evento | Conferência, autoridade pública |
| `feminina-líder-apresentando` | Liderança feminina apresentando | Executiva conduzindo apresentação |
| `businessman-thinking-laptop` | Empresário pensando — laptop | Pausa de pensamento em ambiente quente |

### §2.2 Pessoas ^arquétipos-pessoas

| ID | Nome | Quando usar |
|---|---|---|
| `retrato-individual-confiante` | Retrato individual — confiante | Foto de perfil/about/case nominal |
| `aperto-de-maos-fechamento` | Aperto de mãos — fechamento | Selo de acordo, contrato |
| `time-colaborando-laptops` | Time colaborando com laptops | Execução cotidiana, sintonia operacional |
| `time-celebrando-resultado` | Time celebrando resultado | Comemoração controlada de meta batida |

### §2.3 Resultados ^arquétipos-resultados

| ID | Nome | Quando usar |
|---|---|---|
| `analise-dados-tela` | Análise de dados na tela | Sujeito olhando dashboard, pensando |
| `apresentacao-graficos` | Apresentação de gráficos | Time lendo resultado coletivamente |

### §2.4 Escritório / Ambiente ^arquétipos-ambiente

| ID | Nome | Quando usar |
|---|---|---|
| `sala-reuniao-vazia` | Sala de reunião vazia | Promessa, expectativa, palco da decisão |
| `escritorio-moderno-interior` | Escritório moderno — interior | Ambiente de trabalho organizado |
| `home-office` | Home office | Disciplina profissional em casa |

### §2.5 Branding / Mockups ^arquétipos-branding

| ID | Nome | Quando usar |
|---|---|---|
| `mockup-papelaria-madeira` | Mockup papelaria — madeira | Cartões/papelaria em mesa de carvalho |
| `mockup-papelaria-escura` | Mockup papelaria — escura | Versão premium, fundo escuro |
| `objeto-conceitual-escuro` | Objeto conceitual escuro | Símbolo isolado (relógio, chave) |

### §2.6 Texturas / Backgrounds ^arquétipos-texturas

| ID | Nome | Quando usar |
|---|---|---|
| `textura-gold-on-black` | Textura — dourado em preto | Fundo premium para headlines |
| `textura-luz-raio` | Textura — raios de luz | Atmosfera, profundidade, drama controlado |
| `textura-gradiente-grain` | Textura — gradiente granulado | Fundo neutro com profundidade |

---

## §3. Estrutura do prompt — receita de 7 partes ^estrutura-prompt

Todo prompt no `photo-index.json` segue a mesma estrutura. Quando for adaptar pra um briefing específico, mantenha as 7 seções:

```
1. SUBJECT      — o que está na cena (sujeito + ação)
2. COMPOSITION  — enquadramento, regra dos terços, planos
3. LIGHT        — tipo, direção, qualidade, temperatura
4. MOOD         — sentimento dominante (composto, analítico, decisão)
5. PALETTE      — cores dominantes + acento amarelo Metta
6. CAMERA       — focal length, f-stop, foco
7. POST         — contraste, grain, white balance, NO HDR
```

**Exemplo (arquétipo `executivo-em-decisao`):**

> Editorial portrait of a brazilian executive (40-55) in a moment of analytical decision, alone at a desk or modern office. Composed expression — no smile, no theatrics; the face shows the weight of choice. Side window light from the left, warm afternoon tone falling across the shoulder and document. Subject occupies right third, with significant negative space holding context. 50mm equivalent, f/2.8, focus on the eyes. Palette: charcoal suit, oak desk surface, cream wall, single yellow accent (mug, notebook, or backlit paper). Mid contrast, subtle film grain, no HDR. Documentary feel, no posed corporate-stock energy.

### §3.1 Como adaptar pra briefing específico ^adaptação

Mantém a base do template, adiciona instrução específica no início:

```
[BRIEF: este executivo é fundador de marmoraria, 50+, momento de virada de gestão]
+
[TEMPLATE executivo-em-decisao]
+
[AJUSTE: ambiente é showroom de mármore com peças brancas e veias cinza, ao invés de office padrão]
```

A skill `/marca-metta` (CP6) faz essa fusão automaticamente.

---

## §4. Do / Don't ^do-dont

### Do ^do

- Buscar **luz natural** sempre que possível
- Compor com **negative space** que sustenta narrativa
- Usar **um amarelo focal** como acento cirúrgico
- Capturar **sujeito mid-thought**, mid-action — nunca pose congelada
- Documentar como se a câmera não estivesse lá
- Misturar etnias e gêneros com naturalidade — Brasil corporativo é diverso
- Manter **mid contrast** + **subtle grain** no pós

### Don't ^dont

- ❌ **Sorrisos largos olhando pra câmera** — vira stock-photo na hora
- ❌ **High-five com papéis voando** — euforia falsa
- ❌ **Pose "ideia!" com dedo na têmpora ou lâmpada na mão**
- ❌ **Wide-angle distorcido** ou fisheye em cena de pessoa
- ❌ **Múltiplas cores acessórias competindo com amarelo**
- ❌ **HDR, color grading "cinemático" exagerado, saturação inflada**
- ❌ **Sala de reunião perfeitamente alinhada e vazia de personalidade** — boardroom Metta tem alma
- ❌ **Foto de homem branco de gravata sozinho como default genérico** — diversidade é regra, não exceção

---

## §5. Pipeline de geração via IA ^pipeline-ia

A skill `/marca-metta` (CP6) opera assim:

```
USUÁRIO: "preciso de uma foto pra um carrossel sobre liderança feminina decidindo
          virada de método em uma indústria de bens de consumo"

SKILL:
  1. Identifica arquétipo: feminina-líder-apresentando
  2. Carrega prompt template do photo-index.json
  3. Adiciona briefing: "industrial setting", "consumer goods context"
  4. Adiciona ajuste de cena: "executiva 45+, ambiente fabril ao fundo desfocado"
  5. Roda: codex exec --dangerously-bypass-approvals-and-sandbox
     "gpt-image-1 generate: {prompt fundido}"
  6. Salva em output/{slug}/ + retorna preview
```

A integração técnica vai no `output/brand-system/scripts/generate-image.mjs` (CP6).

---

## §6. Manutenção ^manutenção

- **Quando adicionar foto nova ao banco:** rodar `node scripts/photo-curator.mjs` que reprocessa tudo. Adicionar entrada no `KEYWORD_MAP` se filename for novo padrão.
- **Quando criar arquétipo novo:** adicionar em `ARCHETYPES` no `photo-curator.mjs`, escrever template, atualizar este doc na seção §2.
- **Quando ajustar tom geral:** mudar a constante `METTA_DNA` no `photo-curator.mjs` e regenerar — afeta todos os prompts.

---

## §7. Referências ^referências

- [[brand-system-spec]] — onde este doc se encaixa no Brand System
- [[Metta - PRD Identidade Visual]] — base do DS técnico
- [[manual-de-marca]] — síntese editorial
- [[Metta - Plataforma de Marca]] — onde o tom de voz se conecta com tom visual
