#!/usr/bin/env node
/* ============================================================
   Reescreve data/photo-index.json com as 21 fotos aprovadas
   - Mapeia cada foto pra um arquétipo existente
   - Gera prompt profissional em inglês (estilo nano-banana / gpt-image-1)
   - Atualiza counts dos arquétipos
============================================================ */
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';

const ROOT = resolve(import.meta.dirname, '..');
const INDEX_PATH = join(ROOT, 'data', 'photo-index.json');

const PHOTOS = [
  // ===== ESCRITÓRIO =====
  {
    id: 'esc-001',
    archetype: 'sala-reuniao-vazia',
    tags: { mood: 'composto', composition: 'wide', subject: 'sala-vazia', lighting: 'natural-blinds' },
    prompt: 'Editorial wide-angle photograph of an empty mid-century brazilian boardroom at golden hour. Long oak conference table in foreground with linear shadow patterns from venetian blinds slanting across the surface. Six leather executive chairs (Eames-style) arranged around the table, partially silhouetted. Far wall: floor-to-ceiling windows revealing a brick-and-glass office building in soft natural daylight. Linear ceiling LED tubes overhead, parallel to table. Composition: low angle, deliberate depth, deep negative space, no people. Palette: deep walnut wood, dark slate blue, warm cream walls, single restrained yellow tone in window reflection. 35mm equivalent, f/4, natural light only — no fill. Mid contrast, subtle film grain, no HDR. Mood: prepared stage, decision space about to be inhabited. Aspect 16:9.'
  },
  {
    id: 'esc-002',
    archetype: 'home-office',
    tags: { mood: 'introspectivo', composition: 'close-up', subject: 'maos-laptop', lighting: 'natural-soft' },
    prompt: 'Editorial close-up of a brazilian professional\'s hands typing on a silver laptop, photographed from over-the-shoulder behind. Hands wear a single stack of thin gold bracelets on the right wrist. Wearing a textured mustard-yellow knit sweater, the only intentional color in the frame. Surface: solid dark walnut desk, with a hardbound dark green book partially visible left. Soft directional window light from camera-right, warm afternoon tone. 50mm equivalent, f/2.0, focus locked on the typing hand, sweater texture rendered in soft falloff. Palette: walnut, mustard yellow accent (Metta yellow #FFBE18 family), deep neutral background. Mid contrast, subtle film grain. Mood: quiet focus, intentional craft. Aspect 3:2.'
  },
  {
    id: 'esc-003',
    archetype: 'home-office',
    tags: { mood: 'analitico', composition: 'medium-flat', subject: 'workspace-objeto', lighting: 'natural-lateral' },
    prompt: 'Editorial flat-lay-style photograph of a focused brazilian workspace at mid-morning. Open silver MacBook center, white ceramic coffee cup steaming on the left, leather-bound notebook with rolled paper note clipped to it on the right, smartphone face-down at the edge. All resting on a worn dark walnut desk surface. Behind, a soft-focus dark window frame and concrete wall. 35mm equivalent, f/3.5, slightly elevated angle. Palette: walnut wood, off-white ceramic, charcoal phone, cream paper — no aggressive accent colors. Mid contrast, subtle film grain. Mood: ready-to-think, before-the-meeting calm. Aspect 3:2.'
  },
  {
    id: 'esc-004',
    archetype: 'escritorio-moderno-interior',
    tags: { mood: 'organizado', composition: 'vertical-portrait', subject: 'home-office-completo', lighting: 'natural-traseira' },
    prompt: 'Editorial vertical photograph of a complete designer home office workstation. Long blonde-oak desk against a tall window letting in soft daylight; potted dracaena and small plants arranged left, large iMac monitor center-back, MacBook open in front, magazines and a small camera scattered around mouse and notebook. Dark glossy floor reflecting window light below. 35mm equivalent, f/4, slightly oblique angle to show full desk depth. Palette: blonde oak, white walls, charcoal screens, single touch of greenery, no decorative color. Mid contrast, subtle grain. Mood: organized creative practice. Aspect 4:5.'
  },
  {
    id: 'esc-005',
    archetype: 'time-colaborando-laptops',
    tags: { mood: 'colaborativo', composition: 'over-shoulder', subject: 'dupla-laptop', lighting: 'natural-ambiente' },
    prompt: 'Editorial scene of two brazilian professionals collaborating around a black-glass conference table. Foreground: a man in a light blue chambray shirt with an Apple Watch points his index finger directly at the screen of an open MacBook Air, mid-explanation. His colleague (red-and-black plaid shirt, hands clasped) sits across, listening with a second laptop closed in front. A white iPhone rests on the table edge. Soft natural ambient light from above, no harsh shadows. 50mm equivalent, f/2.8, focus on the pointing hand and screen edge. Palette: black glass surface, charcoal aluminum laptops, chambray blue, plaid texture. Mid contrast, subtle grain. Mood: explaining the data, not selling — quiet pedagogy. Aspect 3:4.'
  },
  {
    id: 'esc-006',
    archetype: 'mockup-papelaria-madeira',
    tags: { mood: 'preparado', composition: 'close-up-flat', subject: 'objetos-mesa', lighting: 'natural-suave' },
    prompt: 'Editorial close-up flat composition on a rich walnut desk surface. Apple Magic Keyboard placed top-right, bound notebook bottom-left with a turquoise post-it note clipped to the page edge, blue ballpoint pen resting diagonally across. Soft directional light from upper-left, no harsh shadows. 50mm equivalent, f/2.2, ultra-shallow focus on the post-it edge with the keyboard going slightly soft. Palette: deep walnut wood, off-white keyboard, single turquoise accent. Mid contrast, fine film grain. Mood: ready-to-write, before-the-decision quiet. Aspect 3:2.'
  },

  // ===== PESSOAS =====
  {
    id: 'pes-001',
    archetype: 'mentoria-1-on-1',
    tags: { mood: 'didatico', composition: 'medium', subject: 'mentor-mentorada', lighting: 'natural-direcional' },
    prompt: 'Editorial scene of a 1-on-1 mentoring moment in a minimal brazilian office. A man (40s, grey-flecked beard, glasses, beige cardigan over dark t-shirt) stands beside a seated woman (30s, blonde shoulder-length hair, beige overshirt over cream tee), both looking together at her iMac screen. He points at the screen with his right hand, mid-explanation; she follows the gesture, hand on keyboard. On the desk: blush-pink notebook, white round mouse, pair of round eyeglasses. Quiet directional light from camera-right; the rest of the room recedes into soft warm shadow. 50mm equivalent, f/2.8, focus split between his pointing hand and her screen-eye line. Palette: warm beige knits, blonde wood desk, charcoal iMac, single muted blush accent. Mid contrast, subtle film grain. Mood: honest counsel — no smiles for the camera, only for the work. Aspect 3:2.'
  },
  {
    id: 'pes-002',
    archetype: 'retrato-individual-confiante',
    tags: { mood: 'confiante', composition: 'medium-close', subject: 'executivo-individual', lighting: 'natural-blue-hour' },
    prompt: 'Editorial portrait of a brazilian businessman (35-45) photographed at urban dusk. Light camel-brown V-neck sweater layered over a sky-blue button-up, arms crossed across chest, head turned slightly camera-left, soft confident half-smile, eyes locked just past lens. Background: out-of-focus modern building facade with warm sodium-yellow ambient lights from inside, deep blue evening sky. 85mm equivalent, f/2.0, sharp on eyes, background dissolved into bokeh. Palette: camel knit, dusty blue shirt, warm sodium accents in background. Mid contrast, subtle film grain. Mood: settled authority, no theatrics. Aspect 3:2.'
  },
  {
    id: 'pes-003',
    archetype: 'time-celebrando-resultado',
    tags: { mood: 'celebrativo', composition: 'group-tight', subject: 'time-evento', lighting: 'evento-misto' },
    prompt: 'Editorial group portrait of eight diverse brazilian professionals (mixed gender, ethnicities, ages 28-55) clustered shoulder-to-shoulder for a candid team photo at a corporate event. Each wears a dark blue conference lanyard over neutral business attire (charcoal blazers, white shirts, beige jackets). All visibly happy — natural laughter and smiles, looking toward camera but unposed. Behind them: soft-focus modern conference space with warm interior lights and parking visible through far window. Mixed natural and event lighting, soft and even on faces. 35mm equivalent, f/4, group sharp, background dissolved. Palette: charcoal/beige professional wear, dark navy lanyards, warm-cool background mix. Mid contrast, subtle grain. Mood: real cohesion, not staged stock-photo cheer. Aspect 3:2.'
  },
  {
    id: 'pes-004',
    archetype: 'aperto-de-maos-fechamento',
    tags: { mood: 'fechamento', composition: 'medium-tight', subject: 'trio-contrato', lighting: 'natural-clara' },
    prompt: 'Editorial scene of three brazilian professionals reviewing a printed proposal together in a modern showroom. Center: a woman (30s, brunette, light grey button-up) signs a clipboard, focused. Left: a man in a dark grey polo shirt observes the document, half-smiling. Right: a man in a navy pinstripe suit and patterned tie holds the clipboard steady, smiling at the woman. All three lean toward the document with shared attention. Bright daylight from large window behind, evenly soft on faces. 50mm equivalent, f/2.8, focus on the document edge and the woman\'s hand mid-signature. Palette: charcoal grey, navy, white shirt, no decorative color. Mid contrast, fine grain. Mood: closing alignment, mutual conviction — never theatrical. Aspect 3:2.'
  },
  {
    id: 'pes-005',
    archetype: 'businessman-thinking-laptop',
    tags: { mood: 'multitask', composition: 'medium', subject: 'individual-trabalhando', lighting: 'natural-cafe' },
    prompt: 'Editorial scene of a brazilian black professional (30-40, short hair, well-trimmed beard) seated at a wooden cafe table, taking a phone call on his right ear while writing notes in an open leather notebook with his left hand. Wears a navy-blue polka-dot button-up shirt. Open dark grey laptop to his right, partially visible. Soft natural side-light from a tall window behind, branches softly visible outside. Genuine half-smile while listening. 50mm equivalent, f/2.4, focus on his eyes and the writing hand. Palette: navy polka-dot shirt, warm walnut wood table, charcoal laptop, neutral ambient. Mid contrast, subtle grain. Mood: simultaneous presence — listening and capturing at once. Aspect 3:2.'
  },
  {
    id: 'pes-006',
    archetype: 'retrato-individual-confiante',
    tags: { mood: 'genuino', composition: 'medium-close', subject: 'retrato-feminino', lighting: 'natural-janela' },
    prompt: 'Editorial portrait of a brazilian afro-latina woman (28-35, shoulder-length curly dark hair) in a relaxed cream-colored silk blouse with a delicate gold pendant necklace, standing near a tall office window. Genuine open laughter — eyes squinted slightly, white teeth showing, no posed smile. Soft natural daylight from camera-right window, background recedes into cool grey office space with subtle furniture silhouettes. 85mm equivalent, f/2.2, sharp on eyes, background dissolved. Palette: cream silk, soft cool grey background, warm skin tone, single gold accent. Mid contrast, fine film grain. Mood: candid joy mid-conversation, not staged. Aspect 16:9.'
  },
  {
    id: 'pes-007',
    archetype: 'time-colaborando-laptops',
    tags: { mood: 'concentrado', composition: 'medium-vertical', subject: 'dupla-mentor-mentorada', lighting: 'natural-janela' },
    prompt: 'Editorial vertical photograph of two young brazilian professionals working together at a single computer screen near a tall office window. The man (left, 28-35, light-blue chambray shirt, holds a metal pen, gentle focused expression) sits closer to camera; the woman (right, dark curly hair pulled back, white blouse) leans in from the right side, observing the screen, her hand resting near the keyboard. Bright soft window light from behind, urban building visible outside. Forest-green binders stacked at desk edge in foreground. 50mm equivalent, f/2.8, focus on his eye line and the screen edge. Palette: chambray blue, white, forest green binders, neutral office. Mid contrast, subtle grain. Mood: shared concentration, peer learning, no posed gestures. Aspect 4:5.'
  },
  {
    id: 'pes-008',
    archetype: 'analise-dados-tela',
    tags: { mood: 'analitico', composition: 'over-shoulder-vertical', subject: 'duas-mulheres-documento', lighting: 'natural-ambiente' },
    prompt: 'Editorial over-the-shoulder photograph of two brazilian women reviewing a printed planning grid on a single sheet of paper. Foreground: a woman with shoulder-length blonde hair (back-of-head visible), black sleeveless top, holds the sheet at angle for the other to read. Second woman across the table (out of focus, dark hair, black blouse, visible tattoo on inner forearm) studies the document. A silver MacBook half-open in foreground, dark stone-textured table surface. Soft directional natural light from camera-left. 50mm equivalent, f/2.8, focus locked on the document grid lines. Palette: muted neutrals, black tops, warm skin tones, slate stone surface. Mid contrast, fine grain. Mood: analyzing the plan together, no eye contact, full attention on data. Aspect 4:5.'
  },
  {
    id: 'pes-009',
    archetype: 'mentoria-1-on-1',
    tags: { mood: 'cordial', composition: 'medium', subject: 'duas-mulheres-conversa', lighting: 'natural-traseira' },
    prompt: 'Editorial scene of two brazilian women in candid one-on-one conversation across a modern conference table. Left: a woman (30s, straight dark hair, beige and white striped longsleeve) leans on her hands, smiling warmly toward her colleague. Right: a black woman (30s, long box braids, glasses, cream turtleneck), smiling back, hand resting on the table. A clear glass of water and out-of-focus laptop in foreground. Soft backlight through frosted glass partition behind, even warm ambient light on faces. 50mm equivalent, f/2.8, focus split between both women\'s eye lines. Palette: warm beige, cream, neutral office grey. Mid contrast, subtle grain. Mood: trusted dialog, real warmth — not networking-event smile. Aspect 3:2.'
  },
  {
    id: 'pes-010',
    archetype: 'home-office',
    tags: { mood: 'leve', composition: 'over-shoulder', subject: 'dupla-cafe-casa', lighting: 'natural-manha' },
    prompt: 'Editorial scene of two brazilian colleagues working from a sunlit kitchen-office at a wood breakfast bar. Left: a man (early 30s, dark beard, white tee) leaning over an open MacBook, mid-explanation. Right (foreground, blurred): a woman with afro-textured hair pulled into a high curly ponytail, wearing a green ribbed top, listens with chin resting on her hand. On the wood counter: a sage-green French press, two ceramic mugs, scattered notes. Soft morning light through open patio doors behind, hint of garden visible. 35mm equivalent, f/3.2, focus on the man\'s face and laptop screen. Palette: pale wood, sage green, white tee, warm morning light. Mid contrast, subtle grain. Mood: easy collaboration outside the corporate frame. Aspect 3:2.'
  },
  {
    id: 'pes-011',
    archetype: 'retrato-individual-confiante',
    tags: { mood: 'cordial-autoridade', composition: 'medium', subject: 'executivo-escritorio', lighting: 'mista-escritorio' },
    prompt: 'Editorial environmental portrait of a brazilian executive (35-45, dark hair, well-trimmed beard, black square-frame glasses) seated at a light wood desk in a modern open-plan office. Wears a navy slim-fit blazer over a thin-striped pale blue shirt, hands clasped together resting on the desk in front of an open silver laptop. Genuine smile, looking just past the camera. Behind: soft-focus warm-toned office floor with linear ceiling lights, large monstera plant left, glass partitions blurred. 50mm equivalent, f/2.8, sharp on his face, background bokeh. Palette: navy blazer, warm gold ambient lights, deep green plant, charcoal laptop. Mid contrast, subtle grain. Mood: approachable authority — leader who explains, not commands. Aspect 3:2.'
  },
  {
    id: 'pes-012',
    archetype: 'retrato-individual-confiante',
    tags: { mood: 'leve', composition: 'medium-wide', subject: 'profissional-cafe', lighting: 'natural-clara' },
    prompt: 'Editorial candid portrait of a brazilian woman (28-35, shoulder-length brunette hair with subtle highlights) seated at a long wood meeting table beside a glass partition. Wears a relaxed black silk button-up. Holds a take-away coffee cup in her right hand, mid-laugh, looking off to the right at someone unseen. Soft natural daylight from large window behind. A red modern chair partially visible left, small plant right. 50mm equivalent, f/2.5, sharp on her face, glass partition adds gentle reflection layer in foreground. Palette: black silk, warm wood, soft grey backdrop, takeaway coffee brown. Mid contrast, subtle grain. Mood: pause-between-meetings, real laugh, no camera-awareness. Aspect 16:9.'
  },
  {
    id: 'pes-013',
    archetype: 'home-office',
    tags: { mood: 'introspectivo', composition: 'medium-wide', subject: 'individual-de-costas', lighting: 'natural-janela' },
    prompt: 'Editorial wide photograph from behind of a brazilian man (30s, short dark hair, white linen shirt) seated at a wide wood home-office desk facing a tall window with a view of a residential neighborhood at golden hour. Two large monitors display documents. To the left: a vibrant potted plant. To the right: a glass desk lamp and smaller plant. The chair is leather, visible from behind. 35mm equivalent, f/4, focus on the back of his head and the screens. Palette: warm wood, white walls, deep green plants, golden window light. Mid contrast, subtle grain. Mood: solitary deep work, pre-decision concentration. Aspect 3:2.'
  },
  {
    id: 'pes-015',
    archetype: 'businessman-thinking-laptop',
    tags: { mood: 'concentrado', composition: 'medium-side', subject: 'individual-podcast', lighting: 'natural-suave' },
    prompt: 'Editorial profile photograph of a brazilian man (30-40, short dark hair, full beard, white button-up shirt) typing focused on a laptop in a quiet recording room. A gold-mesh podcast microphone is visible foreground-left in soft focus. He wears a leather-strap watch, no smile, full concentration on screen. Soft diffused natural daylight from a sheer-curtain window behind, even and clean. A book lies on the white desk in front of him. 50mm equivalent, f/2.8, focus on the side of his face and his hands. Palette: white shirt, white desk, charcoal laptop, gold mic accent. Mid contrast, fine grain. Mood: prepared craft, recording before broadcasting. Aspect 4:5.'
  },
  {
    id: 'pes-017',
    archetype: 'businessman-thinking-laptop',
    tags: { mood: 'foco', composition: 'medium', subject: 'profissional-laptop', lighting: 'natural-clara' },
    prompt: 'Editorial photograph of a brazilian black professional (35-45, short hair, well-trimmed beard, cream cotton crewneck sweater, gold ring on right hand) typing on a silver MacBook in a bright modern office. Calm focused expression, looking at the screen. Behind, slightly out of focus, an older male colleague (white, grey hair, glasses, light-blue shirt) works at the next desk. Soft cool daylight from large window left. 50mm equivalent, f/3.2, sharp on the foreground subject. Palette: cream knit, white desk, charcoal laptop, neutral cool office. Mid contrast, subtle grain. Mood: deep focus, mature professional flow. Aspect 3:2.'
  }
];

