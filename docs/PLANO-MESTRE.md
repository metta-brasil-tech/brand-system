# PLANO-MESTRE — Geração vision-first, conhecimento e auto-melhoria

> **Divisão de trabalho (2 Claudes):** um Claude segue a Fase 4 → 5 → 6 (flywheel +
> avaliador no pipeline, mexe em `generate.py`/`_evaluator.py`/`_bank.py`). O outro foca
> em **qualidade de criativo (Fase 7 — geração reference-aware)**, em módulos novos
> (`_ref_vision.py`) injetados via `briefing_image_text`, sem tocar nos arquivos do
> primeiro. Régua comum: o golden set + o ledger (baseline: SHIP 33%, nota 8.19).

Plano grande e vivo. Cobre tudo o que pensamos, o que falta trazer do plugin
`plugin-metta-ads`, e — principalmente — **como testar cada coisa**. Ordenado por
dependência. Use como mapa; cada fase tem objetivo, tarefas, teste e critério de pronto.

---

## 0. Onde estamos (estado real, 2026-06)

**Princípio que nasceu de tudo isto:** a geração nascia **cega** ao que a marca sabe
(ICP, voz, método, depoimentos, banco). Estamos transformando o brand-system de
arquivo morto em **cérebro da geração**, e fechando o ciclo gerar→avaliar→melhorar.

**Atualizado em 2026-06-21 (pós-merge na main + smoke test local verde).** Tudo abaixo
está **na `main`** (`86e6387`, submódulo `e1278336a`), verificado: 34/34 regressão,
12/12 imports, e **1 geração ponta a ponta real** com todas as camadas disparando.

| Camada | Arquivo | Ligado no pipeline? | Estado |
|---|---|---|---|
| Crítico (same-designer test) | `api/_critic.py` | ✅ sim (`CRITIC_COMPARE=1`) | **na main** |
| Guardrails copy-literal + no_invented_text | `api/_qa.py` | ✅ sim | **na main** |
| Modos de falha gpt-image | `api/_art_director.py` + skill 04 | ✅ sim | **na main** |
| Fix Chrome macOS | `api/_render_png.py` | ✅ sim | **na main** |
| Camada de recuperação | `api/_knowledge.py` | ✅ sim (Fase 1/2) | **na main** |
| ICP inferido no pensador | `_avatar_infer` + `_art_director.direct()` | ✅ sim (verificado: farmácia→varejo-farmacia) | **na main** |
| Decision log | `generate.py` → `03-decision-log.json` | ✅ sim (Fase 3) | **na main** |
| Avaliador critica o raciocínio | `api/_evaluator.py` (lê decision_log) | ✅ **sim** (`FINAL_EVAL=1`, opt-in — Fase 6) | **na main** |
| Loop de auto-melhoria | `api/_autogen.py` | ✅ **sim** (`cli --auto-improve` — Fase 6) | **na main** |
| Flywheel / entrada no banco | `api/_bank.py` (gate de aprovação) | ⚙️ runner manual (`render_out/_flywheel_ingest.py`, dry-run) — **por design** (só entra com aprovação humana, não automático) | **na main** |
| Modo B (ideia→copy) | `api/_copywriter.py` | ✅ no CLI (`cli.py --theme`, com `--pick`/`--propose-only`) | **na main** |
| Ledger de auditoria | `api/_ledger.py` | ⚙️ runner (`_audit_ledger`/`_golden_run`) | **na main** |

**Estado de processo:** tudo committado e **na `main`** (produção atualizada, deploy
disparado). Baseline no ledger: golden set **SHIP 33% · nota 8.19**. Local usa
**OpenAI**; produção usa **Claude + `render.js`** (paridade = Fase 8, ainda a validar).
**Nuance do flywheel:** ingestão no banco é **manual-com-aprovação** (gated), não
automática — se quiser automático-pós-SHIP, é uma adição pequena.

---

## 1. Princípios que guiam o plano

1. **Contexto → decisão → registro → crítica → composição.** Não pule a ordem.
2. **Regra que briga com o banco é regra falsa** (lição do plugin): julgamento visual
   contra a referência > regra rígida de px/cor.
3. **Copy é sagrada** (literal byte-a-byte). **Marca/texto/número nunca na imagem
   gerada** — entram via HTML por cima.
