Documento Mestre — Copy + Estrategista	IA Social · Metta Brasil

**PROJETO AGENTES DE IA SOCIAL**

**Documento Mestre — Copy + Estrategista**

*Metta Brasil  ·  Versão 2.0  ·  Junho 2026*

| **O que mudou nesta versão (v1.0 → v2.0)** Orquestração deixou de ser n8n: o sistema passa a ser um código próprio (a definir entre Python e Node.js) chamando a API do Claude diretamente, sem camada no-code intermediária. Toda menção a n8n foi removida. Modelo corrigido: nunca Haiku. Sonnet como padrão para tarefas estruturais (entrevista, roteamento, formatação); Opus para julgamento de copy (tom, ângulo, calibração de voz). A menção anterior a "Haiku para triagem" não vinha de nenhuma decisão do Tiago — não aparece no PMO nem no briefing — e foi removida. Documento de criação do Copy atualizado para a v5.1, auditada linha a linha contra o PMO de 11/06 (transcrição verbatim) e o briefing de 28/04. Corrige 8 gaps que a v4.0 tinha: LinkedIn, descrição de post como tipo próprio, sequência dor→desejo→necessidade nos Stories, subtipos de Reels, criativos como categoria própria, revisão de gramática/fluência, avaliação de ICP pós-geração, e o segundo agente avaliador. Amanda substitui Renan como operadora do dia a dia — reflete o time atual do projeto, não o time do briefing original de abril. Etapa 3 do roadmap (MVP) atualizada: build em código, não em n8n. |
| --- |

# 1. Visão Geral

O projeto cria dois agentes de IA que operam a produção de conteúdo social das marcas Metta Brasil e Tiago Alves. O objetivo, segundo a direção, não é replicar o processo manual atual — é superá-lo em qualidade e escala.

| **Agente** | **Papel** |
| --- | --- |
| Estrategista | Planeja o período: entrevista, monta calendário por fases, considera tendências e abastece o Monday com a pauta. |
| Copy | Produz a peça: entrevista, escreve por formato no tom certo, valida pela skill com nota e gera variações. |

**Regra inviolável: **as duas marcas têm voz, narrativa e ICP distintos. Tiago vende visão de mundo; Metta vende implementação. Nunca misturar as vozes.

# 2. Arquitetura em uma página

| **Fluxo do sistema** Estrategista entrevista e planeja → gera calendário por fases → cria cards no Monday → Copy consome cada card → entrevista, escreve e valida → peça pronta no brandsystem. |
| --- |

- Orquestração → código próprio (Python ou Node.js, a definir), chamando a API do Claude diretamente — sem camada no-code intermediária.

- Reasoning → Claude via Anthropic API: Sonnet para tarefas estruturais (entrevista, roteamento, formatação); Opus para julgamento de copy (tom, ângulo, calibração de voz). Nunca Haiku.

- Base de conhecimento → arquivos versionados no GitHub, lidos no início de cada ciclo. Sem RAG/embeddings.

- Interface do Copy → brandsystem (web, página única) — destino técnico da saída ainda a confirmar.

- Saída do Estrategista → cards no Monday.com via API.

- Coleta de tendências → busca ativa via código (Google Trends, YouTube, perfis de concorrentes) — mecanismo específico a definir na Etapa 3.

# 3. Mapa de Documentos do Projeto

Todos os documentos que o projeto precisa, em quatro camadas, com o estado atual de cada um.

## 3.1 Base de Conhecimento (o que o agente lê para pensar)

| **Documento** | **Estado** | **Uso** |
| --- | --- | --- |
| ICP Estratégico (Mentoria) | Em mãos | Copy + Estrategista |
| ICP Secundário — Varejo | Em mãos | Copy + Estrategista (recorte segmento) |
| ICP Secundário — Serviços | Em mãos | Copy + Estrategista (recorte segmento) |
| avatar | Em mãos | Copy + Estrategista |
| Código de Conteúdo Metta | Em mãos | Copy + Estrategista |
| glossario | Em mãos | Copy + Estrategista |
| tom-de-voz-metta | Em mãos | Copy (marca Metta) |
| tom-de-voz-tiago | Em mãos | Copy (marca Tiago) |
| mito-fundador-metta | Em mãos | Copy + Estrategista |
| mito-fundador-tiago | Em mãos | Copy + Estrategista |
| posicionamento | Em mãos | Copy + Estrategista |
| oferta | Em mãos | Copy + Estrategista |
| provas | Em mãos | Copy + Estrategista |
| Pesquisa EMIC | v1 consolidada | Copy — ampliar com pesquisa de campo quando disponível |
| Calendário de publicações atual | Em mãos (Base Editorial Canônica) | Estrategista — cadência e formatos |

## 3.2 Skills (as regras que o agente aplica)

| **Skill** | **Estado** | **Plano** |
| --- | --- | --- |
| Skill de Copy por formato | Em mãos (marca Metta) / Produzir (marca Tiago) | Expandir para a marca Tiago antes do MVP cobrir as duas marcas |
| Skill de Validação (nota) | Confirmar | Já existe (confirmado em reunião). Localizar com Alisson e integrar. |
| Skill de Estratégia | Produzir | Regras de fases, cadência e priorização. Produzir ou confirmar com Amanda. |

