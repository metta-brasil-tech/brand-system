# PLANO — Fidelidade ao modelo (logo · prompt/enquadramento na origem · juiz model-aware)

> Hand-off para executar em chat novo. Auto-contido: inclui diagnóstico, mapa de
> arquivos, mudanças por fase, critérios de aceite e comandos de teste.
> Repo: `~/Documents/brand-system`. Tudo solo (sem o outro Claude).

## Contexto / diagnóstico (o que já se sabe)

Pipeline de criativos Metta/Tiago. 3 camadas de avaliação rodam **depois** do
render: `_vision_qa.py` (peça isolada), `_critic.py` (same-designer vs banco),
`_evaluator.py` (juiz final, nota+veredito). Roteamento de correção é **binário**
(`image_fixable` true→regera foto / false→para) em `_autogen.py:101`.

**Buracos confirmados no código:**

1. **Logo some (DARK-CARTA).** `_blueprint_render.py:153` faz
   `dark = theme in ("dark","yellow")` → escolhe wordmark branca/escura. Mas
   `theme: paper` renderiza `#12201a` (verde-escuro, `_engine.css:59`) — canvas
   **escuro** — e "paper" ficou **de fora** do set → wordmark escura sobre fundo
   escuro = invisível. As duas SVGs existem; é bug de mapa de luminância
   incompleto + front-matter não conferido. Suspeito do mesmo: Tiago `theme: photo`
   (assinatura escura sobre foto possivelmente escura) e FOTO-PILL-CASUAL.

2. **Prompt/enquadramento não puxam a DNA do modelo.** `_art_director.direct`
   (`_art_director.py`) recebe só front-matter (`archetype`, `theme`,
   `image.treatment`, `placement`) + briefing do usuário + knowledge + avatar. A
   **prose** do blueprint (`## Intenção`, `## Estrutura visual`, `## Anti-padrões`)
   **nunca entra no prompt**. Prova: DARK-COLAGEM proíbe "foto humana realista"
   mas o prompt gerado foi "A businessman... in a surreal dark labyrinth, mid-shot
   from chest up" (homem realista — o anti-padrão do modelo). Enquadramento idem:
   `crop_focus` é genérico (face/chest/waist/env), não sabe que esse modelo quer
   colagem conceitual centralizada, não retrato.

3. **Portão deixa FAIL subir.** `_evaluator._guardrail` (`_evaluator.py:132-154`)
   rebaixa SHIP só por `invented_text=yes`, `integrity=broken` ou `critic FAIL`.
   **Não** rebaixa por `vision_qa.verdict=FAIL` de relevância. DARK-COLAGEM (visão
   FAIL, crítico PASS, integrity ok) subiu 8.7 SHIP.

**Já entregue (não refazer):** crop determinístico — `crop_focus` →
`background-position` real (`_blueprint_render.py` `_focal_position`/`_photo`,
`generate.py` render calls, `_engine.css` photo-band `center 30%`) + trava
anti-decapitação/pé no prompt (`generate.py:_art_direction_photo`). Resolve só o
"pé"; é estreito. Este plano ataca a fidelidade ao modelo, que é o problema real.

**Arquivos-chave:**
- `api/_blueprint_render.py` — `_brand_mark`, `_parse_front_matter`, `_photo`, `render`
- `api/_art_director.py` — `direct()` (monta o conceito de imagem)
- `api/generate.py` — lê blueprint, chama art director, monta prompt, render, roda QA
- `api/_evaluator.py` / `api/_critic.py` / `api/_vision_qa.py` — juízes pós-render
- `source/ad-blueprints/metta/*.md`, `tiago/*.md` — blueprints (front-matter + prose)
- `source/ad-blueprints/_engine.css` — themes e archetypes

---

## FASE 1 — Logo/theme: visível em todo modelo (rápido, fundação)

**Objetivo:** nenhuma logo/assinatura invisível. Cor derivada da luminância real
do canvas, não de um set incompleto. + auditoria de consistência dos 34 modelos.

