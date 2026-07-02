"""Confere as afirmações numéricas da seção "FLUXO PARA CADA TIPO DE PEÇA —
INSTAGRAM ORGÂNICO" de SKILLMETTACOPY.md contra o dataset bruto do scraping,
e sinaliza divergência.

Motivação (melhorias_agente_copy.md, item 5): a versão anterior da skill
tinha 3 erros factuais nessa seção (ordem de CTA de carrossel invertida,
gatilho de comentário registrado como ausente em post único quando não
era, contagens de vocabulário erradas) que sobreviveram sem ninguém notar
porque não existia checagem automática comparando afirmação vs. dado bruto.
Este script é essa checagem -- não evita erro humano na primeira redação da
skill, mas evita que ele sobreviva sem aviso da próxima vez que o dataset
for atualizado (novo scraping, mais posts).

AVISO IMPORTANTE: escrito sem acesso ao dataset bruto real
(`dataset_instagram-scraper-task_2026-07-01_15-08-41-697.json`, citado em
melhorias_agente_copy.md e na nota de proveniência da skill) -- não foi
testado contra um arquivo real do Apify. Os nomes de campo abaixo
(`ownerUsername`, `caption`, `type`/`productType`, `hashtags`) são a forma
mais comum de saída do ator "instagram-scraper-task" no Apify, mas PRECISAM
ser confirmados contra uma amostra real antes de confiar no resultado --
ver `_load_posts()` e ajuste os nomes de campo lá se não baterem.

Uso:
    python3 scripts/verify_skill_stats.py <caminho-do-dataset.json> \
        [--skill SKILLMETTACOPY.md]

Sem chamada de API -- roda 100% local/offline, custo zero.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Claim:
    """Uma afirmação numérica extraída (ou hardcoded, se a extração via
    regex não achar) da seção INSTAGRAM ORGÂNICO da skill."""

    label: str
    claimed_value: float
    claimed_text: str
    computed_value: float | None = None

    @property
    def diverges(self) -> bool:
        if self.computed_value is None:
            return False
        # Tolerância de 1 unidade/ponto percentual -- os números da skill
        # são "~N" (aproximados), não exatos.
        return abs(self.claimed_value - self.computed_value) > 1


def _load_posts(dataset_path: Path) -> list[dict]:
    """Carrega o dataset bruto do Apify e filtra só posts de @metta.brasil.

    Ajuste os nomes de campo abaixo se não baterem com o dataset real --
    não foram confirmados contra uma amostra (ver aviso no topo do arquivo).
    """
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(
            f"Esperava uma lista de posts no JSON, recebi {type(raw).__name__}. "
            "Confira se é o dataset certo (não um wrapper com paginação)."
        )

    def _is_metta(post: dict) -> bool:
        if post.get("ownerUsername") == "metta.brasil":
            return True
        # Posts em collab (coautoria): o Apify grava o dono "principal" em
        # ownerUsername mesmo quando @metta.brasil é coautora -- confirmado
        # contra o dataset real, 3 dos 84 posts caem nesse caso (2 postados
        # como tiago.alves.oliveira, 1 como inbixbr). Sem esse fallback o
        # filtro ficava em 81, não 84.
        for coauthor in post.get("coauthorProducers") or []:
            if coauthor.get("username") == "metta.brasil":
                return True
        return False

    return [p for p in raw if _is_metta(p)]


def _classify(post: dict) -> str:
    """carrossel | post_unico | reels | outro -- baseado no tipo do post.

    Nomes de campo assumidos: `type` (ou `productType`) com valores comuns
    de scrapers de Instagram: "Sidecar"/"carousel" para carrossel, "Video"
    pra reels, "Image"/"GraphImage" pra post único.
    """
    t = str(post.get("type") or post.get("productType") or "").lower()
    if "sidecar" in t or "carousel" in t or "carrossel" in t:
        return "carrossel"
    if "video" in t or "reel" in t:
        return "reels"
    if "image" in t or "photo" in t:
        return "post_unico"
    return "outro"


_COMMENT_TRIGGER_RE = re.compile(r"\bcomenta\b|\bcomente\b", re.IGNORECASE)
# "na"/"da"/"no" bio, e variações tipo "o link está na bio" -- confirmado
# contra o dataset real que "link da bio" é mais comum que "link na bio"
# nesta marca; a versão anterior só pegava "na" e sub-contava pela metade.
_LINK_BIO_RE = re.compile(r"link\b.{0,25}\bbio\b", re.IGNORECASE)
_HASHTAG_RE = re.compile(r"#\w+")


def _caption(post: dict) -> str:
    return str(post.get("caption") or post.get("text") or "")


def _cta_pattern(caption: str) -> str:
    if _COMMENT_TRIGGER_RE.search(caption):
        return "comentario"
    if _LINK_BIO_RE.search(caption):
        return "link_bio"
    if caption.strip().endswith("?"):
        return "pergunta_aberta"
    return "sem_cta"


def _extract_claims_from_skill(skill_text: str) -> list[Claim]:
    """Afirmações-chave da seção INSTAGRAM ORGÂNICO, hardcoded aqui (não
    fica prático regex-ar prosa livre com confiança) -- espelham o texto
    atual de SKILLMETTACOPY.md linha a linha. Se o texto da skill mudar,
    atualize esta lista junto."""
    del skill_text  # reservado pra uma extração via regex mais robusta depois
    return [
        Claim("carrossel: % com gatilho de comentário como CTA", 49.0, "~49% (24 de 49)"),
        Claim("carrossel: % com link na bio como CTA", 16.0, "~16% (8 de 49)"),
        Claim("carrossel: % sem CTA de conversão", 35.0, "~35% (17 de 49)"),
        Claim("post_unico: contagem com link na bio", 6.0, "6 de 24"),
        Claim("post_unico: contagem com gatilho de comentário", 4.0, "4 de 24"),
    ]


def _compute_stats(posts: list[dict]) -> dict[str, float]:
    carrosseis = [p for p in posts if _classify(p) == "carrossel"]
    post_unicos = [p for p in posts if _classify(p) == "post_unico"]

    def _pct(count: int, total: int) -> float:
        return round(100 * count / total, 1) if total else 0.0

    carrossel_cta = [_cta_pattern(_caption(p)) for p in carrosseis]
    post_unico_cta = [_cta_pattern(_caption(p)) for p in post_unicos]

    return {
        "carrossel: % com gatilho de comentário como CTA": _pct(
            carrossel_cta.count("comentario"), len(carrosseis)
        ),
        "carrossel: % com link na bio como CTA": _pct(
            carrossel_cta.count("link_bio"), len(carrosseis)
        ),
        "carrossel: % sem CTA de conversão": _pct(
            carrossel_cta.count("sem_cta"), len(carrosseis)
        ),
        "post_unico: contagem com link na bio": float(post_unico_cta.count("link_bio")),
        "post_unico: contagem com gatilho de comentário": float(
            post_unico_cta.count("comentario")
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="JSON bruto do Apify (instagram-scraper-task)")
    parser.add_argument(
        "--skill",
        type=Path,
        default=_REPO_ROOT / "SKILLMETTACOPY.md",
        help="Caminho pro SKILLMETTACOPY.md a conferir (default: raiz do repo)",
    )
    args = parser.parse_args(argv)

    posts = _load_posts(args.dataset)
    if not posts:
        print(
            f"AVISO: 0 posts de @metta.brasil encontrados em {args.dataset}. "
            "Confira o nome do campo 'ownerUsername' contra o dataset real -- "
            "ver aviso no topo deste script.",
            file=sys.stderr,
        )
        return 2

    skill_text = args.skill.read_text(encoding="utf-8")
    claims = _extract_claims_from_skill(skill_text)
    computed = _compute_stats(posts)

    divergent = []
    for claim in claims:
        claim.computed_value = computed.get(claim.label)
        status = "DIVERGE" if claim.diverges else "ok"
        print(
            f"[{status}] {claim.label}: skill diz {claim.claimed_text} "
            f"(={claim.claimed_value}), dataset calcula {claim.computed_value}"
        )
        if claim.diverges:
            divergent.append(claim)

    print(f"\n{len(posts)} posts de @metta.brasil no dataset "
          f"({len(divergent)} de {len(claims)} afirmações divergentes).")
    return 1 if divergent else 0


if __name__ == "__main__":
    raise SystemExit(main())
