---
id: METTA-STAT-STACK
display_name: "Pesquisa — estatísticas empilhadas + fonte gigante"
marca: metta
archetype: stat-stack
params: { theme: dark, cta: yellow }
slots: [headline, body, tag, cta]
image: { required: false, treatment: "nenhuma — cards de dado sobre fundo sólido" }
formato_nativo: [feed, story]
status: ativo
---

# METTA-STAT-STACK · slide de pesquisa/dado

## Intenção
Slide de credibilidade por número, típico de carrossel (banco: "pesquisa 2026 /
Gallup"). Empilha 2+ estatísticas em cards, cada uma com o número gigante em
amarelo + descrição, e a fonte/ano em wordmark grande na base.

## Copy
- `headline` — 1ª estatística (ex: "94,1% dos empreendedores enfrentaram problemas de saúde mental").
- `body` — estatísticas seguintes, UMA por linha (`\n`).
- `tag` — fonte + ano (ex: "PESQUISA 2026 · FONTE: GALLUP").

O motor separa o número do começo de cada linha automaticamente (destaca em amarelo).
