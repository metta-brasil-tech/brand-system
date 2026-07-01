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
