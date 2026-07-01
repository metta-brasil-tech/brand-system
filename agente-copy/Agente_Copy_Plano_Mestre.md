Agente Copy — Plano Mestre de Criação	IA Social · Metta Brasil

**IA SOCIAL · METTA BRASIL + TIAGO ALVES**

**Agente Copy — Plano Mestre de Criação**

*Etapas, responsáveis e prompts prontos para iniciar o build.*

| **Status deste documento** Este é o plano de execução do Agente Copy — não substitui o Agente_Copy_Criacao.docx, depende dele. O documento de criação define O QUE o agente faz; este aqui define COMO chegar lá, em que ordem, e com quais prompts. O que está no projeto hoje é a versão 4.0 do documento de criação. Se já existe uma v5.0 fechada com o gap audit completo (PMO + briefing 3.1/3.2 + requisitos do WhatsApp do Tiago), ela precisa estar valendo antes deste plano avançar da Etapa 0. Os prompts da Seção 4 são v1 — desenhados a partir de tudo que está documentado até aqui, mas precisam ser calibrados com os primeiros testes reais (Etapa 3). Trate como ponto de partida forte, não como versão final. |
| --- |

# Sumário

1. Objetivo deste documento

2. Onde estamos agora

3. As cinco etapas  —  3.0 Insumos · 3.1 Validação · 3.2 Skills · 3.3 MVP · 3.4 Qualidade

4. Os prompts  —  4.1 Prompt mestre do Agente Copy · 4.2 Skill de Copy Tiago (Fase 2) · 4.3 Skill de Validação · 4.4 Cards de teste

5. Critérios de aceitação (Copy v1)

6. Riscos e pendências consolidados

7. Próximos passos imediatos

# 1. Objetivo deste documento

Este plano traduz o Agente_Copy_Criacao.docx em uma sequência executável: o que precisa acontecer, em que ordem, quem é dono de cada parte, e — principalmente — os prompts que tiram o projeto do papel. Ele segue a mesma estrutura de 5 etapas já registrada no Documento Mestre (Insumos → Validação → Skills → MVP → Qualidade), recortada e aprofundada só para o Copy.

Não há datas. O próprio Documento Mestre registra que o cronograma depende da nova reunião de validação com o Tiago — este plano define ordem e dependência, não calendário.

# 2. Onde estamos agora

- Documento de criação do Copy: v5.1, auditado linha a linha contra o PMO de 11/06 (transcrição verbatim) e o briefing de 28/04 — sem gaps. Substitui a v4.0.

- Escopo deste MVP: somente marca Metta. Tiago Alves entra na Fase 2, quando a Skill de Copy da marca Tiago existir — hoje só existe a Skill de Copy da Metta (SKILLMETTACOPY.md).

- Duas decisões seguem em aberto: entrada do LinkedIn no escopo do Copy, e se o segundo agente avaliador do briefing original vira distinção por skill ou continua como agente separado.

- Quatro pendências de insumo já mapeadas: Skill de Validação não localizada, Skill de Copy cobrindo só a marca Metta, EMIC em v1 consolidada (não pesquisa de campo), Banco de criativos vencedores ainda não construído.

- Interface de saída no brandsystem ainda registrada como “a confirmar” no próprio documento de criação.

Este plano assume que a Etapa 0 resolve os insumos e a Etapa 1 resolve as duas decisões — nessa ordem, antes de qualquer linha de skill ou build técnico.

# 3. As cinco etapas

Mesma estrutura do Documento Mestre, recortada para o Copy. Cards no Monday e relatório de tendências não aparecem aqui — são saída do Estrategista, não do Copy.

## 3.0 · Insumos

- Documento de criação oficial: v5.1, já auditado e travado — não há mais reconciliação de versão pendente.

- Localizar e integrar a Skill de Validação — sem ela não existe nota automática, e isso é critério de aceitação do MVP.

- Decidir o tratamento da EMIC v1: usar como está, mas marcada como v1 em toda entrega, nunca como definitiva.

- Confirmar o destino técnico do brandsystem como output — ainda não fechado no documento de criação.

*Responsável: Alisson localiza a Skill de Validação; Amanda é ponte; Nathan reconcilia versão do doc e confirma o brandsystem.*

## 3.1 · Validação

- Fechar as duas decisões em aberto antes da reunião — chegar com a decisão tomada, não construir na hora.

- Montar a apresentação direcional ao Tiago: documento de criação fechado + pendências de insumo mapeadas + as duas decisões já resolvidas.

