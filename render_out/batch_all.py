#!/usr/bin/env python3
"""Batch: regenera os 23 previews restantes do wizard (10 Metta + 13 Tiago).
Os 5 já aprovados hoje (yellow-bloco, news-card, yellow-split, light-surreal, i) ficam.
"""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "bin" / "python")
OUT = ROOT / "render_out" / "previews-novos" / "batch-all"
OUT.mkdir(parents=True, exist_ok=True)

# (model, image, preset, formato, tag, headline, subhead, body, cta)
JOBS = [
    # ---------- METTA ----------
    ("YELLOW-OBJETO", "generate", "fotorrealista", "feed", "",
     "Consistência vence talento. Todos os meses.",
     "O método que faz o time inteiro bater meta.", "", "CONHECER O MÉTODO"),
    ("A-headline-foto-dark", "generate", "cinematic-dark", "feed", "",
     "Crescer deixou de ser sorte.",
     "Quando a operação tem método, a próxima venda é previsível.", "", "Conheça a Metta"),
    ("D-foto-fullbleed-overlay", "generate", "cinematic-dark", "feed", "CONVITE PARA DONOS DE VAREJO",
     "Multiplique os resultados do seu melhor vendedor.",
     "Engenharia reversa da venda que funciona — sem depender de talento raro.", "", "Saiba mais"),
    ("C-tipografia-pura-dark", "none", "", "feed", "PARA EMPRESÁRIOS DE SERVIÇOS",
     "Hoje você apaga incêndio. Daqui a 6 meses, sua equipe pode bater meta sem te chamar.",
     "Mentoria para quem quer um comercial previsível, não heróico.", "", "SAIBA MAIS"),
    ("YELLOW-EDITORIAL", "none", "", "feed", "",
     "+1.000 empresas já bateram meta com método.",
     "Método M.E.T.T.A. — estrutura que escala sem depender de herói.", "", "CONHECER O MÉTODO"),
    ("YELLOW-FRAME", "none", "", "feed", "",
     "Meta batida não é sorte. É rotina.",
     "Estrutura comercial que se repete todo mês.", "", "CONHECER"),
    ("METTA-TWEET-CARD", "none", "", "feed", "",
     "Gestor de vendas não nasce — é formado com método, não com motivação.",
     "Estrutura bate inspiração toda semana.", "", "Descubra o Método Metta"),
    ("B-foto-top-headline-mixed", "generate", "fotorrealista", "feed", "SESSÃO 1:1 PARA DONOS DE NEGÓCIOS",
     "Me dê 60 minutos para tirar você do balcão da sua própria loja.",
     "O Plano de Saída da Operação — método aplicado em +1.000 operações no Brasil.", "", "TOQUE NO LINK ABAIXO"),
    ("H-fundo-branco-headline-gigante", "none", "", "feed", "",
     "Empresa que não tem método tem heróis — e heróis se esgotam.",
     "Método Metta — estrutura que sobrevive sem você.", "", "VER MÉTODO"),
    ("LOGO-WALL", "none", "", "feed", "+1.000 EMPRESAS",
     "Já operam com o método Metta.",
     "De pequenas operações a grandes redes — gestão que escala.", "", "VER CASES"),
    # ---------- TIAGO ----------
    ("TIAGO-TWITTER-CARD", "none", "", "feed", "",
     "Time que depende do dono pra vender não tem processo. Tem babá.",
     "Estrutura bate inspiração toda semana.", "", "Seguir @tiagoalves"),
    ("TIAGO-NOTES-MOCKUP", "none", "", "feed", "",
     "Anotei isso depois de mais uma meta batida:",
     "", "Rotina vence talento\nProcesso vence pressão\nMétodo vence motivação", "Salva esse post"),
    ("TIAGO-TYPO-PURE", "none", "", "feed", "",
     "Vendedor herói não é estratégia.",
     "É sintoma de gestão sem método.", "", "Conheça a mentoria"),
    ("TIAGO-EDITORIAL-CTA", "generate", "cinematic-dark", "feed", "",
     "Sua meta não é alta demais. Sua estrutura que é baixa demais.",
     "", "", "Aplicar para a mentoria"),
    ("TIAGO-TWITTER-CARD-IMAGE", "generate", "fotorrealista", "feed", "",
     "O problema nunca foi o mercado. É o seu processo comercial.",
     "", "", "Seguir @tiagoalves"),
    ("TIAGO-STORY-COVER-HERO", "generate", "cinematic-dark", "story", "",
     "Como fazer seu time bater meta sem depender de você.",
     "Aula completa no canal.", "", "ASSISTIR AGORA"),
    ("TIAGO-STORY-YELLOW-BLOCK", "generate", "fotorrealista", "story", "",
     "3 perguntas pro seu gerente antes da próxima meta.",
     "", "Qual o funil desta semana?\nQuem precisa de treino hoje?\nO que trava a primeira venda do dia?", "Responde nos comentários"),
    ("TIAGO-STORY-MINIMAL-QUESTION", "generate", "bw-yellow", "story", "",
     "Seu negócio está superando metas?",
     "", "", "Responde aqui"),
    ("TIAGO-DARK-SURREAL", "generate", "surreal-hbr", "feed", "",
     "A pressão não bate meta. A estrutura bate.",
     "Insights de gestão comercial toda semana.", "", "CONHECER"),
    ("TIAGO-PHOTO-RAW", "generate", "fotorrealista", "feed", "",
     "Só pode cobrar quem ensina.",
     "Liderança de vendas na prática.", "", "VER AULA"),
    ("TIAGO-EDITORIAL-HERO", "generate", "cinematic-dark", "feed", "",
     "Liderança persuasiva: como convencer seu time a bater a meta.",
     "Episódio novo no canal.", "", "VER AULA"),
    ("TIAGO-EDITORIAL-CARD", "generate", "cinematic-dark", "feed", "",
     "Ex-vendedores fracassam na gerência quando levam o talento e esquecem o método.",
     "Por que o melhor vendedor nem sempre vira o melhor gestor.", "", "LER MAIS"),
    ("TIAGO-EDITORIAL-DARK", "generate", "cinematic-dark", "feed", "",
     "Culpa é do dono.",
     "Seu problema nunca foram as vendas.", "", "ASSISTIR"),
]

t0 = time.time()
fails = []
for i, (model, image, preset, fmt, tag, h, s, body, cta) in enumerate(JOBS, 1):
    print(f"\n=== {i}/{len(JOBS)} {model} ({'img' if image=='generate' else 'typo'}, {fmt}) ===", flush=True)
    cmd = [PY, str(ROOT / "cli.py"), "--model", model,
           "--headline", h, "--subhead", s, "--body", body, "--cta", cta,
           "--tag", tag, "--format", fmt, "--image", image,
           "--out", str(OUT)]
    if image == "generate":
        cmd += ["--preset", preset or "fotorrealista", "--auto-improve", "--max-attempts", "2"]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    tail = "\n".join((r.stdout or "").strip().splitlines()[-5:])
    print(tail, flush=True)
    if r.returncode != 0:
        fails.append(model)
        print(f"  !! FALHOU: {model}\n{(r.stderr or '')[-400:]}", flush=True)

print(f"\n=== FIM em {round((time.time()-t0)/60,1)} min · falhas: {fails or 'nenhuma'} ===")
