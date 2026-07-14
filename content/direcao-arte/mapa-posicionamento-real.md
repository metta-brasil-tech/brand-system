# Mapa de posicionamento — banco real (medido)

Fonte de verdade de **onde o texto fica** e **quanto ele ocupa** em cada família do
banco criativo real da Metta. Não é "achismo" nem exemplo montado — é **medição das 66
peças reais** (`assets/applications/ads/thumbs/`), peça por peça.

## Como foi medido
Para cada peça: detecção do "texto" por energia de bordas horizontais por linha (Sobel-x),
ignorando a faixa da logo (topo 8,5%). Daí sai, em % da altura do canvas:
- **texto começa** — onde o primeiro bloco de texto forte aparece;
- **bloco (altura)** — quanto o texto ocupa verticalmente;
- **âncora dominante** — topo / meio / rodapé (pelo centroide do texto).

Dado bruto por peça: `render_out/…/mapa-real.json`. Convenção por família: também gravada
em `data/curated-references.json` (`by_family.<F>.posicionamento_real`), pra o motor consumir.

## Convenções medidas (a calibragem-alvo)

| Família | n | Texto começa (%) | Bloco (altura %) | Âncora | Leitura |
|---|---|---|---|---|---|
| **A** — headline+foto | 22 | 8–60 (méd **27**) | 49 | meio | versátil; card em vários pontos |
| **B** — foto topo | 9 | 11–52 (méd **24**) | 54 | **topo** | headline em cima da foto |
| **C** — tipográfica | 4 | 8–24 (méd **16**) | 53 | meio | texto começa alto, é a peça toda |
| **D** — fullbleed overlay | 6 | 8–25 (méd **13**) | 62 | **topo** | texto no topo, bloco grande |
| **DARK** — objeto/colagem | 4 | 18–23 (méd **21**) | 55 | meio | objeto no centro, texto em volta |
| **LIGHT** — surreal claro | 5 | 22–58 (méd **35**) | 41 | meio | texto **mais baixo/centralizado** |
| **YELLOW** — amarelo | 12 | 8–38 (méd **18**) | 62 | meio | **bloco enorme**, texto domina |
| **NEWS** — card notícia | 1 | 41 | 30 | meio | manchete no miolo |
| **OUTROS** (H/I/K) | 3 | 12–39 (méd 29) | 47 | meio | manifesto / convite |

## A regra que sai daqui
**Cada família posiciona diferente — não existe um número único.**
- **D e B** → texto **no topo, alto** (13–24%). É o caso do fullbleed (a babá).
- **LIGHT** → texto **mais pra baixo/centralizado** (35%). O oposto de D.
- **YELLOW** → bloco **enorme** (62%): o texto é o protagonista.
- **C** → começa **bem alto** (16%): tipografia pura.

O motor deve **respeitar a convenção da família da peça**, não aplicar um posicionamento
único. A folga mínima do topo (clearance de 12,4%, ~168px) existe só pra o texto nunca
colar na logo — o resto (âncora + altura do bloco) vem da família, alimentado no diretor
de arte a partir deste mapa.

## Cobertura
- **Famílias:** 66/66 peças mapeadas.
- **Linguagens (L1–L8):** todas taggeadas (43 completadas em 2026-07-13; antes só a família A tinha).
- **Refs quebradas:** 3 `.svg` inexistentes removidas do curated.

_Medido em 2026-07-13 sobre as 66 peças reais. Regenerar o mapa: rodar a medição de
`mapa-real.json` quando o banco real mudar._