## 3.3 Insumos Operacionais

| **Insumo** | **Estado** | **Uso** |
| --- | --- | --- |
| Lista de concorrentes por marca | Em mãos (5 diretos + indiretos/long-tail) | Estrategista — contexto de tendências |
| Transcrições de reuniões estratégicas | Parcial (PMO 11/06, reuniões 18/05, 01/06, 09/06) | Fechar nuances que não entraram nos documentos formais |

## 3.4 Documentos de Projeto (o que organiza o trabalho)

| **Documento** | **Estado** | **Função** |
| --- | --- | --- |
| Agente Copy — Criação v5.1 | Auditado linha a linha contra PMO 11/06 e briefing 28/04, sem gaps | Escopo e arquitetura do Copy |
| Agente Estrategista — Criação v3.0 | Auditado, sem gaps contra o briefing 3.1 | Escopo e arquitetura do Estrategista |
| Agente Copy — Plano Mestre de Criação | Em mãos | Etapas de execução e prompts do Copy |
| Mapa de Arquitetura da Base v1.1 | Em mãos | Onde cada doc alimenta cada agente |
| Briefing original (28/04) — extrato Copy | Em mãos, uso histórico | Registro do escopo original da camada Copy, superado pela v4.0 onde houver conflito |
| Documento Mestre (este) v2.0 | Em mãos | Ponto único de entrada do projeto |

# 4. Fluxo de Aprovação e Papéis

| **Pessoa** | **Papel no projeto** |
| --- | --- |
| Nathan | Desenvolvimento dos agentes, arquitetura e automação |
| Amanda | Social media. Atua no Estrategista (calendário das duas marcas) e executa publicações pelo Copy. Ponto de conexão e refinamento operacional. |
| Alisson | Revisão técnica do conteúdo; aprovador de publicação; provável detentor da Skill de Validação |
| Tiago | Aprovação final e validação estratégica, inclusive das entregas parciais |
| Raquel | Coordenação (COO); valida prioridades e fluxo |
| Kevin | Contato para mapear donos dos materiais pendentes |

| **Princípios de entrega definidos pelo Tiago** Entregas parciais ao longo do projeto — nada de aprovar tudo só no fim. A entrega final deve ser um sistema pronto para uso, não a primeira visão do resultado. Reserva de agenda do Tiago para testar, com datas definidas previamente. Apresentação a ele deve ser direcional: chegar com decisões estruturadas para aprovar/ajustar, não construir do zero na reunião. |
| --- |

# 5. Roadmap de Execução

Sequência macro. As datas serão definidas após a nova reunião de validação com o Tiago.

| **Etapa** | **O que acontece** | **Depende de** |
| --- | --- | --- |
| 0 · Insumos | Reconciliar versões dos documentos de criação; localizar Skill de Validação; confirmar destino técnico do brandsystem | Alisson / Amanda |
| 1 · Validação | Apresentação direcional ao Tiago; aprovar arquitetura e escopo, inclusive as decisões em aberto (LinkedIn; segundo avaliador vs. skill) | Nova agenda do Tiago |
| 2 · Skills | Montar/estruturar skills de Copy (marca Tiago), Validação e Estratégia | Base + alinhamento Amanda |
| 3 · MVP | Build dos agentes em código próprio; entrevista, geração, cards no Monday | Etapas 0–2 |
| 4 · Qualidade | Variações, retroalimentação, relatório de tendências, documentação | MVP validado |

# 6. Pendências Críticas (curto prazo)

- Reconciliar a versão oficial do documento de criação do Copy (v4.0) antes de iniciar o build.

- Localizar com Alisson a Skill de Validação que já existe.

- Agendar com Amanda para validar fluxo e requisitos da entrevista dos agentes.

- Nova data com o Tiago para a validação estratégica consolidada — incluindo as duas decisões em aberto.

- Definir a stack técnica exata do código (Python ou Node.js) e a arquitetura de execução.

- Mapear no Monday quem produz, valida e executa cada card.

# 7. Decisões Já Registradas

- Modelo: Sonnet para tarefas estruturais, Opus para julgamento de copy. Nunca Haiku — não há decisão do Tiago que sustente seu uso.

- Base de conhecimento versionada no GitHub, lida no início de cada ciclo — sem RAG/embeddings.

- Orquestração via código próprio, sem n8n ou outra camada no-code.

- Amanda atua principalmente no Estrategista e usa o Copy para executar.

- Os agentes entrevistam antes de produzir (Copy) e antes de planejar (Estrategista).

- Calendário do Estrategista é estruturado por fases (aquecimento → autoridade → conversão → oferta).

- Copy e Estrategista são construídos e entregues como IAs distintas e independentes — Copy primeiro.

*Documento Mestre  ·  Projeto Agentes IA Social  ·  Metta Brasil  ·  v2.0  ·  Junho 2026*

	v2.0 · Junho 2026	Página