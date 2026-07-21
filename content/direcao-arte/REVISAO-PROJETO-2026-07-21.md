# 🔍 Revisão do projeto inteiro — o que está acontecendo (2026-07-21)

> Pedido do Nathan: *"revisar o projeto inteiro e ver o que tá acontecendo, sem
> perder o que já fizemos"* — porque a thumb engana (o preview promete uma peça e
> a geração final sai diferente), e ele sentiu que **conhecimento se perdeu**.
> **Veredito curto: nada se perdeu. O problema é 1 desalinhamento específico entre
> o PREVIEW e a GERAÇÃO FINAL.** Detalhe abaixo. HEAD `1862c09`.

---

## 1. Estado do git — respira, nada em risco

- **Local `main` == remoto `origin/main`: 0 atrás, 0 à frente.** Tudo sincronizado.
- Único "não commitado": `render_out/` (saídas de teste, nem entram no deploy) e
  imagens de exemplo soltas. **Nenhum código seu está solto ou em risco.**
- Submódulo `engine` no ponteiro certo (`5b1d3c1`).

---

## 2. O conhecimento NÃO se perdeu — auditoria

Todas as melhorias que a gente fez estão **intactas no caminho FINAL de geração**
(`api/generate.py` + `api/_blueprint_render.py`). Confirmado por auditoria:

| Melhoria | Onde | Status |
|---|---|---|
| **Focus-map** (texto foge do sujeito) | `generate.py` (`focus_anchor`, 5×) | ✅ intacto + reforçado hoje (`f95050f`) |
| **A regra vence o blueprint** | `generate.py` (`f95050f`) | ✅ novo, hoje |
| **Direção do user vence o blueprint** (incl. "sem pessoa") | `generate.py` (`66b4dd9`, `user_briefing_present` 5×) | ✅ intacto, provado em prod |
| **Guarda-anti-cabeça** | `generate.py` (2×) | ✅ intacto |
| **Roteamento Gemini/gpt-image** | `generate.py` (`generate_via_route`) | ✅ intacto |
| **Logo Metta + assinatura Tiago** | `_blueprint_render.py` (`_metta_symbol`, `_BRAND_DIR`, `assinatura` 21×) | ✅ intacto |
| **Avatar real do Tiago** | `_blueprint_render.py` (`_tiago_avatar`) | ✅ intacto |
| **Modelos expostos + colapso Tiago** | `criar.html` (`carouselOnly`) | ✅ intacto |

**"Antes era tudo blueprint; agora melhoramos colocações, logos, posicionamento" —
sim, e tudo isso está no ar, no caminho de geração final.** Não sumiu.

---

## 3. Onde a thumb engana — a causa raiz (precisa)

O preview do picker (`/api/preview`) e a geração final (`/api/generate`) usam o
**MESMO motor de layout** (`_blueprint_render.render`). A diferença é o que cada
um alimenta:

| | Preview do card (concept-first) | Geração final (o que sai) |
|---|---|---|
| Foto | **nenhuma** (caixa vazia) | foto gerada (Gemini/gpt-image) |
| Âncora do texto | **default fixo do blueprint** | **focus-map RE-MEDE na foto** e re-ancora |
| Art-director | **não roda** | roda (pode recompor a headline, crop, ênfase) |
| Vision-QA | não roda | roda (pode regenerar) |

**Consequência:**
- **Estilos SÓ-TEXTO** (Tipografia pura, tweets, notas): preview ≈ final. A foto
  não existe, o layout é o mesmo → **fiel**. ✅
- **Estilos COM IMAGEM** (Objeto, Foto-fullbleed, etc.): preview ≠ final. A foto
  muda tudo — o focus-map re-posiciona o texto conforme a foto, o art-director
  pode recompor. O preview mostra **o layout SEM foto, na posição default do
  blueprint**. ❌ **É AQUI que a thumb engana.**

### O paradoxo (por que "parece que se perdeu conhecimento")
As melhorias de composição (focus-map, art-director) moram no **caminho final**. O
preview é um render **leve, sem foto**, que **não roda essas melhorias** (o
focus-map precisa de uma foto pra medir). Então:

