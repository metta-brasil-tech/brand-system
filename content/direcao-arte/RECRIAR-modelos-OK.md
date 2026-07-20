# 🧩 Recriar no site os 6 modelos que validamos como OK

> Passo a passo pra você entrar no `/criar` e reproduzir cada uma das 6 peças que
> aprovamos (Fase 3.2). Cada bloco tem a **copy exata** que usei na prova — é só
> colar nos campos. Atualizado: 20/07/2026.

---

## ⚠️ Estado do deploy (LEIA ANTES)

O deploy da Vercel está **em conserto** (um endpoint novo, `/api/preview`, quebrou
os builds). Enquanto não volta, o site ao vivo está no **último build bom**, que
**já tem os 6 modelos** — então você CONSEGUE recriar todos. O que pode ainda não
estar no ar é o **fluxo novo** ("Recomendadas / Ver todos os estilos"). Por isso o
passo a passo abaixo funciona nos **dois fluxos**. Quando o deploy voltar verde
(commit ≥ o do concept-first), o fluxo "recomendadas" aparece — mas **modelo + copy
são os mesmos**.

## Antes de começar — o fluxo do site (vale pra todos)

1. Abra **`‹sua-URL-da-Vercel›/criar`** e escolha a marca **Metta**.
2. **Formato:** `Feed` (1080×1350) — foi o que usei em todas.
3. **Selecione o estilo** pelo nome da coluna "Estilo no picker" abaixo:
   - Fluxo **antigo**: escolha o estilo direto no picker de miniaturas.
   - Fluxo **novo** (quando o deploy voltar): digite a copy primeiro; se o estilo
     não aparecer nas "Recomendadas", clique em **"Ver todos os estilos"**.
4. **Preencha a copy** exatamente como nos blocos abaixo (Headline, Corpo/Body, CTA,
   e Tag quando houver).
5. **Estilos sem foto** (grátis): a peça sai pronta na hora — só exportar.
   **Estilos com foto** (marcados 📷): ao gerar, o site **cria a foto pela IA
   (Gemini)** — ~20s e **a foto muda a cada geração** (o layout é sempre igual).
6. Se o texto ficar em cima do foco da imagem, use **"Ajustar posição do texto"**
   (Auto/Topo/Base) no resultado — re-renderiza de graça, sem gerar foto de novo
   *(disponível quando o deploy do concept-first estiver no ar)*.

> **Palavra amarela:** o destaque amarelo sai **automático** (normalmente na
> última palavra / palavra-chave). Se quiser forçar uma palavra específica,
> escreva ela entre asteriscos na headline, ex: `É *régua*.`

> ⚠️ **Foto-real depende do Gemini na Vercel** (você já configurou a chave). Se a
> foto sair fraca/genérica, confirme no painel da Vercel que a `GEMINI_API_KEY`
> está lá e que o último deploy passou.

---

## 1. K — Urgência fundamentada (linha amarela)  ·  sem foto ✅ grátis

- **Estilo no picker:** `Urgência fundamentada (linha amarela)` (id `K-bold-dourado-urgencia`)
- **Formato:** Feed
- **Tag/eyebrow:** `VAGAS LIMITADAS`
- **Headline:** `A porta fecha quando a turma enche.`
- **Corpo/Body:** `Elite roda com grupo pequeno. Não é escassez fake — é capacidade real.`
- **CTA:** `Aplicar agora`
- **O que esperar:** fundo dark, headline gigante com a última palavra em amarelo,
  linha amarela divisória, body curto, CTA pill amarelo. Sai pronto (sem foto).

## 2. LIGHT-TIPO — Statement tipográfico claro  ·  sem foto ✅ grátis

- **Estilo no picker:** `Statement tipográfico claro` (id `LIGHT-TIPO`)
- **Formato:** Feed
- **Headline:** `Método não é sorte. É régua.`
- **Corpo/Body:** *(vazio)*
- **CTA:** `Conhecer o método`
- **O que esperar:** fundo claro, tipografia preta gigante, bloco amarelo na
  palavra-chave (`RÉGUA`). Pra garantir o amarelo em "régua", escreva `É *régua*.`