4. **Toda decisão tem um porquê rastreável** (decision log) — sem registrar, não há
   o que melhorar.
5. **Auto-melhoria com freio:** regenerar só quando o problema é de imagem
   (`image_fixable`); parar e sinalizar quando é de template.
6. **Toda mudança no loop é auditada (regra de ouro).** Nenhuma alteração que afeta a
   geração entra sem uma linha no **ledger** (`docs/IMPROVEMENT-LEDGER.md`) medindo o
   antes→depois no golden set. Flywheel sem "depois disso melhorou X" é proibido — é
   assim que se garante que o loop SOBE a qualidade em vez de degradar às cegas.

---

## 2. Roadmap por fases

### Fase 1 — Camada de recuperação ✅
Puxa ICP+voz+método+depoimento por copy (`_knowledge.py`).
- **Teste:** `retrieve()` em ≥6 copies (Metta+Tiago) → proveniência relevante e sem
  lixo (índices/links). **Pronto:** copies diferentes puxam fatias diferentes e certas.

### Fase 2 — ICP no pensador ✅
Segmento inferido pela copy + `retrieve()` + avatar injetados **dentro do diretor de
arte** (e na skill 04).
- **Teste (A/B):** mesma copy COM vs SEM avatar → a persona/cena muda e fica ancorada?
  **Pronto:** persona deixa de vir de "use mulheres" e passa a vir do ICP.

### Fase 3 — Decision log ✅
`generate.py` salva `artifacts/<run_id>/03-decision-log.json`: rationale + image_concept
+ proveniência do conhecimento + avatar.
- **Teste:** gerar 1 peça → o JSON existe e contém o "porquê". **Pronto:** rationale
  deixa de ser jogado fora.

### Fase 4 — Avaliador critica o raciocínio ✅ (working tree, falta commit)
`_evaluator.py` lê o decision log e julga fidelidade INTENÇÃO→PEÇA (persona bate com
ICP? cena ilustra a copy/método/depoimento?), não só o pixel.
- **Teste:** peça com persona fora do ICP deve cair na nota mesmo se "bonita".
  **Pronto:** o feedback aponta a decisão errada, não o pixel.

### Fase 5 — Flywheel / entrada no banco (F8) ◀ PRÓXIMO
Peça **aprovada (SHIP) pelo usuário** entra automaticamente no banco
(`applications-index.json` + thumb) → crítico mais afiado + geração reference-aware →
melhora composta.
- **Tarefas:** função `ingest_to_bank(piece)`; gate "só com aprovação humana"; gravar
  ficha (mood/intent/archetype_foto/tokens) **olhando o PNG**; append no índice.
- **Teste:** aprovar 1 peça → aparece no banco → o crítico passa a poder escolhê-la
  como referência. **Pronto:** o banco cresce sozinho com peças campeãs.
- **OBRIGATÓRIO junto:** toda entrada no banco / aprendizado dispara uma **auditoria no
  ledger** (Fase 5.5). Flywheel sem auditoria é proibido — pode degradar às cegas.

### Fase 5.5 — Ledger de auditoria (✅ construído, AGORA OBRIGATÓRIO no loop)
O loop roda automático (gera posts, reavalia, aprende, entra no banco). Sem auditoria,
ele pode **piorar e ninguém percebe**. O ledger (`api/_ledger.py` +
`docs/IMPROVEMENT-LEDGER.md`) registra, a cada alteração, o **antes→depois** medido no
mesmo conjunto: "depois dessa alteração, nota 8.0→8.4 (+0.4), SHIP 30%→45% 🟢" — ou
🔴 PIOROU = candidato a reverter.
- **Como funciona:** `compute_metrics(manifest)` (SHIP%, nota média, REVISAR%, regen%) →
  `record(label, metrics, change_desc)` compara com o snapshot anterior, grava em
  `data/improvement-ledger.json` e renderiza o MD. Runner: `render_out/_audit_ledger.py`.
- **Regra de ouro:** **NENHUMA** mudança no loop (novo exemplar no banco, regra
  distilada, ajuste de prompt, ligar uma fase) entra sem uma linha no ledger medida
  contra o **golden set fixo** (5.2). Se a métrica-chave caiu → reverter ou justificar.