- Tiago aprova arquitetura e escopo — entregas parciais valem, não precisa esperar tudo pronto.

*Responsável: Nathan.*

## 3.2 · Skills

- Estruturar a skill pelos 6 tipos de copy do v5.1 (carrossel, post único, descrição de post, stories, reels, criativos), puxando do Manual de Conteúdo (filtro de 10 perguntas + regras por formato) — escopo Metta apenas nesta fase, sobre a SKILLMETTACOPY.md já existente.

- Acoplar a Skill de Validação assim que localizada, com critério de nota definido.

*Responsável: Nathan constrói; Amanda confirma.*

## 3.3 · MVP

- Build do fluxo de entrevista em código: identifica o tipo de copy (dos 6 do v5.1) → aplica as perguntas-base do PMO (objetivo, ICP, ângulo, dor/desejo/necessidade, CTA, formato, tempo) → soma as perguntas próprias do tipo → ângulo A/B/C.

- Capacidade de transformar material bruto (aula, ebook, PDF) em múltiplos formatos a partir do mesmo tema.

- Conectar a leitura da base versionada no GitHub no início do ciclo, e a saída no brandsystem.

- Testar ponta a ponta com 1-2 cards montados manualmente, marca Metta — o Estrategista ainda não existe, e isso já está previsto no próprio documento de criação.

*Responsável: Nathan.*

## 3.4 · Qualidade

- Geração de variações a partir de criativos vencedores — o banco está como “construir”, entra aqui, não no MVP.

- Documentação final do agente.

- Critério de “pronto” do Tiago: qualquer pessoa do time consegue usar — o teste real é a Amanda operando sozinha.

*Responsável: Nathan documenta; Amanda valida uso operacional; Alisson aprova publicação; Tiago aprova entrega.*

# 4. Os prompts

Quatro prompts, do mais importante ao mais auxiliar. O 4.1 é o motor do agente — o system prompt que roda no código a cada chamada à API. O 4.3 e o 4.4 são prompts de apoio para os artefatos que faltam antes do MVP rodar; o 4.2 é referência para a Fase 2 (marca Tiago).

| **Como o 4.1 foi desenhado** O prompt mestre não embute o conteúdo de marca (tom de voz, ICP, EMIC, glossário) diretamente no texto do prompt. Ele referencia esses documentos como contexto injetado a cada ciclo — exatamente como a arquitetura já define (base lida do GitHub no início do ciclo, sem RAG). Isso evita duplicar conteúdo que já está versionado, e significa que atualizar a voz de uma marca não exige tocar no prompt — só no documento-fonte. |
| --- |

## 4.1 · Prompt mestre do Agente Copy (system prompt)

*Vai na chamada à API no código. Pressupõe que a base de conhecimento (glossário, tom de voz, mito fundador, ICP, EMIC, posicionamento, oferta, provas, Skill de Copy, banco de vencedores) está sendo injetada como contexto na mesma chamada.*

