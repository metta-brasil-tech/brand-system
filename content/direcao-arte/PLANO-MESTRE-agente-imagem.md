# 🎯 Plano Mestre — Agente de Imagem (Metta / Tiago)

> Documento vivo. Fonte única do plano de evolução do gerador de criativos.
> Atualizado: 20/07/2026 · Mantido pelo agente de imagem + Nathan.
> Sub-plano: [imagem do tweet com proporção variável](plano-imagem-tweet-variavel.md).

---

## 1. O problema (diagnóstico)

Os criativos **bons** que a gente construiu à mão (o-segredo, babá, método-ICP,
os tweets, o carrossel do crachá) **não são reproduzíveis pela pessoa no site**.
O site roda a pipeline automática, que:

- gera foto genérica (às vezes **slop**: card branco flutuante, texto de IA
  embananado na foto, número inventado, foto que não ilustra a copy);
- **não aplica** a lógica de composição/foco que usamos à mão;
- mostra um picker de ~15 estilos que "parecem todos iguais" e enganam (thumbnail
  estático não é o que vai sair).

**Consequência:** a distância entre "o que demonstramos" e "o que o produto
entrega" é grande. Fechar essa distância é o objetivo deste plano.

---

## 2. Princípios (não-negociáveis)

1. **UX-first** — tudo pensado pela ótica de quem USA o site, não pela estrutura
   interna. Ex: tweet = 1 mensagem, sem título/subtítulo/descrição.
2. **Nunca inventar dado** — nada de faturamento/percentual/nº de empresas
   fabricado. Só número que veio do conhecimento real ou da copy.
3. **A imagem tem que ILUSTRAR a copy** — foto que não conversa com a mensagem é
   defeito, não decoração.
4. **Foto real do Tiago = as que o Nathan enviou** (recortadas), não stock nem
   fotos antigas soltas.
5. **Só mostrar o que entrega qualidade** — estilo sem creative provado vira
   "Em breve", não vai pro picker enganar.

---

## 3. Visão (onde queremos chegar)

> A pessoa **escreve a ideia/copy** → o motor propõe **2–3 composições calibradas
> da copy dela** (com foto limpa que ilustra a mensagem) → ela escolhe, ajusta,
> publica.

O "estilo" deixa de ser uma miniatura cega e vira um **motor de composição** que
garante o nível dos exemplos feitos à mão — automatizado.

---

## 4. As fases

### 🔧 Fase 1 — Levar a lógica calibrada pro MOTOR (raiz)
*Sem isso, mudar o resto é maquiagem. Eleva TODA peça.*

| # | Tarefa | Status |
|---|---|---|
| 1.1 | **Focus map em produção** — medir onde está o sujeito (energia de borda por zona) e jogar o texto pra zona vazia automaticamente. | ✅ `api/_focus_map.py` + wiring no `generate_creative` + steering forte de zona (~45%). Provado: troféu em 1 tentativa, prompt neutro, texto não tampa. FALTA: wirar no fluxo do `generate.py` (site) — hoje só no path `generate_creative`. |
| 1.2 | **Banco de foto limpa curado** — puxar foto on-brand marcada por conceito em vez de gerar cru toda hora (fonte do slop). | ⬜ pendente |
| 1.3 | **Rejeição de slop no QA** — detectar/barrar card branco flutuante, texto de IA dentro da foto, número inventado, foto off-brand. | 🟡 parcial (número inventado ✅) |
| 1.4 | **Medir a imagem e adaptar o layout** — aspecto variável + auto-height. | 🟢 feito no tweet; ⬜ estender às outras peças |
| 1.5 | **Provider routing** — Gemini (Nano Banana) p/ pessoa real/específica com referência; gpt-image p/ conceito/objeto. Confirmar `IMAGE_GEN_PROVIDER` na Vercel. | 🟡 parcial |

### 🔄 Fase 2 — Repensar o PARADIGMA
*Mata o "picker de thumbnails iguais e enganosos".*

| # | Tarefa | Status |
|---|---|---|
| 2.1 | **Fluxo concept-first** — escreve a ideia → vê a copy real renderizada em 2–3 composições calibradas → escolhe. | ⬜ pendente |
| 2.2 | **Preview da copy real** do usuário nos estilos candidatos (não thumbnail estático). | ⬜ pendente |
| 2.3 | **Gating por qualidade** — só entra no picker o estilo com creative provado; resto "Em breve". | 🟢 aplicado (LOGO-WALL, YELLOW-OBJETO) |

### ✨ Fase 3 — Consolidar & polir

| # | Tarefa | Status |
|---|---|---|
| 3.1 | **15 → ~7 recipes calibradas** de verdade. | ⬜ pendente |
| 3.2 | **6 modelos Metta faltando** no picker (DARK-CARTA, DARK-OBJETO, LIGHT-TIPO, FOTO-PILL-CASUAL, K-bold-dourado, YELLOW-DRAW). | ⬜ pendente |
| 3.3 | **LOGO-WALL** — trazer logos reais dos clientes (hoje placeholder → "Em breve"). | ⬜ pendente |
| 3.4 | **UX por formato** — esconder subtítulo/corpo no slide-tweet do carrossel (o fix pegou só a peça única). | ⬜ pendente |
| 3.5 | **Tweet Metta (card-mock)** — aplicar aspecto variável de imagem (só o Tiago tem). | ⬜ pendente |

---

## 5. Já resolvido (histórico recente — tudo na `main`)

- **Card Twitter**: sem destaque amarelo, canto real do X, negrito só na palavra,
  avatar = foto de perfil real, bloco centralizado (mata o vazio), multi-parágrafo.
- **Tweet com imagem**: proporção variável + canvas auto-height (print cru).
- **Bloco de Notas iPhone**: fonte de sistema + status bar com ícones reais.
- **o-segredo**: mão inteira, logo real, legibilidade do header.
- **Bug do briefing por voz** (peça saía vazia) — corrigido.
- **Voz do Tiago** (`tese_central` = copy pronta, não descrição) — calibrada.
- **14 previews** do picker atualizados + **bug de acento clipando** (line-height)
  corrigido no motor.
- **Export 2x/retina** (2160px) em vez de 1080.
- **Fotos reais do Tiago** (as 14 enviadas) ligadas no wizard.
- **Número inventado** ("+R$ 8,5 BI") — removido do art director.
- **Carrossel real** (crachá + 65%) recriado pelo motor, provando o banco.

---

## 6. Pendências abertas (resumo priorizado)

**Grandes (raiz):** 1.1 focus map · 1.2 banco de foto limpa · 1.3 rejeição de
slop (resto) · 1.5 confirmar Gemini na Vercel · 2.1/2.2 paradigma concept-first.

**Médias/menores:** 3.4 UX do slide-tweet no carrossel · 3.5 tweet Metta aspecto
variável · 3.2 6 modelos Metta · 3.3 logos LOGO-WALL · afinar clamp de aspecto ·
remover recortes de palco antigos · atualizar board do Monday.

---

## 7. Como acompanhar

- **Este documento** é a fonte de verdade — atualizar o status das tarefas aqui.
- **Sub-planos** detalhados por workstream (ex: `plano-imagem-tweet-variavel.md`).
- **Monday** (board METTA 5.0) espelha as tarefas com prazo/responsável.
- Recomendação de sequência: **Fase 1 primeiro** (1.1 focus map + 1.2 banco de
  foto), porque é o alicerce que faz Fase 2 entregar qualidade de verdade.