- **Baseline já gravado:** batch parcial, SHIP 30% · nota 8.02 (pré-flywheel).
- **Teste:** fazer uma mudança → rodar o batch → `_audit_ledger.py "rótulo"` → a linha
  aparece com Δ e veredito. **Pronto:** dá pra responder "essa mudança melhorou?" com número.

### Fase 6 — Auto-melhoria no PIPELINE (não só no batch/CLI) ◀
Hoje `_evaluator`/`_autogen` são standalone. Para o **site** se auto-melhorar, o
`generate.py` precisa, opcionalmente, rodar o loop `generate_until_approved`.
- **Tarefas:** flag `AUTO_IMPROVE` no pipeline; teto `max_attempts`; devolver a melhor
  tentativa + a nota no response da API.
- **Teste:** request no endpoint com `auto_improve=true` → a nota sobe entre tentativas
  e devolve a melhor. **Pronto:** o site entrega peça auto-melhorada, com freio de custo.

### Fase 7 — Geração reference-aware ⚠️ (1ª tentativa REGREDIU — refazer como contexto)
O diretor de arte pensa a partir de **texto**. Tentei injetar o craft da referência via
`briefing_image_text` (prioridade máxima) em `_ref_vision.py` → **A/B deu -0.53** (piorou
2 de 3: atropela o conceito bom do diretor de arte). **Aprendizado:** a referência tem
que entrar como **CONTEXTO pro diretor de arte** (ele lidera, informado pela imagem da
ref), **não como override**.
- **Tarefas (refazer):** adapter multimodal no `_art_director.direct()` que RECEBE o PNG
  da referência (`pick_reference`) como contexto + o craft, sem substituir o conceito.
- **Teste:** A/B contexto-imagem vs baseline no golden set → nota sobe (não cai). **Pronto:**
  same-designer test passa mais, sem regressão.

### Fase 8 — Paridade local↔prod + custo ◀
- **Tarefas:** alinhar provider (rodar local no Claude para testes que reflitam prod);
  validar `render.js` vs `_render_png.py`; medir custo por peça com todas as camadas.
- **Teste:** mesmo brief local (Claude) vs prod → diferença visual aceitável.

---

## 2-B. CARROSSEL — fases dedicadas (PRIORIDADE, não deixar de lado)
> A lógica de carrossel/panorâmica vive na **UI** (`embed/criar.html`, modo multi-slide
> `slides[]`), não no core Python. Por isso a **Fase 9 começa com estudo** dessa camada —
> nada de construir às cegas. O Nathan **amou** a panorâmica ("2 cenas que se completam")
> e quer **fazer mais**.

### Fase 9 — Carrossel: direção de série (a F1-C do plugin)
O carrossel deixa de ser N slides soltos e ganha direção: tratamentos por slide
(vocabulário fechado tipo `T-*`), **paleta travada** no slide 1, **2-3 motivos**
recorrentes, **anti-monotonia de família** entre carrosséis.
- **Tarefas:** mapear o data model de slides na UI; `api/_serie.py` (classifica slide →
  escolhe tratamento → trava paleta → define motivos); injetar essa direção em cada slide.
- **Teste:** gerar um carrossel → cada slide com tratamento coerente, paleta travada,
  motivo recorrente. **Pronto:** parece UMA série, não N peças avulsas.

### Fase 10 — Carrossel: guardrails de coerência C1–C8
Porta as regras do `serie-rules.md` + gate `--serie` do plugin: C1 capa não-tipográfica
(stop-scroll) · C2 último = CTA · C3 anti-repetição consecutiva · C4 paleta travada ·
C6 máx 2 tipográficos · C8 um formato/série; C5 motivos + C7 marca = julgamento do crítico.
- **Tarefas:** `_serie.validate_serie(slides)` (mecânico) + camada D do crítico (série).
- **Teste:** carrossel que viola C1/C2 reprova; coeso passa. **Pronto:** gate + crítico de série.

### Fase 11 — Carrossel: panorâmica++ (estender as "2 cenas que se completam")
Generaliza a continuidade panorâmica (imagem larga fatiada com fundo contínuo) — robusta
e além de 2 slides (3+), com emendas perfeitas. É o "fazer mais" que o Nathan pediu.
- **Tarefas:** achar a lógica de fatiar (UI/JS); generalizar pra N fatias; garantir
  continuidade visual; crítico checa a emenda.
