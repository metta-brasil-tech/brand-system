"""Loads the repo-root markdown knowledge base for a given brand.

Per Agente_Copy_Criacao_v5.1_CORRIGIDO.md secao 12 and Documento_Mestre_Projeto_v2.md
secao 2/3.1: the knowledge base is versioned in the repo (no separate store),
read fresh at the start of each cycle, with explicitly no chunking or
embeddings/RAG.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files shared by both brands (ICP, avatar, glossario, mito-fundador, etc.).
SHARED_KNOWLEDGE_FILES = [
    "ICP_Estrategico_Mentoria_V2.md",
    "ICP_Secundario_Servicos.md",
    "ICP_Secundario_Varejo.md",
    "avatar.md",
    "glossario-2.md",
    "posicionamento.md",
    "oferta.md",
    "provas.md",
    "Mapa_Arquitetura_Base.md",
    "Base_Editorial_Canonica.md",
]

# Files specific to a single brand's voice/mythos.
BRAND_KNOWLEDGE_FILES = {
    "metta": [
        "tom-de-voz-metta.md",
        "mito-fundador-metta.md",
        # A mesma skill que generator.py usa pra escrever (_BRAND_FILES) --
        # carregada aqui pra Skill de Validacao reaplicar em modo leitura
        # sobre a peca ja pronta (src.validator.run_skill_de_validacao).
        "SKILLMETTACOPY.md",
    ],
    "tiago": [
        "tom-de-voz-tiago.md",
        # mito-fundador-tiago.md ainda nao existe (Fase 2, pendente); fica
        # listado pra carregar automaticamente assim que for criado --
        # load_knowledge_files pula arquivos ausentes sem quebrar.
        "mito-fundador-tiago.md",
        # A mesma skill que generator.py usa pra escrever a voz Tiago
        # (_BRAND_FILES["tiago"]) -- carregada aqui pra Skill de Validacao
        # reaplicar em modo leitura sobre a peca ja pronta.
        "SKILLTIAGOCOPY.md",
    ],
}


def load_knowledge_files(filenames: list[str]) -> dict[str, str]:
    """Read each filename (relative to repo root) and return {filename: content}.

    Missing files are silently skipped -- some brand-specific files (e.g.
    tom-de-voz-tiago.md) are known to not exist yet per the project docs.
    """
    result: dict[str, str] = {}
    for filename in filenames:
        path = REPO_ROOT / filename
        if path.is_file():
            result[filename] = path.read_text(encoding="utf-8")
    return result


def load_knowledge_for_brand(brand: str) -> dict[str, str]:
    """Load the shared knowledge base plus the given brand's specific files.

    `brand` is expected to be "metta" or "tiago" (matches src.interview.Brand).
    """
    filenames = SHARED_KNOWLEDGE_FILES + BRAND_KNOWLEDGE_FILES.get(brand, [])
    return load_knowledge_files(filenames)
