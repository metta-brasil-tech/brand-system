---
id: TIAGO-TWITTER-CARD-IMAGE
display_name: "Carrossel mock-Twitter com foto — perfil Tiago Alves"
marca: tiago
archetype: tiago-twitter
params: { theme: white, mock: twitter-x, ring: yellow, text: sentence-case }
slots: [headline, subhead, body, cta]
image: { required: true, treatment: "foto contextual embed radius 28px na base do tweet — objeto, cena, screenshot que ilustra o tweet (variant cover)", prompt_ref: "image-prompts/tiago/style-twitter-card.md" }
formato_nativo: [feed]
dna_ref: "design/banco-tiago-conteudo.md#§1"
status: ativo
---

# TIAGO-TWITTER-CARD-IMAGE · mock tweet editorial com foto embed

## Intenção
Mesmo mock de tweet do perfil Tiago Alves (`TIAGO-TWITTER-CARD`), variant **cover**: termina
com uma foto/imagem embed (radius 28px) na base do card, ancorando ou ilustrando o tweet —
igual ao media embed nativo do X/Twitter. Reusa o archetype `tiago-twitter`; a única diferença
é que aqui a imagem é obrigatória.

## Estrutura visual
Idêntica ao `TIAGO-TWITTER-CARD` (header mock fixo + headline/body Inter), mas com o bloco de
texto mais conciso pra abrir espaço pra foto embed que ocupa o restante do canvas.

## Quando brilha
Mesmos casos do `TIAGO-TWITTER-CARD`, quando o tweet precisa de uma foto/cena/screenshot que
ancore a mensagem (ex: print de dashboard, foto de reunião, objeto referenciado no texto).

## Anti-padrões
Os mesmos do `TIAGO-TWITTER-CARD`, mais: foto genérica que não ilustra o tweet (ver QA por
visão — relevância).

## Direção de copy
- **headline** (≤140ch, ≤3 linhas, sentence case): tweet hook — mais curto que a variante
  text-only pra deixar espaço pra foto.
- **body** (opcional, ≤200ch): só se sobrar espaço; priorize headline curta + foto forte.