> **Quanto MAIS a gente melhora a composição final, MAIS o preview diverge dela.**
> O meu fix de hoje (a regra vence o blueprint) — que é bom pro resultado —
> **aumentou** a distância entre o preview (posição do blueprint) e o final
> (posição medida na foto).

Não é conhecimento perdido. São **dois caminhos que se afastaram**: o preview ficou
"burro de propósito" (rápido/grátis) e o final ficou esperto.

### O agravante: a UI promete o que não entrega
Em `criar.html` o texto do passo dizia: *"a foto é gerada depois — **o layout já é
fiel**"*. Pra estilo com imagem isso é **falso** (o layout final re-posiciona). Já
corrigi essa frase (ver §6).

---

## 4. Mapa de saúde do projeto

| Componente | Estado |
|---|---|
| Git / sincronia | 🟢 sincronizado, nada em risco |
| Motor de render (layout, logo, assinatura) | 🟢 sólido |
| Focus-map / regra vence blueprint | 🟢 no ar (`f95050f`) |
| Direção do user vence blueprint | 🟢 no ar (`66b4dd9`) |
| Wizard concept-first (copy→estilo) | 🟢 no ar |
| Preview de estilo SÓ-TEXTO | 🟢 fiel ao final |
| **Preview de estilo COM IMAGEM** | 🔴 **não prediz o final (thumb engana)** |
| Fonte da imagem (Gemini vs gpt-image) | 🟡 quase tudo gpt-image (banco vazio, item 1.2) |
| Cota OpenAI | 🔴 estourada (cérebro + fotos caídos até recarregar billing) |
| Editar imagem no resultado | 🟡 não existe (só edita texto/posição) |

---

## 5. Como consertar a "thumb engana" — SEM perder nada (opções ranqueadas)

1. **🟢 Honestidade primeiro (feito hoje, custo zero):** a UI parou de prometer
   "layout já é fiel". Agora diz que, no estilo com imagem, o preview é do
   **layout+copy**, e a **foto e o enquadramento final** vêm ao gerar (o texto se
   ajusta à foto). No estilo só-texto, é fiel. Isso remove a mentira imediata.
2. **🟡 Foto representativa no preview (precisa do banco 1.2):** em vez da caixa
   vazia, mostrar uma foto curada da família no card — aí o preview PARECE o final.
   Depende de montar o banco de referência.
3. **🟡 Gerar a foto real ao ESCOLHER o estilo** (não só no fim) — o preview vira
   real. Mais caro (1 geração por estilo visto), mas mata a divergência.
4. **🟢 Resultado = editor completo (o jogo longo):** aceitar que o preview é
   aproximado e deixar o RESULTADO 100% editável (hoje edita copy e posição; falta
   editar/regenerar a IMAGEM). Aí a divergência do preview importa pouco, porque
   você conserta tudo no fim.

**Recomendação:** (1) já está feito. Depois **(4) editor completo** + **(2) banco
de referência** juntos resolvem de vez — o preview fica honesto E o final fica bom
E dá pra ajustar. Nada disso apaga o que já foi feito; tudo soma.

---

## 6. O que eu já mudei nesta revisão

- **Frase falsa da UI corrigida** — para de prometer "o layout já é fiel" nos
  estilos com imagem; explica que a foto e o enquadramento final vêm ao gerar.
- (Auditoria acima documentada; git confirmado sincronizado.)

## 7. Decisões pra você (e pra IA revisora)

1. Seguir pro **editor completo no resultado** (opção 4) — é o que casa com o "não
   tem como editar depois?" que você levantou antes?
2. Priorizar o **banco de referência (1.2)** — mata "todas iguais" E faz o preview
   com imagem parecer o final.
3. Recarregar o **billing da OpenAI** — sem isso a geração no site fica degradada
   (cérebro + fotos usam OpenAI, não Gemini como parecia).

*Fim. Retrato em `1862c09`. Se algo divergir do código, o código vence.*