### 1a. Single source of truth da luminância do tema (conserta DARK-CARTA)
Em `api/_blueprint_render.py`, criar:
```python
# Temas de canvas ESCURO → marca clara (branca). Demais → marca escura.
# paper=#12201a é escuro (estava de fora — causava logo invisível no DARK-CARTA).
_DARK_THEMES = {"dark", "yellow", "paper"}          # metta: yellow tem fg escuro,
# (atenção: yellow é claro mas a logo colorida tem símbolo amarelo+wordmark; manter
#  como está hoje — yellow já caía em "dark" no código atual. Validar visualmente.)
def _theme_is_dark(theme: str) -> bool:
    return str(theme).strip().lower() in _DARK_THEMES
```
Trocar em `_brand_mark` (`:153`) `dark = theme in ("dark","yellow")` por
`dark = _theme_is_dark(theme)`. **Tiago:** `theme: photo` é foto (pode ser
escura); decidir — ou tratar "photo" como escuro (assinatura branca) e garantir
scrim, ou adicionar override `brand` no blueprint. Validar nos PNGs Tiago.

> NB: `yellow` hoje já entra em "dark" (wordmark branca sobre amarelo). Se ficar
> ruim visualmente, separar: `yellow` deveria usar wordmark escura. Conferir no PNG
> do YELLOW-DRAW/YELLOW-EDITORIAL antes de fechar.

### 1b. Override explícito por blueprint (escape hatch)
Suportar `params.brand_logo: "light"|"dark"` no front-matter; se presente, vence a
heurística. Útil quando o canvas tem foto e a luminância não é deduzível do theme.

### 1c. Auditoria de consistência dos 34 modelos
Criar `api/_audit_blueprints.py` (script standalone) que, para cada blueprint:
- parseia front-matter + prose;
- **logo:** computa cor da marca (via `_theme_is_dark`) e a luminância do canvas
  (do theme/`_engine.css`); flag se marca e fundo tiverem mesma luminância;
- imprime tabela + total de flags; exit code ≠0 se houver flag (vira teste de CI).
Rodar, revisar os PNGs dos flags (DARK-CARTA, FOTO-PILL-CASUAL, Tiago photo),
corrigir cada um (theme certo ou `brand_logo`).

**Aceite F1:** auditoria sem flags; DARK-CARTA com wordmark branca visível
(re-render e olhar o PNG); nenhum outro modelo regrediu.

---

## FASE 2 — Pré-criação: puxar a DNA do modelo pro prompt + enquadramento

**Objetivo:** o que o blueprint manda/proíbe chega ao prompt de imagem e ao
enquadramento. Conserta o "homem realista" na origem.

### 2a. Extrair a prose do blueprint (hoje só front-matter é lido)
Em `api/_blueprint_render.py` (ou módulo novo `_blueprint_dna.py`), função
`extract_dna(marca, model_id) -> dict` que lê o `.md` e devolve:
```python
{
  "intent": "<## Intenção>",
  "structure": "<## Estrutura visual>",
  "anti_patterns": ["<cada item de ## Anti-padrões>"],
  "image_treatment": fm["image"].get("treatment",""),
  "image_required": fm["image"].get("required"),
  "archetype": fm["archetype"], "theme": ...,
}
```
Parser simples por headings `## `. Best-effort (campos faltando → "").

