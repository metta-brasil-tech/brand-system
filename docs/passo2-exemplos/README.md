# Passo 2 — ICP no pensador (exemplos reais)

Demonstração do passo 2 do roadmap vision-first: ligar a camada de conhecimento
(`api/_knowledge.py`) + o avatar do ICP **dentro do diretor de arte (o pensador)**
E **dentro da skill 04 (o escritor do prompt de imagem)**. Antes, a geração
decidia persona/cena com input pobre → "use uma pessoa/cena genérica".

Mesma copy nos dois exemplos (Metta · modelo `A-headline-foto-dark` · `gpt-image-2`):

> **Headline:** Sua operação tem método ou tem sorte?
> **Subhead:** Quando a gestão tem ritmo, a próxima venda é previsível.
> **CTA:** Aplique para a mentoria

## A progressão (o que mudou)

| Estágio | Cena que o diretor escolheu | Por quê |
|---|---|---|
| **Antes** (código antigo, ICP fora do pipeline) | "modern meeting room, two women and one man" | Sem ICP, recaía na heurística genérica |
| **`01-sem-avatar.png`** (ICP ligado, sem avatar) | `dono-no-chão-de-loja` — store owner, homem brasileiro, relatório de vendas | Só o **ICP** (Empresário, Varejo/Serviço) já ancora a cena no decisor real |
| **`02-com-avatar-farmacia.png`** (ICP + avatar `varejo-farmacia` / `tecnico-virou-empresario`) | `pharmacy-owner` — mulher brasileira, tablet com dashboard, **chão de farmácia** | O **avatar** afia o segmento + ambiente; paridade de gênero alterna o gênero |

## O que provar olhando as imagens

- **`01-sem-avatar.png`** — empresário brasileiro em ambiente corporativo, segurando
  um relatório. Editorial dark, amarelo seletivo em "MÉTODO/SORTE?". Já NÃO é a
  sala de reunião genérica: o ICP puxou "dono de varejo/serviço".
- **`02-com-avatar-farmacia.png`** — proprietária em pé no **chão de farmácia**
  (prateleiras de remédio desfocadas atrás), tablet com o dashboard. O ambiente do
  avatar chegou até a imagem final.

Em ambas: logo Metta, eyebrow "INTELIGÊNCIA COMERCIAL", Zalando Sans Expanded,
copy literal preservada — identidade da marca intacta.

## Como reproduzir

```bash
set -a; . engine/.env; set +a
export BRAND_KNOWLEDGE_PATH="$PWD/engine/brand-knowledge" ARTIFACTS_DIR="$PWD/artifacts"

# sem avatar (ICP ancora sozinho):
python3.11 cli.py --model A-headline-foto-dark \
  --headline "Sua operação tem método ou tem sorte?" \
  --subhead "Quando a gestão tem ritmo, a próxima venda é previsível." \
  --cta "Aplique para a mentoria" --image generate --preset fotorrealista --no-vision-qa \
  --out out/passo2-exemplos/01-sem-avatar

# com avatar (afia segmento + ambiente):
python3.11 cli.py --model A-headline-foto-dark \
  --headline "Sua operação tem método ou tem sorte?" \
  --subhead "Quando a gestão tem ritmo, a próxima venda é previsível." \
  --cta "Aplique para a mentoria" --image generate --preset fotorrealista --no-vision-qa \
  --avatar-segment varejo-farmacia --avatar-variant tecnico-virou-empresario \
  --out out/passo2-exemplos/02-com-avatar-farmacia
```

> As flags `--avatar-segment` / `--avatar-variant` são novas (parte do passo 2).
> `out/` é gitignorado; estas imagens foram copiadas pra cá pra ficarem versionadas.
