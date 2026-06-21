# Inventário completo — plugin-metta-ads → ad-generator

Tudo que o plugin tem, cruzado com o que já trouxemos, o que fizemos ALÉM dele, e o
que ainda dá pra trazer. Verificado no código (grep), não de memória.

## ✅ Já trazido do plugin
| Conceito do plugin | Onde ficou aqui |
|---|---|
| Same-designer test (crítico olha referência do banco) | `api/_critic.py` |
| Anti-slop (16 itens) | `content/direcao-arte/anti-slop.md` + crítico |
| `no_invented_text` + copy literal byte-a-byte | `api/_qa.py` (por sequência de palavras, brand-aware) |
| Modos de falha do gpt-image (mãos/texto/faces/UI) | skill 04 + `_art_director.NEG_MODEL_FAILS` |
| Banco como referência (F1 — consulta visual) | `_critic.pick_reference` |
| feedback → regeneração | `api/_autogen.py` |
| 3 papéis (compõe ≠ aprova) | art-director (compõe) + crítico/avaliador (julga) |
| Modo B (ideia → copy proposta) | `api/_copywriter.py` (ancorada no ICP/voz/método) |
| Entrada no banco (F8) | `api/_bank.py` (construído, gate de aprovação) |

## 🚀 Além do plugin (nossas extensões — NÃO vieram dele)
> A **pontuação** que você gostou é daqui, não do plugin. O plugin tem um crítico
> com veredito (aprovado/reprovado) + gate mecânico. Nós fomos além:
- **Nota holística 0-10 + SHIP/REVISAR/DESCARTAR** (`_evaluator.py`) — não existe no plugin.
- **Ledger de auditoria** (`_ledger.py` + `IMPROVEMENT-LEDGER.md`) — antes→depois por mudança. Não existe no plugin.
- **Loop de auto-melhoria** (`_autogen.py`) — gera→avalia→regera→guarda a melhor. O plugin tem feedback, mas não o loop fechado com nota.
- **Camada de recuperação de conhecimento** (`_knowledge.py`) — puxa ICP/voz/método/depoimento por copy. O plugin tinha um banco estático (`metta-brand`), não recuperação dirigida.
- **Inferência de ICP pela copy** (`_avatar_infer.py`) — a persona nasce do ICP automaticamente.
- **Golden set + régua de qualidade** — não existe no plugin.

## 🔜 Ainda dá pra trazer (ordenado por valor)
| Recurso do plugin | Arquivo-fonte | Valor | Por quê |
|---|---|---|---|
| **Guardrails de carrossel C1–C8** | `serie-rules.md` + gate `--serie` | **alto** | Fazemos carrossel e NÃO temos coerência serial (capa não-tipográfica, último=CTA, paleta travada, anti-repetição, motivos). |
| **Refinamento A↔B do prompt de imagem** | `briefer-propositor` + `briefer-critico` | **alto** | Hoje a skill 04 escreve o prompt e gera. O plugin faz propositor↔crítico (até 5 rodadas) validando contra os limites do gpt-image ANTES de gastar geração → imagem melhor, menos desperdício. |
| **Safe-zones (margens IG)** | `metta-safe-zones.md` | **médio-alto** | Story tem topo (~220px) e base (~280px) comidos pela UI do IG. Não temos check disso → CTA/headline podem cair sob a UI. Vira guardrail no crítico/qa. |
| **2 variantes de famílias divergentes** | hard rule do director | médio-alto | 1 chamada → 2 opções genuinamente diferentes (uma DARK, uma LIGHT/YELLOW). Hoje sai 1 peça por modelo. |
| **Self-inspection por crops** | `designer-ad` (sips) | médio | Recortar CTA/rosto/safe-zone e inspecionar antes de aprovar (pega corte de borda). |
| **Whitelist interativa** | `validation-gate.md` | baixo-médio | Já temos `copy.whitelist`; falta perguntar ao user quando aparece texto-chrome novo. |
| **Avisos de catálogo do banco** | `banco.md` §5 | baixo | Sinalizar peças com mismatch nome↔render / só-webp no nosso banco. |

## Veredito
Os **conceitos** do plugin já estão quase todos aqui, e em avaliação/auto-melhoria/
conhecimento **passamos do plugin**. O que falta é mais "mecânica de produção":
carrossel (C1–C8), o bate-bola A↔B do prompt de imagem, safe-zones e variantes
divergentes. Nenhum é bloqueante; são ganhos incrementais de qualidade/robustez.
