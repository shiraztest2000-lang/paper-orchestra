import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import secure_store


class SecureStoreTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        self.backend = types.SimpleNamespace(
            get_password=lambda service, name: self.values.get((service, name)),
            set_password=lambda service, name, value: self.values.__setitem__((service, name), value),
        )
        self.patcher = patch.object(secure_store, "_backend", return_value=self.backend)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_round_trip_credentials(self):
        secure_store.save_secure_secrets({"GEMINI_API_KEY": "secret-value"})
        self.assertEqual(secure_store.load_secure_secrets()["GEMINI_API_KEY"], "secret-value")
        self.assertNotIn("OPENAI_API_KEY", secure_store.load_secure_secrets())

    def test_legacy_env_migration_removes_plaintext_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "SHZ_LLM_PROVIDER=gemini\nGEMINI_API_KEY=legacy-secret\nSEMANTIC_SCHOLAR_API_KEY=scholar-secret\n",
                encoding="utf-8",
            )
            self.assertTrue(secure_store.migrate_legacy_env(path))
            rewritten = path.read_text(encoding="utf-8")
            self.assertIn("SHZ_LLM_PROVIDER=gemini", rewritten)
            self.assertNotIn("legacy-secret", rewritten)
            self.assertNotIn("scholar-secret", rewritten)
            stored = secure_store.load_secure_secrets()
            self.assertEqual(stored["GEMINI_API_KEY"], "legacy-secret")
            self.assertEqual(stored["SEMANTIC_SCHOLAR_API_KEY"], "scholar-secret")

    def test_migration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("SHZ_LLM_MODEL=test-model\n", encoding="utf-8")
            self.assertFalse(secure_store.migrate_legacy_env(path))


if __name__ == "__main__":
    unittest.main()
