"""Unit tests for src/knowledge_loader.py -- the base used by the Skill de
Validação (api/copy-agent.py), separada do KnowledgeBase de generator.py mas
apontando pros mesmos arquivos de marca. Run with:

    cd agente-copy && python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.knowledge_loader import (  # noqa: E402
    SHARED_KNOWLEDGE_FILES,
    load_knowledge_for_brand,
)


class LoadKnowledgeForBrandTests(unittest.TestCase):
    def test_metta_includes_shared_and_brand_specific_files(self):
        docs = load_knowledge_for_brand("metta")
        for filename in SHARED_KNOWLEDGE_FILES:
            self.assertIn(filename, docs)
        self.assertIn("tom-de-voz-metta.md", docs)
        self.assertIn("SKILLMETTACOPY.md", docs)

    def test_tiago_includes_shared_and_brand_specific_files(self):
        docs = load_knowledge_for_brand("tiago")
        for filename in SHARED_KNOWLEDGE_FILES:
            self.assertIn(filename, docs)
        self.assertIn("tom-de-voz-tiago.md", docs)
        self.assertIn("SKILLTIAGOCOPY.md", docs)

    def test_tiago_skips_missing_mito_fundador_without_crashing(self):
        # mito-fundador-tiago.md ainda não existe (Fase 2, combinado deixar
        # pra depois) -- deve ser pulado silenciosamente, nunca lançar.
        docs = load_knowledge_for_brand("tiago")
        self.assertNotIn("mito-fundador-tiago.md", docs)

    def test_unknown_brand_returns_only_shared_files(self):
        docs = load_knowledge_for_brand("marca-inexistente")
        self.assertEqual(set(docs), set(SHARED_KNOWLEDGE_FILES))


if __name__ == "__main__":
    unittest.main()
