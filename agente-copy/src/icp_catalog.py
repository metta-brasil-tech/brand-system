"""Catálogo dos segmentos de ICP (Ideal Customer Profile), extraído dos
documentos ICP_Estrategico_Mentoria_V2.md, ICP_Secundario_Servicos.md e
ICP_Secundario_Varejo.md.

Exposto como lista de seleção para a pergunta-base "Qual o ICP?" -- em vez de
texto livre, a entrevista (CLI ou a UI web do brandsystem) oferece estes
segmentos nomeados, e o valor que percorre o Brief é o `id` (não o `label`).

NÃO confundir com a chave `icps` de brand-system/data/applications-index.json
(acelera/elite/premium/exclusive) -- aquilo é uma taxonomia de tier de
produto/preço, sem relação com os segmentos de comprador listados aqui.
"""
from __future__ import annotations

ICP_CATALOG: list[dict[str, str]] = [
    {
        "id": "mentoria-estrategica",
        "label": "Empresário em Ponto de Inflexão (Mentoria Estratégica)",
    },
    {"id": "servicos-saude", "label": "Serviços — Saúde"},
    {"id": "servicos-estetica-beleza", "label": "Serviços — Estética e Beleza"},
    {"id": "servicos-fitness", "label": "Serviços — Fitness"},
    {"id": "servicos-pet-outros", "label": "Serviços — Pet e Outros"},
    {"id": "varejo-moda-calcados", "label": "Varejo — Moda e Calçados"},
    {"id": "varejo-construcao-reforma-lar", "label": "Varejo — Construção, Reforma e Lar"},
    {"id": "varejo-oticas", "label": "Varejo — Óticas"},
    {"id": "varejo-farmacias", "label": "Varejo — Farmácias"},
]

# Segmento -> documento de ICP que embasa a geração (v5.1 secao 14: "escreve
# embebido de ICP"). Mapeamento à parte de ICP_CATALOG (em vez de um campo
# "file" em cada entrada) porque test_icp_catalog.py trava a forma de
# ICP_CATALOG como {id, label} apenas -- essa é a extensão aditiva.
ICP_KNOWLEDGE_FILES: dict[str, str] = {
    "mentoria-estrategica": "ICP_Estrategico_Mentoria_V2.md",
    "servicos-saude": "ICP_Secundario_Servicos.md",
    "servicos-estetica-beleza": "ICP_Secundario_Servicos.md",
    "servicos-fitness": "ICP_Secundario_Servicos.md",
    "servicos-pet-outros": "ICP_Secundario_Servicos.md",
    "varejo-moda-calcados": "ICP_Secundario_Varejo.md",
    "varejo-construcao-reforma-lar": "ICP_Secundario_Varejo.md",
    "varejo-oticas": "ICP_Secundario_Varejo.md",
    "varejo-farmacias": "ICP_Secundario_Varejo.md",
}


def icp_knowledge_file(icp_id: str) -> str | None:
    """Nome do arquivo ICP_*.md do segmento, ou None se o id não veio do
    catálogo (texto livre legado ou id desconhecido)."""
    return ICP_KNOWLEDGE_FILES.get(icp_id)
