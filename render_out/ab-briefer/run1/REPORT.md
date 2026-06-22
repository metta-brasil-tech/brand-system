# A/B — Briefer A↔B (Fase 12)

`model=A-headline-foto-dark` · `preset=bw-yellow` · `format=feed` · `rounds=1` · `avatar_segment=varejo-farmacia`

> Imagem é não-determinística — 1 amostra/lado é leitura rápida, não verdade estatística. Pra decidir ligar em prod, rode N≥3/lado e olhe a média.

## Comparativo

| métrica | CONTROLE (off) | TRATAMENTO (on) |
|---|---|---|
| nota avaliador | — (SHIP) | — (SHIP) |
| vision_qa | PASS · Headline protagonista, âncora humana séria, estrutura atende ao modelo; sem anti-padrões. | PASS · Headline é protagonista absoluta, âncora humana séria, estrutura coluna-foto-gradiente-CTA respeitada. |
| qa | PASS | PASS |
| png | control.png | treatment.png |

### CONTROLE — BRIEFER=0
- ok: `True` · run_id: `20260622_153008_191feb`
- qa: `PASS`
- vision_qa: PASS · Headline protagonista, âncora humana séria, estrutura atende ao modelo; sem anti-padrões.
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian man in his mid-40s, warm brown skin, short black hair, clean-shaven, wearing a smart business shirt with sleeves rolled up, standing on the floor of a Brazilian pharmacy. He holds a tablet displaying a sales dashboard, with medicine shelves softly blurred in the background. The lighting is even, typical of retail environments. The man's expression is serious and focused, embodying authority and decisiveness. Subject fully within the frame, positioned in the right 42% of the frame; the left 58% must be clean, softly blurred, EMPTY neutral background with nothing in it. High-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color. Editorial business magazine quality, high detail, without smiling, without stock photo pose, without ring light, without fake teeth-bleached smile, without text or logos in image.
```

### TRATAMENTO — BRIEFER=1
- ok: `True` · run_id: `20260622_153057_461bea`
- qa: `PASS`
- vision_qa: PASS · Headline é protagonista absoluta, âncora humana séria, estrutura coluna-foto-gradiente-CTA respeitada.
- nota avaliador: **— (SHIP)**
- critic: `PASS`

**prompt de imagem usado:**
```
Photograph of a Brazilian businessman in his mid-40s, warm brown skin, short black hair, clean-shaven, wearing a smart business shirt with sleeves rolled up, standing confidently on the floor of a bustling Brazilian pharmacy. He holds a tablet displaying a sales dashboard, embodying authority and decisiveness. The pharmacy shelves and front counter are softly blurred in the background. A subtle yellow Metta logo is visible on the tablet screen. The subject is fully within the frame, positioned in the RIGHT 42% of the frame, with the LEFT 58% showing a clean, softly blurred, EMPTY neutral background. The lighting is even overhead retail light, captured in high-contrast BLACK AND WHITE editorial cinema photography with ONE selective yellow element preserved in full color, deep blacks, sharp contrast, magazine cover quality. The subject's gaze is directed to the left, leading the eye toward the text, without smiling, without stock photo pose, without ring light, without fake teeth-bleached smile, without text or logos in image.
```
**log do briefer:**
- briefer: prompt refinado em 1 rodada(s)
- briefer r1: reprovado — The prompt now specifies the businessman as a decision-maker in a bustling pharmacy environment, incorporating the yellow Metta logo on the tablet to align with brand identity, enhancing the scene's concreteness and relevance to the ICP. | issues=3