- **Teste:** panorâmico de 3 slides com fundo contínuo sem emenda visível. **Pronto:**
  dá pra produzir mais disso com qualidade.

## 2-C. Resto do plugin — fases (formaliza a seção 3)

### Fase 12 — Briefer A↔B (refina o prompt de imagem ANTES de gerar)
Bate-bola propositor↔crítico do plugin: um propõe o prompt de imagem, outro valida contra
os limites do gpt-image + composição, itera (N rodadas) antes de gastar geração.
- **Tarefas:** `api/_briefer.py` (propositor + crítico); roda antes do image-gen com foto.
- **Teste:** A/B prompt-direto vs refinado → menos falhas (mãos/texto) + nota de imagem
  maior no ledger. **Pronto:** o refinamento sobe a qualidade medida.

### Fase 13 — Safe-zones (margens do IG) como guardrail
Porta `metta-safe-zones.md`: story tem topo (~220px) e base (~280px) comidos pela UI do
IG; nada crítico (headline/CTA/marca) pode cair ali.
- **Tarefas:** check no `_qa`/crítico das zonas mortas (story/feed).
- **Teste:** story com CTA na base é flagado. **Pronto:** guardrail de safe-zone ativo.

### Fase 14 — 2 variantes de famílias divergentes por chamada
Hard rule do plugin: 1 brief → 2 variantes de famílias divergentes (ex: DARK + LIGHT/YELLOW).
- **Tarefas:** gerar 2 variantes de famílias forçadamente diferentes; crítico aprova ambas.
- **Teste:** 1 brief → 2 peças claramente distintas. **Pronto:** o usuário escolhe entre opções reais.

### Fase 15 — Acabamentos do plugin
Os menores: **self-inspection por crops** (recortar CTA/rosto/safe-zone e inspecionar
antes de aprovar) · **whitelist interativa** (perguntar quando aparece texto-chrome novo)
· **avisos de catálogo** no banco (mismatch nome↔render / só-webp).
- **Teste:** cada um isolado. **Pronto:** robustez incremental.

---

## 3. Melhorias do plugin que AINDA dá pra trazer

Revisão do `plugin-metta-ads` contra o que já temos:

| Recurso do plugin | Temos? | Vale trazer? |
|---|---|---|
| Same-designer test (crítico) | ✅ | feito |
| Anti-slop | ✅ | feito |
| no_invented_text + copy literal | ✅ | feito |
| Modos de falha gpt-image | ✅ | feito |
| feedback→regeneração | ✅ | feito (autogen) |
| Banco como referência (F1) | ✅ | feito (pick_reference) |
| **Modo B — ideia→copy proposta** | ❌ | **SIM, grande** |
| **Guardrails de carrossel (C1–C8)** | ❌ | **SIM** (fazemos carrossel) |
| **2 variantes de famílias divergentes** | ❌ | SIM |
| **Self-inspection do designer (crops)** | parcial | reforçar |
| **Whitelist montada COM o usuário** | parcial | médio |
| **Entrada no banco (F8)** | ❌ | SIM (= Fase 5) |

### 3.1 Modo B — ideia → copy proposta (ancorada no ICP) — ✅ CONSTRUÍDO
`api/_copywriter.py` — `propose_copy(theme, marca)`: usuário dá um tema → o sistema
**propõe 1 ângulo + 3 headlines + sub + CTA**, **fundamentado no ICP+voz+método+
depoimento** (via `_knowledge`) → declara a proveniência. Usuário escolhe/ajusta → vira
copy LITERAL → segue no pipeline (Modo A).
- **Validado:** tema "dono preso no operacional" → headlines no eixo identitário do ICP
  ("Você é dono do negócio ou apenas o principal funcionário dele?"), ancorado em
  ICP+Voz+Metodologia+Depoimento.
- **Integração (✅ feito):** exposto no CLI — `cli.py --theme "<tema>"` propõe a copy
  ancorada no ICP, mostra ângulo + headlines + subhead/CTA + proveniência, e o "aprovar
  → gerar" é fechado via escolha interativa (TTY) ou `--pick N` / `--propose-only`
  (não-interativo). A headline escolhida vira copy LITERAL e segue no pipeline (Modo A).

