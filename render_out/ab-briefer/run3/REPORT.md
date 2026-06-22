# A/B — Briefer A↔B (Fase 12)

`model=A-headline-foto-dark` · `preset=bw-yellow` · `format=feed` · `rounds=1` · `avatar_segment=varejo-farmacia`

> Imagem é não-determinística — 1 amostra/lado é leitura rápida, não verdade estatística. Pra decidir ligar em prod, rode N≥3/lado e olhe a média.

## Comparativo

| métrica | CONTROLE (off) | TRATAMENTO (on) |
|---|---|---|
| nota avaliador | — (SHIP) | — (SHIP) |
| vision_qa | PASS · Headline é protagonista, âncora humana séria, layout cumpre intenção do modelo. | PASS · A peça sustenta a intenção de autoridade direta, com headline protagonista, âncora humana séria e estrutura fiel ao mode |
| qa | PASS | PASS |
| png | control.png | treatment.png |

### CONTROLE — BRIEFER=0
- ok: `True` · run_id: `20260622_153319_3e4294`
- qa: `PASS`
- vision_qa: PASS · Headline é protagonista, âncora humana séria, layout cumpre intenção do modelo.
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian woman in her early 50s, light skin, shoulder-length dark hair, wearing a structured blazer over a blouse, standing confidently on a pharmacy floor, holding a tablet displaying a sales dashboard, serious expression conveying authority and decisiveness, subject fully within the frame, positioned in the right 42% of the frame, with the left 58% showing softly blurred, clean, EMPTY neutral background, medicine shelves and the front counter softly blurred behind her, even overhead retail light, high-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color, deep blacks, sharp contrast, magazine cover quality, high detail, without smiling, without generic office stock photo, without vague thesis without anchor, without full color photograph, without multiple color highlights, without colorized look, without sepia tone, without text or logos in image
```

### TRATAMENTO — BRIEFER=1
- ok: `True` · run_id: `20260622_153357_cd8db7`
- qa: `PASS`
- vision_qa: PASS · A peça sustenta a intenção de autoridade direta, com headline protagonista, âncora humana séria e estrutura fiel ao mode
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian woman in her mid-40s, light skin, shoulder-length dark hair, wearing a structured blazer over a blouse, standing confidently on the floor of a Brazilian pharmacy. She embodies professionalism and authority, with her gaze directed to the left, leading the eye toward the text. The subject is positioned in the right 42% of the frame, with the left 58% showing a clean, softly blurred background featuring medicine shelves and a front counter. The lighting is even, typical of retail environments, enhancing the serious and direct tone of the scene. A single yellow Metta-branded shopping bag is placed on the counter, adding a touch of color. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. Editorial business magazine quality, high detail, without smiling, without stock photo pose, without ring light, without fake teeth-bleached smile, without text or logos in image, without full color photograph, without multiple color highlights, without colorized look, without sepia tone.
```
**log do briefer:**
- briefer: prompt refinado em 1 rodada(s)
- briefer r1: reprovado — Added a yellow Metta-branded shopping bag to incorporate the brand's color and anchored the scene in a concrete pharmacy environment with visible medicine shelves and a counter. | issues=3