const ARCHETYPE_LABEL = {
  'sala-reuniao-vazia': 'Sala de reunião vazia',
  'home-office': 'Home office',
  'escritorio-moderno-interior': 'Escritório moderno — interior',
  'time-colaborando-laptops': 'Time colaborando com laptops',
  'mockup-papelaria-madeira': 'Mockup papelaria — madeira',
  'mentoria-1-on-1': 'Mentoria 1-on-1',
  'retrato-individual-confiante': 'Retrato individual — confiante',
  'time-celebrando-resultado': 'Time celebrando resultado',
  'aperto-de-maos-fechamento': 'Aperto de mãos — fechamento',
  'businessman-thinking-laptop': 'Empresário pensando — laptop',
  'analise-dados-tela': 'Análise de dados na tela'
};
const ARCHETYPE_CATEGORY = {
  'sala-reuniao-vazia': 'escritorio',
  'home-office': 'escritorio',
  'escritorio-moderno-interior': 'escritorio',
  'time-colaborando-laptops': 'pessoas',
  'mockup-papelaria-madeira': 'branding',
  'mentoria-1-on-1': 'lideranca',
  'retrato-individual-confiante': 'pessoas',
  'time-celebrando-resultado': 'resultados',
  'aperto-de-maos-fechamento': 'pessoas',
  'businessman-thinking-laptop': 'lideranca',
  'analise-dados-tela': 'resultados'
};

const data = JSON.parse(await readFile(INDEX_PATH, 'utf8'));

const counts = {};
const built = PHOTOS.map(p => {
  const archetypeLabel = ARCHETYPE_LABEL[p.archetype];
  const category = ARCHETYPE_CATEGORY[p.archetype];
  counts[p.archetype] = (counts[p.archetype] || 0) + 1;
  return {
    id: p.id,
    archetype: p.archetype,
    archetypeLabel,
    category,
    src: {
      thumb: `assets/fotografia/thumbs/${p.id}.webp`,
      mid:   `assets/fotografia/mid/${p.id}.webp`
    },
    tags: p.tags,
    prompt: p.prompt
  };
});

data.photos = built;
data.archetypes = data.archetypes.map(a => ({ ...a, count: counts[a.id] || 0 }));
data.generatedAt = new Date().toISOString();
delete data.note;

await writeFile(INDEX_PATH, JSON.stringify(data, null, 2));
console.log(`✓ ${built.length} fotos indexadas.`);
console.log('Arquétipos populados:');
Object.entries(counts).sort().forEach(([k, v]) => console.log(`  ${k}: ${v}`));
