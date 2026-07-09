# A/B — Briefer A↔B (Fase 12)

`model=A-headline-foto-dark` · `preset=bw-yellow` · `format=feed` · `rounds=1` · `avatar_segment=varejo-farmacia`

> Imagem é não-determinística — 1 amostra/lado é leitura rápida, não verdade estatística. Pra decidir ligar em prod, rode N≥3/lado e olhe a média.

## Comparativo

| métrica | CONTROLE (off) | TRATAMENTO (on) |
|---|---|---|
| nota avaliador | — (SHIP) | — (REVISAR) |
| vision_qa | PASS · Intenção de autoridade cumpre; foto âncora séria, headline protagonista, estrutura correta e sem anti-padrões. | PASS · Headline protagonista, âncora humana séria, estrutura respeita o modelo, nenhum anti-padrão detectado. |
| qa | PASS | PASS |
| png | control.png | treatment.png |

### CONTROLE — BRIEFER=0
- ok: `True` · run_id: `20260622_153148_899ae9`
- qa: `PASS`
- vision_qa: PASS · Intenção de autoridade cumpre; foto âncora séria, headline protagonista, estrutura correta e sem anti-padrões.
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian woman with light skin and shoulder-length dark hair, wearing a structured blazer over a blouse, standing next to a Brazilian man with warm brown skin and short black hair, clean-shaven, in a smart business shirt with sleeves rolled up. They are on the floor of a Brazilian pharmacy, discussing a sales dashboard displayed on a tablet. Medicine shelves and the front counter are softly blurred in the background, under even overhead retail lighting. The scene conveys a sense of authority and decision-making, with a focus on the sales dashboard and the pharmacy environment. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. All other elements are monochrome black and white. Cinema editorial grade, deep blacks, sharp contrast, magazine cover quality, subject positioned in the right 42% of the frame, with the left 58% showing softly blurred, clean, EMPTY neutral background with nothing in it, subject's gaze directed to the left, leading the eye toward the text, editorial mid-shot from the chest up, full head in frame with headroom, sharp focus on the subject's eyes, shallow background blur, without smiling stock pose, without cartoon, without 3D render, without anime, without children's book illustration, without ring light, without flash, without harsh lighting, without any text, letters, words, numbers, captions, paragraphs, titles, labels, signage, charts, graphs, watermarks or document text anywhere in the image, without fake teeth-bleached smile, without recortes de sujeito principal, without full color photograph, without multiple color highlights, without colorized look, without sepia tone
```

### TRATAMENTO — BRIEFER=1
- ok: `True` · run_id: `20260622_153227_65a1b1`
- qa: `PASS`
- vision_qa: PASS · Headline protagonista, âncora humana séria, estrutura respeita o modelo, nenhum anti-padrão detectado.
- nota avaliador: **— (REVISAR)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian man in his late 40s, warm brown skin, short black hair, clean-shaven, wearing a smart business shirt with sleeves rolled up, standing confidently on the floor of a Brazilian pharmacy. He is examining a product on a shelf, conveying a sense of determination and control. The background softly blurs medicine shelves and the front counter, under even overhead retail lighting. A subtle yellow Metta logo is visible on a product box in the foreground. The image is desaturated with increased contrast, aligning with the editorial style. Subject positioned in the right 42% of the frame, with the left 58% showing softly blurred, clean, EMPTY neutral background with nothing in it. Subject's gaze directed to the left, leading the eye toward the text. Editorial mid-shot from the chest up, full head in frame with headroom. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. All other elements are monochrome black and white. Cinema editorial grade, deep blacks, sharp contrast, magazine cover quality, high detail, without smiling stock pose, without cartoon, without 3D render look generic, without anime, without children's book illustration, without ring light, without flash, without harsh lighting, without any text, letters, words, numbers, captions, paragraphs, titles, labels, signage, charts, graphs, watermarks or document text anywhere in the image, without fake teeth-bleached smile, without recortes de sujeito principal, without full color photograph, without multiple color highlights, without colorized look, without sepia tone
```
**log do briefer:**
- briefer: prompt refinado em 1 rodada(s)
- briefer r1: reprovado — The prompt was refined to specify the male persona from the ICP, include a concrete action (examining a product), and incorporate the yellow Metta logo on a product box to align with brand identity. | issues=3