| **[Papel]** Você é o Agente Copy da Metta Brasil. Foco exclusivo em copy: você não desenha peça nem planeja período — produz a palavra escrita, sempre embebido do ICP, da linguagem do cliente (EMIC) e do tom de voz institucional da Metta. Você não é um gerador de texto: entrevista antes de escrever. **[Escopo desta versão — Metta apenas]** Este MVP cobre exclusivamente a marca Metta Brasil (institucional, vende implementação). A marca Tiago Alves (pessoal, vende visão de mundo) entra na Fase 2, quando a Skill de Copy da marca Tiago estiver pronta — hoje só existe a Skill de Copy da Metta. A regra de separação inviolável de vozes do documento de criação segue valendo: quando a marca Tiago for adicionada, as vozes nunca podem se misturar na mesma peça. **[Base de conhecimento recebida como contexto]** A cada execução, você recebe: glossario (PREVALECE em conflito de termo proprietário); tom-de-voz-metta e mito-fundador-metta; avatar e ICP (estratégico + secundário do segmento); posicionamento, oferta e provas (em conflito, o DEPOIMENTO prevalece sobre número institucional); EMIC (hoje v1 consolidada — trate sempre como v1, nunca como definitiva); Skill de Copy Metta; banco de criativos vencedores quando existir. Nunca invente fato, número, termo proprietário ou citação fora dessa base. Se faltar informação, pergunte antes de inventar. **[Fluxo obrigatório — entrevista antes de escrever]** Núcleo de perguntas, direto da lista do PMO de 11/06 (ou processe de uma vez se o usuário já trouxer tudo junto): 1. Qual é o objetivo? 2. Qual o ICP? 3. Qual tipo de copy? (carrossel / post único / descrição de post / stories / reels / criativos — cada um soma perguntas próprias, seção seguinte) 4. Qual ângulo? Proponha A / B / C com uma linha de justificativa cada, e espere o usuário escolher. 5. Trabalhar dor, desejo ou necessidade — qual? 6. Existe CTA específico? 7. Tempo de leitura (carrossel/texto) ou tempo do vídeo (reels/criativo em vídeo)? **[Os 6 tipos de copy — cada um com perguntas próprias]** Carrossel: ideia solta ou texto bruto a transformar? Leitura em até 40s reais. Até 11 slides, pouco texto por slide. Capa para o scroll, último slide é CTA. Post único (estático): frase chamariz, frase de autor ou texto longo? Há assinatura/@ a exibir? Descrição de post: acompanha qual peça (estático, carrossel, reels)? É o chamariz ou complementa o visual? No estático, a descrição É a copy principal — não o carrossel. Stories: story único ou sequência? Tipo (enquete / caixinha / sequência / levantamento de dor)? Se sequência, monta a progressão dor → desejo → necessidade, terminando em comentário ou caixa de pergunta (social selling) — nunca stories soltos sem essa mecânica quando for sequência. Reels: subtipo (longo de conteúdo / curto / respondendo caixinha)? Ideia ou texto bruto? Duração-alvo? Começa com gancho/pergunta? Se responde caixinha, qual a pergunta de origem? Criativos (estático ou vídeo): novo ou variação de um vencedor (aciona o banco de vencedores)? Qual objetivo (lead/clique/agendamento)? Qual dor/desejo/necessidade ataca? **[Adaptação por plataforma]** Instagram é o foco principal — todos os 6 tipos. Para LinkedIn: reescreva com tom próprio da plataforma, nunca copy-paste; carrossel vira PDF; descrição fica mais densa. LinkedIn está no escopo do documento de criação conforme o briefing original, mas é decisão marcada para confirmação com o Tiago — pergunte se a peça precisa de versão LinkedIn quando não for explícito. **[Validação — duas checagens distintas]** 1. Avalie a peça contra o ICP (“faz sentido para esse público?”) e revise gramática, fluência e aderência ao tom de voz institucional. 2. Aplique a Skill de Validação e retorne a nota junto com a peça. Se a skill não estiver disponível no seu contexto, diga isso explicitamente — nunca invente uma nota. O segundo agente avaliador (auto-crítica antes da entrega final) é uma etapa separada no fluxo, fora deste prompt — não simule o parecer dele aqui. **[Entrega]** Toda peça final inclui: hook + corpo + CTA; no mínimo 3 variações de hook; indicação de pilar de conteúdo e ICP-alvo; nota da Skill de Validação (ou aviso de indisponibilidade); versão adaptada para LinkedIn quando solicitado; e, se pedido, variações a partir de um criativo vencedor, mantendo os elementos responsáveis pela performance original, independente do tipo de saída. **[O que você nunca faz]** Nunca escreve sem ter passado pela entrevista, a menos que o usuário já tenha respondido tudo de uma vez. Nunca apresenta a EMIC v1 como pesquisa de campo definitiva. Nunca inventa prova, número ou citação fora da base fornecida. Nunca publica sozinho — toda peça depende de aprovação humana antes de ir ao ar. |
| --- |

## 4.2 · Fase 2 — Skill de Copy, marca Tiago Alves (adiado)

| **Fora do escopo deste MVP** Este MVP cobre só a marca Metta. A Skill de Copy da marca Tiago Alves fica para a Fase 2, quando essa marca entrar no escopo — mantendo a regra de separação inviolável de vozes do documento de criação v5.1. Quando chegar a hora, o prompt segue a mesma lógica do 4.1/4.3: usar tom-de-voz-tiago.md, mito-fundador-tiago.md, o Manual de Conteúdo e a LISTA REELS JULHO.docx como referência de calibração, construindo a skill no mesmo formato e profundidade da SKILLMETTACOPY.md. |
| --- |

## 4.3 · Prompt de apoio — Skill de Validação

*Para quando a skill original for localizada. Objetivo: transformar o material bruto em critério aplicável de forma determinística pelo agente.*

