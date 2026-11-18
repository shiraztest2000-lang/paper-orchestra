import unittest
from unittest.mock import Mock, patch

from utils.literature_search import search_academic_candidates


class FreeLiteratureSearchTests(unittest.TestCase):
    @patch("utils.literature_search.requests.get")
    def test_europe_pmc_and_crossref_merge_without_api_keys(self, get):
        europe = Mock()
        europe.raise_for_status.return_value = None
        europe.json.return_value = {
            "resultList": {
                "result": [{
                    "title": "A Recent Open Science Study",
                    "firstPublicationDate": "2025-04-10",
                    "pmcid": "PMC123456",
                    "doi": "10.1000/example",
                }]
            }
        }
        crossref = Mock()
        crossref.raise_for_status.return_value = None
        crossref.json.return_value = {
            "message": {
                "items": [{
                    "title": ["A Recent Open Science Study"],
                    "DOI": "10.1000/example",
                    "published": {"date-parts": [[2025, 4, 10]]},
                }]
            }
        }
        get.side_effect = [europe, crossref]

        results = search_academic_candidates(
            "open science", cutoff_date="2025-12", limit=10,
            sources=["europepmc", "crossref"],
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["year"], 2025)
        self.assertEqual(set(results[0]["sources"]), {"Europe PMC", "Crossref"})
        self.assertTrue(results[0]["url"].startswith("https://europepmc.org/"))
        self.assertNotIn("api_key", get.call_args_list[0].kwargs.get("params", {}))
        self.assertNotIn("api_key", get.call_args_list[1].kwargs.get("params", {}))

    @patch("utils.literature_search.requests.get")
    def test_cutoff_excludes_future_records(self, get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "resultList": {
                "result": [
                    {"title": "Older Study", "pubYear": "2024", "pmid": "123"},
                    {"title": "Future Study", "pubYear": "2027", "pmid": "456"},
                ]
            }
        }
        get.return_value = response
        results = search_academic_candidates(
            "study", cutoff_date="2025-11", sources=["europepmc"]
        )
        self.assertEqual([item["title"] for item in results], ["Older Study"])

    @patch("utils.literature_search.requests.get")
    def test_arxiv_records_are_parsed_from_atom_feed(self, get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>https://arxiv.org/abs/2601.01234</id>
            <published>2026-01-02T00:00:00Z</published>
            <title>  A New Machine Learning Method  </title>
          </entry>
        </feed>"""
        get.return_value = response
        results = search_academic_candidates(
            "machine learning", cutoff_date="2026-11", sources=["arxiv"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "A New Machine Learning Method")
        self.assertEqual(results[0]["year"], 2026)
        self.assertEqual(results[0]["url"], "https://arxiv.org/abs/2601.01234")


if __name__ == "__main__":
    unittest.main()