### 2b. Injetar a DNA no diretor de arte / prompt de imagem
- `_art_director.direct(...)` ganha param `model_dna: dict | None = None`.
- Dentro, ao montar o `image_concept`:
  - **anti_patterns → negativos** no prompt ("NOT a realistic human photo",
    "no cartoon", etc., derivados dos itens).
  - **intent + image_treatment → direção positiva** da cena.
  - **structure → dica de composição/enquadramento** (ex.: "colagem conceitual
    centralizada no topo 50-60%", não "retrato chest-up").
- `generate.py`: chamar `extract_dna(marca, chosen_model_id)` perto de onde já lê
  `bp_fm_full`/`bp_treatment` (~`:467`) e passar `model_dna=` para `_ad_direct`
  (`:543`) **e** para o `_ad_direct2` da regen (`:1018`).
- No builder de prompt (`_art_direction_photo` + base template em
  `engine/brand-knowledge/image-prompts/...` lido em `generate.py:~671`):
  anexar os negativos da DNA ao `negative_prompt` do `ImageGenAdapter.generate`.

### 2c. Enquadramento model-aware
`crop_focus` deixa de ser só face/chest/waist/env. Quando a DNA indica imagem
não-humana (objeto, colagem, cena), o enquadramento segue a `structure` do modelo
(ex.: `environment`/centralizado), e `_focal_position` respeita isso (já trata
`object-center`; estender a lógica para colagem/photo-full conceitual). O diretor
de arte escolhe `crop_focus` informado pela DNA, não por default de retrato.

**Aceite F2:** gerar DARK-COLAGEM e conferir no info.md que o prompt **não** pede
humano realista e **inclui** os anti-padrões como negativos; o enquadramento bate
com a estrutura do modelo. Repetir num modelo de objeto (DARK-OBJETO) e num de
retrato (I-retrato-editorial-pb) — cada um puxa a direção certa.

---

## FASE 3 — Juiz model-aware (confere a peça contra o spec do modelo)

**Objetivo:** o juiz carrega a DNA do modelo e reprova quem não condiz — porque o
foco nem sempre é o rosto; cada modelo tem seu "tem que ter / não pode ter".

### 3a. Passar a DNA aos juízes
`evaluate()` (`_evaluator.py`) e `critique()` (`_critic.py`) recebem `model_dna`.
Em `generate.py`/`_autogen.py` passar `extract_dna(...)` (já carregada na F2).

### 3b. Rubric por modelo (não régua única)
No system prompt do `_evaluator`, injetar a DNA e checar, além das dimensões atuais:
- **marca/logo visível** contra o canvas? (backstop runtime do F1)
- **imagem respeita os anti-padrões** do modelo? (ex.: humano realista em
  DARK-COLAGEM = reprova)
- **layout bate com a `## Estrutura visual`**? (colagem no topo vs full-bleed
  enterrado)
- **enquadramento adequado a ESTE modelo** (objeto/colagem/retrato — não exigir
  rosto onde não cabe)
- **todos os textos legíveis** (a pergunta "dá pra ler tudo?").
Adicionar essas como dimensões/flags no JSON de saída + `fix_class` por falha
(cena/posição/layout/marca/copy) — base do roteamento.

### 3c. Fechar o portão (FAIL não sobe)
Em `_evaluator._guardrail`, adicionar:
```python
if vr.get("verdict") == "FAIL":
    reasons.append("vision-qa reprovou (relevância/integridade)")
    if out.get("verdict") == "SHIP": out["verdict"] = "REVISAR"
```
E rebaixar também por falha de anti-padrão/marca-invisível/layout (as do 3b).

### 3d. Roteamento por classe (substitui o binário)
`_autogen.py` deixa de decidir só por `image_fixable`. Usa `fix_class` do juiz:
- `cena/relevância` → regera imagem (conceito novo)
- `posição/enquadramento` → ajusta crop (já determinístico no F2; só re-render)
- `layout/estrutura` → sinaliza trocar modelo/blueprint (não regera foto)
- `marca` → corrige logo (F1) e re-render
- `copy/texto` → não regera imagem
Manter "melhor tentativa" e dizer quando a regen não melhorou (empate).

**Aceite F3:** DARK-COLAGEM atual (homem realista) → juiz **reprova** por
anti-padrão e **não** sobe como SHIP; um caso de logo invisível → reprovado por
marca; o roteamento manda cada classe pro fix certo (não regera foto pra problema
de layout/posição).

---

## Ordem de execução e flags
1. **F1** (fundação, baixo risco, conserta logo já). 2. **F2** (origem do
   homem-realista). 3. **F3** (juiz + portão + roteamento).
- Flags de custo: `VISION_QA=1` (default on), `CRITIC_COMPARE=1`, `FINAL_EVAL`
  (default off — ligar p/ testar o juiz no pipeline). `VISION_QA_MAX=2`.
- Precisa de `OPENAI_API_KEY` (em `engine/.env`) e Chromium p/ `render_png` em
  testes ponta-a-ponta.

## Comandos de teste
```bash
cd ~/Documents/brand-system
python3 -c "import ast;[ast.parse(open(f).read()) for f in ['api/_blueprint_render.py','api/generate.py','api/_evaluator.py','api/_art_director.py']];print('syntax OK')"
python3 api/_audit_blueprints.py            # F1: auditoria de consistência (0 flags)
# F2/F3 ponta-a-ponta: gerar DARK-COLAGEM / DARK-CARTA / DARK-OBJETO e conferir
#   render_out/.../info.md (prompt sem anti-padrão) + o PNG (logo visível, enquadramento)
```

## Pegadinhas
- Inline `background-position`/estilo vence o `_engine.css` (specificity) — ok.
- `render_html` em `generate.py` despacha p/ v3 (blueprint) ou v2 (template
  estático); `crop_focus`/`model_dna` só valem no v3 (já há `kw.pop`). Não passar
  kwargs novos pro `_render_tpl`.
- `theme: yellow` é claro mas hoje cai em "dark" p/ a logo — validar visualmente
  antes de mudar (pode estar certo por causa do símbolo amarelo).
- Não refazer o crop determinístico (já entregue).
