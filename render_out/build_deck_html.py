#!/usr/bin/env python3
"""Gera o deck de apresentação como HTML (16:9, 1 <section> por slide)
pronto pra imprimir em PDF via Chrome headless --print-to-pdf."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FR = ROOT / "render_out" / "demo-video" / "frames"
ADS = ROOT / "assets" / "generated" / "ads"
OUT_HTML = ROOT / "render_out" / "deck.html"

def b64(p: Path) -> str:
    ext = p.suffix.lstrip(".")
    mime = "png" if ext == "png" else "webp"
    return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode()

CSS = """
@page { size: 1280px 720px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }
.slide {
  width: 1280px; height: 720px; position: relative; overflow: hidden;
  page-break-after: always; break-after: page;
}
.slide:last-child { page-break-after: auto; }
.bar { position: absolute; left:0; top:0; width: 16px; height: 100%; background: #FFBE18; }
.eyebrow { position: absolute; font-size: 13px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.h1 { position: absolute; font-weight: 900; letter-spacing: -0.01em; }
.body { position: absolute; line-height: 1.4; }
.pagenum { position: absolute; right: 40px; bottom: 24px; font-size: 11px; }
.card { position: absolute; }
.dot { position: absolute; width: 10px; height: 10px; background: #FFBE18; }
img.shot { display:block; width:100%; height:100%; object-fit: contain; }
</style>
"""

slides_html = []

# ---------- 1. CAPA ----------
slides_html.append(f"""
<section class="slide" style="background:#0A1013;">
  <div class="bar"></div>
  <div class="eyebrow" style="left:70px; top:70px; color:#FFBE18;">METTA · BRAND SYSTEM</div>
  <div class="h1" style="left:66px; top:195px; width:920px; font-size:56px; color:#fff; line-height:1.08;">Ferramenta de<br>geração de criativos.</div>
  <div class="body" style="left:70px; top:400px; width:760px; font-size:19px; color:#94B5C8;">Da marca navegável ao anúncio pronto — com direção de arte, geração de imagem e QA automatizado, tudo com a identidade Metta.</div>
  <div class="body" style="left:70px; top:528px; font-size:14px; color:#435965;">Apresentação · Julho 2026</div>
</section>
""")

# ---------- 2. O QUE É ----------
cards = [
    ("Marca navegável", "Manifesto, ICP, identidade verbal e visual, direção de arte — tudo documentado e vivo, não um PDF esquecido.", "#EFF3F5", "#12181F"),
    ("Gerador de criativos", "Pipeline: briefing → direção de arte → geração de imagem → checagem por visão → crítico anti-slop. Duas marcas: Metta e Tiago Alves.", "#0A1013", "#fff"),
    ("Biblioteca viva", "Catálogo canônico (109 peças de referência) + Criativos Gerados — tudo que a ferramenta produz, com veredito do QA documentado.", "#EFF3F5", "#12181F"),
]
card_html = ""
for i, (title, desc, bg, fg) in enumerate(cards):
    x = 66 + i * 383
    card_html += f"""
    <div class="card" style="left:{x}px; top:210px; width:360px; height:410px; background:{bg};">
      <div style="height:10px; background:#FFBE18;"></div>
      <div style="padding:28px;">
        <div style="font-size:21px; font-weight:900; color:{fg}; margin-bottom:20px;">{title}</div>
        <div style="font-size:14.5px; color:{fg}; line-height:1.45;">{desc}</div>
      </div>
    </div>"""
slides_html.append(f"""
<section class="slide" style="background:#fff;">
  <div class="eyebrow" style="left:66px; top:56px; color:#B38400;">O QUE É</div>
  <div class="h1" style="left:62px; top:88px; width:1000px; font-size:33px; color:#12181F;">Um único sistema, três camadas.</div>
  {card_html}
  <div class="pagenum" style="color:#435965;">02 / 09</div>
</section>
""")

# ---------- 3. PIPELINE ----------
steps = [
    ("01", "Briefing", "Texto livre PT-BR vira briefing estruturado"),
    ("02", "Direção de arte", "Escolhe estilo + composição, referência do banco"),
    ("03", "Geração de imagem", "gpt-image-2 gera a foto, guiado por modos de falha conhecidos"),
    ("04", "Vision-QA", "Uma IA olha o PNG renderizado e julga: passa ou reprova"),
    ("05", "Crítico anti-slop", "Checa 16 padrões de “cara de IA genérica” contra o banco"),
    ("06", "Entrega", "PNG final + HTML, pronto pra publicar"),
]
steps_html = ""
for i, (num, title, desc) in enumerate(steps):
    col = i % 3; row = i // 3
    x = 66 + col * 383; y = 220 + row * 195
    steps_html += f"""
    <div class="card" style="left:{x}px; top:{y}px; width:360px; height:170px; background:#131F25;">
      <div style="padding:22px;">
        <div style="font-size:26px; font-weight:900; color:#FFBE18;">{num}</div>
        <div style="font-size:16px; font-weight:800; color:#fff; margin-top:12px;">{title}</div>
        <div style="font-size:11.5px; color:#94B5C8; margin-top:10px; line-height:1.3;">{desc}</div>
      </div>
    </div>"""
slides_html.append(f"""
<section class="slide" style="background:#0A1013;">
  <div class="eyebrow" style="left:66px; top:56px; color:#FFBE18;">COMO FUNCIONA</div>
  <div class="h1" style="left:62px; top:88px; width:1000px; font-size:33px; color:#fff;">6 etapas, do texto livre ao PNG final.</div>
  {steps_html}
  <div class="pagenum" style="color:#94B5C8;">03 / 09</div>
</section>
""")

def screenshot_slide(idx, title, subtitle, img_path):
    return f"""
<section class="slide" style="background:#EFF3F5;">
  <div class="eyebrow" style="left:66px; top:50px; color:#B38400;">NA PRÁTICA</div>
  <div class="h1" style="left:62px; top:80px; width:900px; font-size:27px; color:#12181F;">{title}</div>
  <div class="body" style="left:66px; top:128px; width:900px; font-size:14px; color:#435965;">{subtitle}</div>
  <div class="card" style="left:64px; top:172px; width:1152px; height:500px; background:#fff; padding:8px;">
    <img class="shot" src="{b64(img_path)}">
  </div>
  <div class="pagenum" style="color:#435965;">{idx:02d} / 09</div>
</section>
"""

slides_html.append(screenshot_slide(4, "Um hub, não um PDF.",
    "Marca, audiência, identidade verbal/visual, direção de arte — navegável, sempre atualizado.", FR / "f_2.png"))
slides_html.append(screenshot_slide(5, "Criar começa simples.",
    "Escolhe a marca (Metta ou Tiago) — o resto do wizard adapta tom, estilos e paleta automaticamente.", FR / "f_14.png"))

# ---------- 6. EXEMPLOS ----------
imgs = [
    ADS / "i-retrato-autoridade-metodo.webp",
    ADS / "light-surreal-escada-escalam-estacionam.webp",
    ADS / "yellow-bloco-convite-mentoria.webp",
    ADS / "tiago-story-hero-foto-real-estrutura.webp",
]
img_html = ""
for i, p in enumerate(imgs):
    x = 66 + i * 288
    img_html += f'<div class="card" style="left:{x}px; top:158px; width:270px; height:508px; background:#EFF3F5; padding:6px;"><img class="shot" src="{b64(p)}"></div>'
slides_html.append(f"""
<section class="slide" style="background:#fff;">
  <div class="eyebrow" style="left:66px; top:56px; color:#B38400;">RESULTADO</div>
  <div class="h1" style="left:62px; top:88px; width:1000px; font-size:30px; color:#12181F;">Peças reais, geradas hoje.</div>
  {img_html}
  <div class="body" style="left:66px; top:680px; font-size:12px; color:#435965;">Todas passaram por vision-QA e crítico anti-slop antes de entrar aqui.</div>
  <div class="pagenum" style="color:#435965;">06 / 09</div>
</section>
""")

slides_html.append(screenshot_slide(7, "Biblioteca de Criativos Gerados.",
    "Toda peça que a ferramenta produz fica registrada — com o veredito do QA, não só a imagem.", FR / "f_22.png"))
slides_html.append(screenshot_slide(8, "+ Catálogo canônico: 109 referências.",
    "Banco vivo de peças aprovadas — é o que a IA usa como referência de “mesmo designer”.", FR / "f_30.png"))

# ---------- 9. ROADMAP ----------
roadmap = [
    "Direção de série completa (paletas P1–P10, guardrails C1–C8) — recuperada do backup, aguardando merge",
    "Recompositor full-bleed — resolve o padrão de foto cortando a pessoa no meio",
    "Mais fotos reais do Tiago (bastidor/selfie) para os modelos que exigem foto real",
    "Calibrar o crítico pra comparar só com referências da mesma família de paleta",
]
road_html = ""
for i, item in enumerate(roadmap):
    y = 210 + i * 90
    road_html += f"""
    <div class="dot" style="left:66px; top:{y+8}px;"></div>
    <div class="body" style="left:96px; top:{y}px; width:1080px; font-size:17px; color:#fff; line-height:1.3;">{item}</div>"""
slides_html.append(f"""
<section class="slide" style="background:#0A1013;">
  <div class="eyebrow" style="left:66px; top:56px; color:#FFBE18;">PRÓXIMOS PASSOS</div>
  <div class="h1" style="left:62px; top:88px; width:1000px; font-size:33px; color:#fff;">O que vem a seguir.</div>
  {road_html}
  <div class="pagenum" style="color:#94B5C8;">09 / 09</div>
</section>
""")

html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</head><body>{''.join(slides_html)}</body></html>"
OUT_HTML.write_text(html, encoding="utf-8")
print("HTML salvo em", OUT_HTML, "-", len(slides_html), "slides")
