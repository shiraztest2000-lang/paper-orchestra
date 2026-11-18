import json
import os
import tempfile
import unittest
from unittest.mock import patch

from utils.proposal_builder import _parse_json, generate_proposal
from utils.proposal_export import export_proposal_docx, proposal_markdown


class ProposalBuilderTests(unittest.TestCase):
    def test_parse_json_accepts_markdown_fence(self):
        fence = chr(96) * 3
        self.assertEqual(_parse_json(fence + 'json\n{"title_fa":"عنوان"}\n' + fence), {"title_fa": "عنوان"})

    @patch("utils.gemini_utils.call_gemini_with_text_prompt")
    @patch("utils.provider_config.get_provider", return_value="gemini")
    @patch("utils.literature_search.search_academic_candidates")
    def test_generation_uses_search_results_and_user_metadata(self, search, provider, call):
        search.return_value = [{
            "title": "A Real Study", "year": 2025, "authors": ["A. Author"],
            "venue": "Journal", "doi": "10.1000/test", "url": "https://doi.org/10.1000/test",
            "sources": ["Crossref"], "open_access": False,
        }]
        payload = {
            "title_fa": "عنوان پیشنهادی", "title_en": "Suggested title",
            "problem_statement": "مسئله پژوهش [1]", "literature_review": "پیشینه [1]",
            "objectives": ["هدف اول"], "timeline": [{"stage": "مرور", "start_month": "1", "end_month": "2"}],
            "variables": [],
        }
        call.return_value = {"raw_response": json.dumps(payload, ensure_ascii=False)}
        with patch.dict(os.environ, {"SHZ_LLM_MODEL": "test-model"}):
            data, refs = generate_proposal(
                "موضوع آزمون", {"student": "دانشجو", "field": "روانشناسی"},
                cutoff_date="2026-11",
            )
        self.assertEqual(data["student"], "دانشجو")
        self.assertEqual(data["title_fa"], "عنوان پیشنهادی")
        self.assertEqual(data["references"][0]["title"], "A Real Study")
        self.assertEqual(data["timeline"][0]["stage"], "مرور")
        self.assertEqual(len(refs), 1)
        self.assertIn("[1]", data["literature_review"])

    def test_docx_and_markdown_exports(self):
        data = {
            "title_fa": "عنوان آزمایشی", "title_en": "Test title",
            "problem_statement": "بیان مسئله", "literature_review": "پیشینه [1]",
            "references": [{"id": 1, "title": "A Real Study", "year": 2025,
                            "authors": ["A. Author"], "venue": "Journal",
                            "doi": "10.1000/test", "url": "https://doi.org/10.1000/test"}],
            "timeline": [], "variables": [],
        }
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "proposal.docx")
            export_proposal_docx(data, path)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 1000)
        self.assertIn("A Real Study", proposal_markdown(data))


if __name__ == "__main__":
    unittest.main()