## 3. YELLOW-DRAW — Amarelo + ilustração à mão  ·  sem foto ✅ grátis

- **Estilo no picker:** `Amarelo + ilustração à mão` (id `YELLOW-DRAW`)
- **Formato:** Feed
- **Headline:** `Crescer sem processo é sorte com prazo de validade.`
- **Corpo/Body:** `Método transforma esforço em previsibilidade.`
- **CTA:** `Conhecer o método`
- **O que esperar:** fundo amarelo, headline preta no topo, **ilustração desenhada
  à mão** (curva de crescimento + seta) na faixa inferior, CTA pill preto. A
  ilustração é um ornamento do motor — sai sem gerar foto.

## 4. DARK-CARTA — Convite formal selado  ·  sem foto ✅ grátis

- **Estilo no picker:** `Convite formal selado` (id `DARK-CARTA`)
- **Formato:** Feed
- **Headline:** `Um convite que não é pra todo mundo.`
- **Corpo/Body:** `Elite roda com grupo pequeno e capacidade real. Candidatura sob análise.`
- **CTA:** `Aplicar para a Elite`
- **O que esperar:** fundo escuro esverdeado, headline branca (última palavra
  amarela), marca d'água de carta/contrato ao fundo e **selo M de cera** na zona
  inferior. CTA pill amarelo. Sai sem gerar foto.

## 5. DARK-OBJETO — Objeto-conceito dark  ·  📷 gera foto (Gemini)

- **Estilo no picker:** `Objeto-conceito dark` (id `DARK-OBJETO`)
- **Formato:** Feed
- **Preset de imagem:** `Cinematic dark`
- **Headline:** `A meta não é troféu. É régua.`
- **Corpo/Body:** *(vazio)*
- **CTA:** `Conhecer o método`
- **O que esperar:** headline no topo, e uma **foto dark do objeto que ilustra a
  copy** embaixo (ex.: troféu enrolado em fita métrica = "a meta é régua"). A foto
  é gerada pela IA e **varia a cada vez** — se não vier o conceito certo, gere de
  novo. Se o texto encostar no objeto, use "Ajustar posição do texto → Topo".

## 6. FOTO-PILL-CASUAL — Foto casual + faixa clara  ·  📷 gera foto (Gemini)

- **Estilo no picker:** `Foto casual + faixa clara` (id `FOTO-PILL-CASUAL`)
- **Formato:** Feed
- **Preset de imagem:** `Fotorrealista`
- **Headline:** `O dono que confia no time cresce mais rápido.`
- **Corpo/Body:** `Operação com método roda sem você apagar incêndio.`
- **CTA:** `Conhecer a Metta`
- **O que esperar:** **foto editorial da pessoa dominando o topo** (~62%) + faixa
  clara embaixo com a headline (palavra amarela), body e CTA pill escuro —
  integrado, sem card flutuante. A foto é gerada e **muda a cada vez**; o layout é
  sempre igual. Se vier uma metáfora de objeto em vez de pessoa, gere de novo.

---

## Resumo rápido

| # | Estilo (picker) | Foto? | Preset | Formato |
|---|---|---|---|---|
| 1 | Urgência fundamentada (linha amarela) | não | — | Feed |
| 2 | Statement tipográfico claro | não | — | Feed |
| 3 | Amarelo + ilustração à mão | não | — | Feed |
| 4 | Convite formal selado | não | — | Feed |
| 5 | Objeto-conceito dark | 📷 sim | Cinematic dark | Feed |
| 6 | Foto casual + faixa clara | 📷 sim | Fotorrealista | Feed |

**4 saem prontos e de graça** (tipográficos/ornamento) — reprodução idêntica.
**2 geram foto pela IA** (5 e 6) — layout idêntico, foto varia a cada geração.

> Os 6 modelos estão no último build bom (`c6ad638`), que está no ar. Se algum não
> aparecer, confirme no painel da Vercel qual build está publicado. O fluxo novo
> (recomendadas/ajuste de texto) só aparece quando o deploy do concept-first
> (`79d9c78`) voltar a passar — hoje os builds estão falhando por causa do
> `/api/preview` (em conserto).
