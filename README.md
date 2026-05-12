# Metta Brand System

Mini-app web (privado, deploy via Vercel) que reúne em uma única casca navegável:

- **Marca** — manifesto, história, plataforma, narrativa
- **Audiência** — ICP, MQL, dossiês, banco de provas
- **Identidade Verbal** — tom, código de conteúdo, linha editorial
- **Identidade Visual** — tokens, componentes, logos, manual de marca, DS técnico (live)
- **Direção de Arte** — princípios fotográficos, arquétipos, galeria curada
- **Produtos** — 6 Gestões, planos SMTM
- **Aplicações** — catálogo de peças produzidas

> Spec canônica: `design/brand-system-spec.md` no vault Obsidian (não versionado neste repo).

---

## Repositório e fonte de conteúdo

Este repo é **auto-contido**: toda a fonte canônica de conteúdo (MDs do vault Obsidian) vive em `source/` e é versionada aqui. O fluxo é:

1. Edite o conteúdo no Obsidian (vault local — fonte editorial).
2. Sincronize a edição pra `source/` deste repo (passo manual — ver "Atualização de conteúdo").
3. Rode `npm run build` localmente pra validar.
4. Commit + push → Vercel auto-deploya.

**Estrutura de `source/`** (espelha caminhos do vault):
- `source/metta/...` — manifesto, plataforma, brandbook, ICP, MQL, metodologia, produtos
- `source/design/...` — PRD identidade visual, manual de marca, tokens, logos, componentes
- `source/compartilhado/brand-system-blog/...` — versões curadas pra blog interno (19 docs)
- `source/transcricoes/...` — 95 transcrições do canal
- `source/embed/design-system-2.0.html` — DS técnico (live) embarcado em iframe

---

## Como rodar localmente

Como o app usa `fetch()` pra carregar `nav.json` e os parciais HTML, abrir por `file://` não funciona (CORS). Precisa de um http server local:

### Opção 1 — npx serve (recomendado)
```bash
cd "Branding Metta 2.0/output/brand-system"
npm start
# abre http://localhost:5173
```

### Opção 2 — Python
```bash
cd "Branding Metta 2.0/output/brand-system"
python -m http.server 5173
```

### Opção 3 — qualquer http server local
Live Server do VS Code, http-server, etc.

---

## Atualização de conteúdo

1. Edite o `.md` no vault Obsidian.
2. Copie o arquivo correspondente pra `source/<mesmo-caminho>/` neste repo.
3. `npm run build` — gera/atualiza HTMLs em `content/`, `embed/` e atualiza `data/nav.json`.
4. `npm start` — confere visualmente.
5. `git add . && git commit -m "..." && git push` — Vercel deploya automaticamente.

> A duplicação vault ↔ source/ é intencional pra manter o repo auto-contido (Vercel não tem acesso ao vault local). Quando a v2 com auth + editor entrar, o fluxo será automatizado.

---

## Princípios

- **Auto-contido** — toda fonte versionada no repo. Vercel buildia direto, sem precisar do vault.
- **DS técnico embarcado** — `embed/design-system-2.0.html` em iframe na aba Identidade Visual.
- **Estética 100% DS** — tokens, SF Pro Variable, ícones SVG line.
- **Roteamento vanilla** — hash routing, sem framework. URLs como `#/marca/manifesto`.
- **Tema light/dark** — toggle persistido em `localStorage`.
- **Sem emojis na UI** — só ícones SVG (line, viewBox 24x24, stroke currentColor 2.2).

---

## Estrutura

```
brand-system/
├── index.html              ← shell: sidebar + topbar + área de conteúdo
├── app.js                  ← roteamento por hash + lazy load de content/
├── package.json
├── styles/
│   ├── tokens.css          ← tier ref/sys/comp (extraído do DS v2.0)
│   ├── shell.css           ← layout do app
│   └── prose.css           ← tipografia para conteúdo md→HTML
├── data/
│   └── nav.json            ← estrutura das 8 abas + sub-itens (CP3 atualiza)
├── content/                ← parciais HTML (vazio até CP3 rodar)
│   ├── marca/
│   ├── audiencia/
│   ├── verbal/
│   ├── visual/
│   ├── direcao-arte/
│   ├── produtos/
│   └── aplicacoes/
├── assets/
│   ├── logos/              ← SVGs (cópia do design system)
│   ├── symbols/
│   └── signatures/
└── scripts/                ← build.mjs (CP3) e photo-curator.mjs (CP4)
```

---

## Status (roadmap CP1-CP6)

| CP | Status |
|---|---|
| CP1 — Spec do Brand System no vault | Concluído |
| **CP2 — Shell + tokens.css extraído** | **Concluído** |
| CP3 — Pipeline build md→HTML | Pendente |
| CP4 — Direção fotográfica + galeria | Pendente |
| CP5 — Catálogo de aplicações | Pendente |
| CP6 — Skill `/marca-metta` | Pendente |

---

## Princípios

- **Vault é fonte única (readonly)** — build pré-compila `.md` em HTML estático. Edição segue 100% no Obsidian.
- **DS técnico atual segue intacto** — `output/design-system-v2/design-system-2.0.html` é embarcado em iframe na aba Identidade Visual → DS Técnico.
- **Estética 100% reaproveitada** — mesmos tokens, mesma tipografia (SF Pro Variable), mesma linguagem visual do DS.
- **Roteamento simples** — hash routing vanilla, sem framework. URLs como `#/marca/manifesto`.
- **Tema light/dark** — toggle persistido em `localStorage`.
- **Sem emojis na UI** — apenas ícones SVG no estilo DS (line, viewBox 24x24, stroke currentColor 2.2).
