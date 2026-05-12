---
title: "Metta — Logos e Assets Drive"
tags:
  - marca/metta
  - status/normativo
  - tema/design
  - tipo/assets
summary: "IDs Drive de todos os logos, backgrounds, modelos de reels e tipografia. Regras de seleção por fundo. Fonte única de verdade pra assets."
created: 2026-04-28
updated: 2026-04-28
---

# Metta — Logos e Assets Drive

> **Status:** NORMATIVO. Toda peça que usa logo Metta deve referenciar daqui.
>
> **Duas fontes de verdade (ambas válidas, mesmos arquivos):**
> 1. **Local (preferido pra código novo):** `system-source/assets/logos/` — SVGs já no vault, sem dependência de rede
> 2. **Remoto (fonte do time):** [Drive Identidade Visual Metta](https://drive.google.com/drive/folders/1I7W7fYQw1NK4iVhMEkgnWIBjeZZtTQ7u) — IDs canônicos pra Plugin API ou download via curl

---

## §0.5 Mapeamento local ↔ Drive

> Pasta local: `design/system-source/assets/` (raiz do vault `Documents/Claude/Projects/`)

### Logos horizontais (`logos/`)

| Variante | Arquivo local | Drive ID (PNG) |
|---|---|---|
| Colorido (fundo escuro) | `logo_metta_colorido_h.svg` | `1zdIiaQedxsWH0IJqmGKUSJPZ8lb16siY` |
| Colorido escuro (fundo claro) | `logo_metta_colorido_escuro_h.svg` | `1xXwyI40wfLmg7euILl1eoUzElCm7G_Kp` |
| Azul (fundo amarelo) | `logo_metta_azul_h.svg` | `1DMqb6w8EMcsY7W8vja2unUkAJC_Oablm` |
| Azul secundário | `logo_metta_azul2_h.svg` | `1hbYDE0jvuksEdcI0Y8aU8AF80bPCsLrr` |
| Branco | `logo_metta_branco_h.svg` | `1dUkDiVqLASKO9b52rnVzlzXkG4LmP09F` |
| Cinza | `logo_metta_cinza_h.svg` | `1KyPV4XPyPPGrrd3mLAQhvlZlz7pQUqhy` |

### Símbolos (`symbols/`)

| Cor | Arquivo local | Drive ID |
|---|---|---|
| Amarelo | `simbolo_metta_amarelo.svg` | `1L6yJ0gmxqKOsbGFg7MI3sc8JJZ-jdqzC` |
| Azul noite | `simbolo_metta_azul.svg` | `1Bnn6DVkar-nNVh6AWsi_Vktj3dViJtsv` |
| Azul secundário | `simbolo_metta_azul2.svg` | `1VBOJm_p8Yc2dc13DaTySh3sFORKMDP45` |
| Branco | `simbolo_metta_branco.svg` | `1b3tKx-ueGbHaAva3qVojXNlfiyK74Bbl` |
| Cinza | `simbolo_metta_cinza.svg` | `1it2DjVaJl5aVCFvyMU9pQdEEPyaXpmkU` |

### Assinaturas (`signatures/`)

| Cor | Arquivo local | Drive ID (SVG) |
|---|---|---|
| Amarelo | `assinatura_metta_amarelo.svg` | `1O2ZBlXo1xkpEoo2fmwpP1Fo37RElRBlf` |
| Azul noite | `assinatura_metta_azul.svg` | `1cwtzuv_pbdUXoZWQMeXOrsRXQcdtee7H` |
| Azul secundário | `assinatura_metta_azul2.svg` | `1nfG03x-L8o3aXw6jVOVqesXJCNObiJ1d` |
| Branco | `assinatura_metta_branco.svg` | `1UDca83ltIA640gTyzeFFkrCitf3nj_cq` |
| Cinza | `assinatura_metta_cinza.svg` | `1om5L1Gr-OUmP1lv55zWeRd69W4zLuDxa` |

### Backgrounds (`backgrounds/`)

JPGs flat plates + gradients. 10 arquivos:
- `bg_gradiente_amarelo_1.jpg`, `bg_gradiente_escuro_1.jpg`
- `bg_liso_amarelo_1/2/3.jpg`, `bg_liso_azul_1/2.jpg`
- `bg_liso_branco_gelo_1.jpg`, `bg_liso_cinza_1.jpg`, `bg_liso_cinza_gelo_1.jpg`

> Em código novo, use referência relativa: `../system-source/assets/backgrounds/bg_liso_amarelo_1.jpg`. Para Plugin API, baixar via curl conforme §7.

---

---

## §0. REGRAS ABSOLUTAS (PRD §6.4)

❌ **PROIBIDO:**
1. **Desenhar o logo** em SVG/CSS/figma vector — sempre baixar do Drive
2. **Usar placeholder textual** `[logo] metta`, `<METTA>` — se asset não pode ser baixado, INTERROMPER e reportar
3. **Aplicar glow/shadow/ghost/outline/blur** no logo — nem em CSS, nem em Figma
4. **Recriar o wordmark** em texto SF Pro — o "metta" textual NÃO substitui o arquivo oficial

---

## §1. Seleção de logo por fundo

| Fundo | Logo recomendado | PNG ID | SVG ID |
|---|---|---|---|
| Escuro (`#0C161B`, `#000`, `#131313`) | Colorido horizontal | `1zdIiaQedxsWH0IJqmGKUSJPZ8lb16siY` | `1KJ4uiqHdX49Uhp2wg3E9HkzqawE7bYMQ` |
| Claro (`#FFF`, `#FAFCFD`) | Colorido escuro horizontal | `1xXwyI40wfLmg7euILl1eoUzElCm7G_Kp` | `1OoU3dGAEPR8S8g10ZuR-vlSyqEv3YDOi` |
| Amarelo (`#FFBE18`) | Azul horizontal | `1DMqb6w8EMcsY7W8vja2unUkAJC_Oablm` | `13Dz57SxqWTj8bpUcyr8P7N88k3atp8wN` |
| Escuro (vertical) | Colorido vertical | `1TAOMF6zc41fK4zGSzbf3WsjUl08b30Np` | `1-McHsQ1dT3RX5rGLWQv2cFL8TJOXidjB` |
| Escuro (apenas símbolo) | Símbolo amarelo | `1L6yJ0gmxqKOsbGFg7MI3sc8JJZ-jdqzC` | `1dwPSsS49LZWJR7hd3HoaNnvgLkWquJs4` |
| Claro (apenas símbolo) | Símbolo azul | `1Bnn6DVkar-nNVh6AWsi_Vktj3dViJtsv` | `1HDDsK0WPyINzOk_ogxRBlaX00yp9dYjP` |

---

## §2. Catálogo completo de logos

> **Pasta:** [Logo Metta](https://drive.google.com/drive/folders/1ut9l5T_ozyUbUjIqBDFPERRMIiEi6LuZ)

### Símbolos (ícone isolado)

| Cor | PNG ID | SVG ID |
|---|---|---|
| Amarelo | `1L6yJ0gmxqKOsbGFg7MI3sc8JJZ-jdqzC` | `1dwPSsS49LZWJR7hd3HoaNnvgLkWquJs4` |
| Azul noite | `1Bnn6DVkar-nNVh6AWsi_Vktj3dViJtsv` | `1HDDsK0WPyINzOk_ogxRBlaX00yp9dYjP` |
| Azul secundário | `1VBOJm_p8Yc2dc13DaTySh3sFORKMDP45` | `1wvZxTOkZbfeRbuLju17XH6RQ2XL95SYk` |
| Branco | `1b3tKx-ueGbHaAva3qVojXNlfiyK74Bbl` | `1y2E3_xpZAAtsp6-CgGYfP4AftaMIVu2s` |
| Cinza | `1it2DjVaJl5aVCFvyMU9pQdEEPyaXpmkU` | `1ZV9SAmeMdRUq89iKWu-YRLaXuohWtn-U` |

### Logo completo (horizontal `_h` e vertical `_v`)

| Versão | PNG H | SVG H | PNG V | SVG V |
|---|---|---|---|---|
| Colorido (fundo escuro) | `1zdIiaQedxsWH0IJqmGKUSJPZ8lb16siY` | `1KJ4uiqHdX49Uhp2wg3E9HkzqawE7bYMQ` | `1TAOMF6zc41fK4zGSzbf3WsjUl08b30Np` | `1-McHsQ1dT3RX5rGLWQv2cFL8TJOXidjB` |
| Colorido escuro (fundo claro) | `1xXwyI40wfLmg7euILl1eoUzElCm7G_Kp` | `1OoU3dGAEPR8S8g10ZuR-vlSyqEv3YDOi` | `1WF7is4MRzYUBz144eVGFl70SKGzW8g6Z` | `1XBx0a3Zi0Gjf8in1Mk-_ynxCYsM834B_` |
| Branco | `1dUkDiVqLASKO9b52rnVzlzXkG4LmP09F` | `1UAttnww1716VzMNZtGWkyEEuEepmVeR4` | `1726eRnBpslYqMi0DsVpm3NxcWGFvfND4` | `14bfXYU44-Vi_GUzt2h9K93u-mQ4tM4km` |
| Azul noite | `1DMqb6w8EMcsY7W8vja2unUkAJC_Oablm` | `13Dz57SxqWTj8bpUcyr8P7N88k3atp8wN` | `1pwxckpUPu_Wbvi2IPt6Cu_eJ06HvrT8E` | `1ON4zqLTBqlDSvU9M_tsAskCQXQH0FL9i` |
| Azul secundário | `1hbYDE0jvuksEdcI0Y8aU8AF80bPCsLrr` | `17g9sUtqsLwV1Pgi6aQD5o72v6WRV4tck` | `11t337xMRuUF2J8__dfxHgO9sXN4qHpr4` | `1waBE3chmyV58bibddkSbWJMTqK7baBUi` |
| Cinza | `1KyPV4XPyPPGrrd3mLAQhvlZlz7pQUqhy` | `1hjaZujL9UExoBb7YH8xHd68kTHa3pm3Z` | `1N3yDA9CA8QonLnGwDKLcAXUYwtU-MWAz` | `1qHpKB3NXwtLBN3LNhKEKnISw3lfQM4d1` |

### Logo com tagline

| Versão | SVG ID |
|---|---|
| Colorida horizontal | `1ml7q5kY5hR_JBThjk11Q53kunxccGKSE` |

### Assinaturas (logo compacto)

| Cor | PNG ID | SVG ID |
|---|---|---|
| Amarelo | `1g2-Wb27NSAv7xyhqHK22vVnoBOGr8fdj` | `1O2ZBlXo1xkpEoo2fmwpP1Fo37RElRBlf` |
| Azul noite | `1Wv9qMgK7MXFfiRIyNjPKlmhsuGHBr6YP` | `1cwtzuv_pbdUXoZWQMeXOrsRXQcdtee7H` |
| Azul secundário | `1C2R_m-JpLW0UaK3ToW0xa_O7Idyp8N_P` | `1nfG03x-L8o3aXw6jVOVqesXJCNObiJ1d` |
| Branco | `16t01tM7AQnwHHt2w2sCKl5OuDN0cZeaT` | `1UDca83ltIA640gTyzeFFkrCitf3nj_cq` |
| Cinza | `1CA4M3Jk0-Lg0vfaMM9f3Utl5ldLCerY4` | `1om5L1Gr-OUmP1lv55zWeRd69W4zLuDxa` |

### Logo Protocolo Metta

> **Pasta:** [Logo Protocolo Metta](https://drive.google.com/drive/folders/1MMSc1AwL8A7sGznoSZ93ZfNb6IOh6Jmm)

| Cor | PNG ID |
|---|---|
| Amarelo | `1TL1HWQJpN9xI8u51R7okcaO8QwEGAK2A` |
| Branco | `1LX8sHyeQLRflCz8YfHgA4SKZmegaaSVW` |
| Cinza claro | `1UHfDdPN5K22ztb1vDK5eYAwHBW59_94Z` |
| Cinza escuro | `1sKpln5cKSUWp1Mp-hWhh1xflF2GXDIad` |

---

## §3. Backgrounds oficiais

> **Pasta:** [Background](https://drive.google.com/drive/folders/12iw_vXsVD7PeqjKvz6O3uNLzhOAbtjYf)

| Background | PNG ID | SVG ID |
|---|---|---|
| Gradiente amarelo | `1GrKUEC_kWb6Aamkj4FPfKHUi1Lr1at7F` | `1_cFZ4mh0-OcTntrV7iYqbVbQDp2rUYjN` |
| Gradiente escuro | `1pbu8JYrEm8DLvbtMbyZfNrpy8fiSX1v6` | `1iIOhDXHw39SEeS-a5zBe41eq8ChSdiSo` |
| Liso amarelo 1 | `1VyOcpC4kQDRZqVtk88WWuVNLDmhDlQoj` | `19WM0kTzLS69ga9mqRLNsG9LfeHvwkOXh` |
| Liso amarelo 2 | `1k0wvNtRLRzX_IkKUq3WeXCqpsKZpeBHB` | `1SC-ssWO9ifWXttwv_sFf1IZrL_Nk3FFc` |
| Liso amarelo 3 | `1m4W_iOIHMkTpzn3V-mF9xRVeXfGyrmnR` | `1_VnqAwB0xcsl_g0H2NntE_qzZPTmXCr5` |
| Liso azul 1 | `1O6AWbrs_oUJcNuusLi_uemXDBV8EQfsk` | `17layZE3m4AW4oEaFR-daGG5L2Hy50nvN` |
| Liso azul 2 | `1tKZxrP53s3R2wZ2M5LJ1j9rNzUEkeIqd` | `1j_4mFdzj6Dtd7EgYfxzpGrzOSdXdIHHz` |
| Liso branco gelo | `1DJnhIyFCL94s7fuJI9ZHhwRXHe31MXsV` | `1N3AMODpJsZ7f1MpvWUmcUbf5ILRkRQnC` |
| Liso cinza | `19soa2bWk0OM9gt9vbiqOBcxnOaAwmKut` | `1ZAIgmME7pqneLeCPqKdOxemgL4mWBf8P` |
| Liso cinza gelo | `1PKsAsdWGmPKJObxn5g8XfXBgoAINNu_j` | `1m0bOiiaw-0mmswBofoLSxSfZViWU8c-S` |

---

## §4. Modelos de Reels

> **Pasta:** [Modelos Reels](https://drive.google.com/drive/folders/19YMuk58uDSZeyf4jdsRkUYbpcRMESRja)

| Modelo | PNG ID |
|---|---|
| 1 | `1aQGMUUrBcUuO9EjcaziF6w-PL3AXSfKy` |
| 2 | `1jpWzEGomVy3IHXOiaTW08RIIQpSLJBxh` |
| 3 | `1JD9Wlx53YfCmWYp4t-ehjUU9FHwmU0s4` |
| 4 | `1UaeIYFGJqr_7XgCXbMSkCOJBGfRbE67v` |
| 5 | `1w4kqQJ6lwSOOFHCe_8Q5GG6vefn9OAKX` |
| 6 | `1-FOeSSowAqMd9oBYWLF3j2qnGFVDG7iz` |
| 7 | `1wJE1Qp62CErh_Ubuyl7GaiwtnEujnZ8l` |
| 8 | `1khaVtZlDxA1TQQmyyktcPXQGhBQuinWq` |
| 9 | `1hFPvKnBpG_wme7znd2BUN9zLPKK9bCaB` |
| 10 | `1HWiSeE4nNIYGpGxaNuIwrfepgNkPJpkd` |
| 11 | `1XkeRQK-aSOUzzTTcr-7PgX-5ojSKbbm_` |
| 12 | `1rVlr90QlEqkp72KZthqllDuEZW-Hwhh0` |
| 13 | `1_YyxJ2pmcVnU8CsYUNO-DTMOOTf2WGRk` |
| 14 | `1oTm-6DmBWipbP8tNe04BZqTCVDYzgEYA` |
| 15 | `1G6RYfsq4g1DcWZttXcwN8CDN2wPxoeYW` |
| 16 | `1seKK7_x7_wkxPfOEAoy_GjRNvw0M-uLT` |

---

## §5. Tipografia (arquivos)

> **Pasta:** [Tipografia](https://drive.google.com/drive/folders/1XQ2Sw51ZPxmNkArZDTp4Egt7P8Drhyrk)

| Arquivo | ID Drive |
|---|---|
| `SF-Pro-Variable-Official.ttf` | `1SDXY_sNrpM9wMxQ5F2_IHq_boVz8jXoB` |
| `SF-Pro-Italic-Variable-Official.ttf` | `1wuCfL7hwMpOvGJgZwxSyr-NPXMDfxaaL` |

---

## §6. Posicionamento do logo

- **Anúncios**: Logo no topo esquerdo (x: 60-84px, y: 48-93px) ou como badge/grupo decorativo
- **Stories**: Logo no topo esquerdo ou centralizado no topo
- **Slides de encerramento**: Logo vertical centralizado

---

## §7. Como baixar (curl + base64 pra Plugin API)

```bash
# Logo colorido horizontal pra fundo escuro
curl -sLk "https://drive.google.com/uc?export=download&id=1zdIiaQedxsWH0IJqmGKUSJPZ8lb16siY" -o /tmp/logo_metta.png

# Pra Plugin API (Read precisa de path Windows)
cp /tmp/logo_metta.png C:/tmp/logo_metta.png
base64 -w 0 /tmp/logo_metta.png > C:/tmp/logo_metta.b64
```

Embedar no Figma: ver [[figma-plugin-api]] §2.

---

## 🔗 Relacionados
- [[metta-tokens]] — paleta de cores (pra escolher o logo certo por fundo)
- [[Metta - PRD Identidade Visual]] — §2 (estrutura do logo) + §6.4 (efeitos proibidos)
- [[figma-plugin-api]] — embedar logo no Figma via Plugin
