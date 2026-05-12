#!/usr/bin/env node
/* ============================================================
   METTA BRAND SYSTEM — PHOTO CURATOR (CP4)
   Lê fotos de .temp-curadoria/, classifica por arquétipo,
   gera thumbnails (400px / 1200px) e escreve photo-index.json
   com prompt profissional por foto pra alimentar gpt-image-1.
============================================================ */

import { readdir, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, join, dirname, extname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const VAULT = resolve(ROOT, '..', '..', '..');
const SOURCE = resolve(VAULT, 'Branding Metta 2.0', '.temp-curadoria');
const OUT_THUMBS = join(ROOT, 'assets', 'fotografia', 'thumbs');
const OUT_MID = join(ROOT, 'assets', 'fotografia', 'mid');
const JSON_OUT = join(ROOT, 'data', 'photo-index.json');

const log = {
  info:  (m) => console.log(`  ${m}`),
  ok:    (m) => console.log(`  \x1b[32m✓\x1b[0m ${m}`),
  warn:  (m) => console.warn(`  \x1b[33m!\x1b[0m ${m}`),
  err:   (m) => console.error(`  \x1b[31m✗\x1b[0m ${m}`),
  group: (m) => console.log(`\n\x1b[1m${m}\x1b[0m`)
};

// ----------- METTA VISUAL DNA (north star pra todos os prompts) -----------
const METTA_DNA = `
Brazilian corporate context. Editorial photography style: high craft, intentional, never staged-stock-photo feeling.
Lighting: natural directional light preferred (window light, golden hour interior), with soft falloff and visible volumetric quality.
Palette: anchored on neutrals (charcoal, oak wood, cream walls, slate grey) with disciplined yellow accents (Metta yellow #FFBE18) appearing as one selective focal point per scene — never decorative.
Composition: deliberate negative space, no busy backgrounds, rule of thirds with strong eye-line lock when subjects are present.
Camera feel: 35mm or 50mm equivalent, mid-to-shallow depth of field (f/2.8–f/4), no fisheye/wide-angle distortion.
Mood: composed, analytical, decision-grade — never euphoric, never anxious, never theatrical.
Post: mid contrast, subtle film grain, neutral white balance with slightly warm shadows, no aggressive color grading or HDR.
Aspect: respect 4:5 (carousel), 1:1 (feed), 9:16 (story), 16:9 (LP hero) — final framing decided per use case.
`.trim().replace(/\s+/g, ' ');

// ----------- ARCHETYPES -----------
// Cada arquétipo é uma "lente" editorial: como a Metta enxerga aquele tipo de cena.
const ARCHETYPES = {
  'executivo-em-decisao': {
    label: 'Executivo em decisão',
    category: 'lideranca',
    description: 'Empresário sozinho em momento analítico — pensando, lendo dado, sustentando peso da escolha.',
    template: `Editorial portrait of a brazilian executive (40-55) in a moment of analytical decision, alone at a desk or modern office. Composed expression — no smile, no theatrics; the face shows the weight of choice. Side window light from the left, warm afternoon tone falling across the shoulder and document. Subject occupies right third, with significant negative space holding context. 50mm equivalent, f/2.8, focus on the eyes. Palette: charcoal suit, oak desk surface, cream wall, single yellow accent (mug, notebook, or backlit paper). Mid contrast, subtle film grain, no HDR. Documentary feel, no posed corporate-stock energy.`,
    tags: { mood: 'analitico', composition: 'medium-close', subject: 'executivo-individual', lighting: 'natural-lateral' }
  },

  'mentoria-1-on-1': {
    label: 'Mentoria 1-on-1',
    category: 'lideranca',
    description: 'Dois empresários em conversa de orientação — mentor e mentorado, conselho, transferência de método.',
    template: `Editorial scene of a 1-on-1 mentoring conversation between two brazilian executives across a wood table. The mentor (left, 50+) leans forward calmly with one hand resting on a document; the mentee (right, 30-45) listens with intent, slightly tilted forward. No smiles — the mood is honest counsel, not pep-talk. Natural light from a tall window behind, soft rim on shoulders. 35mm equivalent, f/3.5, focus split between both subjects. Palette: oak table, white shirt, charcoal blazer, subtle yellow accent on a notebook or pen. Mid contrast, slight grain. Documentary tone, no eye-contact-with-camera, no clichéd handshake.`,
    tags: { mood: 'analitico', composition: 'medium', subject: 'dupla-mentor-mentorado', lighting: 'natural-traseira' }
  },

  'reuniao-mesa-decisao': {
    label: 'Reunião de mesa — decisão',
    category: 'lideranca',
    description: 'Time pequeno em torno da mesa, líder no comando, conversa direta e estratégica.',
    template: `Boardroom scene with 4-6 brazilian executives around an oak conference table. Leader stands at the head, hand on the table, mid-explanation; the others lean in or take notes. Natural light from large window on the right, casting long warm shadows across documents. 35mm equivalent, f/4, depth-of-field keeps the leader and one listener in focus. Palette: dark suits, oak table, off-white walls, single yellow on a folder cover or pen. Mood: strategic alignment, no excessive smiling, no fake laughter. Mid contrast, subtle grain, documentary framing — slightly off-axis, never perfectly centered.`,
    tags: { mood: 'estrategico', composition: 'wide-medium', subject: 'time-em-mesa', lighting: 'natural-lateral' }
  },

  'lider-apresentando-time': {
    label: 'Líder apresentando ao time',
    category: 'lideranca',
    description: 'Líder em pé explicando estratégia ao time sentado — método sendo transmitido.',
    template: `Scene of a brazilian leader standing at the front of a meeting room, gesturing while explaining strategy to 3-5 colleagues seated at the table. The leader is in profile or 3/4 turned to the listeners, not posing. A whiteboard with sparse handwritten notes is visible behind. Natural light from windows on the left, soft and even. 35mm equivalent, f/4. Palette: warm wood floor, charcoal furniture, white walls, single yellow marker or accent in foreground. Mid contrast, light grain. Mood: deliberate transfer of knowledge, intent listening from the team, no theatrical presentation gestures.`,
    tags: { mood: 'didatico', composition: 'wide', subject: 'lider-em-pe-time-sentado', lighting: 'natural-lateral' }
  },

  'palco-evento': {
    label: 'Palco / evento',
    category: 'lideranca',
    description: 'Conferência ou apresentação em palco — autoridade pública, mensagem ampla.',
    template: `Conference stage scene with a brazilian speaker in mid-presentation, addressing a packed audience visible in soft focus background. Speaker stands confidently at center-left, holding a clicker, looking out into the room — not posing for camera. Stage lighting: warm key light, cool rim from behind. 50mm equivalent, f/2.8, sharp on speaker, audience blurred. Palette: deep navy stage, accent yellow on speaker's tie or pin, projected slide visible behind with restrained typography. Mid-to-high contrast, cinematic feel without being theatrical. Capture the authority of public expertise, not the spectacle of a TED-talk-clone.`,
    tags: { mood: 'autoridade', composition: 'medium', subject: 'palestrante-palco', lighting: 'palco-controlado' }
  },

  'time-colaborando-laptops': {
    label: 'Time colaborando com laptops',
    category: 'pessoas',
    description: 'Equipe trabalhando junto em laptops — execução cotidiana, sintonia operacional.',
    template: `Modern open-plan office scene: 3-4 brazilian professionals collaborating around laptops at a shared wood table. Conversation is engaged but quiet — leaning toward screens, occasional pointing. Natural light from large windows on the side, soft and diffused. 35mm equivalent, f/3.5, group composition with one figure slightly closer and in focus. Palette: oak table, white laptop, charcoal/navy clothing, plants in background, one yellow accent (notebook, mug). Mid contrast, restrained grain. Documentary candid quality — no one looking at camera, no fake laughter.`,
    tags: { mood: 'execucao', composition: 'wide-medium', subject: 'time-3-4-pessoas', lighting: 'natural-difusa' }
  },

  'retrato-individual-confiante': {
    label: 'Retrato individual — confiante',
    category: 'pessoas',
    description: 'Retrato editorial de um empresário/executiva — composto, sem sorriso forçado.',
    template: `Editorial business portrait of a single brazilian professional (30-55), 3/4 turn to camera, composed neutral expression — small confident half-smile or fully neutral. Studio or office backdrop in soft gradient charcoal. Key light from upper-left, fill from right, subtle rim from behind. 85mm equivalent, f/2.8, eyes tack-sharp. Palette: dark suit or sharp business-casual, charcoal background, single yellow accent (tie, pin, scarf, notebook in hand). Mid contrast, very slight grain. Posture: shoulders square, slight forward lean. Avoid: cheesy stock smiles, arms crossed defensively, hand-on-chin clichés.`,
    tags: { mood: 'confiante', composition: 'close-portrait', subject: 'retrato-individual', lighting: 'estudio-3-pontos' }
  },

  'aperto-de-maos-fechamento': {
    label: 'Aperto de mãos — fechamento',
    category: 'pessoas',
    description: 'Selo de acordo formal — handshake editorial, não cliché stock.',
    template: `Editorial close-up of a brazilian business handshake at the moment of closure. Frame focuses on the hands and forearms, faces partially out of frame or in soft blur — the handshake itself carries the meaning. Natural light from a side window, warm tone on the skin. 50mm equivalent, f/2.8, sharp on the hands. Palette: charcoal suit cuffs, white shirt cuffs, oak table edge underneath, single yellow tie or pen visible at the edge. Documentary moment — slight motion blur is acceptable. Avoid: corny full-smile two-people-staring-at-each-other handshakes, generic stock framing.`,
    tags: { mood: 'fechamento', composition: 'close-detail', subject: 'maos-handshake', lighting: 'natural-lateral' }
  },

  'time-celebrando-resultado': {
    label: 'Time celebrando resultado',
    category: 'resultados',
    description: 'Comemoração de meta batida — energia controlada, não euforia stock.',
    template: `Brazilian business team (4-6 people) celebrating a milestone in a modern office. Energy is genuine — high-fives, quiet smiles, hands raised — but never euphoric or cheesy. Natural light from windows. 35mm equivalent, f/3.5, capture mid-action with slight motion. Palette: charcoal/navy clothing, oak table, white walls, dashboard screen with charts visible in background, yellow accent on a single object (banner, pin, paper). Mid contrast, slight grain. Documentary mood — looks like a real team, not a stock shoot. Avoid: throw-papers-in-air clichés, exaggerated cheering.`,
    tags: { mood: 'comemoracao-controlada', composition: 'wide-medium', subject: 'time-comemorando', lighting: 'natural-difusa' }
  },

  'analise-dados-tela': {
    label: 'Análise de dados na tela',
    category: 'resultados',
    description: 'Empresário ou time olhando gráficos em tela — cabeça analítica, não decorativa.',
    template: `Brazilian executive at a desk analyzing dashboard charts on a large monitor. Subject leans forward slightly, hand on chin or pen-in-hand mid-thought, eyes locked on the screen. Natural light from window on the left, screen glow on the face. 35mm equivalent, f/2.8, focus on the subject; charts are legible but secondary. Palette: charcoal suit, oak desk, dark screen with restrained typography (numbers and lines, no rainbow), single yellow accent in the chart highlight or on a sticky note. Mid contrast, slight grain. Mood: real analytical work, not posed-with-laptop stock cliché.`,
    tags: { mood: 'analitico-dado', composition: 'medium', subject: 'individual-com-dado', lighting: 'natural-tela-glow' }
  },

  'apresentacao-graficos': {
    label: 'Apresentação de gráficos',
    category: 'resultados',
    description: 'Time olhando gráficos juntos — leitura coletiva de resultado.',
    template: `Conference room scene: brazilian team gathered around a large screen showing a dashboard with charts and KPIs. The presenter (off-frame or partial) gestures toward a specific data point; 3-4 listeners study the chart with focused expressions. Natural light from windows, augmented by ambient screen glow. 35mm equivalent, f/4. Palette: dark navy/charcoal furniture, oak table, screen with restrained chart typography, yellow accent in one highlighted KPI on screen. Mid contrast, light grain. Mood: collective interpretation of result, no fake awe, no over-celebration.`,
    tags: { mood: 'leitura-resultado', composition: 'wide', subject: 'time-com-tela', lighting: 'natural-tela-glow' }
  },

  'sala-reuniao-vazia': {
    label: 'Sala de reunião vazia',
    category: 'escritorio',
    description: 'Boardroom vazio — promessa, expectativa, palco da decisão.',
    template: `Empty modern brazilian boardroom shot from a corner angle. Long oak conference table, leather/fabric chairs aligned, large window with city skyline (muted, soft focus). Late afternoon golden light spills across the table surface. 24mm equivalent, f/8 for full sharpness. Palette: oak wood, charcoal upholstery, off-white walls, blue-grey skyline, single yellow accent (a folder or marker forgotten on the table). High craft, low contrast in shadows, mid contrast in highlights. Mood: charged emptiness — a room that is about to host a decision. Avoid: harsh fluorescents, cluttered desks, generic stock office sterility.`,
    tags: { mood: 'expectativa', composition: 'wide-arquitetura', subject: 'sala-vazia', lighting: 'natural-golden-hour' }
  },

  'escritorio-moderno-interior': {
    label: 'Escritório moderno — interior',
    category: 'escritorio',
    description: 'Ambiente de trabalho moderno, organizado, com luz natural.',
    template: `Wide interior shot of a modern brazilian corporate office space. Open layout with workstations, plants, modular furniture, and floor-to-ceiling windows letting in natural daylight. Some figures in soft focus background going about their work. 24mm equivalent, f/5.6. Palette: light wood floors, white walls, charcoal furniture, green plants, single yellow chair or wall element as focal accent. Mid contrast, no HDR. Architectural-editorial mood — clean but lived-in, not sterile.`,
    tags: { mood: 'ambiente', composition: 'wide-arquitetura', subject: 'interior-escritorio', lighting: 'natural-difusa' }
  },

  'home-office': {
    label: 'Home office',
    category: 'escritorio',
    description: 'Escritório residencial composto e profissional — não bagunça caseira.',
    template: `Editorial shot of a curated brazilian home office: oak desk facing a window, ergonomic chair, single laptop, organized notebook, one plant, framed art on the wall behind. Natural morning light from the window. 35mm equivalent, f/4. Palette: warm wood, white walls, charcoal computer, single yellow accent (notebook, mug, lamp shade). Mid contrast, light grain. Mood: professional discipline at home, not casual lifestyle clutter. Aspect: vertical for story, horizontal for LP.`,
    tags: { mood: 'foco-individual', composition: 'medium', subject: 'home-office-vazio-ou-sutil', lighting: 'natural-manha' }
  },

  'mockup-papelaria-madeira': {
    label: 'Mockup papelaria — madeira',
    category: 'branding',
    description: 'Cartões e papelaria em mesa de madeira — cenário de marca.',
    template: `Top-down or 3/4 angle shot of branded stationery (business cards, envelope, notebook, pen) on a warm oak surface. Composition: rule-of-thirds, with a single yellow element (logo accent, paperclip, brand mark) as the visual anchor. Natural side light, soft shadows. 50mm equivalent, f/4. Palette: oak grain, off-white paper, deep charcoal type, Metta yellow #FFBE18 accent. Mid contrast, subtle grain. Editorial product-photography quality. Avoid: harsh top-light, perfectly symmetric flatlay clichés.`,
    tags: { mood: 'marca-estatica', composition: 'flatlay-3-4', subject: 'papelaria-mockup', lighting: 'natural-lateral-suave' }
  },

  'mockup-papelaria-escura': {
    label: 'Mockup papelaria — escura',
    category: 'branding',
    description: 'Mockup em fundo escuro — premium, contraste alto, marca destacada.',
    template: `Top-down shot of branded stationery on a dark slate or charcoal textured surface. Single yellow accent (logo, edge, paperclip) as the only color in the frame, creating sharp visual hierarchy. Soft directional light from the upper-left. 50mm equivalent, f/5.6. Palette: deep charcoal background, off-white paper, single yellow element. High contrast, subtle texture in the background. Editorial premium feel. Avoid: cluttered flatlays, multiple competing colors.`,
    tags: { mood: 'premium-escuro', composition: 'flatlay', subject: 'papelaria-mockup', lighting: 'controlada-direcional' }
  },

  'objeto-conceitual-escuro': {
    label: 'Objeto conceitual em fundo escuro',
    category: 'branding',
    description: 'Objeto isolado (relógio, copo, chave) com função simbólica em fundo escuro.',
    template: `Editorial product shot of a single symbolic object (clock, glass, key, pen) isolated on a deep charcoal/black background with significant negative space. One side light from upper-right creating directional shadow. 85mm equivalent, f/4. Palette: charcoal background, object in metal/glass tones, single yellow accent (light glow, reflection, label). Mid-high contrast. Mood: concept-led, the object stands as metaphor. Avoid: stock-photo lifestyle clutter, multiple objects.`,
    tags: { mood: 'conceitual-isolado', composition: 'objeto-isolado', subject: 'objeto-simbolico', lighting: 'controlada-direcional' }
  },

  'textura-gold-on-black': {
    label: 'Textura — dourado em preto',
    category: 'texturas',
    description: 'Padrão abstrato amarelo/dourado sobre preto — fundo de marca premium.',
    template: `Abstract texture: golden yellow (#FFBE18 or warmer) particles, brushstrokes, or geometric patterns on a deep charcoal or pure-black ground. Subtle depth and grain. Suitable as background for headlines or as accent layer. No literal objects. Editorial poster feel. Avoid: glitter clichés, rainbow gradients.`,
    tags: { mood: 'fundo-premium', composition: 'fundo-abstrato', subject: 'textura-marca', lighting: 'n-a' }
  },

  'textura-luz-raio': {
    label: 'Textura — raios de luz',
    category: 'texturas',
    description: 'Raios de luz volumétricos — atmosfera, profundidade, drama controlado.',
    template: `Volumetric light rays cutting across a dark space, soft particle-in-light feel. Color palette anchored in cool blue-grey OR warm amber, with one channel dominant. Mood: atmospheric, suggests revelation or insight. Suitable as overlay or hero background. No human figures. Restrained — avoid clichéd "god rays" overcooked dramatic feel.`,
    tags: { mood: 'atmosferico', composition: 'fundo-abstrato', subject: 'raios-luz', lighting: 'volumetrica' }
  },

  'textura-gradiente-grain': {
    label: 'Textura — gradiente granulado',
    category: 'texturas',
    description: 'Gradiente suave com granulação — fundo neutro com profundidade.',
    template: `Smooth gradient background with subtle film grain. Two-tone: one corner deeper, opposite corner lighter. Palette options: charcoal-to-night-blue, cream-to-warm-grey, or yellow-to-amber. Suitable as section background or behind text. Mood: calm depth, no aggressive light bursts. Editorial publication feel.`,
    tags: { mood: 'fundo-calmo', composition: 'fundo-abstrato', subject: 'gradiente', lighting: 'n-a' }
  },

  'textura-arquitetura-ambiente': {
    label: 'Textura — ambiente arquitetônico',
    category: 'texturas',
    description: 'Recorte de ambiente (parede, lounge) usado como pano de fundo de marca.',
    template: `Close architectural detail of a modern lounge or wall: dark stone or wood panels, soft directional light from the side creating depth via shadow. No people. Slight haze in the air. 50mm equivalent, f/4. Palette: charcoal stone, walnut wood, single yellow accent (a lamp glow, a pillow, a small brass detail). Suitable as cover background. Mood: refined materiality, no gaudy luxury cliché.`,
    tags: { mood: 'arquitetura-detalhe', composition: 'detalhe-ambiente', subject: 'ambiente-recorte', lighting: 'natural-lateral' }
  },

  'feminina-lider-apresentando': {
    label: 'Liderança feminina apresentando',
    category: 'pessoas',
    description: 'Executiva mulher conduzindo apresentação — autoridade composta.',
    template: `Brazilian female executive (30-50) standing in a modern meeting room, mid-explanation, gesturing with one hand toward a chart or whiteboard. 3-4 colleagues visible in soft focus listening. Natural light from windows. 50mm equivalent, f/3.5, focus on her face and engaged expression. Palette: charcoal or navy blazer, cream blouse, warm wood floor, single yellow accent (necklace, pen, chart highlight). Mid contrast, light grain. Mood: composed authority, real expertise — not "smiling-female-in-suit" stock cliché.`,
    tags: { mood: 'autoridade-feminina', composition: 'medium', subject: 'mulher-em-pe-explicando', lighting: 'natural-lateral' }
  },

  'businessman-thinking-laptop': {
    label: 'Empresário pensando — laptop',
    category: 'lideranca',
    description: 'Empresário sozinho com laptop em ambiente quente — pausa para pensar.',
    template: `Brazilian executive (30-55) seated alone at a desk with a laptop in a warm-toned office (brick wall or wood panels visible). Subject leans back slightly, hand at chin or temple, eyes in middle-distance focus — mid-thought, not staring at screen. Natural warm light from a side lamp or window, golden tone. 50mm equivalent, f/2.8. Palette: dark blazer, white shirt, single yellow tie or pen, oak desk, brick/wood backdrop. Mid-warm contrast, light grain. Mood: real cognitive pause, no fake-thinking pose.`,
    tags: { mood: 'pausa-pensamento', composition: 'medium', subject: 'individual-pensando', lighting: 'quente-pontual' }
  }
};

// ----------- KEYWORD → ARCHETYPE MATCHER -----------
const KEYWORD_MAP = [
  // Liderança / mentoria / decisão
  { kw: ['Asian_businessman_lost_in_thought'], archetype: 'businessman-thinking-laptop' },
  { kw: ['Stately_bald_man', 'Confident_businessman_crossing_arms', 'Confident_businessman_sits'], archetype: 'retrato-individual-confiante' },
  { kw: ['Speaker_talking', 'AI_conference', 'AI_convention', 'Speaker_talking_on_stage', 'Presenter_talks_with_spectators'], archetype: 'palco-evento' },
  { kw: ['Manager_adviser_consulting', 'Senior_executive_manager_explaining', 'Two_business_executives_discussing', 'Manager_leading_business_meeting', 'Project_manager_leading'], archetype: 'mentoria-1-on-1' },
  { kw: ['Group_Of_Businessmen', 'Multiracial_business_team_having_a_meeting', 'Businessman_Leading_Office_Meeting', 'Business_professionals_discussing_documents', 'Team_leader_explain', 'Young_Businessman_Standing_And_Leading'], archetype: 'reuniao-mesa-decisao' },
  { kw: ['business_executive_making_a_presentation', 'Businessman_training_new_employees', 'Business_team_leader_presenting', 'Confident_business_team_leader_giving', 'Business_man_team_leader_explaining'], archetype: 'lider-apresentando-time' },
  { kw: ['Young_businesswoman_coach_leader', 'female_leader_explaining', 'Young_businesswoman_taking_notes', 'Business_team_meeting__female_leader'], archetype: 'feminina-lider-apresentando' },
  { kw: ['Professional_Business_Consultation', 'Woman_in_Professional_Consultation'], archetype: 'mentoria-1-on-1' },
  { kw: ['Street_Side_Strategy_Session'], archetype: 'mentoria-1-on-1' },
  { kw: ['Young_Professional_Signing_Contract'], archetype: 'aperto-de-maos-fechamento' },

  // Pessoas / time / handshake / portrait
  { kw: ['Handshake', 'Corporate_partnership__deal_and_handshake', 'Professional_business_partners_sealing', 'Executives_in_Formal_Attire_Mark_a_Momentous'], archetype: 'aperto-de-maos-fechamento' },
  { kw: ['Portrait_of_Young_confident_smiling_Asian', 'Portrait_of_a_smiling_happy_young_confident', 'Businesswoman_posing_and_smiling', 'Portrait_of_girl_leader'], archetype: 'retrato-individual-confiante' },
  { kw: ['Diverse_corporate_team_collaborating', 'Diverse_business_team_collaborating', 'Diverse_business_team_collaborating_with_laptops'], archetype: 'time-colaborando-laptops' },
  { kw: ['Excited_business_team_celebrating', 'Overjoyed_business_team_cheering', 'Business_team_celebrating_success', 'Excited_business_team_celebrating_success'], archetype: 'time-celebrando-resultado' },

  // Resultados
  { kw: ['Three_Coworkers_Giving_High_Five', 'Two_businesswomen_enthusiastically_high_fiving', 'Multicultural_Colleagues_Team_Celebrates', 'Businessman_Greeting_Young_Colleague_Celebrating', 'Thrilled_confident_manager', 'Celebrating_Success', 'Diverse_business_team_celebrating_a_milestone', 'Happy_excited_young_female_cryptocurrency_trader'], archetype: 'time-celebrando-resultado' },
  { kw: ['Successful_business_meeting_with_charts', 'Managers_writing_business_plan_on_whiteboard', 'Marketing_team_collaborating__reviewing_data', 'Asian_business_analyst_presenting_data'], archetype: 'apresentacao-graficos' },
  { kw: ['Asian_businesswoman_analyzing_data', 'Office_advisor_examining_KPI', 'Young_asian_woman_analyzing_business_data', 'Young_businesswoman_talking_phone_discussing_analy', 'Close_up_of_tablet_screen', 'Laptop_showing_isolated_chroma_key', 'Entrepreneur_using_isolated_mockup_screen'], archetype: 'analise-dados-tela' },
  { kw: ['Business_team_clapping_hands'], archetype: 'time-celebrando-resultado' },

  // Escritório
  { kw: ['The_boardroom', 'Long_wooden_boardroom_table', 'Modern_conference_room_with_glass_walls'], archetype: 'sala-reuniao-vazia' },
  { kw: ['modern_office_meeting_room_interior', 'Professional_corporate_office_interior', 'Modern_office_interior', 'Modern_Office_Workspace', 'Coworking_space_with_professionals', 'Modern_lounge_with_dark_walls', 'Teamwork_cleaners_in_coworking_space'], archetype: 'escritorio-moderno-interior' },
  { kw: ['Home_office'], archetype: 'home-office' },
  { kw: ['Two_handsome_dark_skinned_executives_having', 'Successful_business_group_celebrating_at_the_meeti', 'Team_of_professionals_celebrating_success', 'happy_managers_with_laptops', 'Young_man_working_on_laptop_outdoors', 'Man_sitting_on_meeting_table_edge', 'Woman_standing_with_arms_crossed_in_modern_office', 'Annoyed_realtor_throwing_cellphone'], archetype: 'time-colaborando-laptops' },
  { kw: ['minimalism_concept__stationery', 'Minimal_women_office_desk', 'Laptop_computer__financial_document'], archetype: 'mockup-papelaria-madeira' },
  { kw: ['Various_blank_rectangular_surfaces', 'Creative_layout_of_blank_cards', 'Blank_stationery_arranged_on_a_wooden_surface', 'Variety_of_blank_papers'], archetype: 'mockup-papelaria-madeira' },

  // Branding (mockups + objects)
  { kw: ['Blank_corporate_stationery_set_on_wood_table', 'blank_business_cards_on_a_wooden_background', 'Two_blank_business_cards_on_a_duotone'], archetype: 'mockup-papelaria-madeira' },
  { kw: ['Black_glasses_and_blank_business_cards_on_a_dark', 'Blank_business_cards_on_dark_grey_background'], archetype: 'mockup-papelaria-escura' },
  { kw: ['Bottle_and_glass_of_red_wine', 'Red_and_white_wine_bottles_mockup_on_dark', 'Alarm_clock_on_dark_background'], archetype: 'objeto-conceitual-escuro' },

  // Texturas
  { kw: ['Acrylic_black_with_gold_splashes', 'Gold_sparkle_paint_on_black', 'Luxury_shiny_glitter_texture', 'Background_wallpaper_golden_yellow_orange', 'Golden_podium_circle_round_background', 'Art_wall_texture_crimson_black'], archetype: 'textura-gold-on-black' },
  { kw: ['blurred_rays_of_light_on_disco_floor', 'blurred_rays_of_light_on_the_disco_floor', 'Blue_light_rays_on_dark_blue_background', 'Light_blue_glowing_abstract_ray_spotlight', 'Into_the_light'], archetype: 'textura-luz-raio' },
  { kw: ['white.jpg', 'White_Abstract_Pattern_and_Texture', 'abstract_texture_background_dark_green_concrete', 'Abstract_dark_gray_white_background', 'Abstract_metallic_background', 'black_3d_background_with_diagonal_white_stripes', 'Green_background_grainy_gradient_abstract', 'Symmetrical_volume_pattern_of_vertical_colored', 'Chocolate_bar_background_with_dark_and_white', 'Chocolate_bar_geometric_pattern_background'], archetype: 'textura-gradiente-grain' }
];

function matchArchetype(filename) {
  for (const rule of KEYWORD_MAP) {
    for (const kw of rule.kw) {
      if (filename.includes(kw)) return rule.archetype;
    }
  }
  return null;
}

// ----------- ID GEN -----------
const ID_PREFIX = {
  branding: 'brd',
  escritorio: 'esc',
  lideranca: 'lid',
  pessoas: 'pes',
  resultados: 'res',
  texturas: 'tex'
};

function makeId(category, idx) {
  return `${ID_PREFIX[category]}-${String(idx).padStart(3, '0')}`;
}

// ----------- IMAGE PROCESSING -----------
async function processImage(srcPath, id) {
  await mkdir(OUT_THUMBS, { recursive: true });
  await mkdir(OUT_MID, { recursive: true });
  const thumbPath = join(OUT_THUMBS, `${id}.webp`);
  const midPath = join(OUT_MID, `${id}.webp`);

  const img = sharp(srcPath);
  const meta = await img.metadata();

  await img.clone()
    .resize({ width: 400, withoutEnlargement: true })
    .webp({ quality: 78 })
    .toFile(thumbPath);

  await img.clone()
    .resize({ width: 1200, withoutEnlargement: true })
    .webp({ quality: 82 })
    .toFile(midPath);

  return { width: meta.width, height: meta.height, aspect: (meta.width / meta.height).toFixed(2) };
}

// ----------- MAIN -----------
const FOLDER_TO_CATEGORY = {
  'Imagens Branding': 'branding',
  'Imagens Escritório': 'escritorio',
  'Imagens Liderança': 'lideranca',
  'Imagens Pessoas': 'pessoas',
  'Imagens Resultados': 'resultados',
  'Imagens Texturas': 'texturas'
};

const CATEGORY_LABEL = {
  branding: 'Branding',
  escritorio: 'Escritório',
  lideranca: 'Liderança',
  pessoas: 'Pessoas',
  resultados: 'Resultados',
  texturas: 'Texturas'
};

async function main() {
  log.group('Metta Brand System — Photo Curator (CP4)');
  log.info(`Source: ${SOURCE}`);
  log.info(`Output thumbs: ${OUT_THUMBS}`);

  const photos = [];
  const archetypeStats = {};
  let unmatched = 0;

  for (const [folder, category] of Object.entries(FOLDER_TO_CATEGORY)) {
    const dir = join(SOURCE, folder);
    if (!existsSync(dir)) {
      log.warn(`pasta não encontrada: ${folder}`);
      continue;
    }
    log.group(`[${category}] ${CATEGORY_LABEL[category]}`);
    const files = (await readdir(dir)).filter(f => /\.(jpe?g|png|webp)$/i.test(f)).sort();
    let i = 1;
    for (const f of files) {
      const id = makeId(category, i++);
      const archetypeId = matchArchetype(f);
      if (!archetypeId) {
        unmatched++;
        log.warn(`${f} — sem arquétipo (revisar manualmente)`);
        continue;
      }
      const arche = ARCHETYPES[archetypeId];

      try {
        const meta = await processImage(join(dir, f), id);
        photos.push({
          id,
          category,
          archetype: archetypeId,
          archetypeLabel: arche.label,
          src: {
            thumb: `assets/fotografia/thumbs/${id}.webp`,
            mid:   `assets/fotografia/mid/${id}.webp`,
            originalName: f
          },
          dimensions: meta,
          tags: { ...arche.tags },
          prompt: arche.template,
          rating: 0,
          notes: ''
        });
        archetypeStats[archetypeId] = (archetypeStats[archetypeId] || 0) + 1;
        log.ok(`${id} [${archetypeId}] ${meta.width}x${meta.height}`);
      } catch (e) {
        log.err(`${id} ${f} — ${e.message}`);
      }
    }
  }

  // Salva photo-index.json
  const index = {
    version: '1.0',
    generatedAt: new Date().toISOString(),
    metta_dna: METTA_DNA,
    archetypes: Object.entries(ARCHETYPES).map(([id, a]) => ({
      id,
      label: a.label,
      category: a.category,
      description: a.description,
      promptTemplate: a.template,
      tags: a.tags,
      count: archetypeStats[id] || 0
    })),
    categories: CATEGORY_LABEL,
    photos
  };

  await writeFile(JSON_OUT, JSON.stringify(index, null, 2), 'utf8');

  console.log('');
  log.group('Resumo');
  log.info(`Total processado: ${photos.length}`);
  log.info(`Sem arquétipo: ${unmatched}`);
  log.info(`Arquétipos ativos: ${Object.keys(archetypeStats).length}`);
  console.log('');
  Object.entries(archetypeStats).sort((a, b) => b[1] - a[1]).forEach(([id, count]) => {
    log.info(`  ${count.toString().padStart(3)} fotos · ${id}`);
  });
  console.log('');
  log.ok(`photo-index.json escrito em data/photo-index.json`);
}

main().catch(err => {
  console.error('\nFalha catastrófica:', err);
  process.exit(2);
});
