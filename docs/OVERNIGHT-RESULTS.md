# Trabalho noturno — qualidade de criativo (Fase 7 reference-aware)

Autônomo enquanto o Nathan dorme. Foco: deixar os criativos **ainda melhores** que o
baseline (a geração passa a OLHAR a referência campeã, não só ler texto). Regras que me
impus: só meu lane (módulos novos `_ref_vision`/experimentos), **sem git**, runs
**isolados** (não colido com o outro Claude na Fase 4→5→6), custo **limitado à agenda**.

Régua: golden set. **Baseline (pré): SHIP 33%, nota 8.19** (`docs/IMPROVEMENT-LEDGER.md`).

## Agenda (vou marcando conforme termina)
- [x] **1. A/B reference-aware** → resultado **NEGATIVO** (não implantado). Ver abaixo.
- [~] **2. Pivot:** reference-aware como override regrediu → troquei por **auto-melhoria
      (autogen)**, que é o lever JÁ validado. Rodando o "best of" com ele.
- [ ] **3. "Best of"** — melhores briefs em qualidade média + autogen → em `render_out/best-of/`.
- [ ] **4. Relatório final** + parar.

## Progresso / resultados

### 1. A/B reference-aware — ❌ NÃO implantado (regrediu)
Testei "o pensador olha o PNG campeão e o craft entra como direção de prioridade máxima".
| brief | baseline | reference-aware | Δ |
|---|---|---|---|
| metta-farmacia | 7.8 | 8.2 | **+0.40** |
| metta-pet | 8.4 (SHIP) | 6.7 (REVISAR) | **-1.70** |
| metta-otica | 8.9 (SHIP) | 8.6 | -0.30 |
| **média** | | | **-0.53** 🔴 |

**Diagnóstico:** injetar o craft via `briefing_image_text` (prioridade máxima) **atropela
o conceito bom do diretor de arte** — quando o baseline já era SHIP, o override piorou.
**Decisão (regra de ouro do ledger):** NÃO implantar como está. **Recomendação:** a
referência deve entrar como **CONTEXTO pro diretor de arte** (ele lidera, informado pela
ref), não como override — mas isso mexe no `_art_director` (lane do outro Claude), fica
pra depois. Output do teste: `render_out/refvision-ab/`.

### Tiers de qualidade — o FUNIL (low → medium → high)
Não é "sempre medium". É um funil de custo:
- **low** = exploração + loop de auto-melhoria (muitas gerações; pixel cru basta pra
  julgar cena/composição). Default do loop e dos testes.
- **medium** = pré-final / "best of" (já filtrou os bons). Foi o tier deste best-of.
- **high** = SÓ o(s) vencedor(es) que vão publicar. Nunca se paga high por descarte.

Mecanismo: `IMAGE_QUALITY` por run. Pro high ser fiel ao aprovado (gpt-image é
estocástico), trava-se a direção de cena do decision-log do vencedor via
`briefing_image_text` e regenera só a imagem em high.

### 2-3. "Best of" via auto-melhoria (autogen, medium)
Resultados (autogen, qualidade média) — em `render_out/best-of/<id>/final.png`:
- metta-otica → **SHIP 9.2** (1 tentativa)
- metta-inflexao-1 → **SHIP 9.0** (1 tentativa)
- metta-inflexao-2 → REVISAR 8.0 (2 tentativas)
- metta-pet → REVISAR 7.7 (2 tentativas)
- tiago-noir / tiago-surreal → _(fechando)_

### 4. Pass HIGH nos vencedores (o topo do funil)
Após o best-of: pego os SHIP de nota mais alta (≥8.5) e regenero a imagem em
**qualidade high**, travando a direção aprovada → ficam em `final-hq.png`. É a prova
do funil low→medium→high e os criativos prontos pra publicar.
Best-of (medium): **otica 9.2, inflexao-1 9.0, tiago-surreal 9.0** (SHIP) → esses 3 vão pro HIGH.

---

## Direções novas do Nathan (madrugada) — pra executar
1. **"Trazer TUDO do plugin"** → executar a lista inteira de `PLUGIN-INVENTARIO.md`
   (carrossel C1–C8, briefer A↔B do prompt de imagem, safe-zones, 2 variantes
   divergentes, self-inspection, whitelist interativa, avisos de catálogo).
2. **Carrossel é prioridade** — ele gostou MUITO da panorâmica ("2 cenas que se
   completam", imagem larga fatiada em 2 com fundo contínuo) e quer **fazer mais**.
   ⚠️ Achado: a lógica de carrossel/panorâmica vive na **UI** (`embed/criar.html`,
   modo multi-slide `slides[]`), NÃO no core Python. Então trazer C1–C8 + estender a
   panorâmica exige estudar essa camada — **prioridade nº1 da manhã**, com cuidado
   (feature que ele ama; não fazer às cegas).
3. **No SITE, tudo em ALTA qualidade.** Implicação importante: high (~35-50s) + cold
   start estoura o **timeout de 60s do Vercel Hobby**. Pra "site = high" funcionar:
   (a) geração **assíncrona/background** (gera e entrega depois), OU (b) plano Vercel
   maior, OU (c) **funil interno por request**: itera em low/medium e entrega o
   vencedor em high. Recomendo (c) quando houver auto-melhoria, senão (a). É decisão
   de infra a confirmar com o Nathan.

## Plano da manhã (ordenado)
1. **Carrossel** (estudar `embed/criar.html` → C1–C8 + estender panorâmica + fazer mais).
2. **Site = high** (decidir async vs plano vs funil-interno).
3. Resto do `PLUGIN-INVENTARIO.md` (briefer A↔B, safe-zones, variantes divergentes).