### 3.2 Guardrails de carrossel (C1–C8 + tratamentos T-* + anti-monotonia de paleta)
O brand-system faz carrossel (builder multi-slide). O plugin tem: capa não-tipográfica
(C1), último = CTA (C2), anti-repetição consecutiva (C3), paleta travada (C4), máx 2
tipográficos (C6), 1 formato/série (C8) + 2–3 motivos recorrentes.
- **Teste:** gerar carrossel e rodar o gate de série → C1–C8 verificados; capa para o
  scroll; série parece UMA série. **Pronto:** coerência serial mecânica + crítico julga
  motivos/marca.

### 3.3 Duas variantes de famílias divergentes por chamada
Hard rule do plugin: o estático sai em 2 variantes de famílias visuais divergentes (ex:
uma DARK, uma LIGHT/YELLOW) — duas escolhas reais, não duas quase-iguais.
- **Teste:** 1 brief → 2 variantes claramente de famílias diferentes; o crítico aprova
  ambas. **Pronto:** o usuário escolhe entre opções genuinamente distintas.

### 3.4 Self-inspection do designer (crops com `sips`)
O autogen já reavalia o render; o plugin vai além: o designer **abre o próprio PNG e
faz crops** (CTA, rosto, safe-zones) antes de reportar. Reforçar a checagem de borda
(CTA cortado, rosto decapitado) no caminho de geração.

### 3.5 Whitelist montada com o usuário
Já há suporte a `copy.whitelist` no `_qa`. Falta o fluxo interativo: ao detectar texto
de chrome não declarado, perguntar ao usuário em vez de só warning.

---

## 4. Melhorias além do plugin

### 4.1 Expandir a camada de conhecimento
Mais fontes (`mql.md`, `marca/narrativa.md`, `manifesto.md`, mais transcrições);
melhorar retrieval (os docs achatados de HTML pioram a recuperação — limpar headings);
recuperação por **segmento de ICP** (não só por copy).

### 4.2 Aprendizado acumulado (o "auto-aprendizado v2" que o plugin adiou)
Distilar o que deu **SHIP** (quais cenas/personas/tratamentos funcionaram por ICP) de
volta pros prompts/regras. O flywheel de **conhecimento**, não só de banco. Ex: "para
copy de método no ICP varejo, cenas de chão de loja com dado à vista ganham" → entra no
`_base.md`/art director.

### 4.3 Paridade local↔prod
OpenAI↔Claude e `_render_png.py`↔`render.js` divergem. Para testar o que o site faz,
rodar local no provider de prod. Decisão: manter um perfil de teste = prod.

### 4.4 Custo e latência
Cada camada = +chamadas de IA (art director + skill 04 + image-gen + vision-qa + crítico
+ avaliador + N regenerações). Em prod isso multiplica. Mitigar: gates condicionais
(crítico/avaliador só quando há foto; pular vision-qa em tipográficas), caching de
recuperação, budget por request, e o `image_fixable` evitando regeneração inútil.

### 4.5 Observabilidade
Dashboard simples: SHIP rate por rodada, nota média, custo/peça, % de peças com persona
derivada do ICP. É como saber que o flywheel está girando.

---

## 5. PLANO DE TESTES (o foco do pedido)

### 5.1 Regressão mecânica
`python3.11 scripts/validate_styles.py` → 34/34 a CADA mudança. Gate de PR.

### 5.2 Golden set (criar)
~12 briefs fixos cobrindo Metta+Tiago × segmentos de ICP (varejo, serviço, ponto de
inflexão) × tipos (foto/tipográfico/carrossel). Vira a régua de qualidade ao longo do
tempo — rodar a cada mudança grande e comparar notas.

### 5.3 Batch completo (baseline)
`render_out/criativos-atuais/_run_all.py` nos 34 modelos (billing voltou). Métricas:
SHIP rate, nota média, % vision-qa PASS, % crítico PASS, custo total, tempo. **É o
baseline** contra o qual mediremos cada melhoria.

### 5.4 A/B do ICP (prova a Fase 2)
Mesma copy COM avatar vs SEM. Esperado: relevância↑, crítico↑, "genérico" (rel=weak)↓.
Se não subir, a injeção do ICP no pensador não está pegando.

