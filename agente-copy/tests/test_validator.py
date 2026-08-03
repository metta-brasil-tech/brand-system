"""Unit tests for src/validator.py.

Mocked client.messages.create -- no network calls, no Anthropic credits
spent. Run with: cd agente-copy && python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import validator as v  # noqa: E402

from tests._fakes import empty_message, json_message  # noqa: E402


PIECE = {
    "full_text": "Peça de teste completa, hook + corpo + cta.",
    "hook": "hook de teste",
    "corpo": "corpo de teste",
    "cta": "cta de teste",
}


class CheckIcpFitTests(unittest.TestCase):
    def test_parses_passed_and_reasoning(self):
        client = MagicMock()
        client.messages.create.return_value = json_message(
            {"passed": True, "reasoning": "Faz sentido pro ICP descrito."}
        )
        result = v.check_icp_fit(client, PIECE, icp="dono de PME")
        self.assertTrue(result.passed)
        self.assertEqual(result.reasoning, "Faz sentido pro ICP descrito.")


class CheckGrammarToneTests(unittest.TestCase):
    def test_parses_all_four_fields(self):
        client = MagicMock()
        client.messages.create.return_value = json_message(
            {
                "passed": False,
                "correcao": "sem erros",
                "fluencia": "boa",
                "aderencia_tom": "quebra o tom em dois pontos",
                "reasoning": "reprovado por tom",
            }
        )
        result = v.check_grammar_tone(client, PIECE, tom_de_voz="voz de teste")
        self.assertFalse(result.passed)
        self.assertEqual(result.aderencia_tom, "quebra o tom em dois pontos")


class RunSecondEvaluatorTests(unittest.TestCase):
    def test_parses_approved_and_feedback(self):
        client = MagicMock()
        client.messages.create.return_value = json_message(
            {"approved": True, "feedback": "pronto pra publicar"}
        )
        result = v.run_second_evaluator(client, PIECE, tom_de_voz="voz de teste")
        self.assertTrue(result.approved)
        self.assertEqual(result.feedback, "pronto pra publicar")


class RunSkillDeValidacaoTests(unittest.TestCase):
    def test_returns_stub_and_skips_api_call_when_skill_content_empty(self):
        client = MagicMock()
        result = v.run_skill_de_validacao(client, PIECE, skill_content="")
        self.assertTrue(result.is_stub)
        self.assertIsNone(result.score)
        client.messages.create.assert_not_called()

    def test_returns_real_score_when_skill_content_present(self):
        client = MagicMock()
        client.messages.create.return_value = json_message(
            {"score": 8.5, "note": "cumpre o checklist item a item"}
        )
        result = v.run_skill_de_validacao(
            client, PIECE, skill_content="skill de teste não vazia"
        )
        self.assertFalse(result.is_stub)
        self.assertEqual(result.score, 8.5)


class TextOfTests(unittest.TestCase):
    def test_raises_runtime_error_without_text_block(self):
        with self.assertRaises(RuntimeError):
            v._text_of(empty_message(), stage="test")


if __name__ == "__main__":
    unittest.main()
