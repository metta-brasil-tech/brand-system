"""Unit tests for src/generator.py.

No network calls, no Anthropic credits spent: client.messages.create is
always a MagicMock returning tests/_fakes.py doubles. Run with:

    cd agente-copy && python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("COPY_AGENT_RAG", "0")  # RAG selection is pure text
# processing (no network) but disabling it keeps these tests independent of
# how retrieval.select_pool happens to score real knowledge-base content.

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import generator as g  # noqa: E402
from src.interview import Brand, Brief, CopyType, EmotionalAxis, Platform  # noqa: E402

from tests._fakes import empty_message, json_message, text_message  # noqa: E402


DRAFT = {
    "hook": "Você não lidera a sua empresa.",
    "corpo": "Corpo de teste, sem travessão real.",
    "cta": "Comente TESTE.",
    "hook_variations": ["Variação A", "Variação B", "Variação C"],
    "content_pillar": "pilar de teste",
    "target_icp": "dono de teste",
    "descricao": "Legenda de teste.",
}

APPROVED_JUDGMENT = {"approved": True, "feedback": "", "piece": DRAFT}


def _make_brief(brand, copy_type=CopyType.REELS, include_case=True):
    return Brief(
        brand=brand,
        copy_type=copy_type,
        objective="objetivo de teste",
        icp="icp de teste",
        angle_choice="ângulo de teste",
        emotional_axis=EmotionalAxis.DOR,
        cta="cta de teste",
        platform=Platform.INSTAGRAM,
        include_case=include_case,
    )


class RemoveTravessaoTests(unittest.TestCase):
    def test_removes_em_dash_mid_sentence(self):
        self.assertEqual(
            g._remove_travessao("O método funciona — sempre."),
            "O método funciona, sempre.",
        )

    def test_removes_multiple_em_dashes_in_same_text(self):
        self.assertEqual(
            g._remove_travessao("Você para — e pensa — depois age."),
            "Você para, e pensa, depois age.",
        )

    def test_preserves_en_dash_in_numeric_ranges(self):
        # Regra explícita do Nathan: en-dash (–) segura faixa numérica
        # legítima e não pode ser tocado, só o em-dash (—) é proibido.
        text = "R$ 200k–600k por mês, 90–180 caracteres"
        self.assertEqual(g._remove_travessao(text), text)

    def test_no_dash_returns_same_string(self):
        text = "Frase comum sem nenhum traço especial."
        self.assertEqual(g._remove_travessao(text), text)

    def test_dash_at_start_of_line_is_stripped_not_left_as_comma(self):
        result = g._remove_travessao("— Filho, o que você quer fazer?")
        self.assertFalse(result.startswith(","))
        self.assertNotIn("—", result)


class SanitizeJsonTextTests(unittest.TestCase):
    def test_escapes_raw_newline_inside_string_value(self):
        raw = '{"corpo": "linha um\nlinha dois"}'
        data = json.loads(g._sanitize_json_text(raw))
        self.assertEqual(data["corpo"], "linha um\nlinha dois")

    def test_leaves_structural_json_parseable(self):
        raw = '{\n  "a": "b"\n}'
        self.assertEqual(json.loads(g._sanitize_json_text(raw)), {"a": "b"})


class ExtractJsonTests(unittest.TestCase):
    def test_extracts_json_surrounded_by_prose(self):
        msg = json_message({"ok": True})
        msg.content[0].text = "Aqui está:\n" + msg.content[0].text + "\nFim."
        self.assertEqual(g._extract_json(msg, stage="test"), {"ok": True})

    def test_raises_on_missing_text_block(self):
        with self.assertRaises(RuntimeError):
            g._text_of(empty_message(), stage="test")


class KnowledgeBaseTests(unittest.TestCase):
    def test_metta_loads_all_files_listed_in_brand_files(self):
        kb = g.KnowledgeBase(Brand.METTA)
        for filename in g._BRAND_FILES["metta"]:
            self.assertIn(filename, kb._documents)
            self.assertTrue(kb._documents[filename].strip(), filename)

    def test_tiago_loads_all_files_listed_in_brand_files(self):
        kb = g.KnowledgeBase(Brand.TIAGO)
        for filename in g._BRAND_FILES["tiago"]:
            self.assertIn(filename, kb._documents)
            self.assertTrue(kb._documents[filename].strip(), filename)

    def test_unsupported_brand_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            g.KnowledgeBase("golias")

    def test_document_lookup_matches_loaded_content(self):
        kb = g.KnowledgeBase(Brand.TIAGO)
        self.assertEqual(
            kb.document("SKILLTIAGOCOPY.md"), kb._documents["SKILLTIAGOCOPY.md"]
        )


class BuildSystemPromptTests(unittest.TestCase):
    def test_metta_prompt_is_institutional_voice(self):
        prompt = g._build_system_prompt(Brand.METTA, "carrossel")
        self.assertIn("INSTITUCIONAL da Metta", prompt)
        self.assertIn("travessão", prompt)

    def test_tiago_prompt_is_personal_voice(self):
        prompt = g._build_system_prompt(Brand.TIAGO, "reels")
        self.assertIn("primeira pessoa", prompt)
        self.assertIn("PROTAGONISTA é o leitor", prompt)
        self.assertIn("travessão", prompt)

    def test_unsupported_brand_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            g._build_system_prompt("golias", "reels")

    def test_anti_ia_rule_is_shared_not_duplicated(self):
        # Guarda contra o texto da regra "sem travessão" divergir entre as
        # duas marcas ao longo do tempo -- ambas devem referenciar a MESMA
        # constante, não uma cópia colada à mão.
        metta = g._build_system_prompt(Brand.METTA, "reels")
        tiago = g._build_system_prompt(Brand.TIAGO, "reels")
        self.assertIn(g._ANTI_IA_RULE, metta)
        self.assertIn(g._ANTI_IA_RULE, tiago)


class BuildJudgmentPromptTests(unittest.TestCase):
    def test_metta_pulls_metta_voice_and_skill(self):
        kb = g.KnowledgeBase(Brand.METTA)
        prompt = g._build_judgment_prompt(_make_brief(Brand.METTA), kb, DRAFT)
        self.assertIn("SKILLMETTACOPY.md", prompt)

    def test_tiago_pulls_tiago_voice_and_skill(self):
        # Regressão do bug corrigido no PR #3: document('tom-de-voz-metta.md')
        # fixo aqui lançaria KeyError, pois este KnowledgeBase só tem os
        # arquivos do Tiago carregados. Não lançar já é o teste.
        kb = g.KnowledgeBase(Brand.TIAGO)
        prompt = g._build_judgment_prompt(_make_brief(Brand.TIAGO), kb, DRAFT)
        self.assertIn("SKILLTIAGOCOPY.md", prompt)
        self.assertIn("PROTAGONISTA é o leitor", prompt)

    def test_skip_case_note_present_when_include_case_false(self):
        kb = g.KnowledgeBase(Brand.METTA)
        brief = _make_brief(Brand.METTA, include_case=False)
        prompt = g._build_judgment_prompt(brief, kb, DRAFT)
        self.assertIn("NÃO reprove por falta de case", prompt)


class CopyGeneratorGenerateTests(unittest.TestCase):
    @staticmethod
    def _client_returning(*messages):
        client = MagicMock()
        client.messages.create.side_effect = list(messages)
        return client

    def test_metta_end_to_end_approves_on_first_judgment(self):
        client = self._client_returning(
            json_message(DRAFT),  # _draft_structural
            json_message(APPROVED_JUDGMENT),  # _judge
        )
        brief = _make_brief(Brand.METTA, copy_type=CopyType.POST_UNICO)
        result = g.CopyGenerator(client).generate(brief, skip_linkedin=True)
        self.assertEqual(result.hook, DRAFT["hook"])
        self.assertEqual(result.revision_notes, [])
        self.assertEqual(client.messages.create.call_count, 2)

    def test_tiago_end_to_end_does_not_raise(self):
        # Regressão: brand=tiago lançava NotImplementedError incondicional
        # dentro de generate() antes do PR #3 (4 guards espalhados pelo
        # arquivo). Não lançar já é o teste.
        client = self._client_returning(
            json_message(DRAFT),
            json_message(APPROVED_JUDGMENT),
        )
        brief = _make_brief(Brand.TIAGO, copy_type=CopyType.REELS)
        result = g.CopyGenerator(client).generate(brief, skip_linkedin=True)
        self.assertEqual(result.hook, DRAFT["hook"])

    def test_removes_em_dash_from_every_output_field(self):
        draft_with_dash = dict(DRAFT, hook="Hook com travessão — no meio.")
        judgment_with_dash = {
            "approved": True,
            "feedback": "",
            "piece": draft_with_dash,
        }
        client = self._client_returning(
            json_message(draft_with_dash),
            json_message(judgment_with_dash),
        )
        result = g.CopyGenerator(client).generate(
            _make_brief(Brand.METTA), skip_linkedin=True
        )
        self.assertNotIn("—", result.hook)
        self.assertNotIn("—", result.full_text)

    def test_loops_on_rejection_then_approves_and_keeps_feedback(self):
        rejected = {
            "approved": False,
            "feedback": "reescreva o hook",
            "piece": DRAFT,
        }
        client = self._client_returning(
            json_message(DRAFT),  # draft
            json_message(rejected),  # judge #1: reprova
            json_message(APPROVED_JUDGMENT),  # judge #2: aprova
        )
        result = g.CopyGenerator(client).generate(
            _make_brief(Brand.METTA), skip_linkedin=True
        )
        self.assertEqual(result.revision_notes, ["reescreva o hook"])
        self.assertEqual(client.messages.create.call_count, 3)


class AdaptLinkedinPublicMethodTests(unittest.TestCase):
    def test_public_adapt_linkedin_removes_em_dash(self):
        # Regressão do primeiro bug corrigido nesta frente de trabalho:
        # adapt_linkedin() (público, roda FORA de generate()) não passava
        # por _remove_travessao -- só a adaptação interna ao generate()
        # passava. Corrigido; este teste trava o comportamento.
        client = MagicMock()
        client.messages.create.return_value = text_message(
            "Versão LinkedIn com travessão — no meio da frase."
        )
        brief = _make_brief(Brand.METTA, copy_type=CopyType.POST_UNICO)
        adapted = g.CopyGenerator(client).adapt_linkedin(brief, DRAFT)
        self.assertNotIn("—", adapted)


if __name__ == "__main__":
    unittest.main()