| A Skill de Validação existe — confirmado em reunião — mas ainda não foi localizada nem integrada ao fluxo do Copy. Quando o material bruto for encontrado (provável fonte: Alisson), preciso estruturá-lo para o agente conseguir aplicar e devolver uma nota junto com cada peça. A partir do material bruto, organize os critérios em um checklist objetivo. Escala de nota a definir com quem criou a skill original (0 a 10, ou aprovado/ajustar/reprovado). Estruture por quatro blocos: critérios de tom de voz (a peça soa da marca certa?); critérios de formato (segue as regras do formato — tempo de leitura, número de slides, gancho nos 3 segundos?); critérios de ICP (a peça faz sentido pro público daquele segmento?); critérios de CTA (está alinhado à fase da jornada?). O resultado final precisa ser algo que o Agente Copy aplique de forma determinística a cada peça gerada — não uma rubrica subjetiva que dependa de interpretação caso a caso. |
| --- |

## 4.4 · Prompt de apoio — Cards de teste manuais

*Para a Etapa 3. Substitui o Estrategista, que ainda não existe, no teste ponta a ponta do Copy.*

| O Estrategista ainda não existe, então o teste ponta a ponta do Copy precisa de cards montados à mão, no mesmo formato que o Estrategista entregaria depois. Monte 1-2 cards de teste da marca Metta com os campos: data, plataforma, tipo de copy, pilar de conteúdo, hook proposto, fase da jornada (aquecimento / autoridade / conversão / oferta), e uma linha de contexto explicando por que esse tema agora. Use um tema real da base atual — por exemplo, um dos pilares já documentados em posicionamento.md, ou um gancho já testado na Base_Editorial_Canonica.docx — para o teste nascer calibrado, não genérico. |
| --- |

# 5. Critérios de aceitação (Copy v1)

Direto do Agente_Copy_Criacao.docx — o gate que decide se o MVP está pronto para a Etapa de Qualidade.

- Entrevista antes de escrever, com o núcleo do PMO (objetivo, ICP, ângulo, dor/desejo/necessidade, CTA, formato, tempo).

- Trata cada um dos 6 tipos de copy de forma independente (carrossel, post único, descrição de post, stories, reels, criativos).

- Monta a sequência dor→desejo→necessidade nos Stories quando for sequência, não stories soltos.

- Escreve embebido de ICP, EMIC e tom de voz, sem misturar as vozes das marcas.

- Sugere ângulos A/B/C antes de escrever.

- Avalia contra o ICP e revisa gramática, fluência e tom.

- Valida pela skill (nota) e passa pelo segundo agente avaliador.

- Adapta para LinkedIn quando solicitado, com reescrita e não cópia.

- Gera no mínimo 3 variações de hook por peça.

- Está rodando e qualquer pessoa do time consegue usar — definição de entrega do Tiago.

# 6. Riscos e pendências consolidados

| **Risco / pendência** | **Impacto** | **Próximo passo** |
| --- | --- | --- |
| EMIC ainda em v1 consolidada | Copy menos calibrado à linguagem real | Usar v1 agora, sinalizado como tal; ampliar quando a pesquisa de campo chegar |
| Marca Tiago fora do MVP | Nenhum — decisão consciente de sequenciamento, não pendência | Retomar na Fase 2, via prompt 4.2 quando ativado |
| Skill de Validação não localizada | Sem nota automática — bloqueia critério de aceitação | Confirmar com Alisson; rodar o prompt 4.3 assim que localizada |
| Banco de criativos vencedores não existe | Sem benchmark de performance no MVP | Tratar como item da Etapa de Qualidade, não do MVP |
| Interface brandsystem ainda “a confirmar” | Saída técnica do Copy sem destino fechado | Fechar antes da Etapa 3 (MVP) |
| Versão do documento de criação (v4 vs. eventual v5) | Build pode partir de uma base desatualizada | Reconciliar na Etapa 0, antes de qualquer outra coisa |
| Escopo amplo para prazo curto | Estouro de prazo ou queda de qualidade | Entregar 1 marca + formatos core primeiro, como já decidido |

# 7. Próximos passos imediatos

- Rodar o segundo agente avaliador como etapa separada, ou confirmar com o Tiago se ele quer os dois passos (skill + avaliador) ou só a skill.

- Confirmar com Alisson o paradeiro da Skill de Validação.

- Montar 1-2 cards de teste manuais (prompt 4.4), marca Metta, para já ter material pronto assim que o build técnico começar.

*Fim do documento.*

	v1.0 · Junho 2026	Página