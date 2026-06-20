# Camada de Recuperação de Conhecimento (`api/_knowledge.py`)

## Por que existe
O brand-system tem dezenas de milhares de linhas de conhecimento curado (ICP,
voz verbal, metodologia, depoimentos, transcrições) e a geração carregava ~3
arquivos pequenos. O resultado: a "IA que pensa" (diretor de arte) decidia cena e
persona com input pobre — daí "use mulher / cena genérica". Esta camada puxa as
**fatias relevantes** do acervo e entrega um bloco compacto pra injetar no prompt.

## Como funciona
Determinística (token-overlap + difflib, sem embeddings — mesmo padrão de
`_resolve_catalog`/`_critic.pick_reference`). Cacheia os docs no módulo.

1. **Indexa** as fontes (`_SOURCES`), quebrando cada `.md` em seções por heading.
   - Sub-janela blocos grandes (>1200 chars) → docs achatados de HTML (ex:
     `identidade-verbal.md`, 920 linhas sob 1 heading) ficam recuperáveis.
   - Pula seções não-conteúdo (índice, TL;DR, "Documentos Relacionados", links).
2. **`retrieve(copy, marca)`** seleciona:
   - **ICP** (sempre) — a essência (campo `summary:` do frontmatter).
   - **Voz da marca** (sempre) — a fatia com mais densidade de tom/voz (arquétipos,
     pilares de tom), independente do tema da copy.
   - **Metodologia** (Metta, por tópico) — a seção do método que casa com a copy.
   - **Depoimento real** (por tópico) — o case que casa com a copy.
   - **Fala do Tiago** (Tiago, por tópico) — trecho de transcrição que casa.
3. **`build_block(picks)`** formata em texto pronto pro prompt; `picks["provenance"]`
   lista (tipo, fonte) pro **decision log** (de onde cada decisão se fundamenta).

## Fontes (`_SOURCES`)
| id | arquivo | marca | modo |
|---|---|---|---|
| icp | `content/audiencia/icp.md` | ambas | sempre |
| voz | `content/verbal/identidade-verbal.md` | ambas | sempre |
| metodo | `content/metodologia/*.md` | metta | tópico |
| prova | `content/audiencia/depoimentos.md` | ambas | tópico |
| fala | `content/transcricoes/*.md` | tiago | tópico |

## Exemplo (real)
Copy *"Sua operação tem método ou tem sorte?"* (Metta) →
- ICP: essência (empresário em ponto de inflexão, decisão identitária)
- Voz: arquétipos Sábio+Governante, 5 pilares de tom
- Metodologia: `gestao-metodo · Amplie o Relacionamento`
- Depoimento: `Platano — Alexandre, dono`

## Status
Construída e testada **standalone**. **Ainda não está ligada** na geração — isso é
o próximo passo (o "passo ICP"): injetar o bloco + o avatar no diretor de arte (o
pensador), e gravar a proveniência no decision log.

## Limitação honesta
A qualidade da recuperação depende da estrutura dos docs. `identidade-verbal.md` é
achatado (HTML→md) — a sub-janela resolve, mas o ideal de longo prazo é
re-estruturar os docs com headings limpos. A camada surfaceia essa dívida.