### 5.5 Auditoria do decision log (prova Fases 3/4)
Amostrar 10 peças: a persona/cena bate com o ICP registrado no `03-decision-log.json`?
O avaliador apontou quando NÃO bate? Esperado: 100% das personas derivadas do ICP.

### 5.6 Loop de auto-melhoria (prova Fase 6)
Rodar `_autogen` nos REVISAR → a nota sobe entre tentativas? guarda a melhor? para
quando `image_fixable=false`? (Já validado 1×: 6.5→7.8→6.8, manteve 7.8.)

### 5.7 Guardrails (segurança)
- Copy adulterada (trocar 1 palavra) → `copy_*_literal` reprova. ✅ testado.
- Texto inventado na imagem → crítico flagra.
- Chrome legítimo (eyebrow Metta / assinatura Tiago) → NÃO falso-positiva. ✅ testado.

### 5.8 Imagem (moderação + falhas)
Prompts que batiam moderação ou geravam mãos/texto tortos → confirmar que skill 04 +
`NEG_MODEL_FAILS` reduzem. Medir taxa de imagem ruim antes/depois.

### 5.9 Paridade local↔prod (prova Fase 8)
Mesmo brief no OpenAI (local) e no Claude (prod). Diferença visual deve ser aceitável;
se gritar, alinhar antes de confiar nos testes locais.

### 5.10 Custo/latência
Medir chamadas de IA e tempo por peça com TODAS as camadas ligadas. Definir teto
aceitável por geração em prod.

---

## 6. Métricas de sucesso (como saber que melhorou)
- **SHIP rate sobe** rodada a rodada (sinal do flywheel).
- **Nota média sobe** e **"rel=weak" cai** (geração deixa de ser genérica = ICP/conhecimento funcionando).
- **100% das personas derivadas do ICP** (decision log), 0% da heurística "use mulheres".
- **Custo/peça sob teto** definido.
- **Banco cresce** com peças aprovadas (Fase 5).

---

## 7. Sequência sugerida (com dependências)

**Já feito (commitado):** Fases 1–6 + 5.5 (camada de conhecimento, ICP no pensador,
decision-log, avaliador critica o raciocínio, flywheel/F8, ledger, auto-melhoria no
pipeline via `FINAL_EVAL`) + Modo B (`_copywriter`) + golden set + baseline no ledger.

**Agora em diante (ordem):**
1. **CARROSSEL — prioridade (Fases 9 → 10 → 11).** Começa pelo estudo da UI
   (`embed/criar.html`) → direção de série → guardrails C1–C8 → panorâmica++. **Não
   deixar de lado.**
2. **Fase 7 refeita** (reference-aware como **contexto**, não override — a 1ª versão regrediu).
3. **Fase 12 (briefer A↔B)** — sobe a qualidade da imagem; alto valor.
4. **Fase 13 (safe-zones)** + **Fase 14 (2 variantes divergentes)**.
5. **Fase 8 (paridade local↔prod + custo)** + **decisão site=high** (async/plano/funil-interno).
6. **Fase 15 (acabamentos)** + contínuo: aprendizado acumulado (4.2) + observabilidade (4.5).
7. **Só então → produção:** PR `feat/vision-first-knowledge → main`, com o golden set
   verde e os defaults de prod confirmados (crítico ON = custo; severidade dos guardrails).

> **Regra de ouro (princípio 6):** cada fase entra com uma linha no ledger medindo o
> antes→depois no golden set. 🔴 PIOROU = reverter (foi o que matou o reference-aware-override).

---

## 8. Riscos e mitigações
- **Custo (várias IAs):** gates condicionais, caching, budget, `image_fixable`.
- **Deploy de código não-verificado:** PR + golden set antes da `main` (prod deploya da main).
- **2 Claudes no mesmo repo:** commits frequentes, branches, não rodar batch + git ao mesmo tempo.
- **Retrieval ruim por doc achatado:** limpar docs / melhorar chunking (já há sub-janela).
- **Billing OpenAI:** monitorar; em prod a imagem depende da OpenAI (gpt-image-2).
- **Paridade local↔prod:** testar no provider de prod antes de confiar.
