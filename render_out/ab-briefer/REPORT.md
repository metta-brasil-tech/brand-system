# A/B — Briefer A↔B (Fase 12)

`model=A-headline-foto-dark` · `preset=bw-yellow` · `format=feed` · `rounds=1` · `avatar_segment=varejo-farmacia`

> Imagem é não-determinística — 1 amostra/lado é leitura rápida, não verdade estatística. Pra decidir ligar em prod, rode N≥3/lado e olhe a média.

## Comparativo

| métrica | CONTROLE (off) | TRATAMENTO (on) |
|---|---|---|
| nota avaliador | — (SHIP) | — (REVISAR) |
| vision_qa | PASS · Imagem transmite autoridade direta, headline protagonista, âncora humana séria, estrutura e contraste corretos. | PASS · Headline protagonista, âncora humana séria, estrutura e hierarquia corretas. |
| qa | PASS | PASS |
| png | control.png | treatment.png |

### CONTROLE — BRIEFER=0
- ok: `True` · run_id: `20260622_124535_7bbffd`
- qa: `PASS`
- vision_qa: PASS · Imagem transmite autoridade direta, headline protagonista, âncora humana séria, estrutura e contraste corretos.
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian woman in her early 40s, light skin, shoulder-length dark hair, wearing a structured blazer over a blouse, standing confidently on the floor of a pharmacy, holding a tablet displaying a sales dashboard, with medicine shelves and the front counter softly blurred behind her. The lighting is even, typical of a retail environment, conveying authority and professionalism. Subject positioned in the right 42% of the frame, with the left 58% showing clean, softly blurred, EMPTY neutral background. Subject's gaze directed to the left, leading the eye toward the text. Editorial mid-shot from the chest up, full head in frame with headroom. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. Deep blacks, sharp contrast, magazine cover quality, high detail, without smiling stock pose, without cartoon, without 3D render, without anime, without children's book illustration, without ring light, without flash, without harsh lighting, without any text, letters, words, numbers, captions, paragraphs, titles, labels, signage, charts, graphs, watermarks or document text anywhere in the image, without fake teeth-bleached smile, without recortes de sujeito principal.
```

### TRATAMENTO — BRIEFER=1
- ok: `True` · run_id: `20260622_124620_9a0a17`
- qa: `PASS`
- vision_qa: PASS · Headline protagonista, âncora humana séria, estrutura e hierarquia corretas.
- nota avaliador: **— (REVISAR)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian man in his late 40s, warm brown skin, short black hair, clean-shaven, wearing a smart business shirt with sleeves rolled up, standing confidently on the floor of a Brazilian pharmacy. He embodies professionalism and authority, with his gaze directed to the left, leading the eye toward the text. The background softly blurs medicine shelves and the front counter, under even overhead retail lighting. A yellow Metta-branded shopping bag is held in his left hand, adding a pop of color. Subject positioned in the right 42% of the frame, with the left 58% showing softly blurred, clean, EMPTY neutral background with nothing in it. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. Deep blacks, sharp contrast, magazine cover quality, high detail, without smiling stock pose, without cartoon, without 3D render, without text or logos in image, without fake teeth-bleached smile, without suffering or despair.
```
**log do briefer:**
- briefer: prompt refinado em 1 rodada(s)
- briefer r1: reprovado — The prompt now specifies a Brazilian man as the subject, aligning with the ICP, and introduces a yellow Metta-branded shopping bag to incorporate the brand's color, enhancing the scene's concreteness and brand identity. | issues=3
