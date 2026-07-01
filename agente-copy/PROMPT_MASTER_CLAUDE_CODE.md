# Prompt Master — Build do Agente Copy (Metta Brasil)

Cole isso direto no Claude Code, na raiz do repositório, junto com o arquivo `Build do Agente Copy — Instrução para o Claude Code` que já foi escrito separadamente. Os dois se complementam: aquele define a ordem de construção; este fecha as decisões, lacunas e regras de precedência que vieram de uma auditoria da base de conhecimento contra o próprio documento de build.

## Papel

Você vai construir o Agente Copy da Metta Brasil: copywriter especialista que entrevista antes de escrever, produz 6 tipos de peça de conteúdo social e valida antes de entregar. Escopo desta versão: só marca Metta (institucional). Antes de escrever qualquer linha de código, leia todos os arquivos de `knowledge-base/` listados abaixo, na ordem de precedência descrita — a ordem importa porque em caso de conflito de termo proprietário o glossário vence, e em conflito de metodologia o Protocolo M.E.T.T.A. vence.

## Stack (decidido, não reabrir)

Python. SDK oficial `anthropic` do PyPI. Sonnet para tarefas estruturais (entrevista, roteamento, formatação de saída); Opus para julgamento de copy (escrita final, calibração de tom, ângulo). **Nunca Haiku** — se qualquer documento da base mencionar Haiku em roteamento de modelo, ignore: é resquício de versão anterior já corrigida, não decisão vigente. Sem RAG, sem embeddings, sem vector DB — leitura direta de arquivo e concatenação no prompt. Sem framework de agente (LangChain, CrewAI etc.) — chamada direta à API, controle de fluxo em código puro.

## Arquivos a colocar em `knowledge-base/`, nesta ordem de leitura no `context_loader.py`

1. `glossario-2.md` — prevalece sobre qualquer outra fonte em conflito de termo proprietário.
2. `tom-de-voz-metta.md`
3. `mito-fundador-metta.md`
4. `posicionamento.md` — contém o resumo do Protocolo M.E.T.T.A. (ver lacuna abaixo).
5. `oferta.md`
6. `provas.md` — em conflito de número, a transcrição de depoimento vence o número institucional.
7. `avatar.md`
8. ICP Estratégico (Mentoria), ICP Secundário Varejo, ICP Secundário Serviços — converter os `.docx` para `.md` antes de commitar.
9. `SKILLMETTACOPY.md` — ver lacuna abaixo antes de usar como regra definitiva de formato.
10. Base Editorial Canônica — converter `.docx` para `.md`.

**Não** coloque `Agente_Copy_Plano_Mestre.docx` nem `Agente_Copy_Criacao_v5.1_CORRIGIDO.docx` dentro de `knowledge-base/`. Eles não são contexto de runtime — extraia o prompt de sistema pronto (seção 4.1 do Plano Mestre) direto para `prompts/system_prompt.py`, como string estática, sem reescrever. O documento de criação v5.1 corrigido é a especificação funcional para você seguir durante o build, não algo que o agente lê em produção.

## Duas lacunas reais — trate como limitação conhecida, não invente

**Protocolo M.E.T.T.A. V9.** É definido como fonte canônica da metodologia em três documentos da base, mas o documento original ("Protocolo METTA - Metodologia Aplicada V9") não está disponível — só existe um resumo das 5 etapas dentro de `posicionamento.md`. Use esse resumo por enquanto. Não invente detalhamento da metodologia além do que está escrito lá. Se em algum momento o documento original for adicionado à `knowledge-base/`, ele deve substituir a dependência do resumo.

**Skill de Validação.** Confirmada como existente, mas não localizada. Implemente `validation.py` retornando sempre `{"nota": null, "aviso": "Skill de Validação não disponível nesta execução"}` até que o arquivo real seja adicionado. Nunca gere uma nota simulada, mesmo que pareça razoável — isso é regra explícita do prompt mestre (4.1) e do documento de criação.

## Uma lacuna parcial — não trava o build, mas limita o resultado inicial

`SKILLMETTACOPY.md`, hoje, cobre bem tom de voz, psicologia do avatar e um checklist de QA geral — mas o "fluxo por tipo de peça" dela é estruturado para formatos de funil de vendas (criativo de tráfego, landing page, e-mail, apresentação comercial, VSL), não para os 6 tipos orgânicos de Instagram que o Copy precisa produzir (carrossel, post único, descrição de post, stories, reels, criativos). Construa o `copy_generator.py` de forma que as regras específicas de cada tipo fiquem inteiramente no conteúdo do `.md`, nunca hardcoded no código Python — porque esse arquivo vai ser substituído por uma versão expandida em breve (expansão está em andamento a partir de conteúdo real do Instagram da Metta). O código não deve precisar mudar quando o `.md` for atualizado.

## Human-in-the-loop — não implementar publicação

Nenhuma peça vai ao ar sem aprovação humana (Alisson aprova). Nesta versão a saída é só texto formatado em terminal ou arquivo — não implemente nenhuma integração de publicação, nem com o brandsystem (destino técnico ainda não confirmado) nem com qualquer rede social.

## Critério de pronto para esta primeira entrega

Carrossel funcionando ponta a ponta: entrevista → geração → validação (placeholder) → saída formatada com hook + corpo + CTA + 3 variações de hook + nota (ou aviso de indisponibilidade). Só depois disso replicar o padrão pros outros 5 tipos.
